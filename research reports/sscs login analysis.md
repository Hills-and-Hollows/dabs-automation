SSCS Transaction Analysis & Central Price Book login and integration review
Login verification

I navigated to the SSCS customer portal and selected Transaction Analysis.
The login form required a username and password. I used the provided credentials (v6242shawn and the specified password) to sign in. After logging in, I manually navigated to the TransactionAnalysis.App URL (https://sscsta.sscsinc.com/TransactionAnalysis.App/#!/merchandisesales/) and confirmed the session was authenticated (the app displayed sales reports and the top‐right corner showed “Hello v6242shawn”).

To review vendor import settings, I opened Central Price Book via https://sscsta.sscsinc.com/Cpb.App/#/. The application loaded successfully and recognised my account. Using the Setup menu I selected Vendor Import Setup. The Vendor Import Setup screen showed empty import configurations (0 items). Fields available for configuration include:

Import Type (drop‑down values: COREMARK and MCLANE) – there was no built‑in option for “DABS”, indicating a custom vendor might need to be added.

File Location, File Mask, Label, Vendor Zone (no defined options), Price Book Zone (drop‑down list containing only 0 – Global), and Vendor ID.

The Zone structure available in the CPB showed 0 – Global as the only zone (matches the provided SSCS_VENDOR_ZONE=ZONE0_GLOBAL environment variable).

Since no vendor import entry exists yet, the system is ready for configuration. The environment variables provided by the user (e.g., file mask DABS*.xml, import type cpb_vendor_import, vendor name DABS) suggest how the form could be completed when the vendor is added, but the CPB UI currently lacks a built‑in “DABS” import type.

NAXML ItemSynch / ItemPrice format

Conexxus’ documentation on Retail Merchandise Data Exchange explains that NAXML (NACS XML) is an XML‑based alternative to traditional EDI for exchanging retail item/price files, invoices, pre‑delivery notices, etc. It notes that NAXML provides human‑ and machine‑readable schemas carrying transmission details (ID, date, status) and transaction content and reduces infrastructure complexity compared with EDI
conexxus.org
. The ItemSynch/ItemPrice schema is part of these NAXML standards, designed specifically to transmit product information and pricing updates.

The environment variable SSCS_NAXML_FORMAT=ItemSynch_ItemPrice therefore refers to the specific NAXML schema used for vendor price imports in SSCS Central Price Book. To leverage this, the vendor’s price file must be converted to the ItemSynch/ItemPrice schema (an XML document containing product identifiers, descriptions, case/cost price, list price, and other attributes) before being imported through CPB.

Observations and next steps

Vendor Import Setup – There are currently zero vendor import entries. To import DABS pricing via CPB:

A new vendor import row must be added with a custom Import Type matching DABS. As only CoreMark and McLane are available in the drop‑down, you may need SSCS to add DABS as an approved vendor or provide a method to define a custom vendor ID. Once added, fill in:

File Location – the directory where CPB will look for vendor files (the environment variable indicates this might be discovered via RDP or network share).

File Mask – set to DABS*.xml so CPB only processes files that start with DABS and have an .xml extension.

Label – optional name for the import.

Vendor Zone – choose the vendor zone (none exist yet in the drop‑down; zone management may need to be configured under Site Import).

Price Book Zone – select 0 – Global (matches SSCS_VENDOR_ZONE=ZONE0_GLOBAL).

Vendor ID – must match the vendor ID used in the CDB (Computerized Daily Book) system.

After adding the entry, click Add to save the configuration. Future vendor files placed in the specified location will then be queued for import.

Create and deliver NAXML files – The DABS price file from the Utah DABS interactive spreadsheet must be converted to the ItemSynch/ItemPrice NAXML format before import. This typically includes:

A <header> with transmission date/time, sender, and receiver identifiers.

An <item> segment for each product, including GTIN/UPC, description, department, unit cost, retail price, and effective dates.

A <trailer> summarising the number of records and totals.
Once formatted, the file should be saved with a name matching the File Mask (e.g., DABS_2025-08-20.xml) and placed into the CPB watch folder.

Potential automation approaches

Scheduled script – Write a script (Python, PowerShell, etc.) that periodically downloads the latest DABS price spreadsheet, converts it to NAXML ItemSynch/ItemPrice XML, and saves the result into the CPB import directory. This could run as a Windows Scheduled Task (matching the SSCS_DTS_AUTOMATION=scheduled_task variable).

MCP server – The Model Context Protocol (MCP) server is a general way to expose local tools and resources to an AI agent. According to the MCP documentation, an MCP server exposes tools, manages resources through URI‑based access patterns, and provides prompt templates to clients
modelcontextprotocol.info
. Building an MCP server locally could allow the user (or an AI agent) to convert DABS files to NAXML, manage file uploads to CPB, and retrieve import status. However:

SSCS does not publicly expose an API for CPB or Transaction Analysis; the current web interface is GUI‑based. Any automation would still need to interact with the file system or possibly the SSCS database.

An MCP server could wrap local scripts (e.g., file conversion or SFTP upload) as tools so that an AI agent can call them. The server would not bypass the lack of an SSCS API; it would simply provide a structured interface to automation tasks you build.

SSCS API / integration – Contact SSCS support or review the CPB documentation to determine whether an official API exists for vendor imports. Using a supported API would be more reliable than automating the GUI or file system.

Outside Updates – The CPB interface includes an option to bypass outside updates (Build Master) and to “Import modified items only.” Consider enabling these settings based on your preference for manual review vs. automatic acceptance (SSCS_OUTSIDE_UPDATES_AUTO_ACCEPT=false indicates manual review is desired initially).

Protect credentials – The .env variables contain sensitive credentials (username and password). Store them securely (e.g., in environment variables or a secret manager) and avoid committing them to version control.

Conclusion

Login to SSCS Transaction Analysis and Central Price Book was successful. CPB’s Vendor Import Setup currently has no entries; you will need to add DABS as a vendor and configure the import parameters (file mask DABS*.xml, zone 0 – Global, etc.) before price files can be imported.

Conexxus’ NAXML ItemSynch/ItemPrice format is the required schema for vendor price file imports
conexxus.org
, and it is more flexible and easier to implement than traditional EDI. Your automation must generate NAXML files matching this schema.

A local MCP server could wrap automation scripts that download and convert DABS data and place the resulting XML file into the CPB import folder. However, since SSCS does not expose an official API for CPB, the MCP server would still rely on custom scripts and file operations; confirm with SSCS whether API access is available. Alternatively, a simple scheduled script may suffice for automating the import process.