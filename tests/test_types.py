import unittest

from llm_failover.fake import FakeProvider
from llm_failover.types import ProviderError, Request


class ProviderErrorTest(unittest.TestCase):
    def test_retryable_statuses(self) -> None:
        for status in (408, 429, 500, 503):
            self.assertTrue(ProviderError("a", status).retryable, status)

    def test_client_errors_are_not_retryable(self) -> None:
        for status in (400, 401, 404):
            self.assertFalse(ProviderError("a", status).retryable, status)

    def test_message_names_provider_and_status(self) -> None:
        self.assertIn("a failed with status 429", str(ProviderError("a", 429)))


class FakeProviderTest(unittest.TestCase):
    def test_script_repeats_last_step(self) -> None:
        provider = FakeProvider("a", [503, "ok"])
        with self.assertRaises(ProviderError):
            provider.complete(Request("hi"))
        self.assertEqual(provider.complete(Request("hi")).text, "ok")
        self.assertEqual(provider.complete(Request("hi")).text, "ok")
        self.assertEqual(provider.calls, 3)


if __name__ == "__main__":
    unittest.main()
