import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
SCRIPT = Path(__file__).resolve().parents[1] / 'skills/amazingmarvin/scripts/marvin.py'

class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        env = dict(os.environ)
        env.pop('MARVIN_API_TOKEN', None)
        return subprocess.run([sys.executable, str(SCRIPT), *args], env=env, cwd='/tmp', capture_output=True, text=True)
    def test_missing_credentials_json_error(self):
        result = self.run_cli('today')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['error']['code'], 'missing_credentials')
    def test_unknown_command_json_error(self):
        result = self.run_cli('delete-all')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['error']['code'], 'invalid_input')
    def test_help_no_token(self):
        result = self.run_cli('--help')
        self.assertEqual(result.returncode, 0)
        self.assertIn('today', result.stdout)
