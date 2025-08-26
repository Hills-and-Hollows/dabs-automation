#!/usr/bin/env python3
"""
Process DABS Order 233811 with Complete UPC Verification
Find UPC numbers for all 10 items in the order
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.append('src')
sys.path.append('src/upc_verification')

from src.upc_verification.dabs_upc_integration import DABSUPCIntegrator

async def process_order_233811():
    """Process the complete DABS order 233811"""
    
    # DABS Order 233811 items extracted from PDF
    order_text = """🍷 DABS Order 233811 - 10 Items
SUGAR HOUSE VODKA 1750ml (039593) - $227.94
ARETTE CLASICA BLANCO TEQUILA 1000ml (087123) - $395.88
WILLAMETTE VLY PINOT NOIR WL CLST 750ml (523110) - $299.88
KING ESTATE PINOT GRIS SIGNATURE 750ml (580790) - $252.96
SEGURA VIUDAS BRUT 750ml (733238) - $167.88
BUCKLIN BAMBINO ZIN'22 750ml (908418) - $287.88
POE ROSÉ'23 750ml (918761) - $251.88
LARCHAGO RIOJA RESERVE 750ml (918951) - $275.88
LORENZA ROSE 750ml (919829) - $239.88
HELPER BEER CIRCLE BACK IPA 473ml (926272) - $108.00"""

    print("🎯 Processing DABS Order 233811 - Complete UPC Verification")
    print("=" * 70)
    print(f"Order Date: 8/22/2025")
    print(f"Total Items: 10")
    print(f"Total Value: $2,508.06")
    print()
    
    async with DABSUPCIntegrator() as integrator:
        # Process the complete order
        naxml_content, report, naxml_path = await integrator.process_dabs_order(
            order_text, 
            order_id="233811"
        )
        
        # Display comprehensive report
        print(report)
        
        # Display NAXML file location
        print(f"\n📄 Complete NAXML with UPCs saved to:")
        print(f"   {naxml_path}")
        
        # Show summary of UPC findings
        print(f"\n🎯 UPC Verification Summary for Order 233811:")
        print("=" * 50)
        
        # Parse the items to show individual results
        items = integrator.parse_dabs_order_text(order_text)
        await integrator.verify_upcs_for_items(items)
        
        print(f"\n📋 Individual Item Results:")
        for i, item in enumerate(items, 1):
            status_icon = "✅" if item.has_upc else "❌"
            print(f"\n{i:2d}. {status_icon} {item.item_name}")
            print(f"     DABS Code: {item.dabs_code}")
            print(f"     Price: ${item.price:.2f}")
            
            if item.has_upc:
                print(f"     UPC-12: {item.upc_result.upc_code}")
                print(f"     Verifone UPC-11: {item.verifone_upc}")
                print(f"     Confidence: {item.upc_result.confidence:.2f}")
                print(f"     Sources: {', '.join(item.upc_result.sources)}")
            else:
                print(f"     UPC: ❌ NOT FOUND - Requires manual lookup")
                if item.upc_result and item.upc_result.error:
                    print(f"     Error: {item.upc_result.error}")
        
        # Calculate final statistics
        found_count = sum(1 for item in items if item.has_upc)
        success_rate = (found_count / len(items)) * 100
        
        print(f"\n📊 Final Statistics:")
        print(f"   Total Items: {len(items)}")
        print(f"   UPCs Found: {found_count}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Manual Review Needed: {len(items) - found_count}")
        
        if found_count == len(items):
            print(f"\n🎊 SUCCESS: All items have UPCs - Ready for EDI delivery!")
        else:
            print(f"\n⚠️  {len(items) - found_count} items need manual UPC lookup using DABS Product Locator")
        
        return naxml_path, found_count, len(items)

if __name__ == "__main__":
    asyncio.run(process_order_233811())
