DABS New Workflow Analysis - Manual Labor Hours & Process Pain Points
Executive Summary
The Utah Department of Alcoholic Beverage Services (DABS) has implemented a major change to their package agency system, discontinuing their contract with Talech (the previous POS provider) effective July 1, 2025. This change has shifted significant manual labor responsibilities to Hills & Hollows management, creating multiple inefficient workflows that require immediate automation solutions.

What Changed: From Automated to Manual
The Old System (Pre-July 2025)
DABS provided Talech POS system: All hardware, software, and payment processing managed by DABS
Automatic payment processing: Alcohol sales payments went directly to DABS
Integrated reporting: Monthly reports generated automatically
No monthly fees: System cost covered by DABS

The New System (Post-July 2025)
Own and manage individual POS system: Hills & Hollows must purchase, maintain, and operate their own POS
Net 30 Invoice system: DABS sends weekly Net 30 invoices that must be paid by Hills & Hollows
Manual data entry and reconciliation: All processes now require manual intervention
Monthly fees: Estimated $150/month plus equipment costs

Current DABS Workflow: Step-by-Step Manual Processes
1. Invoice Input Process (Most Labor-Intensive)
Source:


Meeting follow up Tessa's detailed explanation to Shawn Owen (July 22, 2025)

Step-by-Step Manual Process:
Physical Delivery Verification
Manually count all items delivered
Report missing/broken items to DABS for credit
Physical verification required for every delivery
Invoice Data Entry into SSCS
DABS sends invoice with delivery (or emails PDF)
Manual line-by-line entry: Type 5-digit vendor item numbers for each product
Manual quantity adjustments: Enter quantities and prices individually
Complex bottle count conversions:
Invoice shows "24" for beer case
Must convert to actual inventory units:
6 units (if 4-packs)
4 units (if 6-packs)
Variables for singles, 12-packs, etc.
New Item Setup (High Labor for Restaurant Orders)
Manual inventory creation for items not in system
Physical UPC extraction: Open boxes, remove items, scan UPC codes
Complete data entry:
Item brand, name, size, quantity
Department classification
UPC, item number, price, cost
Restaurant orders require extensive new item setup since many items are unique
Payment Processing for Restaurant Orders
Create separate invoice for each restaurant order
Open each case, remove one item for scanning
Process through register, remove tax
Execute Elavon transaction with stored credit card info

2. Monthly Price Change Updates (Critical Time Window)
Source:


Meeting follow up "This is reallllllly annoying, please help! 🙃" - Tessa

Current Process:
Third week of month: DABS sends Excel spreadsheet with ALL package agency inventory (not just Hills & Hollows items)
Manual price matching: Go through entire spreadsheet, find items Hills & Hollows carries
Critical timing window: Must complete all price changes between close on last day of month and opening on first day of new month
Mixed change types: Some prices are permanent, others are monthly sales that expire
No automation: Entirely manual process for potentially hundreds of items

Pain Points:
Extremely tight deadline: Must be completed overnight between months
High error potential: Manual matching between DABS spreadsheet and SSCS inventory
Inefficient search: Searching through entire DABS catalog for relevant items
Risk of missed changes: No automated verification that all relevant items were updated

3. Monthly Reporting Process
Source:


Meeting follow up Plus monthly sales detail report instructions

Current Process:
Export reports from SSCS system
Manual reformatting into DABS required format
Data reconciliation between SSCS output and DABS reporting requirements
Submit monthly inventory and sales reports to DABS

Issues:
Format incompatibility: SSCS reports don't match DABS format requirements
Manual data manipulation: Requires reformatting and potential recalculation
Time-consuming research: Understanding proper report types and procedures

System Integration Challenges
SSCS Integration Decision
Source:




Kristel Owen and 1 other ... Tessa's Slack message (February 5, 2025)

"It would be our preference to use our current POS system, SSCS, for alcohol sales as well as store sales. Todd says that this is fine and they do not require any specific POS systems. If we used SSCS, we would only have one register and this would actually make things easier for both Heather and I and for staff."
Rationale for SSCS Integration:
Operational efficiency: Single register system for all transactions
Proven functionality: "Before the DABS got us set up with Talech, all of the alcohol sales were put through our store register and through SSCS so it has been tested"
Staff familiarity: Reduced training requirements
Reporting capability: SSCS can provide sufficient reporting for DABS requirements

Payment Processing Change
Source:




Kristel Owen and 1 other ... Key operational change

"The new way that paying the DABS will work is that they will send us weekly Net 30 Invoices that we can pay or set up ACH for."
Major Change Impact:
From automatic to manual: Previously automatic payment processing now requires manual invoice management
Weekly invoice volume: Multiple invoices to track and pay each month
Cash flow impact: Net 30 terms vs. previous automatic settlement
ACH setup required: Additional administrative setup needed

Specific Manual Labor Hours Analysis
Daily Tasks (New Manual Requirements)
Invoice Processing: 30-60 minutes per delivery
Basic delivery verification: 10 minutes
SSCS data entry: 15-30 minutes
New item setup (restaurant orders): 15-30 minutes per unique item
Payment Processing: 15 minutes per restaurant order
Item scanning and register processing
Elavon credit card transaction

Monthly Tasks (High Labor Impact)
Price Updates: 2-4 hours monthly
Critical constraint: Must be completed overnight between months
Error-prone: Manual matching of hundreds of potential items
High stress: Time-sensitive with significant operational impact if missed
Monthly Reporting: 1-2 hours monthly
SSCS report export and formatting
Data reconciliation and validation
DABS submission process

Weekly Tasks
Invoice Management: 30 minutes weekly
Review and process DABS Net 30 invoices
ACH payment setup and execution
Invoice tracking and reconciliation

Total Additional Manual Labor: Estimated 8-12 hours monthly

Critical Pain Points Requiring Automation
Priority 1: Monthly Price Updates
Business Impact: Highest risk due to critical timing window and operational consequences Automation Potential: High - Excel matching with SSCS inventory database Required Solution:
Automated cross-reference between DABS price spreadsheet and SSCS inventory
Batch price update capability
Automated change validation and reporting

Priority 2: Invoice Processing
Business Impact: High daily labor burden, especially for restaurant orders Automation Potential: Medium - Can automate data entry but physical verification still required Required Solution:
PDF invoice parsing and SSCS integration
Automated bottle count conversion logic
Pre-populated item templates for common products

Priority 3: Monthly Reporting
Business Impact: Medium - Monthly overhead but manageable manually Automation Potential: High - Format conversion and data mapping Required Solution:
SSCS report export transformation
Automated DABS format generation
Validation and submission workflow

Recommended Solutions for Streamlined Workflow
Immediate Implementation (Next 30 days)
Price Update Automation
Create automated Excel parser to match DABS prices with SSCS inventory
Implement batch price update functionality
Add validation and error checking
Invoice Processing Templates
Pre-configure common DABS vendor items in SSCS
Create bottle count conversion calculator
Standardize new item entry workflow

Medium-term Implementation (60-90 days)
Automated Reporting System
SSCS to DABS format converter
Automated monthly report generation
ACH payment automation for invoices
Integration API Development
Direct SSCS to DABS data integration where possible
Automated inventory synchronization
Real-time reporting capabilities

Long-term Optimization (90+ days)
Complete Workflow Automation
End-to-end invoice processing (except physical verification)
Automatic price change implementation
Comprehensive reporting and compliance dashboard

Cost-Benefit Analysis
Current Manual Labor Costs
8-12 hours monthly at $20-25/hour = $160-300/month in labor costs
Error risk costs: Potential pricing mistakes, compliance issues
Opportunity costs: Management time diverted from strategic activities

Automation Investment ROI
Development costs: One-time investment in automation
Monthly savings: $160-300 in direct labor + reduced error risk
Operational efficiency: Improved accuracy, compliance, and management focus
Scalability: System supports future growth without proportional labor increases

The automation solutions would pay for themselves within 3-6 months while significantly reducing operational stress and error risk for Hills & Hollows management.