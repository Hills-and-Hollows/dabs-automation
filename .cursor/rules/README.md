# DABS PROJECT RULES - CURSOR FRAMEWORK
Atomic project rules for DABS automation system enforcement

## CURSOR PROJECT RULES STRUCTURE
This directory contains specialized `.mdc` files that enforce different aspects of the DABS project architecture:

### Always Applied Rules (alwaysApply: true)
- **archon-workflow.mdc** - Archon MCP workflow enforcement
- **dabs-business-logic.mdc** - DABS business rules and Utah compliance
- **project-structure.mdc** - Project organization enforcement

### Context-Sensitive Rules (globs: pattern)
- **security-compliance.mdc** - Security standards (applies to .py, .json, config files)
- **testing-requirements.mdc** - Testing enforcement (applies to test files)
- **api-design.mdc** - API standards (applies to src/api and .py files)
- **performance-gates.mdc** - Performance requirements (applies to all source)
- **integration-hub.mdc** - Integration patterns (applies to integration_hub and processors)

## RULE ACTIVATION
Rules automatically activate based on:
1. **Always Applied**: Core workflow and business logic rules
2. **File Context**: Rules activate when working with matching file patterns
3. **Description-Based**: Agent can request specific rules when needed

## FRAMEWORK ENFORCEMENT
Each rule enforces specific architectural requirements:
- **Archon-First Development**: MCP server workflow patterns
- **DABS Compliance**: Utah Package Agency requirements
- **Security Standards**: OAuth 2.0, encryption, audit trails
- **Performance Gates**: 15-minute processing, <2s response times
- **Testing Coverage**: 90% minimum with proper test pyramid
- **API Design**: RESTful principles and integration patterns

## USAGE
Cursor automatically loads and applies these rules based on context. No manual intervention required - the framework enforces architectural compliance automatically.

For more information, see the main project documentation and CURSOR_RULES_IMPLEMENTATION_COMPLETE.md.
