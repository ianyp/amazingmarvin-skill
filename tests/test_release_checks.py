"""Release verification of existing behaviour, not feature stubs."""
import json
import multiprocessing
from pathlib import Path
import tempfile
import time
import unittest
from test_client import Client, MarvinError
from marvin_rate import RateLimiter


def reserve_worker(path, output):
    try:
        RateLimiter(path).reserve()
        output.put(('ok', time.time()))
    except MarvinError as error:
        output.put((error.code, time.time()))


class ReleaseChecks(unittest.TestCase):
    def test_concurrent_processes_cannot_bypass_spacing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / 'rate.json')
            output = multiprocessing.Queue()
            workers = [multiprocessing.Process(target=reserve_worker, args=(path, output)) for _ in range(3)]
            for worker in workers: worker.start()
            for worker in workers:
                worker.join(10)
                self.assertFalse(worker.is_alive())
                self.assertEqual(worker.exitcode, 0)
            results = [output.get(timeout=1) for _ in workers]
            times = sorted(stamp for code, stamp in results if code == 'ok')
            self.assertGreaterEqual(len(times), 1)
            self.assertTrue(all(code in ('ok', 'rate_busy') for code, _ in results))
            for left, right in zip(times, times[1:]): self.assertGreaterEqual(right - left, 2.9)
            self.assertEqual(len(json.loads(Path(path).read_text())['requests']), len(times))

    def test_header_token_never_in_failed_request_message(self):
        def transport(*args): raise RuntimeError('secret-value was rejected')
        with self.assertRaises(MarvinError) as caught:
            Client('secret-value', transport=transport).today('2026-11-13')
        self.assertNotIn('secret-value', str(caught.exception))
        self.assertFalse(caught.exception.outcome_unknown)
