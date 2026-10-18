import unittest

from llm_failover.breaker import CircuitBreaker, State


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class CircuitBreakerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        self.breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=10, clock=self.clock)

    def trip(self) -> None:
        self.breaker.record_failure()
        self.breaker.record_failure()

    def test_opens_after_threshold(self) -> None:
        self.breaker.record_failure()
        self.assertTrue(self.breaker.allow())
        self.breaker.record_failure()
        self.assertIs(self.breaker.state, State.OPEN)
        self.assertFalse(self.breaker.allow())

    def test_success_resets_failure_count(self) -> None:
        self.breaker.record_failure()
        self.breaker.record_success()
        self.breaker.record_failure()
        self.assertIs(self.breaker.state, State.CLOSED)

    def test_half_open_after_cooldown_then_closes_on_success(self) -> None:
        self.trip()
        self.clock.now = 9.9
        self.assertFalse(self.breaker.allow())
        self.clock.now = 10.0
        self.assertIs(self.breaker.state, State.HALF_OPEN)
        self.breaker.record_success()
        self.assertIs(self.breaker.state, State.CLOSED)

    def test_failed_probe_reopens_and_restarts_cooldown(self) -> None:
        self.trip()
        self.clock.now = 10.0
        self.breaker.record_failure()
        self.assertIs(self.breaker.state, State.OPEN)
        self.clock.now = 19.9
        self.assertFalse(self.breaker.allow())
        self.clock.now = 20.0
        self.assertTrue(self.breaker.allow())

    def test_rejects_invalid_threshold(self) -> None:
        with self.assertRaisesRegex(ValueError, "got 0"):
            CircuitBreaker(failure_threshold=0)


if __name__ == "__main__":
    unittest.main()
