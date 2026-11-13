import tempfile
import unittest
from pathlib import Path
from test_client import MarvinError
from marvin_rate import RateLimiter

class RateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'rate.json'
        self.now = 100000.
        self.waits = []
    def sleep(self, seconds):
        self.waits.append(seconds)
        self.now += seconds
    def limiter(self, **kwargs):
        return RateLimiter(self.path, clock=lambda: self.now, sleep=self.sleep, **kwargs)
    def test_spacing_persists_between_instances(self):
        self.limiter().reserve()
        self.limiter().reserve()
        self.assertEqual(self.waits, [3.0])
    def test_budget_no_wait_or_request(self):
        self.limiter(budget=1).reserve()
        with self.assertRaises(MarvinError): self.limiter(budget=1).reserve()
        self.assertEqual(self.waits, [])
    def test_expired_budget(self):
        self.limiter(budget=1).reserve()
        self.now += 86401
        self.limiter(budget=1).reserve()
    def test_corrupt_state_fails_closed(self):
        self.path.write_text('not-json')
        with self.assertRaises(MarvinError): self.limiter().reserve()
        self.assertEqual(self.path.read_text(), 'not-json')
    def test_cooldown_shared(self):
        self.limiter().defer(60)
        with self.assertRaises(MarvinError): self.limiter().reserve()
        self.assertEqual(self.waits, [])
        self.now += 60
        self.limiter().reserve()
    def test_state_has_no_credentials(self):
        self.limiter().reserve()
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
