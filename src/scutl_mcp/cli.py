"""CLI that emits hosted MCP connection configuration."""

from __future__ import annotations

import argparse
import json
import os
import sys

from scutl_mcp.config import get_hosted_config

_API_KEY_MIGRATION = (
    "SCUTL_API_KEY is not used by hosted MCP. Remove it from the MCP configuration; "
    "the client will discover browser OAuth when a protected tool is invoked."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scutl-mcp",
        description=(
            "Print configuration for Scutl's hosted Streamable HTTP MCP endpoint. "
            "This package no longer runs a local tool server."
        ),
    )
    parser.add_argument(
        "--format",
        choices=["json", "url", "claude-code"],
        default="json",
    )
    parser.add_argument(
        "--url",
        help="Credential-free HTTPS /mcp URL for a self-hosted deployment",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        config = get_hosted_config(args.url)
    except ValueError as exc:
        print(
            json.dumps({"error": "invalid_mcp_url", "message": str(exc)}),
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    if os.environ.get("SCUTL_API_KEY"):
        print(
            json.dumps(
                {"warning": "api_key_ignored", "message": _API_KEY_MIGRATION},
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
    transport = config["transport"]
    if not isinstance(transport, dict) or not isinstance(transport.get("url"), str):
        raise RuntimeError("Hosted MCP configuration is missing its transport URL.")
    url = transport["url"]
    if args.format == "url":
        print(url)
    elif args.format == "claude-code":
        print(f"claude mcp add --transport http scutl {url}")
    else:
        print(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()
