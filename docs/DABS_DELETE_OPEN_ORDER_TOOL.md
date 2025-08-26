# DABS Delete Open Order Tool

## Purpose
Reliable, repeatable deletion of the single pending DABS order with proof via source-of-truth page state.

## Commands
```bash
# Headless (default). Optional: DABS_ORDER_ID=234102 to target a specific row
make dabs-delete-open-order
make dabs-delete-open-order DABS_ORDER_ID=234102

# Headed (visible browser) for guaranteed success during operations
make dabs-delete-open-order-headed
make dabs-delete-open-order-headed DABS_ORDER_ID=234102
```

## Implementation
- Script: `scripts/delete_dabs_order.py`
- Trigger selector (row-scoped): `div.tableOpen tbody tr a.open-AddDialog.delete`
- Modal confirm (Delete-not-Cancel): `#DeleteOrder input[type="submit"][value="Delete"]`
- Optional row targeting: `DABS_ORDER_ID=<ID>`
- Headless/Headed: `DABS_HEADLESS=true|false` (default true)

## Verification (Non-Negotiable)
After confirming Delete, the script:
- Reloads the Orders page `.../OnlineOrders/Orders`
- Asserts both:
  - The specific order row is absent
  - The banner “Pending order must be submitted or deleted before a new order can be created.” is not present

Artifacts stored in `data/playwright_screenshots/`:
- `debug_dabs_interface.png` (before)
- `debug_dabs_interface_after.png` (after)
- `orders_list_headed.html` / `orders_list_after.html` (HTML state)

## Notes
- If the row Delete trigger is not visible, the script falls back to the Edit page and uses the same Delete modal flow there.
- Cancel does not delete; it only dismisses the modal. Always use the Delete button in the confirmation modal.

## MCP Usage
Trigger via the simplified MCP server (`src/mcp/dabs_simple_mcp_server.py`).

### Tool: dabs_delete_open_order
```json
{
  "name": "dabs_delete_open_order",
  "arguments": {
    "confirm": true,
    "headed": false,
    "order_id": "234102",
    "return_artifacts": true
  }
}
```

### Safety Requirements
- `confirm=true` is mandatory.
- Additionally, one of the following must be true: `headed=true` or `return_artifacts=true` (audit traceability).
- Headed mode shells out to `scripts/delete_dabs_order.py`; both modes return artifact paths when `return_artifacts=true`.

### Orchestrator Helper
- Use `dabs_ensure_clean_state` to guarantee there is no pending order before create/edit routines.

