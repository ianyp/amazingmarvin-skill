import unittest
from test_client import Client, MarvinError
from marvin_transport import Transport
import test_transport

class ErrorTests(unittest.TestCase):
    def test_structured_transport_error_preserved(self):
        def reject(*args): raise MarvinError('Denied', code='http_401')
        client = Client('fake', transport=reject)
        with self.assertRaises(MarvinError) as caught: client.add({'title': 'x'})
        self.assertEqual(caught.exception.code, 'http_401')
        self.assertFalse(caught.exception.outcome_unknown)

class CooldownTests(unittest.TestCase):
    setUp = test_transport.TransportTests.setUp
    tearDown = test_transport.TransportTests.tearDown
    def test_429_records_shared_cooldown(self):
        delays = []
        transport = Transport(base_url=self.base, allow_loopback=True, reserve=lambda: None, defer=delays.append)
        self.server.reply = (429, {'Retry-After': '120'}, b'no')
        with self.assertRaises(MarvinError): transport('GET', 'labels', {}, None)
        self.assertEqual(delays, [120])
