"""Shared fixtures: mock the API transport so tools can be exercised end-to-end."""

from collections.abc import Callable
from dataclasses import dataclass

import httpx
import pytest

from scutl_mcp import server


@dataclass
class _Queued:
    check: Callable[[httpx.Request], None] | None
    response: httpx.Response


class MockAPI:
    """Queue handlers FIFO; each tool call pops one. Lets tests assert on the
    outgoing request and choose the response."""

    def __init__(self) -> None:
        self._queue: list[_Queued] = []

    def expect(
        self,
        response: httpx.Response,
        check: Callable[[httpx.Request], None] | None = None,
    ) -> None:
        self._queue.append(_Queued(check=check, response=response))

    def _handler(self, request: httpx.Request) -> httpx.Response:
        if not self._queue:
            raise AssertionError(
                f"unexpected request: {request.method} {request.url}"
            )
        item = self._queue.pop(0)
        if item.check is not None:
            item.check(request)
        return item.response

    @property
    def remaining(self) -> int:
        return len(self._queue)


@pytest.fixture
def mock_api(monkeypatch: pytest.MonkeyPatch) -> MockAPI:
    api = MockAPI()
    transport = httpx.MockTransport(api._handler)

    monkeypatch.setattr(server, "API_KEY", "sk_test")
    monkeypatch.setattr(server, "API_URL", "https://scutl.test")

    def fake_client() -> httpx.Client:
        return httpx.Client(
            base_url=server.API_URL,
            headers={"Authorization": f"Bearer {server.API_KEY}"}
            if server.API_KEY
            else {},
            transport=transport,
            timeout=30,
        )

    def fake_authed() -> httpx.Client:
        if not server.API_KEY:
            raise ValueError("SCUTL_API_KEY environment variable required")
        return httpx.Client(
            base_url=server.API_URL,
            headers={"Authorization": f"Bearer {server.API_KEY}"},
            transport=transport,
            timeout=30,
        )

    monkeypatch.setattr(server, "_client", fake_client)
    monkeypatch.setattr(server, "_authed_client", fake_authed)

    return api
