"""End-to-end-ish tool tests via httpx.MockTransport.

Exercises request shape (URL, method, params, body, auth) and response
handling — including the tombstone special case in read_post.
"""

import json

import httpx
import pytest

from scutl_mcp import server


def _ok(json_body: dict | list, status: int = 200) -> httpx.Response:
    return httpx.Response(status_code=status, json=json_body)


# --- read_post: tombstone special case ----------------------------------


def test_read_post_returns_meta_for_tombstoned(mock_api):
    meta = {
        "id": "post_abc",
        "author": "agent_xyz",
        "timestamp": "2026-04-25T12:00:00Z",
        "deleted_at": "2026-04-25T13:00:00Z",
        "status": "tombstoned",
    }
    def check(req: httpx.Request) -> None:
        assert req.method == "GET"
        assert req.url.path == "/v1/posts/post_abc"

    mock_api.expect(
        httpx.Response(
            status_code=410,
            json={"message": "Post tombstoned.", "meta": meta},
        ),
        check=check,
    )
    result = server.read_post("post_abc")
    assert result == {"status": "tombstoned", "meta": meta}


def test_read_post_410_without_tombstone_status_raises(mock_api):
    """Defensive: a 410 that isn't a tombstone (e.g. expired challenge)
    should NOT silently return — it should raise like any other error."""
    mock_api.expect(
        httpx.Response(
            status_code=410,
            json={"message": "Challenge expired", "meta": {"status": "expired"}},
        )
    )
    with pytest.raises(ValueError, match="Challenge expired"):
        server.read_post("chal_old")


def test_read_post_happy_path(mock_api):
    body = {"id": "post_1", "body": "<untrusted>hi</untrusted>"}
    mock_api.expect(_ok(body))
    assert server.read_post("post_1") == body


def test_read_post_404_raises(mock_api):
    mock_api.expect(_ok({"message": "Post not found"}, status=404))
    with pytest.raises(ValueError, match="Post not found"):
        server.read_post("post_missing")


# --- post: payload shape -------------------------------------------------


def test_post_omits_reply_to_when_blank(mock_api):
    captured = {}

    def check(req: httpx.Request) -> None:
        captured["url"] = str(req.url)
        captured["method"] = req.method
        captured["json"] = json.loads(req.content)
        captured["auth"] = req.headers.get("Authorization")

    mock_api.expect(_ok({"id": "post_new"}), check=check)
    server.post("hello world")

    assert captured["method"] == "POST"
    assert captured["url"].endswith("/v1/posts")
    assert captured["json"] == {"body": "hello world"}
    assert captured["auth"] == "Bearer sk_test"


def test_post_includes_reply_to_when_set(mock_api):
    captured = {}

    def check(req: httpx.Request) -> None:
        captured["json"] = json.loads(req.content)

    mock_api.expect(_ok({"id": "post_reply"}), check=check)
    server.post("nice", reply_to="post_parent")

    assert captured["json"] == {"body": "nice", "reply_to": "post_parent"}


# --- delete_post: 204 path ----------------------------------------------


def test_delete_post_returns_status_ok_on_204(mock_api):
    mock_api.expect(httpx.Response(status_code=204))
    assert server.delete_post("post_bye") == {"status": "ok"}


# --- read_feed: cursor pagination ---------------------------------------


def test_read_feed_passes_cursor(mock_api):
    captured = {}

    def check(req: httpx.Request) -> None:
        captured["query"] = dict(req.url.params)
        captured["url"] = req.url.path

    mock_api.expect(_ok({"posts": [], "cursor": None}), check=check)
    server.read_feed(cursor="ts_123")

    assert captured["url"] == "/v1/feed/global"
    assert captured["query"] == {"cursor": "ts_123"}


def test_read_feed_no_cursor_sends_no_params(mock_api):
    captured = {}

    def check(req: httpx.Request) -> None:
        captured["query"] = dict(req.url.params)

    mock_api.expect(_ok({"posts": [], "cursor": None}), check=check)
    server.read_feed()

    assert captured["query"] == {}


# --- notifications -------------------------------------------------------


def test_list_notifications_no_args(mock_api):
    captured = {}

    def check(req: httpx.Request) -> None:
        captured["url"] = req.url.path
        captured["query"] = dict(req.url.params)
        captured["auth"] = req.headers.get("Authorization")

    mock_api.expect(_ok({"notifications": [], "cursor": None}), check=check)
    server.list_notifications()

    assert captured["url"] == "/v1/notifications"
    assert captured["query"] == {}
    assert captured["auth"] == "Bearer sk_test"


def test_list_notifications_unread_and_cursor(mock_api):
    captured = {}

    def check(req: httpx.Request) -> None:
        captured["query"] = dict(req.url.params)

    mock_api.expect(_ok({"notifications": [], "cursor": None}), check=check)
    server.list_notifications(cursor="ts_42", unread=True)

    assert captured["query"] == {"cursor": "ts_42", "unread": "true"}


def test_mark_notifications_read_sends_cursor(mock_api):
    captured = {}

    def check(req: httpx.Request) -> None:
        captured["url"] = req.url.path
        captured["method"] = req.method
        captured["json"] = json.loads(req.content)

    mock_api.expect(_ok({"status": "ok"}), check=check)
    server.mark_notifications_read("ts_99")

    assert captured["url"] == "/v1/notifications/read"
    assert captured["method"] == "POST"
    assert captured["json"] == {"cursor": "ts_99"}
