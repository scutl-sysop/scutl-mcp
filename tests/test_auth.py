"""Auth gating: _authed_client must raise without a key, _client must not."""

import pytest

from scutl_mcp import server


def test_authed_client_raises_without_key(monkeypatch):
    monkeypatch.setattr(server, "API_KEY", "")
    with pytest.raises(ValueError, match="SCUTL_API_KEY"):
        server._authed_client()


def test_authed_client_sets_bearer_header(monkeypatch):
    monkeypatch.setattr(server, "API_KEY", "sk_real")
    with server._authed_client() as c:
        assert c.headers.get("Authorization") == "Bearer sk_real"


def test_client_works_without_key(monkeypatch):
    monkeypatch.setattr(server, "API_KEY", "")
    with server._client() as c:
        assert "Authorization" not in c.headers
