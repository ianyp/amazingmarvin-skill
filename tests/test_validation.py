import unittest
from test_client import Client, MarvinError

class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.client = Client('fake-token', transport=self.transport)
    def transport(self, *args):
        self.calls.append(args)
        return 'OK'
    def test_invalid_values_never_reach_transport(self):
        for fields in ({'title': ' '}, {'title': 'x', 'estimateMinutes': True},
                       {'title': 'x', 'estimateMinutes': float('nan')},
                       {'title': 'x', 'labelIds': 'not-a-list'},
                       {'title': 'x', 'dueDate': '2026-2-2'}):
            with self.subTest(fields=fields), self.assertRaises(MarvinError): self.client.add(fields)
        self.assertEqual(self.calls, [])
    def test_success_without_id_is_preserved(self):
        self.assertEqual(self.client.add({'title': 'x'}), 'OK')
    def test_non_json_write_response_is_unknown(self):
        self.client._transport = lambda *args: None
        with self.assertRaises(MarvinError) as caught:
            self.client.add({'title': 'x'})
        self.assertTrue(caught.exception.outcome_unknown)
    def test_constructor_rejects_header_injection(self):
        with self.assertRaises(MarvinError):
            Client('token\r\nInjected: yes', transport=self.transport)
