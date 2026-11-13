import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/amazingmarvin/scripts'))
from marvin_client import Client, MarvinError

class ClientTests(unittest.TestCase):
    def make(self, reply=None):
        self.calls = []
        def transport(method, path, headers, body):
            self.calls.append((method, path, headers, body))
            return [] if reply is None else reply
        return Client('synthetic-secret', transport=transport)

    def test_missing_token_prevents_request(self):
        with self.assertRaises(MarvinError): Client('', transport=lambda *args: None)

    def test_today_explicit_date(self):
        client = self.make()
        self.assertEqual(client.today('2026-11-13'), [])
        self.assertEqual(self.calls[0][:2], ('GET', 'todayItems?date=2026-11-13'))
        self.assertEqual(self.calls[0][2], {'X-API-Token': 'synthetic-secret'})

    def test_due_uses_by(self):
        self.make().due('2026-11-13')
        self.assertEqual(self.calls[0][1], 'dueItems?by=2026-11-13')

    def test_bad_date_no_network(self):
        client = self.make()
        with self.assertRaises(MarvinError): client.today('2026-02-30')
        self.assertEqual(self.calls, [])

    def test_create_literal_title_and_units(self):
        self.make({'_id': 'task1'}).add({'title': 'Call #literal', 'estimateMinutes': 15, 'day': '2026-11-13'})
        method, path, headers, body = self.calls[0]
        self.assertEqual((method, path), ('POST', 'addTask'))
        self.assertEqual(headers['X-Auto-Complete'], 'false')
        self.assertEqual(body, {'title': 'Call #literal', 'timeEstimate': 900000, 'day': '2026-11-13'})

    def test_unknown_field_rejected(self):
        client = self.make()
        with self.assertRaises(MarvinError): client.add({'title': 'x', 'unexpected': True})
        self.assertEqual(self.calls, [])

    def test_response_error_not_success(self):
        with self.assertRaises(MarvinError): self.make({'error': 'not_found'}).today('2026-11-13')

    def test_read_requires_array(self):
        with self.assertRaises(MarvinError): self.make({'surprise': True}).due('2026-11-13')

    def test_write_timeout_not_replayed_or_leaked(self):
        calls = []
        def fail(*args):
            calls.append(args)
            raise TimeoutError('synthetic-secret')
        client = Client('synthetic-secret', transport=fail)
        with self.assertRaises(MarvinError) as caught: client.add({'title': 'x'})
        self.assertTrue(caught.exception.outcome_unknown)
        self.assertNotIn('synthetic-secret', str(caught.exception))
        self.assertEqual(len(calls), 1)

if __name__ == '__main__': unittest.main()
