"""Replay a primary-provider outage against scripted providers and print where each request went."""
from llm_failover.breaker import CircuitBreaker
from llm_failover.fake import FakeProvider
from llm_failover.router import FailoverRouter
from llm_failover.types import Request

REQUESTS = 10
OUTAGE_STATUS = 503
FAILURE_THRESHOLD = 3


def main() -> None:
    primary = FakeProvider("primary", [OUTAGE_STATUS])
    backup = FakeProvider("backup", ["ok"])
    router = FailoverRouter(
        [primary, backup], lambda: CircuitBreaker(failure_threshold=FAILURE_THRESHOLD)
    )
    for i in range(1, REQUESTS + 1):
        served_by = router.complete(Request(f"q{i}")).provider
        print(f"request {i:>2}: served by {served_by:<7} primary circuit={router.breaker('primary').state.value}")
    print(f"primary calls: {primary.calls}/{REQUESTS}, backup calls: {backup.calls}/{REQUESTS}")


if __name__ == "__main__":
    main()
