import time
from collections import deque
from collections.abc import Callable
from threading import Lock

_MAX_TRACKED_KEYS = 10_000


class AttemptLimiter:
    """Ventana deslizante en memoria: bloquea temporalmente, nunca de forma permanente.

    El estado vive en el proceso: se reinicia al reiniciar el backend y no se comparte entre varios workers.
    """

    def __init__(self, max_attempts: int, window_seconds: int, clock: Callable[[], float] = time.monotonic) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._clock = clock
        self._attempts: dict[str, deque[float]] = {}
        self._lock = Lock()

    def _prune(self, key: str, now: float) -> deque[float]:
        attempts = self._attempts.setdefault(key, deque())
        while attempts and now - attempts[0] >= self.window_seconds:
            attempts.popleft()
        return attempts

    def retry_after(self, key: str) -> int:
        """Segundos hasta poder reintentar; 0 si no está bloqueado."""
        with self._lock:
            now = self._clock()
            attempts = self._prune(key, now)
            if len(attempts) < self.max_attempts:
                return 0
            return max(1, int(self.window_seconds - (now - attempts[0])) + 1)

    def record(self, key: str) -> None:
        with self._lock:
            now = self._clock()
            if len(self._attempts) >= _MAX_TRACKED_KEYS:
                for stale in [k for k in self._attempts if not self._prune(k, now)]:
                    del self._attempts[stale]
            self._prune(key, now).append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._attempts.clear()


# Solo se cuentan los fallos de credenciales; un inicio de sesión correcto reinicia el contador del par IP+correo.
login_pair_limiter = AttemptLimiter(max_attempts=5, window_seconds=15 * 60)
login_ip_limiter = AttemptLimiter(max_attempts=20, window_seconds=15 * 60)
register_limiter = AttemptLimiter(max_attempts=10, window_seconds=60 * 60)


def reset_all() -> None:
    for limiter in (login_pair_limiter, login_ip_limiter, register_limiter):
        limiter.clear()
