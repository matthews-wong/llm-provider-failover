from collections.abc import Iterable

from .types import ProviderError, Request, Response


class FakeProvider:
    """Replays a script: an int raises ProviderError with that status, a str is returned."""

    def __init__(self, name: str, script: Iterable[int | str]) -> None:
        self.name = name
        self._script = list(script)
        self.calls = 0

    def complete(self, request: Request) -> Response:
        step = self._script[min(self.calls, len(self._script) - 1)]
        self.calls += 1
        if isinstance(step, int):
            raise ProviderError(self.name, step)
        return Response(text=step, provider=self.name)
