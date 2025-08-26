import json
import pytest

from src.mcp.dabs_simple_mcp_server import SimpleMCPServer


async def call_tool(server: SimpleMCPServer, name: str, arguments: dict):
    request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    response = await server.handle_request(request)
    text = response["result"]["content"][0]["text"]
    return json.loads(text)


@pytest.mark.asyncio
async def test_tools_list_contains_expected():
    server = SimpleMCPServer("dabs-simple-mcp-test")

    request = {"jsonrpc": "2.0", "id": "list-1", "method": "tools/list", "params": {}}
    response = await server.handle_request(request)

    tools = response["result"].get("tools", [])
    names = {t.get("name") for t in tools}

    assert "dabs_delete_open_order" in names
    assert "dabs_ensure_clean_state" in names


@pytest.mark.asyncio
async def test_delete_requires_confirm():
    server = SimpleMCPServer("dabs-simple-mcp-test")
    result = await call_tool(server, "dabs_delete_open_order", {"confirm": False})

    assert result.get("success") is False
    error_blob = (result.get("error") or "") + json.dumps(result.get("details", {}))
    assert "confirm" in error_blob.lower()


@pytest.mark.asyncio
async def test_delete_requires_headed_or_artifacts():
    server = SimpleMCPServer("dabs-simple-mcp-test")
    result = await call_tool(
        server,
        "dabs_delete_open_order",
        {"confirm": True, "headed": False, "return_artifacts": False},
    )

    assert result.get("success") is False
    error_blob = (result.get("error") or "") + json.dumps(result.get("details", {}))
    assert "headed" in error_blob.lower() or "artifacts" in error_blob.lower()


@pytest.mark.asyncio
async def test_login_status_standardized_schema():
    server = SimpleMCPServer("dabs-simple-mcp-test")
    result = await call_tool(server, "dabs_login_status", {})

    # Standardized envelope
    assert "success" in result
    assert "action" in result
    assert "details" in result
    assert "timestamp" in result
    assert result.get("action") == "dabs_login_status"


