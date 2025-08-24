# Create a mapping workbook template and a sample NAXML ItemPrice file for the team.
import pandas as pd
import os
from datetime import date

# Ensure directories
os.makedirs("/mnt/data/samples", exist_ok=True)

# Define the mapping workbook columns
columns = [
    "DABS_CSC_Code",
    "DABS_Product_Name",
    "DABS_Size_ml",
    "DABS_CasePack",
    "DABS_Status_Code",
    "DABS_Category",
    "DABS_Current_Retail",
    "DABS_New_Retail",
    "DABS_Effective_Date",
    "SSCS_Item_ID",
    "SSCS_Description",
    "SSCS_Department",
    "SSCS_TaxGroup",
    "SSCS_UnitOfMeasure",
    "SSCS_UnitList",
    "SSCS_VendorID",
    "SSCS_ApplyVendorListPrice",
    "SSCS_Pricing_Zone",
    "NAXML_MessageType",
    "NAXML_FileName",
    "NAXML_ItemID",
    "NAXML_ReceiptDescription",
    "NAXML_Price",
    "NAXML_EffectiveDate",
    "NAXML_TaxStructure",
    "NAXML_DepartmentMapping",
    "Comments"
]

# Create an empty DataFrame with one illustrative row
example = [ 
    "056828",                          # DABS_CSC_Code (from Alpha Price List example)
    "BACARDI MOJITO 1750ml",           # DABS_Product_Name
    1750,                               # DABS_Size_ml
    6,                                  # DABS_CasePack
    "U",                                # DABS_Status_Code
    "PREMIXED - MISC",                  # DABS_Category
    22.19,                              # DABS_Current_Retail (illustrative; adjust as needed)
    19.99,                              # DABS_New_Retail (illustrative new retail)
    date.today().isoformat(),           # DABS_Effective_Date
    "DABS-056828",                      # SSCS_Item_ID (using CSC as primary key)
    "BACARDI MOJITO 1.75L",             # SSCS_Description
    "Spirits",                          # SSCS_Department
    "Taxable",                          # SSCS_TaxGroup
    "Each",                             # SSCS_UnitOfMeasure
    1,                                  # SSCS_UnitList
    "DABS",                             # SSCS_VendorID
    True,                               # SSCS_ApplyVendorListPrice
    "ZONE0_GLOBAL",                     # SSCS_Pricing_Zone
    "ItemPrice",                        # NAXML_MessageType
    "DABS_YYYYMM_ItemPrice.xml",        # NAXML_FileName
    "DABS-056828",                      # NAXML_ItemID
    "BACARDI MOJITO 1.75L",             # NAXML_ReceiptDescription
    19.99,                              # NAXML_Price
    date.today().isoformat(),           # NAXML_EffectiveDate
    "DefaultTax",                       # NAXML_TaxStructure
    "Spirits",                          # NAXML_DepartmentMapping
    "Example row; replace with production values"
]

df = pd.DataFrame([example], columns=columns)

# Save the mapping workbook
mapping_path = "/mnt/data/DABS_to_SSCS_Mapping_Workbook.csv"
df.to_csv(mapping_path, index=False)

# Create a very small sample NAXML ItemPrice payload (illustrative)
naxml_sample = f"""<?xml version="1.0" encoding="UTF-8"?>
<NAXML_PBIPriceChange xmlns="http://www.naxml.org/POSBO/Vocabulary/2003-10-16">
  <TransmissionHeader>
    <StoreLocationID>HILLS_HOLLOWS_BOULDER</StoreLocationID>
    <TransmissionDate>{date.today().isoformat()}</TransmissionDate>
  </TransmissionHeader>
  <ItemPriceChange>
    <ItemID>DABS-056828</ItemID>
    <ReceiptDescription>BACARDI MOJITO 1.75L</ReceiptDescription>
    <PriceEffectiveDate>{date.today().isoformat()}</PriceEffectiveDate>
    <Price>19.99</Price>
  </ItemPriceChange>
</NAXML_PBIPriceChange>
"""

naxml_path = "/mnt/data/samples/DABS_ItemPrice_sample.xml"
with open(naxml_path, "w", encoding="utf-8") as f:
    f.write(naxml_sample)

mapping_path, naxml_path
Result
('/mnt/data/DABS_to_SSCS_Mapping_Workbook.csv',
 '/mnt/data/samples/DABS_ItemPrice_sample.xml')
Below is a technical‑specification research report that consolidates only publicly available, official documentation and aligns it to a no‑outreach implementation path. It is written to let our developers implement SSCS integrations using our existing SSCS credentials and tools we build, to import/export inventory and push price updates—while keeping QuickBooks in sync.

DABS → SSCS Integration Research Report (No‑Outreach Path)
Client: Hills & Hollows LLC (Utah Package Agency, Boulder, UT)
Scope: Automated pricing & inventory sync using only official, public docs; implementation using our SSCS/CDB/CPB access—no vendor contact required.

1) Executive Summary
Feasible, no‑outreach method: Use SSCS Central Price Book (CPB) Vendor Import to ingest price files we generate (in NAXML format), dropped into the SSCS EDI folder per site. CPB stages changes in Outside Updates, then we Distribute to Sites (DTS)—manually or on a Scheduled Task. This flow is fully documented by SSCS and requires only credentials we already have (CDB/CPB login; secure access to the EDI directory). 
portal.sscsinc.com
+1

Standards: CPB’s Vendor Import supports NAXML ItemSynch/ItemPrice (listed for McLane). We can leverage that standards‑based format for our own generated “vendor file” (DABS → NAXML) and deposit it to the EDI directory CPB watches. 
portal.sscsinc.com

DABS inputs: Utah DABS publishes official Monthly Price Books (Alpha/Master Category/Numeric lists) and an interactive spreadsheet export for the current period—sufficient for automated download & transform. 
Utah DABS
+1

POS distribution: CPB distributes accepted changes to CDB sites/zones and then to POS via SSCS poller interfaces (Verifone Commander/RubyCi supported). 
portal.sscsinc.com
sscsinc.com

Accounting: CDB includes a G/L Bridge to create import files for QuickBooks and other GLs (we can consume that export into QBDT via IIF; QuickBooks Desktop officially supports IIF import). 
sscsinc.com
QuickBooks

2) Source Documents (Key Passages & What They Enable)
SSCS Central Price Book User’s Guide (v4.x) — official PDF

Vendor Import Setup supports “a variety of vendor file formats”, including McLane – NAXML ItemSynch/ItemPrice; files are delivered to the system’s EDI folder; File Mask supports *.xml. This is the technical basis for a no‑outreach, file‑based integration. 
portal.sscsinc.com

Vendor Import procedure and Outside Updates review; Apply Vendor List Price option (default behavior is to ignore list prices unless enabled). 
portal.sscsinc.com
+1

Distribute to Sites (DTS) mechanics and Scheduled Tasks to automate DTS. 
portal.sscsinc.com
+2
portal.sscsinc.com
+2

SSCS Vendors (Approved Vendors & Formats) — public list

Confirms Approved Central Price Book Vendors, including McLane – NAXML ItemSynch/ItemPrice; corroborates that CPB’s vendor import accepts NAXML. 
sscsinc.com

SSCS POS Interface — product page

Describes SSCS poller interfaces for POS (incl. Verifone Commander/RubyCi) and uploading prices to the console. This is how DTS ultimately programs the registers. 
sscsinc.com

SSCS Bookkeeping & Computerized Daily Book (CDB)

Lists QuickBooks under Integration with General Ledger. The G/L Bridge “creates an import file” that QuickBooks can ingest. 
sscsinc.com
+1

Utah DABS (official site)

Monthly Price Books (Alpha/Master Category/Numeric), and interactive product spreadsheet export; product attributes include CSC (unique product code) and Status codes—both needed for mapping. 
Utah DABS
+1

Conexxus (formerly PCATS) NAXML references

Retail Merchandise Data Exchange overview + Design Rules for XML; establishes that NAXML is the standardized schema family used for POS/Back‑Office interchange (e.g., PBIMaintenance/Item/Price). 
conexxus.org
+1

3) Target Architecture (No‑Vendor‑Contact Path)
Flow (monthly or ad‑hoc):

Fetch DABS data (Alpha/Master/Numeric lists and/or interactive spreadsheet) → normalize to tabular. 
Utah DABS
+1

Transform to NAXML (ItemPrice and, if needed, ItemMaintenance for new items). Use NAXML/Conexxus naming and required transmission header fields per the public design rules. 
conexxus.org

Deliver file(s) to SSCS EDI folder for the target site (set File Mask to *.xml or DABS*.xml). CPB Vendor Import will pick up files in this folder. 
portal.sscsinc.com

CPB → Outside Updates: changes are staged; ensure Apply Vendor List Price is enabled when we want the vendor retail to carry through. 
portal.sscsinc.com

CPB → DTS (Distribute to Sites): push accepted changes to CDB sites/zones and then to POS via the SSCS poller (e.g., Verifone Commander). Optionally automate via Scheduled Tasks. 
portal.sscsinc.com
+1

Accounting: Use CDB G/L Bridge to generate QuickBooks‑ready import files for sales/A/R/A/P; ingest with QuickBooks Desktop IIF import (officially supported by Intuit). 
sscsinc.com
QuickBooks

4) Technical Specifications & Mappings
4.1 CPB Vendor Import (What we must configure)
Import Type: select NAXML ItemSynch/ItemPrice (listed under McLane, but format is standard NAXML). 
portal.sscsinc.com

File Location: CPB uses a per‑site EDI folder. We deliver XML files there. (We can copy via RDP session or map a network path from our integration host.) 
portal.sscsinc.com

File Mask: narrow to *.xml (or DABS*.xml) to avoid picking up unrelated EDI files. 
portal.sscsinc.com

Vendor Zone: CPB expects a vendor‑defined zone present in the file; we’ll emit a consistent zone ID in the NAXML payload and select the target CDB zone to receive it. 
portal.sscsinc.com

Apply Vendor List Price: enable this in Preferences if we want imported list/retail to override defaults; CDB ignores list prices by default. 
portal.sscsinc.com

Processing path in CPB: Vendor Import → Outside Updates (review/accept) → Distribute to Sites (manual or Scheduled Task). 
portal.sscsinc.com
+1

4.2 DABS → SSCS field mapping (minimum viable)
DABS field (source)	Needed for	CPB/CDB/NAXML target
CSC (unique product ID) – interactive list	Key	ItemID / SKU in NAXML & CPB Item ID
Product Name / Description	Receipt/long desc.	ReceiptDescription / Description
Category codes (Div/Dept/Class)	Dept mapping	CPB Department / price book grouping
Status (A/D/L/X/U…)	Lifecycle flags	(Optional) Staging logic; Inactive rules
Size (mL)	UoM/pack	UnitList / UOM / Pack
Retail price (current/new & effective date—published with each monthly list)	Price	NAXML ItemPrice (Price, PriceEffectiveDate)

DABS source references: Monthly Price Books index + interactive spreadsheet page (which describes CSC and status codes). 
Utah DABS
+1

4.3 NAXML payloads we generate
Message types:

ItemPrice for monthly price changes (primary).

ItemMaintenance for adds/fixes when needed (description, department, size).

Structure: follow Conexxus/NAXML naming & header conventions (Transmission header, party/store identifiers, effective dates). 
conexxus.org

Note: CPB explicitly lists NAXML ItemSynch/ItemPrice as supported import types (McLane profile), establishing that CPB ingests standard NAXML XML into the price book pipeline. 
portal.sscsinc.com

4.4 Distribution to registers (POS)
After acceptance, use Distribute to Sites to push changes to CDB sites/zones and onward to POS via SSCS pollers (Verifone Commander/RubyCi listed). This can be scheduled in CDB (Schedule Type CPB DTS). 
portal.sscsinc.com
+1
sscsinc.com

4.5 Accounting export (QuickBooks)
Use CDB G/L Bridge to generate QuickBooks import files for sales/A/R/A/P. QuickBooks Desktop officially supports IIF import; we can include a post‑DTS accounting export in our runbook. 
sscsinc.com
QuickBooks

5) Implementation Plan (what devs do now)
5.1 Access & environment
SSCS access: RDP to Sunray / CDB/CPB with our credentials. 
sscsinc.com

Locate per‑site EDI folder (on the SSCS host) for Vendor Import; note the path used for File Location in CPB. 
portal.sscsinc.com

Create a CPB “vendor” profile labeled DABS:

Import Type: NAXML ItemSynch/ItemPrice.

File Location: site’s EDI subfolder.

File Mask: DABS*.xml.

Vendor Zone: set a static code we also place in the file header (e.g., ZONE0_GLOBAL). 
portal.sscsinc.com

Preferences: enable Apply Vendor List Price if we want imported list/retail to be honored. 
portal.sscsinc.com

5.2 Our integration services (build)
DABS Fetcher

Pulls the latest Monthly Price Book PDFs and/or the interactive spreadsheet export (preferred for machine‑readable). 
Utah DABS
+1

Normalizer & Variance Engine

Parses spreadsheet into canonical items (CSC, name, size, category, status, price, effective date).

Compares to last accepted SSCS snapshot for variance report (for management/audit).

NAXML Generator

Emits ItemPrice (primary) and ItemMaintenance (as needed); includes TransmissionHeader, consistent Vendor Zone string, effective dates, and mapped department/tax structures per our configuration. 
conexxus.org

Drop‑off to SSCS

Copies produced DABS_YYYYMM_ItemPrice.xml into the EDI site folder observed by CPB Vendor Import (RDP copy or a secure mapped path). 
portal.sscsinc.com

Orchestration

Trigger CPB Vendor Import (user‑initiated or by schedule) → Outside Updates → Distribute to Sites (manual for UAT; Scheduled Task for production). 
portal.sscsinc.com
+1

Accounting

After DTS, run CDB G/L Bridge → produce QuickBooks import → IIF import into QuickBooks Desktop (or equivalent method per our QuickBooks edition). 
sscsinc.com
QuickBooks

6) Error Handling, Audit, and Monitoring
Outside Updates is the governed staging queue. We can script a checklist that confirms counts and deltas before acceptance. 
portal.sscsinc.com

Item Conflicts report and DTS report in CPB help catch data mismatches before POS programming. 
portal.sscsinc.com

Email Report and Scheduled Tasks documented by SSCS support alerts/automation. 
portal.sscsinc.com

7) Security & Access (no outreach required)
Sunray Cloud Hosting provides secure RDP access to the SSCS environment; we only need our login. We do not need external vendor access to complete this design. 
sscsinc.com

File delivery to EDI occurs within the hosted Windows environment (RDP copy or internal share); CPB reads from that path. 
portal.sscsinc.com

8) Acceptance Criteria (technical)
CPB imports DABS NAXML files without manual file conversion (visible entries in Outside Updates). 
portal.sscsinc.com

Apply Vendor List Price honored—resulting retail in CPB equals DABS retail for affected items. 
portal.sscsinc.com

DTS successfully schedules & runs (Schedule Type CPB DTS), pushing to all mapped sites; POS receives updated prices via SSCS poller. 
portal.sscsinc.com
sscsinc.com

QuickBooks import succeeds via CDB G/L Bridge generated file (e.g., IIF into QBDT). 
sscsinc.com
QuickBooks

9) Developer Artifacts (ready to use)
Mapping workbook template (CSV):
Download: DABS_to_SSCS_Mapping_Workbook.csv
Columns cover DABS → CPB/CDB → NAXML, including zone, tax, department, and file naming fields.

Sample NAXML ItemPrice file:
Download: DABS_ItemPrice_sample.xml
(Illustrative structure aligned to Conexxus naming; adjust header/store IDs and pricing payload to production.) 
conexxus.org

10) Runbook (Production)
Fetch & transform: DABS monthly spreadsheet → normalize → generate DABS_YYYYMM_ItemPrice.xml. 
Utah DABS

Deposit: Copy XML to EDI folder for the site; ensure File Mask matches. 
portal.sscsinc.com

Import: In CPB, run Vendor Import → review Outside Updates → accept. 
portal.sscsinc.com

Distribute: Run Distribute to Sites (or rely on Scheduled Task – CPB DTS). 
portal.sscsinc.com

Verify: Run DTS Report and Item Conflicts as needed; confirm POS price push (poller status). 
portal.sscsinc.com

Accounting: Run G/L Bridge and import to QuickBooks. 
sscsinc.com
QuickBooks

11) Notes & Inferences (clearly marked)
Why NAXML? SSCS documents NAXML ItemSynch/ItemPrice as an accepted CPB import format (via McLane profile), and Conexxus publishes public design rules—so generating our own NAXML files is the most standards‑aligned way to load DABS prices without vendor coordination. This is an inference based on SSCS’s listed acceptance of NAXML and Conexxus documentation. 
portal.sscsinc.com
conexxus.org

QuickBooks format: SSCS states CDB “creates an import file” for common GLs (including QuickBooks). QuickBooks Desktop officially supports IIF imports; therefore an IIF‑based handoff is a reasonable default unless our specific QuickBooks edition dictates another import path. (Inference tied to SSCS GL Bridge statement + Intuit IIF support.) 
sscsinc.com
QuickBooks

12) Appendix — Key Screens & Excerpts (from SSCS PDF)
Vendor Import Setup: *“A variety of vendor file formats are supported… File Location: …delivered to your system’s EDI folder… File Mask e.g., .xml… Vendor Zone… Price Book Zone…” (see included screenshots in the manual pages referenced). 
portal.sscsinc.com

Vendor Import → Outside Updates flow and Apply Vendor List Price note: “Default behavior of the CDB is to ignore list prices… select Apply Vendor List Price…” 
portal.sscsinc.com
+1

Scheduling DTS: “Central Price Book allows you to distribute changes to sites automatically using the Scheduled Tasks feature of the CDB (Schedule Type: CPB DTS).” 
portal.sscsinc.com

Bottom Line
Using only public, official documentation, we can implement a zero‑touch (no vendor outreach) path:

DABS → NAXML → CPB Vendor Import → Outside Updates → DTS → POS, and

CDB G/L Bridge → QuickBooks,

all with tools we build and our SSCS credentials. The documents above are sufficient for developers to implement, test, and ship the automation. 
portal.sscsinc.com
+2
portal.sscsinc.com
+2
sscsinc.com
+1
Utah DABS
+1

Deliverables included:

Mapping workbook: Download CSV

Sample NAXML payload: Download XML

