Analyze this page and help me come up with a way to automate creating a new order using this system from running code automatically
 https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/Orders

 Analyze this research from the current human workflow to identify ways to automatically use the ordering portal orders once finalized and ordered on our page to then export and duplicate in the officiall DABS LICENSEE Ordering Site to place the orders to match. 
@DABS LICENSEE ORDERING PAGE AUTOMATION RESEARCH.md

Here’s a concrete, end-to-end plan to automate creating a new order in this DABS Licensee Orders system from code, based on inspecting the live page and flows you’re on.

What the site exposes and how it behaves
- There is an Orders landing page with buttons for Create New Order and Copy Previous Order. If any order is in Created (pending) state, the UI blocks starting a brand-new order with the message: “Pending order must be submitted or deleted before a new order can be created.”[1]
- You can reach an editable order form at a URL like /Orders/EditOrder?orderId={id}. The form shows an Order Id, a table of line items, quantities, unit prices, and a Submit Order action. Line items appear to be tied to a warehouse-specific catalog.[1]
- Item search/add appears to be loaded dynamically via a URL like /Orders/GetItemsForWarehouse?OrderId={id}, which returns paginated item rows compatible with adding to the cart by entering quantities.[1]
- Actions are authenticated via your browser session (cookies). No public API is visible; it’s a classic server-rendered app plus AJAX calls. You should expect anti-CSRF tokens in form posts or in request headers for mutating calls.

Automation approaches you can choose from
1) Headless browser automation (recommended)
- Tools: Playwright or Puppeteer (Node.js), or Playwright/Pyppeteer (Python).
- Why: Safest way to stay compliant (uses your logged-in session, renders the same UI, respects CSRF and any dynamic scripts). It can click the same buttons your team uses and is resilient to CSRF changes.
- High-level flow your bot would implement:
  - Log in once with stored credentials or SSO; persist the authenticated storage (cookies/localStorage).
  - Navigate to /ProdApps/OnlineOrders/Orders. If a pending order exists:
    - Either open the most recent Created order and continue editing/submitting it,
    - Or programmatically delete/cancel it (only if your policy allows), then proceed.
  - Start a new order:
    - If Create New Order is blocked by a pending order, you can use the “Copy Previous Order” path if that yields an editable order page (EditOrder?orderId=…). Otherwise, click “Create New Order” when permitted.
  - On EditOrder?orderId={id}:
    - Add items: open the items dialog (warehouse search), query by code/description, set quantities, add to order. The UI provides GetItemsForWarehouse?OrderId={id} to populate the table; your headless code just interacts with the visible controls.
    - Validate: read totals from the totals row and ensure extended price matches expectations.
    - Submit: click Submit Order and wait for confirmation/success status.
  - Record the resulting Sales Order number shown in the orders list.

- Practical details to code:
  - Persist auth: With Playwright, use storageState to save cookies after interactive login. Subsequent runs load this state for true “headless cron” execution.
  - Selectors: Target the visible labels (“Create New Order”, “Copy Previous Order”, “Submit Order”) and stable attributes around the order table rows and item quantity inputs.
  - Error handling: Detect the “Pending order must be submitted or deleted…” banner and branch logic accordingly.
  - Idempotency: Before creating a new order, search your Order History table for today’s order to avoid duplicates.
  - Scheduling: Run from a CI job (GitHub Actions) or a server cron with environment secrets for credentials.

2) Programmatic HTTP automation (advanced, brittle)
- Tools: HTTP client (Python requests/Node fetch) + cookie jar.
- Why: Fast and lightweight, but you must reverse-engineer CSRF tokens, form payloads, and endpoints; more likely to break.
- Steps required:
  - Session: Perform login flow and capture cookies.
  - CSRF: Scrape the EditOrder page to extract hidden anti-forgery token (commonly __RequestVerificationToken) or headers; include it in all POSTs.
  - Endpoints to discover:
    - Create order (or “copy previous”) POST endpoint and payload schema.
    - Add item endpoint: likely something like Orders/AddItem or a cart mutation endpoint tied to OrderId and ItemCode with quantity.
    - Submit order endpoint: exact POST URL and required fields.
  - You would parse EditOrder?orderId={id} HTML to confirm current line items and totals after each change.
- Caveats: Any change in tokens, field names, or UI logic will require maintenance.

3) RPA with a controlled browser (e.g., Selenium)
- Similar to headless browser but you can run visible mode for debugging. Trade-offs similar to 1).

Putting this into code quickly (Playwright example, Node.js)
- One-time: run an interactive script to log in and save session state.
- Recurring job: reuse storage state to create-and-submit an order.

Example structure (pseudo-Playwright)
- login.js (interactive, run once):
  - Launch chromium with headful UI
  - Navigate to Orders URL, complete login
  - Save storageState to auth.json
- order-bot.js (headless, run on schedule):
  - Launch chromium with storageState: 'auth.json'
  - Go to Orders page
  - If pending Created order exists: decide to submit/delete/continue
  - Else: click Create New Order or Copy Previous Order
  - On EditOrder?orderId={id}:
    - Open “Add Items”, search codes, input quantities, add to order
    - Submit order, confirm success
  - Log the new Sales Order number

Data you’ll feed the bot
- A JSON list of items to order (codes and desired cases), e.g.:
  - [{ "itemCode": "038177", "cases": 10 }, { "itemCode": "087619", "cases": 6 }]
- Rules for minimums, stock checks, and substitutions.

Handling the “pending order” restriction
- Option A: If a Created order exists, open it, adjust items to your desired list (add/remove/modify), then click Submit.
- Option B: If policy allows, delete/cancel the pending order first, then click Create New Order.
- Option C: Use “Copy Previous Order” to reach a fresh EditOrder state (observed path showed EditOrder?orderId=234061), then proceed to modify and submit.[1]

What we observed you can rely on in the flow
- Orders page path and layout, including the Created state rows and action links to view/edit.
- Edit page with line items, quantities, extended prices, and a Submit Order button.
- Warehouse item list loads from GetItemsForWarehouse?OrderId={id}, which the UI uses to populate the add-to-order dialog (your automation can simply interact with the visible dialog without calling this endpoint directly).[1]

Security, compliance, and robustness
- Keep credentials and storageState secure (CI secrets or a secrets manager).
- Implement retries for transient failures and clear logging for audit.
- Add alerts if the DOM changes (selectors break) or if submission fails.
- Rate-limit interactions; avoid hammering item search endpoints.

If you want, I can:
- Generate a Playwright starter project with:
  - login.js to capture auth
  - order-bot.js reading an items.json payload
  - Robust selectors matching the current page labels and structure
  - A dry-run mode that fills the cart but skips final Submit
- Or provide a Python (Playwright) variant instead.

Let me know your preferred language/runtime and whether you want to submit a pending order, create a new one, or copy a previous order as the base. I can then output ready-to-run code with clear selectors and steps aligned to the current UI you’re using.

[1](https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/Orders)
[2](https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/Orders)
[3](https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/Orders/EditOrder?orderId=234061)
[4](https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/Orders/GetItemsForWarehouse?OrderId=234061)