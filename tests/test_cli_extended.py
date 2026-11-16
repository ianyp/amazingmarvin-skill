from datetime import datetime
from zoneinfo import ZoneInfo
import unittest
import test_cli_workflows

class ExtendedCliTests(unittest.TestCase):
    run_workflow = test_cli_workflows.CliWorkflowTests.run_workflow
    def test_project_cli(self):
        status,result,calls=self.run_workflow(['--full-access','project','--input-json','-'],{'_id':'p'},datetime(2026,11,16,tzinfo=ZoneInfo('UTC')),'{"title":"test"}')
        self.assertEqual(status,0);self.assertEqual(calls[0][1],'addProject');self.assertIn('X-Full-Access-Token',calls[0][2])
    def test_date_tracks_summer(self):
        status,result,calls=self.run_workflow(['tracks','--date','2026-07-01'],[],datetime(2026,11,16,tzinfo=ZoneInfo('UTC')))
        self.assertEqual(status,0);self.assertEqual(calls[0][3]['timeZone'],-60)
    def test_habits_cli_full(self):
        status,result,calls=self.run_workflow(['--full-access','habits','--raw'],[],datetime(2026,11,16,tzinfo=ZoneInfo('UTC')))
        self.assertEqual(status,0);self.assertEqual(calls[0][1],'habits?raw=1')
    def test_minimal_and_default_headers(self):
        for flags in ([], ['--minimal-access']):
            status,result,calls=self.run_workflow(flags+['today'],[],datetime(2026,11,16,tzinfo=ZoneInfo('UTC')))
            self.assertEqual(status,0)
            self.assertIn('X-API-Token',calls[0][2])
            self.assertNotIn('X-Full-Access-Token',calls[0][2])
    def test_conflicting_access_flags_rejected(self):
        status,result,calls=self.run_workflow(['--minimal-access','--full-access','today'],[],datetime(2026,11,16,tzinfo=ZoneInfo('UTC')))
        self.assertNotEqual(status,0)
        self.assertEqual(calls,[])
    def test_minimal_rejects_full_operation_before_network(self):
        status,result,calls=self.run_workflow(['--minimal-access','notebooks'],[],datetime(2026,11,16,tzinfo=ZoneInfo('UTC')),'{"title":"test"}')
        self.assertNotEqual(status,0)
        self.assertEqual(result['error']['code'],'missing_capability')
        self.assertEqual(calls,[])
