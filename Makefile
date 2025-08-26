# DABS Project - Structure Enforcement

.PHONY: check-structure fix-structure init-structure

check-structure:
	@echo "🔍 Checking DABS project structure..."
	@python3 scripts/enforce_structure.py

fix-structure:
	@echo "🔧 Auto-fixing structure violations..."
	@python3 scripts/auto_organize.py

init-structure:
	@echo "🏗️ Initializing DABS structure..."
	@python3 scripts/init_structure.py
	@chmod +x .git/hooks/pre-commit

# Block any operation if structure is violated
%: check-structure
	@echo "✅ Structure verified - proceeding with $@"

.PHONY: dabs-delete-open-order dabs-delete-open-order-headed

# Delete open DABS order (headless by default). Optional: DABS_ORDER_ID=234102
dabs-delete-open-order: check-structure
	@echo "🗑️ Deleting open DABS order (headless)..."
	@python3 scripts/delete_dabs_order.py

# Delete open DABS order (headed/visible for guaranteed success). Optional: DABS_ORDER_ID=234102
dabs-delete-open-order-headed: check-structure
	@echo "🗑️ Deleting open DABS order (headed)..."
	@DABS_HEADLESS=false python3 scripts/delete_dabs_order.py

.PHONY: test-mcp

# Run MCP integration tests only (ignore legacy conflicting paths)
test-mcp: check-structure
	@echo "🧪 Running MCP integration tests..."
	@./venv/bin/python -m pip -q install pytest >/dev/null 2>&1 || true
	@./venv/bin/pytest -q tests/integration/test_dabs_mcp_tools.py --ignore "Analyze and remove when done/python/tests" | cat

.PHONY: dabs-delete-open-order-smoke

# Smoke test: headless run, summarize result and note artifacts
dabs-delete-open-order-smoke: check-structure
	@echo "🧪 Smoke: delete open DABS order (headless)"
	@python3 scripts/delete_dabs_order.py || true
	@echo "📄 Artifacts: data/playwright_screenshots/"