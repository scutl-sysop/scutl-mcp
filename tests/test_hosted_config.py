import importlib.util
import json

import pytest

from scutl_mcp import HOSTED_MCP_URL, get_hosted_config
from scutl_mcp.cli import main


def test_default_configuration_points_to_hosted_streamable_http_oauth():
    config = get_hosted_config()
    assert HOSTED_MCP_URL == "https://scutl.org/mcp"
    assert config == {
        "name": "scutl",
        "transport": {
            "type": "streamable_http",
            "url": "https://scutl.org/mcp",
        },
        "authentication": {
            "type": "oauth",
            "resource_metadata_url": (
                "https://scutl.org/.well-known/oauth-protected-resource/mcp"
            ),
        },
        "connection_guide": "https://scutl.org/connect",
    }


def test_self_hosted_url_must_be_credential_free_mcp_endpoint():
    assert get_hosted_config("https://agents.example/mcp")["transport"]["url"] == (
        "https://agents.example/mcp"
    )
    for invalid in (
        "http://agents.example/mcp",
        "https://user:secret@agents.example/mcp",
        "https://agents.example/api",
        "https://agents.example/mcp?token=secret",
    ):
        with pytest.raises(ValueError):
            get_hosted_config(invalid)


def test_cli_emits_machine_configuration_without_api_key(monkeypatch, capsys):
    monkeypatch.setenv("SCUTL_API_KEY", "sk_must_not_appear")
    monkeypatch.setattr("sys.argv", ["scutl-mcp", "--format", "json"])
    main()
    captured = capsys.readouterr()
    config = json.loads(captured.out)
    warning = json.loads(captured.err)
    assert config["transport"]["url"] == "https://scutl.org/mcp"
    assert config["authentication"]["type"] == "oauth"
    assert warning == {
        "warning": "api_key_ignored",
        "message": (
            "SCUTL_API_KEY is not used by hosted MCP. Remove it from the MCP "
            "configuration; the client will discover browser OAuth when a protected "
            "tool is invoked."
        ),
    }
    assert "sk_must_not_appear" not in captured.out + captured.err


def test_cli_supports_url_and_claude_code_configuration(monkeypatch, capsys):
    monkeypatch.delenv("SCUTL_API_KEY", raising=False)
    monkeypatch.setattr("sys.argv", ["scutl-mcp", "--format", "url"])
    main()
    assert capsys.readouterr().out.strip() == "https://scutl.org/mcp"

    monkeypatch.setattr("sys.argv", ["scutl-mcp", "--format", "claude-code"])
    main()
    assert capsys.readouterr().out.strip() == (
        "claude mcp add --transport http scutl https://scutl.org/mcp"
    )


def test_package_contains_no_local_server_or_duplicated_tool_module():
    assert importlib.util.find_spec("scutl_mcp.server") is None
    assert importlib.util.find_spec("scutl_mcp.tools") is None
