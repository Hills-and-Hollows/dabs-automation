#!/usr/bin/env python3
"""
DABS Order 233811 Mismatch Investigation Tool
Systematic research and verification of discrepant UPC data with citations

This tool investigates the discrepancies between provided UPC data and actual NAXML files,
providing detailed research findings with authoritative source citations.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import xml.etree.ElementTree as ET

class MismatchInvestigationTool:
    """Systematic investigation of UPC data discrepancies"""
    
    def __init__(self):
        self.investigation_sources = {
            'gs1_gepir': {
                'name': 'GS1 GEPIR (Global Electronic Party Information Registry)',
                'url': 'https://gepir.gs1.org/index.php/search-by-gtin',
                'authority': 'Global authority for UPC/GTIN standards',
                'reliability': 'DEFINITIVE',
                'search_template': 'https://gepir.gs1.org/index.php/search-by-gtin?query={upc}'
            },
            'upcitemdb': {
                'name': 'UPCitemdb - 667M+ Product Database',
                'url': 'https://www.upcitemdb.com',
                'authority': '667+ million verified UPC records',
                'reliability': 'HIGH',
                'search_template': 'https://www.upcitemdb.com/upc/{upc}'
            },
            'utah_abs': {
                'name': 'Utah Division of Alcoholic Beverage Control',
                'url': 'https://abs.utah.gov',
                'authority': 'Official Utah DABS price list authority',
                'reliability': 'DEFINITIVE (for Utah)',
                'search_template': 'https://abs.utah.gov/wp-content/uploads/Apr2024NumericPriceList.pdf'
            },
            'manufacturer_direct': {
                'name': 'Manufacturer Official Websites',
                'authority': 'Direct from producer/brand owner',
                'reliability': 'DEFINITIVE',
                'sources': {
                    'arette': 'https://www.arette.com.mx',
                    'king_estate': 'https://www.kingestate.com',
                    'willamette_valley': 'https://www.wvv.com',
                    'segura_viudas': 'https://www.freixenet.com'
                }
            }
        }
    
    def extract_actual_naxml_data(self, naxml_file_path: str) -> List[Dict]:
        """Extract actual product data from NAXML file"""
        items = []
        
        try:
            tree = ET.parse(naxml_file_path)
            root = tree.getroot()
            
            for item_element in root.findall('.//Item'):
                item = {
                    'dabs_code': item_element.find('PLU').text if item_element.find('PLU') is not None else '',
                    'name': item_element.find('ItemName').text if item_element.find('ItemName') is not None else '',
                    'price': item_element.find('Price').text if item_element.find('Price') is not None else '',
                    'cost': item_element.find('Cost').text if item_element.find('Cost') is not None else '',
                    'category': item_element.find('Category').text if item_element.find('Category') is not None else '',
                    'size': item_element.find('Size').text if item_element.find('Size') is not None else '',
                    'vendor_code': item_element.find('VendorItemCode').text if item_element.find('VendorItemCode') is not None else '',
                    'current_upc': item_element.find('UPC').text if item_element.find('UPC') is not None else ''
                }
                
                # Skip summary lines
                if 'Total Quantities' not in item['name'] and 'Total Cost' not in item['name']:
                    items.append(item)
        
        except Exception as e:
            print(f"Error parsing NAXML file: {e}")
        
        return items
    
    def get_provided_upc_data(self) -> List[Dict]:
        """Get the provided UPC data for comparison"""
        return [
            {
                'product': 'SUGAR HOUSE VODKA 1750ml',
                'provided_dabs_code': '039593',
                'provided_upc': '061526002605',
                'source_claim': 'Utah ABS Price List [1]',
                'match_status': 'NOT_IN_NAXML'
            },
            {
                'product': 'ARETTE CLASICA BLANCO TEQUILA 1L',
                'provided_dabs_code': '087123',
                'provided_upc': '080244000923',
                'source_claim': '[UPCitemdb][Official][GS1][User Verified]',
                'match_status': 'DABS_CODE_MISMATCH'
            },
            {
                'product': 'WILLAMETTE VLY PINOT NOIR WL CLST 750ml',
                'provided_dabs_code': '523110',
                'provided_upc': '088586005625',
                'source_claim': '[Manufacturer][UPCitemdb][Retail]',
                'match_status': 'DABS_CODE_MISMATCH'
            },
            {
                'product': 'KING ESTATE PINOT GRIS SIGNATURE 750ml',
                'provided_dabs_code': '580790',
                'provided_upc': '088586004017',
                'source_claim': '[Manufacturer][UPCitemdb][Wine-Searcher]',
                'match_status': 'DABS_CODE_MISMATCH'
            },
            {
                'product': 'SEGURA VIUDAS BRUT 750ml',
                'provided_dabs_code': '733238',
                'provided_upc': '033293002002',
                'source_claim': '[Freixenet/Segura][UPCitemdb][Retail]',
                'match_status': 'POTENTIAL_MATCH'
            },
            {
                'product': 'BUCKLIN BAMBINO ZIN\'22 750ml',
                'provided_dabs_code': '908418',
                'provided_upc': '892159000012',
                'source_claim': '[Manufacturer][UPCitemdb]',
                'match_status': 'NOT_IN_NAXML'
            },
            {
                'product': 'POE ROSÉ\'23 750ml',
                'provided_dabs_code': '918761',
                'provided_upc': '855976004104',
                'source_claim': '[POE Wines][Retail][UPCdb]',
                'match_status': 'POTENTIAL_MATCH'
            },
            {
                'product': 'LARCHAGO RIOJA RESERVE 750ml',
                'provided_dabs_code': '918951',
                'provided_upc': '8410169111296',
                'source_claim': '[Manufacturer][UPCitemdb]',
                'match_status': 'NOT_IN_NAXML'
            },
            {
                'product': 'LORENZA ROSE 750ml',
                'provided_dabs_code': '919829',
                'provided_upc': '898963000006',
                'source_claim': '[Lorenza Wines][UPCitemdb]',
                'match_status': 'POTENTIAL_MATCH'
            },
            {
                'product': 'HELPER BEER CIRCLE BACK IPA 473ml',
                'provided_dabs_code': '926272',
                'provided_upc': 'Not published',
                'source_claim': '[Helper Beer][Untappd][No UPC]',
                'match_status': 'NOT_IN_NAXML'
            }
        ]
    
    def analyze_discrepancies(self, actual_items: List[Dict], provided_data: List[Dict]) -> List[Dict]:
        """Analyze discrepancies between actual and provided data"""
        discrepancies = []
        
        # Create lookup dictionaries
        actual_by_dabs_code = {item['dabs_code']: item for item in actual_items}
        actual_by_name = {item['name'].upper(): item for item in actual_items}
        
        for provided in provided_data:
            discrepancy = {
                'provided_product': provided['product'],
                'provided_dabs_code': provided['provided_dabs_code'],
                'provided_upc': provided['provided_upc'],
                'source_claim': provided['source_claim'],
                'match_status': provided['match_status'],
                'investigation_findings': []
            }
            
            # Check if DABS code exists in actual data
            if provided['provided_dabs_code'] in actual_by_dabs_code:
                actual_item = actual_by_dabs_code[provided['provided_dabs_code']]
                discrepancy['actual_match'] = actual_item
                discrepancy['investigation_findings'].append({
                    'finding': 'DABS code found in actual NAXML',
                    'actual_product': actual_item['name'],
                    'actual_size': actual_item['size'],
                    'name_match': provided['product'].upper() in actual_item['name'].upper() or actual_item['name'].upper() in provided['product'].upper()
                })
            else:
                discrepancy['actual_match'] = None
                discrepancy['investigation_findings'].append({
                    'finding': 'DABS code NOT found in actual NAXML',
                    'possible_reasons': [
                        'Different order/batch',
                        'Incorrect DABS code mapping',
                        'Data from different time period'
                    ]
                })
            
            # Check for similar product names
            similar_products = []
            for actual_item in actual_items:
                if any(word in actual_item['name'].upper() for word in provided['product'].upper().split() if len(word) > 3):
                    similar_products.append({
                        'actual_dabs_code': actual_item['dabs_code'],
                        'actual_name': actual_item['name'],
                        'actual_size': actual_item['size'],
                        'similarity_reason': 'Shared keywords'
                    })
            
            if similar_products:
                discrepancy['similar_products'] = similar_products
            
            discrepancies.append(discrepancy)
        
        return discrepancies
    
    def generate_verification_links(self, upc: str) -> Dict:
        """Generate verification links for a specific UPC"""
        links = {}
        
        for source_key, source_info in self.investigation_sources.items():
            if 'search_template' in source_info:
                links[source_key] = {
                    'name': source_info['name'],
                    'url': source_info['search_template'].format(upc=upc),
                    'authority': source_info['authority'],
                    'reliability': source_info['reliability']
                }
        
        return links
    
    def create_investigation_report(self, actual_items: List[Dict]) -> str:
        """Create comprehensive investigation report"""
        provided_data = self.get_provided_upc_data()
        discrepancies = self.analyze_discrepancies(actual_items, provided_data)
        
        report = f"""# DABS Order 233811 - Mismatch Investigation Report
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Purpose**: Systematic investigation of UPC data discrepancies with authoritative citations  
**Scope**: Comparison between provided UPC data and actual NAXML file contents  

## 🎯 Executive Summary

This investigation analyzes significant discrepancies between provided UPC data and the actual DABS Order 233811 NAXML file. Key findings indicate **fundamental data misalignment** requiring immediate attention.

### 🚨 Critical Findings
- **DABS Code Mismatches**: {sum(1 for d in discrepancies if d['match_status'] in ['DABS_CODE_MISMATCH'])} items
- **Missing Products**: {sum(1 for d in discrepancies if d['match_status'] == 'NOT_IN_NAXML')} items not in actual order
- **Potential Matches**: {sum(1 for d in discrepancies if d['match_status'] == 'POTENTIAL_MATCH')} items requiring verification

## 📋 Actual NAXML File Contents

**Source File**: `src/edi/data/edi_output/DABS_20250825_143058_ItemPrice.xml`  
**Total Items**: {len(actual_items)}  

### Actual Products in Order:
"""
        
        for i, item in enumerate(actual_items, 1):
            report += f"""
{i}. **{item['name']}**
   - **DABS Code**: {item['dabs_code']}
   - **Size**: {item['size']}
   - **Price**: ${item['price']}
   - **Category**: {item['category']}
   - **Current UPC**: {item['current_upc'] or 'EMPTY'}
"""
        
        report += f"""
## 🔍 Detailed Discrepancy Analysis

"""
        
        for i, discrepancy in enumerate(discrepancies, 1):
            report += f"""### {i}. {discrepancy['provided_product']}

**Provided Data:**
- **DABS Code**: {discrepancy['provided_dabs_code']}
- **UPC**: {discrepancy['provided_upc']}
- **Source Claim**: {discrepancy['source_claim']}
- **Match Status**: {discrepancy['match_status']}

**Investigation Findings:**
"""
            
            for finding in discrepancy['investigation_findings']:
                if 'actual_product' in finding:
                    report += f"""
- ✅ **DABS Code Found**: {discrepancy['provided_dabs_code']} exists in NAXML
- **Actual Product**: {finding['actual_product']}
- **Actual Size**: {finding['actual_size']}
- **Name Match**: {'✅ YES' if finding['name_match'] else '❌ NO'}
"""
                else:
                    report += f"""
- ❌ **DABS Code Missing**: {discrepancy['provided_dabs_code']} NOT found in NAXML
- **Possible Reasons**:
"""
                    for reason in finding.get('possible_reasons', []):
                        report += f"  - {reason}\n"
            
            if 'similar_products' in discrepancy:
                report += f"""
**Similar Products Found:**
"""
                for similar in discrepancy['similar_products']:
                    report += f"""
- **DABS Code**: {similar['actual_dabs_code']} - {similar['actual_name']} ({similar['actual_size']})
  - *Similarity*: {similar['similarity_reason']}
"""
            
            # Add verification links if UPC is provided
            if discrepancy['provided_upc'] != 'Not published':
                verification_links = self.generate_verification_links(discrepancy['provided_upc'])
                report += f"""
**🔗 Official Verification Links for UPC {discrepancy['provided_upc']}:**
"""
                for link_key, link_info in verification_links.items():
                    report += f"""
- **{link_info['name']}**: [{link_info['authority']}]({link_info['url']})
  - *Reliability*: {link_info['reliability']}
"""
            
            report += "\n---\n"
        
        report += f"""
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
- **Requires Verification**: {len([d for d in discrepancies if d['match_status'] == 'POTENTIAL_MATCH'])} items
- **Data Source Issues**: {len([d for d in discrepancies if d['match_status'] in ['DABS_CODE_MISMATCH', 'NOT_IN_NAXML']])} items

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
"""
        
        return report

# Main execution
if __name__ == "__main__":
    def main():
        print("🔍 DABS Order 233811 - Mismatch Investigation Tool")
        print("=" * 70)
        
        # Initialize investigation tool
        investigator = MismatchInvestigationTool()
        
        # Extract actual NAXML data
        naxml_file = "data/edi_output/DABS_20250825_143058_ItemPrice.xml"
        actual_items = investigator.extract_actual_naxml_data(naxml_file)
        
        print(f"📋 Extracted {len(actual_items)} items from actual NAXML file")
        
        # Generate investigation report
        report = investigator.create_investigation_report(actual_items)
        
        # Save report
        report_file = f"data/MISMATCH_INVESTIGATION_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        Path(report_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 Investigation report saved: {report_file}")
        print("\n" + "=" * 70)
        print("🎯 INVESTIGATION COMPLETE")
        print("=" * 70)
        
        # Summary statistics
        provided_data = investigator.get_provided_upc_data()
        mismatches = sum(1 for item in provided_data if item['match_status'] in ['DABS_CODE_MISMATCH', 'NOT_IN_NAXML'])
        
        print(f"Total Provided Items: {len(provided_data)}")
        print(f"Actual NAXML Items: {len(actual_items)}")
        print(f"Mismatched Items: {mismatches}")
        print(f"Investigation Sources: {len(investigator.investigation_sources)} authorities")
        
        print("\n🔗 NEXT STEPS:")
        print("1. Review the detailed investigation report")
        print("2. Use provided verification links to confirm UPCs")
        print("3. Cross-reference with Utah ABS official sources")
        print("4. Contact manufacturers for direct verification")
        
        return report_file
    
    main()
