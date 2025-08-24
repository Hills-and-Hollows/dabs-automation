EDI Electronic Delivery Invoices in SSCS (Computerized Daily Book)

Electronic Data Interchange (EDI) in SSCS refers to digital vendor invoices that can be imported directly into the Computerized Daily Book (CDB) system. This allows delivered inventory to be recorded without manual entry or item-by-item scanning. Below is a comprehensive guide on how EDI delivery invoices work in SSCS and how to implement them using official documentation and standards.

What is EDI in SSCS?

EDI (Electronic Data Interchange) is the computer-to-computer exchange of business documents in a standard format. In the SSCS CDB context, EDI enables a vendor’s invoice to be transmitted electronically into your back-office system. This serves as an electronic alternative to dealing with paper invoices or scanning each product’s barcode during a delivery
blog.sscsinc.com
. If your vendor supports EDI, the invoice data is sent directly into the CDB, eliminating the need to manually key in or scan each item one by one
sscsinc.com
.

 

Most EDI invoices follow the ANSI X12 standard – specifically the EDI 810 Invoice document, which is widely used in retail and grocery industries. (The EDI 810 is essentially an electronic invoice that sellers send to buyers to request payment
spscommerce.com
.) By adhering to such standards, the invoice file can be automatically read and processed by SSCS software without custom data entry.

How EDI Works with SSCS Daily Books (Inventory Receiving)

When a delivery arrives from a vendor who is EDI-enabled, two things arrive together: the physical products and an electronic invoice file (EDI file) summarizing those products. The CDB recognizes the incoming EDI invoice and uses it to record the delivery in your inventory instantly
blog.sscsinc.com
. This means you can add the entire shipment to your inventory all at once, instead of scanning boxes of items. The simultaneous arrival of the electronic invoice and goods makes the receiving process much faster and more accurate
blog.sscsinc.com
.

 

If the vendor is not set up for EDI, the fallback is to use SSCS’s handheld scanning or manual entry: you would scan the barcode of each delivered item type and enter the quantity delivered into the system
sscsinc.com
. EDI thus streamlines the process by skipping these manual steps whenever possible.

 

Once imported, the EDI invoice’s line-item data (item codes, descriptions, quantities, and costs) are recorded in the CDB. This automatically updates your on-hand inventory counts and purchase records, just as if you had entered an invoice by hand, but with far less effort and potential for error. You can even run discrepancy reports at receiving time – for example, to compare what was ordered versus what was delivered – since the EDI data is captured immediately
sscsinc.com
blog.sscsinc.com
.

Benefits of Using EDI for Deliveries in SSCS

Using EDI electronic invoices within SSCS’s Direct Store Deliveries workflow provides several advantages:

Automated Receiving: The entire delivery invoice can be posted in one action, automating item receiving and entry. This eliminates the need to scan or type in items one-by-one, greatly speeding up delivery processing
blog.sscsinc.com
. It adds the speed and accuracy of SSCS technology to what was once a manual process
blog.sscsinc.com
.

Improved Accuracy: Since data comes directly from the vendor’s system, mistakes from manual data entry are avoided. The CDB captures all item details, pricing, and totals as provided on the electronic invoice
blog.sscsinc.com
. This reduces paperwork and data entry errors for both the retailer and vendor
spscommerce.com
.

Price and Item Change Alerts: SSCS’s direct store delivery module automatically alerts you to any price changes or new items on the invoice
sscsinc.com
. For example, if a vendor changes the cost on an item or delivers a product not seen before, the system flags it so you can adjust retail pricing or confirm the new item in your database.

Inventory Database Updates: Newly delivered items from an EDI invoice are instantly added to your inventory database, which is fully searchable and interconnected. You can easily look up what was delivered, when it was purchased, and even send this updated information to your POS system with minimal effort
sscsinc.com
. Every vendor invoice is stored and accessible, so you gain a complete electronic history of purchases for analysis and auditing.

Automated Reordering: The CDB can use the detailed sales and inventory information (bolstered by EDI data) to perform Computer Assisted Ordering (CAO). With item-level sales history and recent delivery data, the system can generate optimal reorders so that you stock exactly what you need
sscsinc.com
blog.sscsinc.com
. This prevents over- or under-stocking and ties directly into the EDI process – when you place an electronic order, the vendor’s corresponding EDI invoice on delivery can be used to quickly receive those goods into inventory.

In short, EDI integration with SSCS makes direct store deliveries faster, more accurate, and information-rich, benefiting store operations and accounting on multiple fronts.

Supported EDI Vendor File Types and Delivery Methods

SSCS maintains a list of approved EDI vendors – these are suppliers whose electronic invoice file formats are known to be compatible with the CDB system
sscsinc.com
. Each approved vendor typically has an “invoice spec” (specification) on file with SSCS, indicating the format of the data they send. Many convenience store distributors use standardized formats such as:

ANSI X12 810 Invoice – the common EDI format for invoices (as mentioned above).

Industry-specific flat files (e.g. the PDI 7500 series format popular among wholesalers).

NAXML (XML) files – an XML format defined by the convenience/petroleum industry (for example, McLane Company uses a NAXML Item/Price file format)
portal.sscsinc.com
.

SSCS’s system can accept a variety of such formats as long as they match an approved vendor spec. The Central Price Book documentation for SSCS even lists accepted vendor file formats like PDI 7500 and NAXML for major suppliers
portal.sscsinc.com
. This means if your vendor can output any of these standard electronic invoice formats, you should be able to import it into the CDB (after proper setup).

 

File Delivery Methods: Vendors send EDI invoice files to your SSCS system using one of two main methods:

Email Attachments: Many vendors deliver the invoice file via email. Typically, the EDI file (often a text file like .txt, .csv, or .xml) is attached to an email sent to a designated address. SSCS provides each client with a unique EDI email address (using an @edidelivery.com domain) where these files should be sent or forwarded
sscsinc.com
. The CDB monitors that inbox and imports any recognized vendor invoice files. (For example, if a vendor posts an invoice on a portal like OneDrive instead of emailing, you can download it and forward it to your ...@edidelivery.com address to ingest it
sscsinc.com
.)

AS2 Transfers: Some larger vendors use AS2, which is a direct computer-to-computer protocol for securely exchanging EDI data over the internet. SSCS supports AS2 transfers – in these cases, the vendor’s system will send the invoice file straight to an SSCS server (no manual email handling). The vendor list identifies which suppliers have AS2 transfer verified for their EDI files
sscsinc.com
sscsinc.com
. If your vendor uses AS2, you would work with SSCS support to configure the connection, but the end result is similarly automatic import of the invoice.

The SSCS Approved Vendors page clearly indicates for each vendor whether they send invoices by email or AS2 (or in a few cases via a third-party or special arrangement)
sscsinc.com
sscsinc.com
. It’s a good practice to check this list for your specific vendors. If a vendor is not on the approved list, it means they haven’t yet provided a compatible electronic format to SSCS – in those cases, you may need to rely on scanning or talk to the vendor about starting EDI. (SSCS can also work with “data translation companies” to handle non-standard formats – more on this below.)

Setting Up EDI Electronic Invoices in the CDB

Implementing EDI invoices in your SSCS Daily Book involves a few setup steps:

Verify Vendor EDI Support: First, confirm that your supplier is an SSCS-approved EDI vendor. You can find the complete list on the SSCS website under Vendors
sscsinc.com
 or in the “Approved EDI Vendors” section
sscsinc.com
. If your vendor is listed, note the invoice spec name and the transfer method (Email or AS2). If they are not listed, you might encourage them to work with SSCS or use a translation service, but initially you’ll handle those deliveries via barcode scanning into the system.

Obtain the Invoice File Specification: Each approved vendor has a defined format for their electronic invoice. Obtain the file specification document for your vendor’s EDI invoices. This might come from SSCS (they maintain specs for each vendor) or directly from the vendor or EDI provider. For example, vendors using a standard like X12 810 or PDI will have a spec detailing the file layout (which fields correspond to UPC, quantity, cost, etc.). Having this spec is useful for understanding and troubleshooting the data import. SSCS support can provide the spec sheet or mapping details for any vendor on their approved list upon request.

Set Up EDI File Delivery: Arrange for the vendor’s EDI files to reach your CDB. If using email, give the vendor your store’s designated EDI email address (the one ending in @edidelivery.com) and have them email the invoice file whenever a delivery is made. Some store operators set up an auto-forward rule from their regular email to the SSCS EDI address if the vendor can only send to the store’s personal email. If using AS2, coordinate with SSCS support to establish the AS2 connection – SSCS will provide the AS2 endpoint details and credentials to the vendor. Once configured, AS2 transmissions are automatic.

Importing the Invoice: When the EDI file is received (via email or AS2), the CDB software will import it and create a pending Direct Store Delivery record in your system. This record contains all the line items from the invoice. In CDBWin (the SSCS back-office interface), you would typically navigate to the Direct Store Deliveries or Vendor Import section to review and post the invoice. You can verify the items, quantities, and prices, then finalize the delivery to update inventory on-hand counts and create the payable entry. The Central Price Book or CDB may provide an import log or “outside updates” review screen for new items or cost changes that came in with the EDI file
sscsinc.com
 – you should review any alerts (e.g. adjust retail prices for cost changes) and accept new items into inventory as needed.

Handle New Items or Errors: If the EDI file contains any items that are not yet in your database (new UPCs), the system will flag them. SSCS provides an interface to add these new items to your inventory list (often pulling details from the invoice like description and category)
sscsinc.com
. Similarly, if there are any format issues (e.g. the file didn’t import), you may need to consult the spec or have the vendor correct their file format. Common issues could be missing data fields or incorrect codes – these are usually resolved during the initial setup with help from support or a data translator.

Leverage Translation Services if Needed: If your vendor cannot output a format that SSCS understands, you have the option to use an EDI translation service. SSCS acknowledges several third-party companies (e.g., Chimpkey, Deep Water Software, Vendor Invoice Hub) that specialize in converting vendor invoices into SSCS-compatible files
sscsinc.com
. These services can take a PDF or proprietary format from the vendor and generate an electronic file matching an SSCS spec. While this may incur extra cost, it can enable EDI automation for vendors who aren’t natively supported.

Once set up, the process becomes routine: for each delivery, simply ensure the EDI invoice is sent, then retrieve/import it in CDB. The inventory is updated in seconds, and the invoice is recorded for accounting. You can then proceed with any reporting or payment steps as you normally would, confident that the data matches the vendor’s records.

Additional EDI Formats and Specifications for SSCS

In addition to the standard EDI 810 format, SSCS systems can work with a few other electronic invoice formats commonly used in the convenience store industry:

PDI 7500 Series – This is a flat-file format (text file with fixed-width or delimited fields) historically used by many distributors and supported by systems like PDI. SSCS lists many vendors whose “Invoice spec” corresponds to a PDI 7500 format variant
portal.sscsinc.com
. If your vendor uses a PDI file, SSCS can import it just like an EDI file (the setup in CDB might refer to it as a “Vendor Import” of type PDI 7500).

NAXML (NACS XML) – An XML-based standard from the National Association of Convenience Stores, often used by wholesalers for item and price data. SSCS supports NAXML for vendors like McLane
portal.sscsinc.com
. These files are XML documents that contain invoice details and can be imported via the Central Price Book or CDB vendor import function.

DEX/UCS (Direct Exchange) – Some deliveries, especially from snack and beverage vendors, might use DEX via a handheld device. DEX is a real-time data exchange standard at the store back door (scanning items and then transferring an invoice file over a serial connection). SSCS’s system is capable of receiving DEX invoices as well (the 2014 SSCS blog notes their CDB can take in a DEX file via a tool like StoreDEX)
blog.sscsinc.com
blog.sscsinc.com
. This is less common now in the age of internet, but worth knowing if you deal with older DSD methods.

Regardless of format, the goal is to have an electronic file that lists the invoice details in a structured way. All these formats (X12 EDI, PDI text, XML, DEX) contain similar information – items, quantities, costs, totals – just structured differently. SSCS provides a mapping for each supported format to the fields in the CDB. It’s important to use the exact format expected; for instance, a vendor’s “invoice spec” might require a certain file naming convention or particular columns in a CSV. Always refer to the official spec sheet for that format. If the file is correctly formatted, the SSCS import process will recognize it and parse everything into the system automatically.

 

Note: If you are interested in the technical standards, the ANSI X12 810 EDI specification defines segments like IT1 (line items with UPC, quantity, price) and TDS (total invoice amount) among others
spscommerce.com
spscommerce.com
. However, you usually do not need to manually read these files – the software does it. The key is making sure the trading partner (vendor) sends a file that conforms to one of the SSCS-accepted formats.

Official Documentation and Support Resources

Setting up EDI in SSCS is a technical process, but SSCS provides documentation and help to guide you:

SSCS User Manuals/Guides: The Computerized Daily Book and Central Price Book manuals contain sections on “Vendor Import” or EDI. These detail how to configure the import settings and list the supported formats. For example, the Central Price Book User’s Guide lists accepted vendor file formats and how to route files into the system’s EDI folder
portal.sscsinc.com
portal.sscsinc.com
. Check the SSCS customer portal or documentation site for any EDI-specific setup instructions.

Online Knowledge Base and Vendor List: The SSCS website’s Vendors page is a useful reference for EDI. It not only lists approved vendors but also has a section for Data Translation Companies (for third-party conversion services)
sscsinc.com
. Reviewing this page can be helpful to identify if your vendors are ready for EDI and what method they use.

Direct Support from SSCS: For detailed, location-specific guidance, you should reach out to SSCS Support. They can provide the exact steps or documentation for enabling EDI at your site. This includes obtaining your EDI email address, setting up AS2 connections, and providing examples of invoice files. You can contact SSCS support via email or phone – for instance, at support@sscsinc.com or (831) 755-1800
sscsinc.com
. They can also give you the “invoice spec” file or mapping details for each vendor you plan to use with EDI.

Vendor Collaboration: It often helps to talk with your vendor’s EDI coordinator. Vendors that are already on SSCS’s list will know about sending invoices to CDB. If a vendor is new to EDI, you might request that they format their invoices according to an SSCS-supported standard (like an 810 file or a PDI file) – possibly with the assistance of a translation service. Providing them the contact for SSCS or the spec documentation can speed up this process. As noted in an industry insight, many distributors are willing to adopt electronic invoicing when a retailer requests it, since all parties benefit from the efficiency
blog.sscsinc.com
.

Remember: once EDI is set up, it should run largely in the background – “the data just gets there — it just happens” as one expert put it
blog.sscsinc.com
. You’ll know it’s working when deliveries arrive and you see invoices populating your CDB without any manual input. Always test with a vendor on a small order first to ensure the data imports correctly, and keep an eye on those price change and new item alerts during initial runs.

By leveraging EDI electronic delivery invoices with SSCS, you can significantly reduce the labor at the back door, improve data accuracy, and keep your inventory and pricing instantly in sync with what your vendors deliver. For further details or troubleshooting, consult the official SSCS resources or reach out to their support team – they can provide the latest documentation and one-on-one assistance to ensure your EDI setup is successful
sscsinc.com
.

Sources