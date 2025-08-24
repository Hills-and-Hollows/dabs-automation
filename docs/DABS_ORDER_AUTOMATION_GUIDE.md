# DABS Order Automation System Guide
**Hills & Hollows LLC - Utah Package Agency**  
*Complete automation for order data extraction, analysis, and tracking*

---

## 🎯 System Overview

The DABS Order Automation System eliminates manual work for Tessa by automatically:
- **Extracting order data** from Utah DABS Licensee Ordering system
- **Downloading and processing** PDF invoices  
- **Analyzing purchase patterns** and price trends
- **Generating automated reports** for purchase tracking
- **Monitoring price variances** and compliance

**Time Savings**: Eliminates 2-3 hours weekly of manual order tracking and analysis

---

## 🔐 Authentication Configuration

The system uses secure credentials stored in:
- **`config/dabs_ordering.env`** - Environment variables
- **`config/secure_credentials.json`** - Secure credential storage

### DABS Ordering Credentials:
```
Login URL: https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/
Username: hillshollows
Password: Hills2025!@
```

---

## 🚀 Quick Start

### 1. Installation
```bash
# Install system and dependencies
python scripts/install_dabs_order_automation.py

# Manual dependency installation if needed
pip install -r requirements_dabs_orders.txt
```

### 2. Run Manual Extraction (Testing)
```bash
# Extract last 30 days of orders
python src/automation/dabs_order_automation.py --extract --days 30

# Analyze extracted data
python src/automation/dabs_invoice_analyzer.py --analyze
```

### 3. Setup Automated Scheduling
```bash
# Configure daily automation
python src/automation/dabs_order_manager.py --setup
```

---

## 📁 System Architecture

### Core Components:

**`src/automation/dabs_order_automation.py`**
- Automated login to DABS system
- Order history extraction
- PDF invoice download
- Data extraction from PDFs

**`src/automation/dabs_invoice_analyzer.py`**  
- Purchase pattern analysis
- Price trend monitoring
- Inventory insights generation
- Cost optimization recommendations

**`src/automation/dabs_order_manager.py`**
- Workflow orchestration
- Integration with existing DABS systems
- Automated reporting and notifications
- Scheduling coordination

### Data Storage Structure:
```
data/dabs_orders/
├── pdfs/                          # Downloaded PDF invoices
├── extracted_data/                # Structured order data (JSON)
└── analysis/                      # Analysis results and reports

data/reports/                      # Generated Excel/CSV reports
```

---

## ⚙️ Automation Workflows

### Daily Processing (2:00 AM)
- **Extracts**: Last 7 days of orders
- **Processes**: New PDF invoices  
- **Analyzes**: Purchase patterns and price changes
- **Duration**: 15-30 minutes
- **Output**: Daily summary report

### Weekly Full Analysis (Sunday 1:00 AM)
- **Extracts**: Full 90-day historical data
- **Generates**: Comprehensive purchase analysis
- **Identifies**: Cost optimization opportunities
- **Duration**: 45-60 minutes  
- **Output**: Weekly executive summary for Tessa

### Monthly Reconciliation (1st of month, 4:00 AM)
- **Reconciles**: Order data with DABS pricing
- **Identifies**: Price discrepancies
- **Prepares**: Compliance reporting data
- **Duration**: 30-45 minutes
- **Output**: Monthly reconciliation report

---

## 📊 Analysis Capabilities

### Purchase Pattern Analysis
- **Product frequency** - High/medium/low purchase frequency
- **Reorder intervals** - Average days between orders
- **Seasonal patterns** - Quarterly and monthly trends
- **ABC classification** - Value-based product categorization

### Price Monitoring  
- **Price variance tracking** - Products with >20% price changes
- **Trend analysis** - Increasing/decreasing/stable price trends
- **Reconciliation** - Order prices vs current DABS pricing
- **Alert generation** - Automated notifications for significant changes

### Inventory Insights
- **Fast vs slow movers** - Turnover analysis
- **Demand forecasting** - 30-day demand predictions  
- **Bulk purchase opportunities** - Cost optimization identification
- **Stock optimization** - Inventory level recommendations

---

## 🔔 Notifications and Alerts

### Automated Notifications to Tessa:
- **Daily**: Processing completion status
- **Weekly**: Executive summary with key insights
- **Immediate**: Critical price discrepancies (>50% variance)
- **Monthly**: Compliance preparation and reconciliation results

### Alert Thresholds:
- **HIGH**: Price variance >50%
- **MEDIUM**: Price variance 20-50%  
- **CRITICAL**: >5 price discrepancies with DABS pricing

---

## 📈 Sample Analysis Output

### Executive Summary:
```
Total Orders: 45
Total Spend: $15,234.67
Unique Products: 187
High Variance Items: 3
Price Discrepancies: 1
```

### Key Insights:
- **Top Product by Value**: ESPOLON BLANCO TEQUILA ($2,319.12 total)
- **Most Frequent**: SEGURA VIUDAS BRUT (8 orders)
- **Price Alert**: CROWN ROYAL REGAL APPLE (+35% increase)
- **Recommendation**: Review bulk purchasing for top 10 products

---

## 🛠️ Manual Operations

### Extract Specific Date Range:
```bash
python src/automation/dabs_order_automation.py --extract --days 180
```

### Analyze Only (No Extraction):
```bash  
python src/automation/dabs_invoice_analyzer.py --analyze
```

### Generate Custom Report:
```bash
python src/automation/dabs_order_manager.py --weekly
```

---

## 🔧 Troubleshooting

### Common Issues:

**Login Failures:**
- Verify credentials in `config/dabs_ordering.env`
- Check DABS system availability
- Ensure Chrome browser is installed

**PDF Processing Errors:**
- Verify pdfplumber installation: `pip install pdfplumber`
- Check PDF file permissions
- Ensure sufficient disk space

**Data Analysis Errors:**
- Verify pandas installation: `pip install pandas>=2.0.2`
- Check extracted data file existence
- Validate data file format

### Log Files:
- **Main log**: `logs/dabs_order_automation.log`
- **Manager log**: `logs/dabs_order_manager.log`
- **Installation log**: System output during installation

---

## 📋 Integration with Existing Systems

### DABS Processing Integration:
- **Price tracking updates**: Feeds into main DABS processor
- **Variance alerts**: Triggers SSCS sync if needed
- **Audit trail**: Logs all automation events

### Notification System:
- **Uses existing TessaNotificationSystem**
- **Integrates with current email alerts**
- **Follows established notification patterns**

### Scheduling Integration:
- **Adds to master automation scheduler**
- **Coordinates with monthly price automation**
- **Maintains performance monitoring**

---

## 🎊 Business Impact

### For Tessa (Store Manager):
- **Eliminates**: 2-3 hours weekly manual order tracking
- **Provides**: Automated purchase insights and trends
- **Alerts**: Price changes and discrepancies automatically
- **Reports**: Ready-to-use Excel reports for management

### For Operations:
- **Compliance**: Automated preparation for Utah reporting
- **Efficiency**: Streamlined purchase tracking and analysis
- **Accuracy**: Eliminates manual data entry errors
- **Insights**: Data-driven inventory and purchasing decisions

---

## 📞 Support and Maintenance

### Automated Monitoring:
- System health checks built into workflows
- Performance monitoring with alerts
- Error notifications to admin team
- Audit trail for all operations

### Manual Maintenance:
- **Monthly**: Review automation performance metrics
- **Quarterly**: Validate price variance thresholds  
- **Annually**: Update DABS credentials if changed

---

## 🔮 Future Enhancements

### Planned Capabilities:
- **QuickBooks Integration**: Automatic invoice reconciliation
- **Predictive Analytics**: Advanced demand forecasting
- **Mobile Alerts**: SMS notifications for critical issues
- **Dashboard**: Real-time monitoring interface

---

*This automation system is part of the comprehensive DABS automation project delivering 90% time reduction for Hills & Hollows operations.*
