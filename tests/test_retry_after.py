import unittest
import test_transport
from marvin_client import MarvinError
from marvin_transport import Transport

class RetryAfterTests(unittest.TestCase):
    setUp = test_transport.TransportTests.setUp
    tearDown = test_transport.TransportTests.tearDown
    def test_http_date_cooldown(self):
        delays = []
        transport = Transport(base_url=self.base, allow_loopback=True, reserve=lambda: None,
                              defer=delays.append, clock=lambda: 0)
        self.server.reply = (429, {'Retry-After': 'Thu, 01 Jan 1970 00:02:00 GMT'}, b'')
        with self.assertRaises(MarvinError): transport('GET', 'labels', {}, None)
        self.assertEqual(delays, [120])
