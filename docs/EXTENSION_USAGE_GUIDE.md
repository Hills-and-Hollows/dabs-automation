# 🔧 VS Code Extension Usage Guide - DABS Automation Project

## 🎯 **Purpose**
This guide provides specific configuration and usage instructions for each enabled extension in the DABS Automation workspace to ensure optimal development workflow.

---

## 🐍 **Python Development Extensions**

### **`ms-python.python` - Python Language Support**
**Purpose**: Core Python development for Integration Hub and Processing Engines

**Key Configurations**:
```json
"python.defaultInterpreterPath": "./venv/bin/python",
"python.linting.enabled": true,
"python.linting.pylintEnabled": true,
"python.formatting.provider": "black"
```

**Usage Guidelines**:
- Use for all `.py` files in `/src/`, `/scripts/`, `/tests/`
- Automatic formatting on save (Black formatter)
- Pylint integration for code quality
- IntelliSense for FastAPI/Django development

### **`ms-python.debugpy` - Python Debugging**
**Purpose**: Debug Integration Hub, DABS processing, and API connections

**Usage Guidelines**:
- F5 to launch debugger for main application
- Set breakpoints in DABS file processing logic
- Debug OAuth flows for QuickBooks integration
- Step through CSV processing for 1,239 SKU validation

---

## 📊 **Documentation & Diagrams**

### **`bierner.markdown-mermaid` - Mermaid Diagram Rendering**
**Purpose**: Render architecture diagrams in `dabs-architecture-diagram.md`

**Key Files**:
- `docs/dabs-architecture-diagram.md` - Main system architecture
- `docs/visual.md` - Additional diagrams

**Usage**:
- Cmd+Shift+V (Mac) / Ctrl+Shift+V (Windows) for preview
- Live preview while editing diagrams
- Export diagrams for documentation

### **`streetsidesoftware.code-spell-checker` - Spell Checking**
**Purpose**: Maintain documentation quality across extensive doc suite

**Custom Dictionary**:
```json
"cSpell.words": ["DABS", "SSCS", "QuickBooks", "Verifone", "OAuth", "SKUs", "PostgreSQL", "FastAPI"]
```

**Usage Guidelines**:
- Check all `.md` files before commits
- Add project-specific terms to workspace dictionary
- Critical for client-facing documentation quality

### **`yzhang.markdown-all-in-one` - Comprehensive Markdown**
**Purpose**: Enhanced editing for 15+ documentation files

**Key Features**:
- Table of contents generation
- Keyboard shortcuts for formatting
- Math equation support
- Link validation

### **`davidanson.vscode-markdownlint` - Markdown Linting**
**Purpose**: Consistent documentation formatting

**Custom Rules**:
```json
"markdownlint.config": {
    "MD013": false,  // Line length (disabled for code blocks)
    "MD041": false   // First line heading (disabled for templates)
}
```

---

## 📁 **Data & Configuration**

### **`mechatroner.rainbow-csv` - CSV Processing**
**Purpose**: Process DABS Excel files with 1,239+ SKUs

**Key Files**:
- `data/sscs_pricing_update.csv` - DABS price data
- Any exported Excel files from DABS system

**Configuration**:
```json
"rainbow_csv.enable_auto_csv_lint": true,
"csv-preview.resizeColumns": "all"
```

**Usage Guidelines**:
- Automatic column colorization for large datasets
- CSV linting to catch data format errors
- Essential for validating DABS file structure

### **`redhat.vscode-yaml` - YAML Configuration**
**Purpose**: Docker, CI/CD, and configuration file management

**Key Files**:
- `docker-compose.yml` - Container orchestration
- `.github/workflows/` - CI/CD pipelines
- `config/` - Application configuration

### **`mikestead.dotenv` - Environment Variables**
**Purpose**: Secure credential management for API integrations

**Key Files**:
- `.env` - Local development credentials
- `.env.example` - Template for team setup

**Security Guidelines**:
- Never commit actual `.env` files
- Use for QuickBooks OAuth secrets
- SSCS API credentials (when available)
- Database connection strings

---

## 🔄 **Version Control**

### **`eamodio.gitlens` - Advanced Git Integration**
**Purpose**: Track changes across complex multi-phase project

**Key Features**:
- Blame annotations for debugging
- File history for documentation changes
- Branch comparison for phase reviews

**Configuration**:
```json
"gitlens.codeLens.enabled": false  // Reduce UI clutter
```

---

## 🔍 **Code Quality & Productivity**

### **`usernamehw.errorlens` - Inline Error Display**
**Purpose**: Immediate feedback for Python development

**Configuration**:
```json
"errorLens.enabledDiagnosticLevels": ["error", "warning"]
```

**Usage**: Critical for API integration debugging and data validation

### **`gruntfuggly.todo-tree` - Project Management**
**Purpose**: Track PHASE-based development and TODOs

**Custom Configuration**:
```json
"todo-tree.general.tags": ["TODO", "FIXME", "NOTE", "PHASE"],
"todo-tree.highlights.customHighlight": {
    "PHASE": {
        "icon": "📋",
        "type": "line"
    }
}
```

**Usage Guidelines**:
- Use `// PHASE 2: SSCS Integration` for phase-specific tasks
- `// TODO: Implement QuickBooks rate limiting`
- `// FIXME: Handle DABS file format changes`

### **`christian-kohler.path-intellisense` - File Path Completion**
**Purpose**: Navigate complex project structure efficiently

**Key Usage**:
- Import statements in Python modules
- File references in documentation
- Configuration file paths

---

## 🗄️ **Database Development**

### **`ckolkman.vscode-postgres` - PostgreSQL Support**
**Purpose**: Database development for Integration Hub

**Setup Requirements**:
- Connect to local PostgreSQL instance
- Database schema management
- Query development and testing

**Usage Guidelines**:
- Design tables for DABS data storage
- Develop audit trail schema
- Test data synchronization queries

---

## 🔧 **API Development**

### **`humao.rest-client` - API Testing**
**Purpose**: Test QuickBooks OAuth and SSCS API integrations

**Key Files to Create**:
- `tests/api/quickbooks.http` - QuickBooks API tests
- `tests/api/sscs.http` - SSCS API tests (when available)
- `tests/api/auth.http` - OAuth flow testing

**Usage Guidelines**:
- Test OAuth 2.0 flows before implementation
- Validate API responses and rate limits
- Document API endpoints for team reference

---

## 🎨 **Visual Enhancements**

### **`pkief.material-icon-theme` - File Icons**
**Purpose**: Improve navigation in complex project structure

**Benefits**:
- Distinguish between Python, Markdown, YAML files
- Quick identification of configuration vs. code files

### **`ibm.output-colorizer` - Console Output**
**Purpose**: Debug Python automation scripts and API responses

**Usage**:
- Colorized logs for DABS processing
- API response debugging
- Error message clarity

---

## 🚀 **Workflow Integration**

### **Daily Development Workflow**:
1. **Start**: Check TODO Tree for PHASE tasks
2. **Code**: Use Python extensions for development
3. **Test**: Use REST Client for API validation
4. **Document**: Update Markdown files with spell check
5. **Data**: Process CSV files with Rainbow CSV
6. **Commit**: Use GitLens for change review

### **Phase-Specific Usage**:
- **Phase 2**: Focus on REST Client, PostgreSQL, Python debugging
- **Phase 3**: Emphasize documentation extensions and TODO Tree
- **Phase 4**: Utilize all extensions for full system integration

---

## ⚙️ **Extension Maintenance**

### **Regular Tasks**:
- Update custom spell checker dictionary monthly
- Review TODO Tree tags at phase transitions
- Validate REST Client API tests weekly
- Update PostgreSQL connection settings as needed

### **Team Onboarding**:
1. Install recommended extensions via workspace
2. Review this usage guide
3. Configure local `.env` file
4. Test Mermaid diagram preview
5. Verify PostgreSQL connection

---

**📋 This guide ensures consistent, efficient use of all workspace extensions for maximum DABS project productivity!**