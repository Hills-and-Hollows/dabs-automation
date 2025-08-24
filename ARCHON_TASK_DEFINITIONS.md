# 🎯 DABS TASKS FOR ARCHON - MASTER SOURCE OF TRUTH

**Use these task definitions in Archon UI (Add Task button) to establish universal coordination**

---

## 🚨 **CRITICAL BLOCKER TASKS** (Priority: Highest)

### **Task 1: DABS Excel Processing Engine**
- **Title**: `🚨 CRITICAL: Build DABS Excel Processing Engine`
- **Description**: `Core automation system to process 1,239+ SKUs from monthly DABS Excel files. Must complete processing in <15 minutes with <0.1% error rate. This IS the 90% time reduction for Tessa - the main value delivery of the entire project.`
- **Assignee**: `AI IDE Agent`
- **Priority**: `Critical`
- **Feature**: `dabs_processing`
- **Status**: `Backlog`

### **Task 2: SSCS POS Integration System**
- **Title**: `🚨 CRITICAL: SSCS POS Integration System`
- **Description**: `Complete SSCS POS integration with NAXML export generation, automated price sync, validation, and rollback capability. 1-hour sync time target from DABS file receipt. The core connection between DABS and POS.`
- **Assignee**: `AI IDE Agent`
- **Priority**: `Critical`
- **Feature**: `sscs_integration`
- **Status**: `Backlog`

### **Task 3: Restaurant Processing Fee Solution**
- **Title**: `🚨 CRITICAL BUSINESS: Restaurant Processing Fee Solution`
- **Description**: `CRITICAL BUSINESS ISSUE - Implement restaurant credit card processing fee system to prevent profit loss. Add POS 'Restaurant Processing Fee' button with automatic percentage calculation, separate GL accounting, and receipt disclosure compliance.`
- **Assignee**: `User`
- **Priority**: `Critical`
- **Feature**: `payment_processing`
- **Status**: `Backlog`

---

## ⚡ **HIGH PRIORITY TASKS** (Manager Relief)

### **Task 4: Real-time Validation & Alert System**
- **Title**: `⚡ HIGH: Real-time Validation & Alert System`
- **Description**: `Build real-time processing dashboard for Tessa with progress tracking, exception alerts (missing SKUs, >20% price variances), mobile notifications (SMS/email), success confirmation reports, and complete audit trail logging.`
- **Assignee**: `AI IDE Agent`
- **Priority**: `High`
- **Feature**: `validation_alerts`
- **Status**: `Backlog`

### **Task 5: Restaurant Order Automation System**
- **Title**: `⚡ HIGH: Restaurant Order Automation System`
- **Description**: `Replace manual email orders with standardized web form, customer portal for direct submissions, Thursday deadline enforcement, Friday confirmation workflow, Sunday cutoff lock mechanism. Target 90% time reduction (45 min → 5 min per order).`
- **Assignee**: `AI IDE Agent`
- **Priority**: `High`
- **Feature**: `restaurant_orders`
- **Status**: `Backlog`

### **Task 6: UPC Resolution System**
- **Title**: `⚡ HIGH: UPC Resolution System`
- **Description**: `CRITICAL ISSUE: 'Only items already in SSCS are ordered' - Build OCR system for PDF invoice scanning, DABS UPC database creation, SSCS import file preparation with UPCs, new item processing workflow, UPC validation and cross-referencing.`
- **Assignee**: `AI IDE Agent`
- **Priority**: `High`
- **Feature**: `upc_resolution`
- **Status**: `Backlog`

### **Task 7: PCI-Compliant Payment Security System**
- **Title**: `⚡ HIGH: PCI-Compliant Payment Security System`
- **Description**: `Implement secure restaurant credit card storage with payment token management, secure card-on-file storage, POS integration for pickup charging, cashier interface (no card exposure). Alternative: House account setup.`
- **Assignee**: `AI IDE Agent`
- **Priority**: `High`
- **Feature**: `payment_security`
- **Status**: `Backlog`

---

## 📊 **MEDIUM PRIORITY TASKS** (Full Automation)

### **Task 8: QuickBooks OAuth Integration System**
- **Title**: `📊 MEDIUM: QuickBooks OAuth Integration System`
- **Description**: `Set up QuickBooks OAuth 2.0 authentication, real-time inventory synchronization, financial reconciliation automation, rate-limited API implementation (500 req/min). Credentials: shawn@owenent.com.`
- **Assignee**: `AI IDE Agent`
- **Priority**: `Medium`
- **Feature**: `quickbooks_integration`
- **Status**: `Backlog`

### **Task 9: Utah Package Agency Compliance Automation**
- **Title**: `📊 MEDIUM: Utah Package Agency Compliance Automation`
- **Description**: `Build automated SSCS sales data extraction, beer singles conversion logic (6-packs → singles for DABC reporting), monthly DABS report generation, automated portal upload system. Monthly deadline: 10th of following month.`
- **Assignee**: `AI IDE Agent`
- **Priority**: `Medium`
- **Feature**: `utah_compliance`
- **Status**: `Backlog`

### **Task 10: Case vs Bottle POS Handling System**
- **Title**: `📊 MEDIUM: Case vs Bottle POS Handling System`
- **Description**: `Implement case-level POS scanning support, UOM conversion in POS system, back-office case setup without handheld scanner. Addresses pain point: 'There is not a UPC for a case count yet in the POS'.`
- **Assignee**: `AI IDE Agent`
- **Priority**: `Medium`
- **Feature**: `pos_optimization`
- **Status**: `Backlog`

### **Task 11: ACH & Financial Reconciliation System**
- **Title**: `📊 MEDIUM: ACH & Financial Reconciliation System`
- **Description**: `Build DABC ACH withdrawal monitoring, bank reconciliation automation, purchase vs invoice reconciliation, credit memo handling, cash flow integration for QuickBooks.`
- **Assignee**: `AI IDE Agent`
- **Priority**: `Medium`
- **Feature**: `financial_reconciliation`
- **Status**: `Backlog`

---

## 🔧 **IMPLEMENTATION TASKS** (Specific Configuration)

### **Task 12: Restaurant Processing Fee POS Button**
- **Title**: `🔧 IMPLEMENTATION: Add Restaurant Processing Fee POS Button`
- **Description**: `Configure SSCS POS with 'Restaurant Processing Fee' button, auto-calculation based on percentage, separate GL mapping for fees collected, receipt disclosure verbiage. Requires POS admin access.`
- **Assignee**: `User`
- **Priority**: `Medium`
- **Feature**: `pos_configuration`
- **Status**: `Backlog`

### **Task 13: Friday Restaurant Confirmation Workflow**
- **Title**: `🔧 IMPLEMENTATION: Friday Restaurant Confirmation Workflow`
- **Description**: `Build Friday order confirmation system with inventory checking against SSCS, out-of-stock alert system, order modification interface for Tessa, confirmation email automation to restaurants by 4pm Friday, Sunday cutoff lock.`
- **Assignee**: `AI IDE Agent`
- **Priority**: `Medium`
- **Feature**: `friday_workflow`
- **Status**: `Backlog`

### **Task 14: Tuesday Delivery Optimization System**
- **Title**: `🔧 IMPLEMENTATION: Tuesday Delivery Optimization System`
- **Description**: `Build Tuesday delivery quick checkout optimization: invoice verification system, box scanning workflow, case vs bottle handling, automated charge to stored payment method, receipt generation with invoice + payment confirmation.`
- **Assignee**: `AI IDE Agent`
- **Priority**: `Medium`
- **Feature**: `tuesday_delivery`
- **Status**: `Backlog`

### **Task 15: System Monitoring & Health Checks**
- **Title**: `🔧 IMPLEMENTATION: System Monitoring & Health Checks`
- **Description**: `Implement comprehensive system monitoring with 99% uptime alerts, automated health checks, backup validation, disaster recovery procedures, and performance monitoring for all DABS automation components.`
- **Assignee**: `AI IDE Agent`
- **Priority**: `Low`
- **Feature**: `monitoring`
- **Status**: `Backlog`

---

## 🎯 **ADDING TASKS TO ARCHON**

### **Method 1: Through UI (Recommended)**
1. Click "Add Task" button in your Archon interface
2. Copy/paste each task definition above
3. Set proper priority and assignee
4. All agents will see the same tasks

### **Method 2: Bulk Import**
- Use the task definitions above to create all 15 tasks
- Start with Critical tasks (1-3) first
- Then High Priority (4-7)
- Then Medium Priority (8-11)
- Finally Implementation (12-15)

---

## 🌐 **UNIVERSAL ACCESS CONFIRMED**

Once tasks are added to Archon, ALL development platforms can access them:

- **✅ Cursor IDE**: Already configured via MCP
- **✅ Augment**: `MCP_SERVER_URL=http://localhost:8151/mcp/sse`
- **✅ Roo Code**: `ARCHON_ENDPOINT=http://localhost:8151`
- **✅ Any MCP Tool**: `localhost:8151` with SSE transport

---

## 🎯 **SUCCESS METRICS TO TRACK IN ARCHON**

- **90% Time Reduction**: Monthly DABS processing (10+ hours → <1 hour)
- **Error Rate**: <0.1% (vs current 2% manual rate)
- **Processing Speed**: <15 minutes for 1,239 SKUs
- **Staff Relief**: Return Tessa/Heather to 40-hour weeks
- **Universal Coordination**: Zero duplicate work across agents

---

**🎉 RESULT: Archon becomes the single source of truth for all DABS development work across all platforms and agents.**
