# 🍾 DABS Automation System

**Automated Pricing & Inventory Sync for Hills & Hollows LLC**  
*Utah Package Agency - Boulder, UT*

---

## 🎯 Project Overview

The DABS Automation System eliminates manual data entry for liquor inventory management by creating seamless integration between:

- **DABS** (Utah State System) - Monthly pricing updates
- **SSCS POS** - Point of sale system  
- **QuickBooks Online** - Inventory and financial management
- **Verifone** - Payment processing

**Business Impact**: 90% reduction in manual processing time, saving 10+ hours/week

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL database
- Active QuickBooks Online account
- Utah Package Agency credentials

### Installation
```bash
# Clone and setup
git clone <repository-url>
cd dabc-pricing-inventory

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/setup_database.py

# Configure environment
cp .env.example .env
# Edit .env with your API credentials
```

### Hero Mode Quick Launch
For non-technical users, simply double-click:
```
start_hero_system.py
```

---

## 🧹 Routine Ops: Delete Open DABS Order

```bash
# Headless (default). Optional: DABS_ORDER_ID=234102 to target the row
make dabs-delete-open-order
make dabs-delete-open-order DABS_ORDER_ID=234102

# Headed/visible (recommended for operations)
make dabs-delete-open-order-headed
make dabs-delete-open-order-headed DABS_ORDER_ID=234102
```

Flow and verification:
- Trigger selector: `div.tableOpen tbody tr a.open-AddDialog.delete`
- Confirm in modal: `#DeleteOrder input[type="submit"][value="Delete"]` (not Cancel)
- Post-condition: reload Orders; verify missing row and absence of the banner
  “Pending order must be submitted or deleted before a new order can be created.”
Artifacts saved to `data/playwright_screenshots/` (before/after screenshots and HTML).

---

## 📊 System Architecture

```
DABS Price Updates → Integration Hub → SSCS POS
                                   ↓
                           QuickBooks ← Inventory Sync
                                   ↓
                           DABS Reports ← Compliance Module
```

**Core Components**:
- **Integration Hub**: Central processing engine (Python/FastAPI)
- **DABS Processor**: Excel file automation (1,239+ SKUs)
- **Sync Engine**: Real-time inventory management
- **Compliance Engine**: Automated reporting and audit trails

---

## 📋 Project Structure

```
src/
├── integration_hub/     # Core system coordination
├── processors/          # DABS file processing
└── api/                # REST API endpoints

docs/                   # Complete technical documentation
├── FUNCTIONAL_REQUIREMENTS.md
├── TECHNICAL_ARCHITECTURE.md
├── ACCEPTANCE_CRITERIA.md
└── [12 additional spec files]

data/
├── dabs_backups/       # DABS file archives
└── exports/           # Generated reports

tests/                  # Comprehensive test suite
config/                # System configuration
scripts/               # Utility and setup scripts
```

---

## 🔧 Development

### Running Tests
```bash
# Run all tests
pytest tests/

# Test coverage
pytest --cov=src tests/

# Specific test modules
pytest tests/test_integration_hub.py
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code  
pylint src/

# Type checking
mypy src/
```

### Structure Validation
```bash
# Check project structure compliance
make check-structure

# Auto-fix structure violations
make fix-structure
```

### DABS Open Order Deletion
```bash
# Headless (default). Optional: DABS_ORDER_ID=234102 to target a specific row
make dabs-delete-open-order

# Headed (visible browser) for guaranteed success
make dabs-delete-open-order-headed

# Equivalent direct call
# DABS_HEADLESS=false DABS_ORDER_ID=234102 python3 scripts/delete_dabs_order.py
```

Artifacts and verification:
- Before/after screenshots and HTML captured in `data/playwright_screenshots/`
- Script verifies: row removed and no pending-order banner present

### MCP Triggers (DABS Ordering)
Use the simplified MCP server (`src/mcp/dabs_simple_mcp_server.py`) to trigger automations via tools. Key tools and arguments:

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

- Safety: destructive operations require `confirm=true` AND either `headed=true` or `return_artifacts=true`.
- Headed mode shells out to `scripts/delete_dabs_order.py`; both modes return artifact paths when `return_artifacts=true`.

```json
{
  "name": "dabs_ensure_clean_state",
  "arguments": {
    "headed": true,
    "confirm": true,
    "return_artifacts": true
  }
}
```

Standardized response schema (all tools):
- `success` (bool), `action` (string), `message` (string), `error` (string|optional),
- `details` (object with tool-specific fields), `artifacts` (paths if requested), `timestamp` (ISO8601)

---

## 📊 Key Metrics & Success Criteria

### Performance Targets
- **Processing Speed**: 1,239 SKUs in <15 minutes
- **Accuracy**: <0.1% pricing error rate  
- **Availability**: >99% uptime
- **Response Time**: <2 seconds for dashboard queries

### Business KPIs
- **Time Reduction**: >90% decrease in manual processing
- **Compliance**: 100% on-time DABS reporting
- **User Satisfaction**: >8/10 staff satisfaction score
- **ROI**: Positive return within 24 months

---

## 🔌 Integration Status

| System | Status | Integration Method |
|--------|--------|-------------------|
| **DABS State System** | ✅ Ready | Excel file processing + API |
| **QuickBooks Online** | ✅ Ready | OAuth 2.0 REST API (500 req/min) |
| **Verifone POS** | ✅ Ready | Local config + Cloud API |
| **SSCS POS** | ⚠️ Pending | API/DB/File (vendor contact required) |

---

## 📞 Support & Documentation

### For Developers
- **Technical Specs**: `/docs/TECHNICAL_ARCHITECTURE.md`
- **API Documentation**: `/docs/api/`
- **Testing Strategy**: `/docs/TESTING_STRATEGY.md`

### For Users  
- **User Guide**: `/docs/USER_GUIDE.md`
- **Troubleshooting**: `/docs/TROUBLESHOOTING.md`
- **Training Materials**: `/docs/training/`

### For Stakeholders
- **Project Summary**: `PROJECT_SUMMARY.md`
- **Implementation Plan**: `/docs/PRD_FRAMEWORK.md`
- **Risk Assessment**: `/docs/RISK_ASSESSMENT.md`

---

## 🚨 Critical Next Steps

### Phase 2: Core Integrations (Starting Soon)
1. **SSCS Vendor Contact** - Request technical documentation
2. **QuickBooks OAuth Setup** - Establish API connection  
3. **DABS Processing Engine** - Automate file processing
4. **Integration Hub Development** - Central coordination system

### Getting Help
- **Technical Issues**: Create GitHub issue
- **Business Questions**: Contact project stakeholders
- **Emergency Support**: See `/docs/SUPPORT.md`

---

**🏆 Project Investment**: $43K-65K | **Projected ROI**: 180-250% (5-year)**  
**🎯 Mission**: Transform manual liquor inventory management into automated excellence**

---

*This system is specifically designed for Utah Package Agency compliance and Hills & Hollows LLC operational requirements.*
