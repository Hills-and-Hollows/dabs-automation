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