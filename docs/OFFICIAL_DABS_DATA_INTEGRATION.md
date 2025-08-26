# Official DABS Data Integration Guide

This guide explains how to integrate the complete official Utah DABS product catalog (4000+ items) into the restaurant ordering system.

## 📋 Overview

Based on the comprehensive documentation of Utah DABS data sources, we've created a system to process official DABS data and integrate it into our restaurant portal.

## 🔗 Official DABS Data Sources

### 1. Monthly Retail Price Books (PDF)
- **URL**: https://abs.utah.gov/vendors/monthly-price-books/
- **Formats**: Alphabetical, Category, Numeric
- **Contains**: CSC codes, product names, sizes, case packs, prices, categories
- **Updates**: Monthly (1st of each month)

### 2. Interactive Product List Spreadsheet (Excel) ⭐ **PRIMARY SOURCE**
- **URL**: https://abs.utah.gov/shop-products/interactive-product-list/
- **File Example**: "August-2025-Product-List_FY26_P2.xlsx"
- **Contains**: Complete product catalog with all fields
- **Updates**: Monthly/fiscal period
- **Best For**: Bulk data import and processing

### 3. DABS Online Product Locator
- **URL**: https://webapps2.abc.utah.gov/ProdApps/ProductLocatorCore
- **Contains**: Live inventory, real-time pricing, search functionality
- **Best For**: Real-time verification and availability checks

### 4. Special Order Products Portal
- **URL**: https://webapps2.abc.utah.gov/ProdApps/SpecialOrdersCore
- **Contains**: Special order items (status "S")
- **Best For**: Extended catalog beyond regular stock

### 5. Approved Canned Cocktails (RTDs)
- **URL**: Google Looker Studio report via DABS site
- **Contains**: RTD cocktails with ABV for on-premise sales
- **Best For**: Specialized cocktail products

### 6. Off-Premise Approved Products
- **URL**: https://abs.utah.gov/licenses-permits/off-premise-products
- **Contains**: Beer ≤5% ABV for grocery/convenience stores
- **Best For**: Off-premise retail products

## 🛠️ Integration Workflow

### Step 1: Download Official Excel File

1. Visit: https://abs.utah.gov/shop-products/interactive-product-list/
2. Download the latest Excel file (e.g., "August-2025-Product-List_FY26_P2.xlsx")
3. Place in: `data/official_dabs_sources/`

### Step 2: Process Excel Data

```bash
python3 scripts/process_official_dabs_excel.py
```

This script will:
- ✅ Parse all products from the official Excel file
- ✅ Apply DABS packaging standards for case sizing
- ✅ Generate UPC codes for SSCS integration
- ✅ Create comprehensive search terms
- ✅ Filter active products (status 1, L, N)
- ✅ Generate `official_dabs_catalog.json`

### Step 3: Update Restaurant Portal

```bash
python3 scripts/update_restaurant_portal_to_official_catalog.py
```

This script will:
- ✅ Update HTML to load from `official_dabs_catalog.json`
- ✅ Update console messages and references
- ✅ Ensure portal uses official data

### Step 4: Build and Deploy

```bash
cd archon-mcp/archon-ui-main
npm run build
git add .
git commit -m "Update to official DABS catalog with 4000+ products"
git push origin main
```

## 📊 Data Fields and Mapping

### DABS Excel Columns → Our Format

| DABS Field | Our Field | Description |
|------------|-----------|-------------|
| CSC | sku, vendor_item_code | Control State Code (unique ID) |
| Product Name | product_name, description | Full product name |
| Size | size | Volume (mL, L, etc.) |
| Case Pack | case_size | Units per case |
| Status | status | 1=General, S=Special, D=Discontinued |
| Category | category | Product category |
| Retail Price | price | Unit price |
| - | upc | Generated from CSC for SSCS |
| - | case_price | Calculated: price × case_size |
| - | search_terms | Generated for search functionality |

### Status Codes

| Code | Description | Include in Catalog |
|------|-------------|-------------------|
| 1 | General | ✅ Yes |
| L | Limited | ✅ Yes |
| N | New | ✅ Yes |
| S | Special Order | ⚠️ Optional |
| D | Discontinued | ❌ No |

### Case Sizing Rules (Based on Order 233813)

| Product Type | Case Size | Examples |
|--------------|-----------|----------|
| 750ml bottles | 12/case | Spirits, wines, liqueurs |
| 1L bottles | 6/case | Large spirits |
| 3L boxes | 4/case | Boxed wines |
| 500ml bottles | 12/case | Craft beer |
| 355ml cans | 24/case | Beer, cider |

## 🎯 Benefits of Official Data Integration

### ✅ Complete Product Catalog
- **4000+ authentic DABS products** instead of 28 demo items
- **Real pricing** from official DABS sources
- **Accurate case sizing** based on DABS packaging standards
- **Current product status** (active, limited, discontinued)

### ✅ SSCS Integration Ready
- **UPC codes generated** from CSC for barcode scanning
- **Case-to-unit conversions** for accurate ordering
- **Vendor item codes** matching DABS system
- **Complete product metadata** for seamless import

### ✅ Professional Restaurant Experience
- **Comprehensive search** across all DABS products
- **Category filtering** by official DABS categories
- **Real-time case calculations** for bulk ordering
- **Authentic product information** for informed decisions

### ✅ Automated Updates
- **Monthly refresh capability** with new Excel files
- **Consistent data format** across all products
- **Version tracking** and change management
- **Audit trail** of data sources and updates

## 🔄 Maintenance Schedule

### Monthly Updates (Recommended)
1. **Download** latest Excel file from DABS (around 1st of month)
2. **Process** with `process_official_dabs_excel.py`
3. **Test** catalog in development environment
4. **Deploy** updated catalog to production
5. **Verify** restaurant portal functionality

### Quarterly Reviews
- **Validate** case sizing rules against actual orders
- **Update** category mappings if DABS changes structure
- **Review** status code handling for new codes
- **Optimize** search terms and filtering

## 🚨 Important Notes

### Data Limitations
- **UPC codes**: Not provided by DABS, generated from CSC
- **ABV percentages**: Only in specialized lists (RTD, off-premise)
- **Detailed descriptions**: Limited to product names in Excel
- **Images**: Not available in DABS data sources

### Access Requirements
- **No API access**: DABS doesn't provide public APIs
- **Manual download**: Excel files must be downloaded manually
- **Update frequency**: Limited to DABS publication schedule
- **File format changes**: May require script updates if DABS changes Excel structure

### Integration Considerations
- **File size**: 4000+ products create large JSON files (~2-5MB)
- **Load time**: May need optimization for mobile devices
- **Search performance**: Consider indexing for large catalogs
- **Cache strategy**: Implement appropriate caching for production

## 📞 Support and Troubleshooting

### Common Issues

**Excel file not found**
- Ensure file is in `data/official_dabs_sources/`
- Check file permissions and format

**Parsing errors**
- Verify Excel file structure matches expected format
- Check for empty rows or unusual data

**Missing products in catalog**
- Verify status filtering (only 1, L, N included by default)
- Check category mapping and filtering

**Portal not loading new data**
- Ensure `official_dabs_catalog.json` is generated
- Verify portal HTML references correct file
- Clear browser cache after deployment

### Getting Help

1. **Check logs** from processing scripts for detailed error messages
2. **Verify file formats** match DABS documentation
3. **Test with smaller datasets** to isolate issues
4. **Review DABS website** for any format changes or updates

---

**This integration provides a complete, professional-grade restaurant ordering system with authentic DABS data and real-world case management capabilities.** 🏆
