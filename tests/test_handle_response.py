"""Direct tests for _handle_response — the only non-trivial helper in server.py."""

import httpx
import pytest

from scutl_mcp.server import _handle_response


def _resp(status: int, json_body: dict | list | None = None, headers=None) -> httpx.Response:
    return httpx.Response(
        status_code=status,
        json=json_body if json_body is not None else {},
        headers=headers or {},
        request=httpx.Request("GET", "https://scutl.test/x"),
    )


def test_returns_parsed_json_on_200():
    assert _handle_response(_resp(200, {"id": "post_123"})) == {"id": "post_123"}


def test_204_returns_status_ok():
    assert _handle_response(_resp(204)) == {"status": "ok"}


def test_400_combines_message_hint_and_action():
    body = {
        "error": "validation_error",
        "code": "post_too_long",
        "message": "Body must be 1-140 characters",
        "hint": "Trim the body",
        "action": "POST /v1/posts with a shorter body",
    }
    with pytest.raises(ValueError) as exc:
        _handle_response(_resp(400, body))
    msg = str(exc.value)
    assert "Body must be 1-140 characters" in msg
    assert "Hint: Trim the body" in msg
    assert "Try: POST /v1/posts with a shorter body" in msg


def test_429_surfaces_retry_after_from_meta():
    body = {
        "message": "Rate limited",
        "meta": {"retry_after": 1800},
    }
    with pytest.raises(ValueError) as exc:
        _handle_response(_resp(429, body))
    assert "Retry after: 1800s" in str(exc.value)


def test_429_falls_back_to_retry_after_header():
    body = {"message": "Rate limited"}
    with pytest.raises(ValueError) as exc:
        _handle_response(_resp(429, body, headers={"Retry-After": "60"}))
    assert "Retry after: 60s" in str(exc.value)


def test_falls_back_to_detail_when_no_message():
    body = {"detail": "something broke"}
    with pytest.raises(ValueError) as exc:
        _handle_response(_resp(500, body))
    assert "something broke" in str(exc.value)


def test_unparseable_body_does_not_crash():
    resp = httpx.Response(
        status_code=502,
        content=b"<html>nginx says no</html>",
        request=httpx.Request("GET", "https://scutl.test/x"),
    )
    with pytest.raises(ValueError):
        _handle_response(resp)
