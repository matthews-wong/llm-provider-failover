import time
from collections.abc import Callable
from enum import Enum


class State(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


DEFAULT_FAILURE_THRESHOLD = 3
DEFAULT_COOLDOWN_SECONDS = 30.0


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = DEFAULT_FAILURE_THRESHOLD,
        cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError(f"failure_threshold must be >= 1, got {failure_threshold}")
        self._threshold = failure_threshold
        self._cooldown = cooldown_seconds
        self._clock = clock
        self._failures = 0
        self._opened_at = 0.0
        self._state = State.CLOSED

    @property
    def state(self) -> State:
        if self._state is State.OPEN and self._clock() - self._opened_at >= self._cooldown:
            self._state = State.HALF_OPEN
        return self._state

    def allow(self) -> bool:
        return self.state is not State.OPEN

    def record_success(self) -> None:
        self._failures = 0
        self._state = State.CLOSED

    def record_failure(self) -> None:
        self._failures += 1
        # A failed half-open probe reopens at once; no need to count up to the threshold again.
        if self.state is State.HALF_OPEN or self._failures >= self._threshold:
            self._state = State.OPEN
            self._opened_at = self._clock()
