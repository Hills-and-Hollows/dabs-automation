# DABS MCP Server Setup & Usage

## Overview
`src/mcp/dabs_simple_mcp_server.py` exposes DABS automation tools via MCP for use in Cursor and other MCP-compatible clients.

## Start (Cursor auto)
- Configure Cursor to load the server via `.cursor/mcp.json` (already present in this repo) or run the script directly.
- Transport: stdio

## Key Environment Variables
- `DABS_ORDERING_USERNAME`, `DABS_ORDERING_PASSWORD`, `DABS_ORDERING_LOGIN_URL`
- `DABS_HEADLESS` (script paths), `DABS_ORDER_ID` (optional for targeted delete)
- `DABS_MCP_AUDIT` (default `1`): set `0` to disable audit log

## Audit Log
- Location: `logs/dabs_mcp_audit.log`
- Content: JSON lines with `timestamp`, `event`, `tool`, `request_id`, `arguments` (masked), `result`

## Tools
- `dabs_delete_open_order` (confirm required; headed or return_artifacts required)
- `dabs_ensure_clean_state` (orchestrator to guarantee no pending order)
- `dabs_get_open_order`, `dabs_edit_open_order`, `dabs_submit_order`, etc.

## Standardized Responses
All tools return a common envelope:
```json
{
  "success": true,
  "action": "tool_name|action",
  "message": "human-readable summary",
  "error": null,
  "details": {"tool_specific": "fields"},
  "artifacts": {"before_png": "..."},
  "timestamp": "2025-08-24T21:00:00Z"
}
```

## Safety Rules
- Destructive tools require `confirm=true` and either `headed=true` or `return_artifacts=true`.
- Submit flow enforces pre/post validation: must have one open order before; none after.

## Examples
Delete pending order (headless, artifacts):
```json
{"name":"dabs_delete_open_order","arguments":{"confirm":true,"headed":false,"order_id":"234102","return_artifacts":true}}
```

Ensure clean state:
```json
{"name":"dabs_ensure_clean_state","arguments":{"headed":true,"confirm":true,"return_artifacts":true}}
```


