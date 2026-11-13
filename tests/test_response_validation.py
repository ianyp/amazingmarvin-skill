import unittest
import test_transport
from test_client import Client, MarvinError

class ResponseValidationTests(unittest.TestCase):
    def test_malformed_list_item_rejected(self):
        for response in [[None], ['garbage'], [42]]:
            with self.subTest(response=response), self.assertRaises(MarvinError):
                Client('fake', transport=lambda *args: response).today('2026-11-13')
    def test_huge_estimate_rejected_before_transport(self):
        calls = []
        client = Client('fake', transport=lambda *args: calls.append(args))
        with self.assertRaises(MarvinError): client.add({'title':'x','estimateMinutes':1e308})
        self.assertEqual(calls, [])

class StrictJsonTests(unittest.TestCase):
    setUp = test_transport.TransportTests.setUp
    tearDown = test_transport.TransportTests.tearDown
    def test_nonfinite_json_response_is_unknown_write(self):
        self.server.reply = (200, {}, b'{"_id":"x","number":NaN}')
        with self.assertRaises(MarvinError) as caught:
            self.transport('POST', 'addTask', {}, {})
        self.assertTrue(caught.exception.outcome_unknown)
