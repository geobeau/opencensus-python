# Copyright 2017, OpenCensus Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import threading
import mock

from opencensus.trace import span as span_module
from opencensus.trace.ext.threading import trace
from opencensus.trace import execution_context

class Test_threading_trace(unittest.TestCase):

    def tearDown(self):
        execution_context.clear()


    def test_trace_integration(self):
        mock_wrap_start = mock.Mock()
        mock_wrap_run = mock.Mock()
        mock_threading = mock.Mock()

        wrap_start_result = 'wrap start result'
        wrap_run_result = 'wrap run result'
        mock_wrap_start.return_value = wrap_start_result
        mock_wrap_run.return_value = wrap_run_result

        mock_start_func = mock.Mock()
        mock_run_func = mock.Mock()
        mock_start_func.__name__ = 'start'
        mock_run_func.__name__ = 'run'
        setattr(mock_threading.Thread, 'start', mock_start_func)
        setattr(mock_threading.Thread, 'run', mock_run_func)

        patch_wrap_start = mock.patch(
            'opencensus.trace.ext.threading.trace.wrap_threading_start',
            mock_wrap_start)
        patch_wrap_run = mock.patch(
            'opencensus.trace.ext.threading.trace.wrap_threading_run',
            mock_wrap_run)
        patch_threading = mock.patch(
            'opencensus.trace.ext.threading.trace.threading', mock_threading)

        with patch_wrap_start, patch_wrap_run, patch_threading:
            trace.trace_integration()

        self.assertEqual(getattr(mock_threading.Thread, 'start'),
                         wrap_start_result)
        self.assertEqual(getattr(mock_threading.Thread, 'run'),
                         wrap_run_result)

    def test_wrap_threading(self):
        global global_tracer
        mock_span = mock.Mock()
        span_id = '1234'
        mock_span.span_id = span_id
        mock_tracer = MockTracer(mock_span)
        execution_context.set_opencensus_tracer(mock_tracer)

        trace.trace_integration()

        t = threading.Thread(target=self.fake_threaded_func)
        t.start()
        t.join()
        assert isinstance(global_tracer, MockTracer)

    def fake_threaded_func(self):
        global global_tracer
        global_tracer = execution_context.get_opencensus_tracer()


class MockTracer(object):
    def __init__(self, span=None):
        self.span = span

    def current_span(self):
        return self.span

    def start_span(self):
        span = mock.Mock()
        span.attributes = {}
        span.context_tracer = mock.Mock()
        span.context_tracer.span_context = mock.Mock()
        span.context_tracer.span_context.trace_id = '123'
        span.context_tracer.span_context.span_id = '456'
        span.context_tracer.span_context.tracestate = None
        self.span = span
        return span

    def end_span(self):
        pass

    def add_attribute_to_current_span(self, key, value):
        self.span.attributes[key] = value
