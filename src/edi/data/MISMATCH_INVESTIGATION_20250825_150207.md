# DABS Order 233811 - Mismatch Investigation Report
**Generated**: 2025-08-25 15:02:07  
**Purpose**: Systematic investigation of UPC data discrepancies with authoritative citations  
**Scope**: Comparison between provided UPC data and actual NAXML file contents  

## 🎯 Executive Summary

This investigation analyzes significant discrepancies between provided UPC data and the actual DABS Order 233811 NAXML file. Key findings indicate **fundamental data misalignment** requiring immediate attention.

### 🚨 Critical Findings
- **DABS Code Mismatches**: 3 items
- **Missing Products**: 4 items not in actual order
- **Potential Matches**: 3 items requiring verification

## 📋 Actual NAXML File Contents

**Source File**: `src/edi/data/edi_output/DABS_20250825_143058_ItemPrice.xml`  
**Total Items**: 9  

### Actual Products in Order:

1. **ARETTE CLASICA BLANCO TEQUILA**
   - **DABS Code**: 039593
   - **Size**: 750ml
   - **Price**: $395.88
   - **Category**: SPIRITS
   - **Current UPC**: 08024400092

2. **WILLAMETTE VLY PINOT NOIR WL**
   - **DABS Code**: 087123
   - **Size**: 750ml
   - **Price**: $299.88
   - **Category**: WINE
   - **Current UPC**: 12345678901

3. **KING ESTATE PINOT GRIS SIGNATURE**
   - **DABS Code**: 523110
   - **Size**: 750ml
   - **Price**: $252.96
   - **Category**: WINE
   - **Current UPC**: EMPTY

4. **SEGURA VIUDAS BRUT 750ml - 733238**
   - **DABS Code**: 580790
   - **Size**: 750ml
   - **Price**: $167.88
   - **Category**: SPIRITS
   - **Current UPC**: EMPTY

5. **POE ROSÉ'23 750ml - 918761**
   - **DABS Code**: 908418
   - **Size**: 750ml
   - **Price**: $251.88
   - **Category**: SPIRITS
   - **Current UPC**: EMPTY

6. **LORENZA ROSE 750ml - 919829**
   - **DABS Code**: 918951
   - **Size**: 750ml
   - **Price**: $239.88
   - **Category**: SPIRITS
   - **Current UPC**: EMPTY

7. **SEGURA VIUDAS BRUT 750ml**
   - **DABS Code**: 733238
   - **Size**: 750ml
   - **Price**: $167.88
   - **Category**: SPIRITS
   - **Current UPC**: EMPTY

8. **POE ROSÉ'23 750ml**
   - **DABS Code**: 918761
   - **Size**: 750ml
   - **Price**: $251.88
   - **Category**: SPIRITS
   - **Current UPC**: EMPTY

9. **LORENZA ROSE 750ml**
   - **DABS Code**: 919829
   - **Size**: 750ml
   - **Price**: $239.88
   - **Category**: SPIRITS
   - **Current UPC**: EMPTY

## 🔍 Detailed Discrepancy Analysis

### 1. SUGAR HOUSE VODKA 1750ml

**Provided Data:**
- **DABS Code**: 039593
- **UPC**: 061526002605
- **Source Claim**: Utah ABS Price List [1]
- **Match Status**: NOT_IN_NAXML

**Investigation Findings:**

- ✅ **DABS Code Found**: 039593 exists in NAXML
- **Actual Product**: ARETTE CLASICA BLANCO TEQUILA
- **Actual Size**: 750ml
- **Name Match**: ❌ NO

**🔗 Official Verification Links for UPC 061526002605:**

- **GS1 GEPIR (Global Electronic Party Information Registry)**: [Global authority for UPC/GTIN standards](https://gepir.gs1.org/index.php/search-by-gtin?query=061526002605)
  - *Reliability*: DEFINITIVE

- **UPCitemdb - 667M+ Product Database**: [667+ million verified UPC records](https://www.upcitemdb.com/upc/061526002605)
  - *Reliability*: HIGH

- **Utah Division of Alcoholic Beverage Control**: [Official Utah DABS price list authority](https://abs.utah.gov/wp-content/uploads/Apr2024NumericPriceList.pdf)
  - *Reliability*: DEFINITIVE (for Utah)

---
### 2. ARETTE CLASICA BLANCO TEQUILA 1L

**Provided Data:**
- **DABS Code**: 087123
- **UPC**: 080244000923
- **Source Claim**: [UPCitemdb][Official][GS1][User Verified]
- **Match Status**: DABS_CODE_MISMATCH

**Investigation Findings:**

- ✅ **DABS Code Found**: 087123 exists in NAXML
- **Actual Product**: WILLAMETTE VLY PINOT NOIR WL
- **Actual Size**: 750ml
- **Name Match**: ❌ NO

**Similar Products Found:**

- **DABS Code**: 039593 - ARETTE CLASICA BLANCO TEQUILA (750ml)
  - *Similarity*: Shared keywords

**🔗 Official Verification Links for UPC 080244000923:**

- **GS1 GEPIR (Global Electronic Party Information Registry)**: [Global authority for UPC/GTIN standards](https://gepir.gs1.org/index.php/search-by-gtin?query=080244000923)
  - *Reliability*: DEFINITIVE

- **UPCitemdb - 667M+ Product Database**: [667+ million verified UPC records](https://www.upcitemdb.com/upc/080244000923)
  - *Reliability*: HIGH

- **Utah Division of Alcoholic Beverage Control**: [Official Utah DABS price list authority](https://abs.utah.gov/wp-content/uploads/Apr2024NumericPriceList.pdf)
  - *Reliability*: DEFINITIVE (for Utah)

---
### 3. WILLAMETTE VLY PINOT NOIR WL CLST 750ml

**Provided Data:**
- **DABS Code**: 523110
- **UPC**: 088586005625
- **Source Claim**: [Manufacturer][UPCitemdb][Retail]
- **Match Status**: DABS_CODE_MISMATCH

**Investigation Findings:**

- ✅ **DABS Code Found**: 523110 exists in NAXML
- **Actual Product**: KING ESTATE PINOT GRIS SIGNATURE
- **Actual Size**: 750ml
- **Name Match**: ❌ NO

**Similar Products Found:**

- **DABS Code**: 087123 - WILLAMETTE VLY PINOT NOIR WL (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 523110 - KING ESTATE PINOT GRIS SIGNATURE (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 580790 - SEGURA VIUDAS BRUT 750ml - 733238 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 908418 - POE ROSÉ'23 750ml - 918761 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 918951 - LORENZA ROSE 750ml - 919829 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 733238 - SEGURA VIUDAS BRUT 750ml (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 918761 - POE ROSÉ'23 750ml (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 919829 - LORENZA ROSE 750ml (750ml)
  - *Similarity*: Shared keywords

**🔗 Official Verification Links for UPC 088586005625:**

- **GS1 GEPIR (Global Electronic Party Information Registry)**: [Global authority for UPC/GTIN standards](https://gepir.gs1.org/index.php/search-by-gtin?query=088586005625)
  - *Reliability*: DEFINITIVE

- **UPCitemdb - 667M+ Product Database**: [667+ million verified UPC records](https://www.upcitemdb.com/upc/088586005625)
  - *Reliability*: HIGH

- **Utah Division of Alcoholic Beverage Control**: [Official Utah DABS price list authority](https://abs.utah.gov/wp-content/uploads/Apr2024NumericPriceList.pdf)
  - *Reliability*: DEFINITIVE (for Utah)

---
### 4. KING ESTATE PINOT GRIS SIGNATURE 750ml

**Provided Data:**
- **DABS Code**: 580790
- **UPC**: 088586004017
- **Source Claim**: [Manufacturer][UPCitemdb][Wine-Searcher]
- **Match Status**: DABS_CODE_MISMATCH

**Investigation Findings:**

- ✅ **DABS Code Found**: 580790 exists in NAXML
- **Actual Product**: SEGURA VIUDAS BRUT 750ml - 733238
- **Actual Size**: 750ml
- **Name Match**: ❌ NO

**Similar Products Found:**

- **DABS Code**: 087123 - WILLAMETTE VLY PINOT NOIR WL (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 523110 - KING ESTATE PINOT GRIS SIGNATURE (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 580790 - SEGURA VIUDAS BRUT 750ml - 733238 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 908418 - POE ROSÉ'23 750ml - 918761 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 918951 - LORENZA ROSE 750ml - 919829 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 733238 - SEGURA VIUDAS BRUT 750ml (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 918761 - POE ROSÉ'23 750ml (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 919829 - LORENZA ROSE 750ml (750ml)
  - *Similarity*: Shared keywords

**🔗 Official Verification Links for UPC 088586004017:**

- **GS1 GEPIR (Global Electronic Party Information Registry)**: [Global authority for UPC/GTIN standards](https://gepir.gs1.org/index.php/search-by-gtin?query=088586004017)
  - *Reliability*: DEFINITIVE

- **UPCitemdb - 667M+ Product Database**: [667+ million verified UPC records](https://www.upcitemdb.com/upc/088586004017)
  - *Reliability*: HIGH

- **Utah Division of Alcoholic Beverage Control**: [Official Utah DABS price list authority](https://abs.utah.gov/wp-content/uploads/Apr2024NumericPriceList.pdf)
  - *Reliability*: DEFINITIVE (for Utah)

---
### 5. SEGURA VIUDAS BRUT 750ml

**Provided Data:**
- **DABS Code**: 733238
- **UPC**: 033293002002
- **Source Claim**: [Freixenet/Segura][UPCitemdb][Retail]
- **Match Status**: POTENTIAL_MATCH

**Investigation Findings:**

- ✅ **DABS Code Found**: 733238 exists in NAXML
- **Actual Product**: SEGURA VIUDAS BRUT 750ml
- **Actual Size**: 750ml
- **Name Match**: ✅ YES

**Similar Products Found:**

- **DABS Code**: 580790 - SEGURA VIUDAS BRUT 750ml - 733238 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 908418 - POE ROSÉ'23 750ml - 918761 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 918951 - LORENZA ROSE 750ml - 919829 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 733238 - SEGURA VIUDAS BRUT 750ml (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 918761 - POE ROSÉ'23 750ml (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 919829 - LORENZA ROSE 750ml (750ml)
  - *Similarity*: Shared keywords

**🔗 Official Verification Links for UPC 033293002002:**

- **GS1 GEPIR (Global Electronic Party Information Registry)**: [Global authority for UPC/GTIN standards](https://gepir.gs1.org/index.php/search-by-gtin?query=033293002002)
  - *Reliability*: DEFINITIVE

- **UPCitemdb - 667M+ Product Database**: [667+ million verified UPC records](https://www.upcitemdb.com/upc/033293002002)
  - *Reliability*: HIGH

- **Utah Division of Alcoholic Beverage Control**: [Official Utah DABS price list authority](https://abs.utah.gov/wp-content/uploads/Apr2024NumericPriceList.pdf)
  - *Reliability*: DEFINITIVE (for Utah)

---
### 6. BUCKLIN BAMBINO ZIN'22 750ml

**Provided Data:**
- **DABS Code**: 908418
- **UPC**: 892159000012
- **Source Claim**: [Manufacturer][UPCitemdb]
- **Match Status**: NOT_IN_NAXML

**Investigation Findings:**

- ✅ **DABS Code Found**: 908418 exists in NAXML
- **Actual Product**: POE ROSÉ'23 750ml - 918761
- **Actual Size**: 750ml
- **Name Match**: ❌ NO

**Similar Products Found:**

- **DABS Code**: 580790 - SEGURA VIUDAS BRUT 750ml - 733238 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 908418 - POE ROSÉ'23 750ml - 918761 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 918951 - LORENZA ROSE 750ml - 919829 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 733238 - SEGURA VIUDAS BRUT 750ml (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 918761 - POE ROSÉ'23 750ml (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 919829 - LORENZA ROSE 750ml (750ml)
  - *Similarity*: Shared keywords

**🔗 Official Verification Links for UPC 892159000012:**

- **GS1 GEPIR (Global Electronic Party Information Registry)**: [Global authority for UPC/GTIN standards](https://gepir.gs1.org/index.php/search-by-gtin?query=892159000012)
  - *Reliability*: DEFINITIVE

- **UPCitemdb - 667M+ Product Database**: [667+ million verified UPC records](https://www.upcitemdb.com/upc/892159000012)
  - *Reliability*: HIGH

- **Utah Division of Alcoholic Beverage Control**: [Official Utah DABS price list authority](https://abs.utah.gov/wp-content/uploads/Apr2024NumericPriceList.pdf)
  - *Reliability*: DEFINITIVE (for Utah)

---
### 7. POE ROSÉ'23 750ml

**Provided Data:**
- **DABS Code**: 918761
- **UPC**: 855976004104
- **Source Claim**: [POE Wines][Retail][UPCdb]
- **Match Status**: POTENTIAL_MATCH

**Investigation Findings:**

- ✅ **DABS Code Found**: 918761 exists in NAXML
- **Actual Product**: POE ROSÉ'23 750ml
- **Actual Size**: 750ml
- **Name Match**: ✅ YES

**Similar Products Found:**

- **DABS Code**: 580790 - SEGURA VIUDAS BRUT 750ml - 733238 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 908418 - POE ROSÉ'23 750ml - 918761 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 918951 - LORENZA ROSE 750ml - 919829 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 733238 - SEGURA VIUDAS BRUT 750ml (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 918761 - POE ROSÉ'23 750ml (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 919829 - LORENZA ROSE 750ml (750ml)
  - *Similarity*: Shared keywords

**🔗 Official Verification Links for UPC 855976004104:**

- **GS1 GEPIR (Global Electronic Party Information Registry)**: [Global authority for UPC/GTIN standards](https://gepir.gs1.org/index.php/search-by-gtin?query=855976004104)
  - *Reliability*: DEFINITIVE

- **UPCitemdb - 667M+ Product Database**: [667+ million verified UPC records](https://www.upcitemdb.com/upc/855976004104)
  - *Reliability*: HIGH

- **Utah Division of Alcoholic Beverage Control**: [Official Utah DABS price list authority](https://abs.utah.gov/wp-content/uploads/Apr2024NumericPriceList.pdf)
  - *Reliability*: DEFINITIVE (for Utah)

---
### 8. LARCHAGO RIOJA RESERVE 750ml

**Provided Data:**
- **DABS Code**: 918951
- **UPC**: 8410169111296
- **Source Claim**: [Manufacturer][UPCitemdb]
- **Match Status**: NOT_IN_NAXML

**Investigation Findings:**

- ✅ **DABS Code Found**: 918951 exists in NAXML
- **Actual Product**: LORENZA ROSE 750ml - 919829
- **Actual Size**: 750ml
- **Name Match**: ❌ NO

**Similar Products Found:**

- **DABS Code**: 580790 - SEGURA VIUDAS BRUT 750ml - 733238 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 908418 - POE ROSÉ'23 750ml - 918761 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 918951 - LORENZA ROSE 750ml - 919829 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 733238 - SEGURA VIUDAS BRUT 750ml (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 918761 - POE ROSÉ'23 750ml (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 919829 - LORENZA ROSE 750ml (750ml)
  - *Similarity*: Shared keywords

**🔗 Official Verification Links for UPC 8410169111296:**

- **GS1 GEPIR (Global Electronic Party Information Registry)**: [Global authority for UPC/GTIN standards](https://gepir.gs1.org/index.php/search-by-gtin?query=8410169111296)
  - *Reliability*: DEFINITIVE

- **UPCitemdb - 667M+ Product Database**: [667+ million verified UPC records](https://www.upcitemdb.com/upc/8410169111296)
  - *Reliability*: HIGH

- **Utah Division of Alcoholic Beverage Control**: [Official Utah DABS price list authority](https://abs.utah.gov/wp-content/uploads/Apr2024NumericPriceList.pdf)
  - *Reliability*: DEFINITIVE (for Utah)

---
### 9. LORENZA ROSE 750ml

**Provided Data:**
- **DABS Code**: 919829
- **UPC**: 898963000006
- **Source Claim**: [Lorenza Wines][UPCitemdb]
- **Match Status**: POTENTIAL_MATCH

**Investigation Findings:**

- ✅ **DABS Code Found**: 919829 exists in NAXML
- **Actual Product**: LORENZA ROSE 750ml
- **Actual Size**: 750ml
- **Name Match**: ✅ YES

**Similar Products Found:**

- **DABS Code**: 580790 - SEGURA VIUDAS BRUT 750ml - 733238 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 908418 - POE ROSÉ'23 750ml - 918761 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 918951 - LORENZA ROSE 750ml - 919829 (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 733238 - SEGURA VIUDAS BRUT 750ml (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 918761 - POE ROSÉ'23 750ml (750ml)
  - *Similarity*: Shared keywords

- **DABS Code**: 919829 - LORENZA ROSE 750ml (750ml)
  - *Similarity*: Shared keywords

**🔗 Official Verification Links for UPC 898963000006:**

- **GS1 GEPIR (Global Electronic Party Information Registry)**: [Global authority for UPC/GTIN standards](https://gepir.gs1.org/index.php/search-by-gtin?query=898963000006)
  - *Reliability*: DEFINITIVE

- **UPCitemdb - 667M+ Product Database**: [667+ million verified UPC records](https://www.upcitemdb.com/upc/898963000006)
  - *Reliability*: HIGH

- **Utah Division of Alcoholic Beverage Control**: [Official Utah DABS price list authority](https://abs.utah.gov/wp-content/uploads/Apr2024NumericPriceList.pdf)
  - *Reliability*: DEFINITIVE (for Utah)

---
### 10. HELPER BEER CIRCLE BACK IPA 473ml

**Provided Data:**
- **DABS Code**: 926272
- **UPC**: Not published
- **Source Claim**: [Helper Beer][Untappd][No UPC]
- **Match Status**: NOT_IN_NAXML

**Investigation Findings:**

- ❌ **DABS Code Missing**: 926272 NOT found in NAXML
- **Possible Reasons**:
  - Different order/batch
  - Incorrect DABS code mapping
  - Data from different time period

---

## 🏛️ Authoritative Sources for Verification

### Primary Authorities
1. **GS1 GEPIR** - [Global UPC Authority](https://gepir.gs1.org)
   - **Authority**: Definitive global UPC/GTIN registry
   - **Reliability**: DEFINITIVE
   - **Use**: Verify UPC authenticity and product details

2. **Utah Division of Alcoholic Beverage Control** - [Official DABS Authority](https://abs.utah.gov)
   - **Authority**: Official Utah DABS price list and product codes
   - **Reliability**: DEFINITIVE (for Utah)
   - **Use**: Verify DABS codes and official product listings

3. **UPCitemdb** - [667M+ Product Database](https://www.upcitemdb.com)
   - **Authority**: Comprehensive commercial UPC database
   - **Reliability**: HIGH
   - **Use**: Cross-reference product information

### Manufacturer Sources
- **Arette Tequila**: [Official Website](https://www.arette.com.mx)
- **King Estate Winery**: [Official Website](https://www.kingestate.com)
- **Willamette Valley Vineyards**: [Official Website](https://www.wvv.com)
- **Segura Viudas (Freixenet)**: [Official Website](https://www.freixenet.com)

## 📊 Investigation Summary

### Data Quality Assessment
- **Reliable Matches**: 0 items (no perfect matches found)
- **Requires Verification**: 3 items
- **Data Source Issues**: 7 items

### Recommended Actions

#### Immediate Actions
1. **Verify Data Source**: Confirm which NAXML file is the correct/current version
2. **Cross-Reference DABS Codes**: Use Utah ABS official price list to verify DABS codes
3. **Manufacturer Verification**: Contact manufacturers directly for UPC confirmation

#### Systematic Verification
1. **Use GS1 GEPIR**: Verify each provided UPC against official database
2. **Check Utah ABS List**: Cross-reference DABS codes with official state list
3. **Manufacturer Contact**: Direct verification with brand owners

#### Data Management
1. **Document Sources**: Maintain clear citations for all UPC data
2. **Version Control**: Ensure NAXML files are properly versioned and current
3. **Validation Process**: Implement systematic UPC verification before production

## ⚠️ Critical Warnings

1. **DO NOT USE** provided UPC data without verification - significant discrepancies found
2. **VERIFY DABS CODES** against official Utah ABS sources before proceeding
3. **CONFIRM NAXML VERSION** - ensure using current/correct order file
4. **VALIDATE SOURCES** - many provided citations lack specific URLs or timestamps

## 🎯 Next Steps

1. **Immediate**: Verify which NAXML file represents the actual Order 233811
2. **Short-term**: Use official verification links to confirm UPC authenticity
3. **Long-term**: Establish systematic UPC verification process with authoritative sources

**This investigation reveals fundamental data alignment issues requiring resolution before production use.**
