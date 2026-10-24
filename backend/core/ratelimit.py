"""Tiny in-memory brute-force guard for login endpoints (one process, which is how we run)."""
import time
from collections import defaultdict, deque

from starlette.requests import Request


class FailureLimiter:
    def __init__(self, max_failures: int = 8, window_seconds: int = 300):
        self.max_failures = max_failures
        self.window = window_seconds
        self._fails: dict[str, deque] = defaultdict(deque)

    def _prune(self, key: str) -> deque:
        q = self._fails[key]
        cutoff = time.monotonic() - self.window
        while q and q[0] < cutoff:
            q.popleft()
        if not q:
            self._fails.pop(key, None)
            return deque()
        return q

    def blocked(self, key: str) -> bool:
        return len(self._prune(key)) >= self.max_failures

    def fail(self, key: str) -> None:
        self._prune(key)
        self._fails[key].append(time.monotonic())

    def reset(self, key: str) -> None:
        self._fails.pop(key, None)


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


login_limiter = FailureLimiter()
