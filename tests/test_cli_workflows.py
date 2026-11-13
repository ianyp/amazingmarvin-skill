import contextlib
from datetime import datetime
import io
import json
import os
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo
from test_client import Client  # establishes helper import path for standalone discovery
import marvin

class CliWorkflowTests(unittest.TestCase):
    def run_workflow(self, args, reply, instant, stdin=''):
        calls = []
        def transport(*values):
            calls.append(values)
            return reply
        class Clock:
            @staticmethod
            def now(zone): return instant.astimezone(zone)
        output = io.StringIO()
        with patch.dict(os.environ, {'MARVIN_API_TOKEN': 'synthetic'}), patch.object(marvin, 'Transport', return_value=transport), patch.object(marvin, 'datetime', Clock), patch('sys.stdin', io.StringIO(stdin)), contextlib.redirect_stdout(output):
            status = marvin.main(args)
        return status, json.loads(output.getvalue()), calls
    def test_summer_completion_offset(self):
        status, result, calls = self.run_workflow(['done', '--id', 'task1'], 'OK', datetime(2026, 7, 1, tzinfo=ZoneInfo('UTC')))
        self.assertEqual(status, 0)
        self.assertTrue(result['ok'])
        self.assertEqual(calls[0][3]['timeZoneOffset'], 60)
    def test_local_day_across_midnight(self):
        _, _, calls = self.run_workflow(['today'], [], datetime(2026, 7, 1, 23, 30, tzinfo=ZoneInfo('UTC')))
        self.assertEqual(calls[0][1], 'todayItems?date=2026-07-02')
    def test_winter_completion_offset(self):
        _, _, calls = self.run_workflow(['done', '--id', 'task1'], 'OK', datetime(2026, 11, 13, tzinfo=ZoneInfo('UTC')))
        self.assertEqual(calls[0][3]['timeZoneOffset'], 0)
    def test_capture_stdin_preserves_separate_dates(self):
        data = {'title':'Test', 'day':'2026-11-14', 'dueDate':'2026-11-20'}
        status, result, calls = self.run_workflow(['add','--input-json','-'], {'_id':'test'}, datetime(2026,11,13,tzinfo=ZoneInfo('UTC')), json.dumps(data))
        self.assertEqual(status, 0)
        self.assertEqual(calls[0][3], data)
        self.assertEqual(result['data']['_id'], 'test')
    def test_bad_json_never_calls_api(self):
        status, result, calls = self.run_workflow(['add','--input-json','-'], {}, datetime(2026,11,13,tzinfo=ZoneInfo('UTC')), 'oops')
        self.assertEqual(status, 1)
        self.assertFalse(result['ok'])
        self.assertEqual(calls, [])
