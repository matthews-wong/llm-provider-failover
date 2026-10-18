from dataclasses import dataclass
from typing import Protocol

RETRYABLE_STATUSES = frozenset({408, 429, 500, 502, 503, 504})


@dataclass(frozen=True)
class Request:
    prompt: str
    max_tokens: int = 256


@dataclass(frozen=True)
class Response:
    text: str
    provider: str


class ProviderError(Exception):
    def __init__(self, provider: str, status: int, message: str = "") -> None:
        super().__init__(f"{provider} failed with status {status}: {message or 'no detail'}")
        self.provider = provider
        self.status = status

    @property
    def retryable(self) -> bool:
        return self.status in RETRYABLE_STATUSES


class Provider(Protocol):
    name: str

    def complete(self, request: Request) -> Response: ...
