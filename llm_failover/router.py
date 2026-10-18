from collections.abc import Callable, Sequence

from .breaker import CircuitBreaker
from .types import Provider, ProviderError, Request, Response


class AllProvidersFailed(Exception):
    def __init__(self, errors: Sequence[ProviderError], skipped: Sequence[str]) -> None:
        tried = ", ".join(f"{e.provider}={e.status}" for e in errors) or "none"
        super().__init__(f"all providers failed (tried: {tried}; circuit open: {list(skipped)})")
        self.errors = list(errors)
        self.skipped = list(skipped)


class FailoverRouter:
    def __init__(
        self,
        providers: Sequence[Provider],
        breaker_factory: Callable[[], CircuitBreaker] = CircuitBreaker,
    ) -> None:
        if not providers:
            raise ValueError("at least one provider is required")
        self._providers = list(providers)
        self._breakers = {p.name: breaker_factory() for p in providers}

    def breaker(self, name: str) -> CircuitBreaker:
        return self._breakers[name]

    def complete(self, request: Request) -> Response:
        errors: list[ProviderError] = []
        skipped: list[str] = []
        for provider in self._providers:
            breaker = self._breakers[provider.name]
            if not breaker.allow():
                skipped.append(provider.name)
                continue
            try:
                response = provider.complete(request)
            except ProviderError as error:
                if not error.retryable:
                    raise
                breaker.record_failure()
                errors.append(error)
                continue
            breaker.record_success()
            return response
        raise AllProvidersFailed(errors, skipped)
