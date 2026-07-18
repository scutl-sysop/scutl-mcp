"""Portable configuration for Scutl's hosted MCP endpoint."""

from __future__ import annotations

import os
from urllib.parse import urlsplit

HOSTED_MCP_URL = "https://scutl.org/mcp"


def _validated_endpoint(url: str) -> tuple[str, str]:
    if len(url) > 2048:
        raise ValueError("MCP URL is too long")
    try:
        parsed = urlsplit(url)
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("invalid MCP URL") from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path != "/mcp"
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("MCP URL must be a credential-free HTTPS origin with the exact /mcp path")
    endpoint = f"{parsed.scheme}://{parsed.netloc}/mcp"
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return endpoint, origin


def get_hosted_config(url: str | None = None) -> dict[str, object]:
    """Return generic Streamable HTTP and OAuth discovery configuration."""
    endpoint, origin = _validated_endpoint(url or os.environ.get("SCUTL_MCP_URL", HOSTED_MCP_URL))
    return {
        "name": "scutl",
        "transport": {"type": "streamable_http", "url": endpoint},
        "authentication": {
            "type": "oauth",
            "resource_metadata_url": (f"{origin}/.well-known/oauth-protected-resource/mcp"),
        },
        "connection_guide": f"{origin}/connect",
    }
