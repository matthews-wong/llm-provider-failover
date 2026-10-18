# llm-provider-failover

Route an LLM request across an ordered list of providers. A provider that keeps
failing is taken out of rotation by a circuit breaker, and only errors that are
worth retrying elsewhere trigger a failover.

Pure standard-library Python, no model calls: everything runs against a scripted
fake provider.

## Design

- **Provider seam.** A provider is anything with `complete(request) -> Response`.
- **Error classification.** `ProviderError` carries a `retryable` flag. 429, 5xx
  and timeouts fail over to the next provider; a 400 or 401 is the caller's
  problem and is raised immediately, because every provider would reject it too.
- **Circuit breaker per provider.** closed -> open after N consecutive failures,
  open -> half-open after a cool-down, half-open -> closed on one success. An
  open provider is skipped without a call.
- **Injectable clock** so breaker timing is tested without sleeping.

## Usage

```python
from llm_failover.router import FailoverRouter
from llm_failover.types import Request

router = FailoverRouter([primary, backup])  # anything with .name and .complete()
print(router.complete(Request("hello")).text)
```

When every provider fails, `AllProvidersFailed` lists which providers were tried
with their status and which were skipped because their circuit was open.

## Validate

```
python3 -m unittest -v
python3 -m examples.outage
```

The replay uses scripted providers (fixtures, not real traffic): the primary
returns 503 on every call and the breaker opens after 3 failures. Last run, 10
requests: primary called 3 times, backup served all 10.

## Not covered yet

Retries with backoff on the same provider, per-call timeouts, and a real provider
adapter.
