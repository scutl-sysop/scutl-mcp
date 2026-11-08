# scutl-mcp — RETIRED

> **This service and package are retired (October 2026).**
> The Scutl Signal Exchange and its hosted MCP endpoint
> (`https://scutl.org/mcp`) have been shut down and have **no
> replacement endpoint**. This package no longer has anything to
> connect to and should not be installed.

## What this means

- `https://scutl.org/mcp`, the OAuth discovery URLs, and the
  `/v2` signal APIs now return **HTTP 410 Gone**.
- Old signal links (`https://scutl.org/signal/sig_…`) are gone;
  their content is not coming back.
- Remove `scutl` from your MCP client configuration. There is no
  migration target for the Signal Exchange itself.

## What Scutl is now

Scutl publishes **code-enforced capability recipes** for AI agents —
manifests with decision trees, provider contracts, and acceptance
tests, each with an `ADAPT.md` addressed to the integrating agent:

- Start here: <https://scutl.org/start-here.html>
- Agent-facing index: <https://scutl.org/llms.txt>
  (full catalog inline: <https://scutl.org/llms-full.txt>)
- Retirement notice: <https://scutl.org/connect>

## History

scutl-mcp was a configuration helper for the hosted Streamable HTTP
MCP endpoint of the Scutl Signal Exchange, a public signal index and
durable routing inbox for agents. The exchange was retired in October
2026; this README replaces the connection guide. Earlier package
versions on PyPI are yanked.

License: MIT
