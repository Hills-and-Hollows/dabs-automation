# SSCS NAXML BusDocInvoice 1.5 — Implementation Guide
**Status:** Final  
**Last updated:** 2025-08-26 02:50 UTC  
**Audience:** Vendor EDI developers & SSCS CDB administrators  
**Scope:** Inbound **Conexxus NAXML _BusDocInvoice_ 1.5** electronic delivery invoices delivered via e‑mail or AS2 and imported into **SSCS Computerized Daily Book (CDB)**.

---

## 1) Why this guide
This guide turns the previous generic NAXML template into an **invoice‑only, vendor‑agnostic** specification that:
- Uses the **Conexxus BusDocInvoice 1.5** schema (not ItemSynch / ItemPrice).
- Includes the **namespace + schemaLocation** required by many validators.
- Documents **file naming & routing** conventions that affect SSCS’s “Receive and Convert” so your file goes to the **Invoice** importer instead of item/price maintenance.
- Codifies line math & **GTIN‑14** rules, and separates inbound invoice concerns from any **POS export**.

> Keep all **examples** out of the production template. Examples belong in test fixtures or separate example docs.

---

## 2) Quick start (10 steps)

1. **Prepare vendor record in CDB**  
   - Create/confirm the vendor **ID** (e.g., DABS) in CDB.  
   - In **EDI ▸ Map Vendor**, set *Import Type* to **NAXML (Invoice)** / BusDocInvoice (not Item/Price).  
   - Ensure there are **no blank rows** in mapping tables (avoid “index/primary key NULL” errors).

2. **Build the XML using the clean template** (`NAXML_BusDocInvoice_1.5_template.xml`).  
   - Fill every element marked **REQUIRED**.  
   - Use **GTIN‑14** in `<InvoiceUnitId identType="GTIN">`. Left‑pad to 14 if starting from UPC‑A (12).  
   - Use **ISO 4217** in `<Currency code="…"/>`.

3. **Namespace & schema** (root element)  
   ```xml
   <NAXML-BusDoc
     xmlns="http://www.naxml.org/Retail-EDI/Vocabulary/2003-10-16"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.naxml.org/Retail-EDI/Vocabulary/2003-10-16 NAXML-BusDocInvoice15.xsd">
   ```

4. **File name & extension (routing)**  
   - Name attachments to **signal “Invoice”** to the importer.  
   - **Do not** include “ItemPrice” or “ItemSynch” in the file name.  
   - If your site historically uses the **`.na.xml`** extension for NAXML, keep it (e.g., `Vendor_Invoice_123456.na.xml`).

5. **Delivery**  
   - **Email** the attachment to the site’s SSCS EDI mailbox (or transmit via **AS2** if configured).  
   - Subject line is informational only; routing is primarily by **attachment filename** and vendor mapping.

6. **Receive & Convert in CDB**  
   - In **EDI ▸ Receive And Convert**, fetch the message and convert.  
   - On success, a converted file is created and the **invoice appears in Open Invoice**.

7. **Reconcile line math**  
   - `LineItemNetAmt = InvoiceUnitCost × InvoiceUnitQty − Allowances + Charges`.  
   - `TotalInvoiceDueAmt = Σ(LineItemNetAmt) + Taxes`.

8. **Validate GTINs** (GS1 Mod‑10). See §6.

9. **Keep POS export concerns separate** (this guide is inbound‑only).

10. **Retain artifacts** (raw email, saved attachment, converted file) for audit.

---

## 3) Minimal BusDocInvoice 1.5 structure (required set)

- **Root**: `NAXML-BusDoc` with Conexxus namespace & schemaLocation (see §2.3).  
- **TransmissionHeader**: `TransmissionId`, `TransmissionDate`, `TransmissionTime`, `TransmissionStatus`.  
- **Parties**: `Supplier`, `Buyer`, `ShipTo`.  
- **Invoice**  
  - `Location/Name[@ident]` (store/site key)  
  - `InvoiceNumber`, `InvoiceDate`, `Currency[@code]`  
  - `InvoiceDetail/LineItem…` (repeatable)  
    - `InvoiceUnit/InvoiceUnitId[@identType="GTIN"]` (GTIN‑14)  
    - `InvoiceUnit/InvoiceUnitDescription`  
    - `InvoiceUnit/InvoiceUnitQty[@cstoreUOMBasis]`  
    - `InvoiceUnit/InvoiceUnitCost[@currency]`  
    - `InvoiceUnit/LineItemGrossAmt` (extended before allowances)  
    - `InvoiceUnit/LineItemNetAmt`  
    - *(optional)* `RetailUnitPricing/RetailPrice[@currency]`  
  - `InvoiceSummary/InvoiceTotals`  
    - `TotalInvoiceUnits`  
    - `TotalLineItemNetAmt[@currency]`  
    - `TotalTaxes`  
    - `TotalInvoiceDueAmt[@currency]`  
  - `Terms/TermsType[@ident]`, `Terms/InvoiceDueDate`

> Add other Conexxus elements only if your vendor/source system provides them (e.g., allowances, taxes, references).

---

## 4) Data & formatting rules

### 4.1 Identifiers
- **GTIN‑14** required for `<InvoiceUnitId identType="GTIN">`  
  - If you start with a **UPC‑A (12)**, left‑pad with two zeros to 14 digits before calculating/validating the check digit.  
  - No spaces/dashes. Preserve leading zeros.

### 4.2 Dates & times
- `TransmissionDate`, `InvoiceDate`: `YYYY-MM-DD`  
- `TransmissionTime`: `HH:MM:SS` (24‑hour)  
- `InvoiceDueDate`: `YYYY-MM-DD`

### 4.3 Currency
- Use `Currency/@code` (**attribute**) with ISO 4217 (e.g., `USD`). The element may be empty/self‑closed.

### 4.4 Units
- `InvoiceUnitQty/@cstoreUOMBasis`: common values include `each`, `case`, `pack`. Use the unit that matches your delivered quantity semantics.

### 4.5 Math & totals
- Ensure line extensions and invoice totals are internally consistent; receivers often reject on math mismatch.  
- Prefer two decimal places for currency amounts; avoid thousand separators.

---

## 5) File naming & routing (SSCS specifics)

Inbound processing in SSCS looks at **attachment names** and **vendor mapping** to decide which converter to run. Avoid names that imply *ItemPrice*/*ItemSynch* if your payload is a **BusDocInvoice**.

**Recommended patterns**
- `{VENDOR}_{INVOICE}_Invoice.na.xml`  
- `{VENDOR}_BusDocInvoice_{INVOICE}.na.xml`

**Do not use**
- `*_ItemPrice.xml`, `*_ItemSynch.xml` for invoice payloads.

If your site history shows converted backups like `…\edi\001\BAK\…_0.na.xml`, keep using **`.na.xml`** for NAXML invoices.

---

## 6) GTIN‑14 check digit (GS1 Mod‑10)

**Algorithm (right‑to‑left weighting):**
1. Start with the first 13 digits of the GTIN‑14.  
2. From **right to left**, multiply digits alternately by **3, 1, 3, 1…** (odd positions ×3).  
3. Sum the products.  
4. The check digit = `(10 − (sum mod 10)) mod 10`.  
5. Full GTIN = base13 + check digit.

> Validate every line’s GTIN before sending to reduce rejects.

---

## 7) Troubleshooting

| Symptom | Likely cause | Resolution |
|---|---|---|
| Email received; no invoice in Open Invoice | Attachment name implies **ItemPrice** or wrong import profile | Rename to **…Invoice.na.xml** and ensure **Map Vendor** import type = NAXML Invoice. Re‑ingest. |
| “File Not Found” in converter file picker | Converter is filtering for `*.na.xml` or for invoice mask | Keep `.na.xml` and/or use the site’s expected invoice naming mask. |
| “Index or primary key cannot contain a Null value” during mapping | Blank row(s) in mapping grid | Remove empty rows; fill all key columns in **Map Expenses/Map Vendor**. |
| Validation fail on GTIN | Wrong check digit or not 14 digits | Left‑pad to 14 digits; recalc GS1 Mod‑10. |
| Totals mismatch | Rounding or extension logic | Recompute: Net = Qty × UnitCost ± allowances; Invoice = ΣNet + taxes. |

---

## 8) Separation of concerns (important)
- This guide covers **inbound invoices only**.  
- **Do not** mix POS export or **Verifone‑specific** UPC fields with inbound invoice files. If your POS needs different UPC encodings, transform **after** the invoice safely lands in CDB.

---

## 9) Template files
- **Clean XML template**: `NAXML_BusDocInvoice_1.5_template.xml` (no example values).  
- Keep a copy of your **filled, validated** test files alongside the raw emails for audit.

---

## 10) Change log
- **Now**: Switched from ItemSynch/ItemPrice to **BusDocInvoice**; added Conexxus namespace/schema; clarified `.na.xml` routing; added GTIN‑14 rules; math checks; troubleshooting; separated POS export concerns.

---

*End of guide*
