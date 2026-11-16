import unittest
from test_client import Client, MarvinError

class FullAccessTests(unittest.TestCase):
    def test_full_header(self):
        calls = []
        client = Client('fake', transport=lambda *a: calls.append(a) or 'OK', full_access=True)
        client.check_auth()
        self.assertEqual(calls[0][2], {'X-Full-Access-Token': 'fake'})
    def test_full_flag_must_be_boolean(self):
        with self.assertRaises(MarvinError):
            Client('fake', transport=None, full_access='false')
