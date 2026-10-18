import unittest

from llm_failover.breaker import CircuitBreaker, State
from llm_failover.fake import FakeProvider
from llm_failover.router import AllProvidersFailed, FailoverRouter
from llm_failover.types import ProviderError, Request

REQUEST = Request("hello")


def router(*providers: FakeProvider, threshold: int = 2) -> FailoverRouter:
    return FailoverRouter(providers, lambda: CircuitBreaker(failure_threshold=threshold))


class FailoverRouterTest(unittest.TestCase):
    def test_uses_first_healthy_provider(self) -> None:
        primary, backup = FakeProvider("primary", ["a"]), FakeProvider("backup", ["b"])
        self.assertEqual(router(primary, backup).complete(REQUEST).provider, "primary")
        self.assertEqual(backup.calls, 0)

    def test_fails_over_on_retryable_error(self) -> None:
        primary, backup = FakeProvider("primary", [429]), FakeProvider("backup", ["b"])
        self.assertEqual(router(primary, backup).complete(REQUEST).text, "b")

    def test_client_error_is_raised_without_failover(self) -> None:
        primary, backup = FakeProvider("primary", [400]), FakeProvider("backup", ["b"])
        with self.assertRaises(ProviderError) as ctx:
            router(primary, backup).complete(REQUEST)
        self.assertEqual(ctx.exception.status, 400)
        self.assertEqual(backup.calls, 0)

    def test_client_error_does_not_trip_breaker(self) -> None:
        primary = FakeProvider("primary", [400])
        r = router(primary, threshold=1)
        with self.assertRaises(ProviderError):
            r.complete(REQUEST)
        self.assertIs(r.breaker("primary").state, State.CLOSED)

    def test_open_circuit_skips_provider_without_a_call(self) -> None:
        primary, backup = FakeProvider("primary", [503]), FakeProvider("backup", ["b"])
        r = router(primary, backup, threshold=2)
        for _ in range(3):
            r.complete(REQUEST)
        self.assertEqual(primary.calls, 2)
        self.assertEqual(backup.calls, 3)

    def test_all_failed_reports_tried_and_skipped(self) -> None:
        a, b = FakeProvider("a", [500]), FakeProvider("b", [502])
        r = router(a, b, threshold=1)
        with self.assertRaises(AllProvidersFailed) as first:
            r.complete(REQUEST)
        self.assertIn("a=500, b=502", str(first.exception))
        with self.assertRaises(AllProvidersFailed) as second:
            r.complete(REQUEST)
        self.assertEqual(second.exception.skipped, ["a", "b"])

    def test_requires_a_provider(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one"):
            FailoverRouter([])


if __name__ == "__main__":
    unittest.main()
