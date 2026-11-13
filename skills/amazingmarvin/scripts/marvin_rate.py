"""Linux cross-process rate accounting. Stores timestamps only, not task data."""
import fcntl
import json
import math
import os
import time
from contextlib import contextmanager
from pathlib import Path
from marvin_client import MarvinError


class RateLimiter:
    def __init__(self, path, *, clock=time.time, sleep=time.sleep, budget=1440):
        self.path = Path(path)
        self.clock = clock
        self.sleep = sleep
        self.budget = budget

    @contextmanager
    def _state(self):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'r+') as file:
            try:
                fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise MarvinError('Another request owns the rate lock; retry later', code='rate_busy') from None
            raw = file.read()
            try:
                state = json.loads(raw) if raw else {'requests': [], 'until': 0}
                if set(state) != {'requests', 'until'} or not isinstance(state['requests'], list):
                    raise ValueError
                if any(isinstance(x, bool) or not isinstance(x, (float, int)) or not math.isfinite(x) for x in [state['until'], *state['requests']]):
                    raise ValueError
            except (ValueError, TypeError):
                raise MarvinError('Rate state is invalid; no request sent', code='rate_state_invalid') from None
            yield state
            file.seek(0)
            json.dump(state, file)
            file.truncate()
            file.flush()
            os.fsync(file.fileno())

    def reserve(self):
        with self._state() as state:
            now = self.clock()
            state['requests'] = [x for x in state['requests'] if x > now - 86400]
            if len(state['requests']) >= self.budget:
                raise MarvinError('Local daily request budget reached', code='rate_budget')
            due = max(state['until'], max(state['requests'], default=now - 3) + 3)
            wait = max(0, due - now)
            if wait > 5:
                raise MarvinError('Rate cooldown active; retry later', code='rate_cooldown')
            if wait:
                self.sleep(wait)
            state['requests'].append(self.clock())

    def defer(self, seconds):
        with self._state() as state:
            state['until'] = max(state['until'], self.clock() + max(60, seconds))
