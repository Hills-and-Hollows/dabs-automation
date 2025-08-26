#!/usr/bin/env python3
"""
UPC Lookup for Remaining DABS Order 233811 Items
Systematic lookup using enhanced verification system
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add src path for imports
sys.path.append('src')
sys.path.append('src/upc_verification')

try:
    from src.upc_verification.enhanced_upc_verifier import EnhancedUPCVerifier, EnhancedUPCResult
    from src.upc_verification.verifone_formatter import VerifoneFormatter
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying direct imports...")
    from enhanced_upc_verifier import EnhancedUPCVerifier, EnhancedUPCResult
    from verifone_formatter import VerifoneFormatter

# Remaining items from DABS Order 233811 that need UPC lookup
REMAINING_ITEMS = [
    {
        "dabs_code": "523110",
        "name": "WILLAMETTE VLY PINOT NOIR WL CLST 750ml",
        "category": "WINE",
        "size": "750ml",
        "search_terms": ["Willamette Valley Pinot Noir", "Willamette Valley Wine", "Oregon Pinot Noir"]
    },
    {
        "dabs_code": "580790", 
        "name": "KING ESTATE PINOT GRIS SIGNATURE 750ml",
        "category": "WINE",
        "size": "750ml",
        "search_terms": ["King Estate Pinot Gris", "King Estate Signature", "Oregon Pinot Gris"]
    },
    {
        "dabs_code": "733238",
        "name": "SEGURA VIUDAS BRUT 750ml", 
        "category": "WINE",
        "size": "750ml",
        "search_terms": ["Segura Viudas Brut", "Segura Viudas Cava", "Spanish Sparkling Wine"]
    },
    {
        "dabs_code": "908418",
        "name": "BUCKLIN BAMBINO ZIN'22 750ml",
        "category": "WINE", 
        "size": "750ml",
        "search_terms": ["Bucklin Bambino Zinfandel", "Bucklin Zinfandel 2022", "Sonoma Zinfandel"]
    },
    {
        "dabs_code": "918951",
        "name": "LARCHAGO RIOJA RESERVE 750ml",
        "category": "WINE",
        "size": "750ml", 
        "search_terms": ["Larchago Rioja Reserve", "Larchago Rioja", "Spanish Rioja Reserve"]
    },
    {
        "dabs_code": "919829",
        "name": "LORENZA ROSE 750ml",
        "category": "WINE",
        "size": "750ml",
        "search_terms": ["Lorenza Rose", "Lorenza Rosé", "Italian Rose Wine"]
    },
    {
        "dabs_code": "926272",
        "name": "HELPER BEER CIRCLE BACK IPA 473ml",
        "category": "BEER",
        "size": "473ml",
        "search_terms": ["Helper Beer Circle Back IPA", "Helper Brewing Circle Back", "Utah IPA"]
    }
]

async def lookup_item_upc(verifier: EnhancedUPCVerifier, item: dict) -> dict:
    """Lookup UPC for a single item using multiple search terms"""
    print(f"\n🔍 Looking up: {item['name']} ({item['dabs_code']})")
    
    results = []
    
    # Try each search term
    for search_term in item['search_terms']:
        print(f"  Searching: {search_term}")
        try:
            result = await verifier.lookup_single_upc_enhanced(search_term, item['dabs_code'])
            if result and result.upc_code and result.confidence > 0.6:
                results.append({
                    'search_term': search_term,
                    'upc': result.upc_code,
                    'confidence': result.confidence,
                    'sources': result.sources,
                    'product_name': result.item_name
                })
                print(f"    ✅ Found: {result.upc_code} (confidence: {result.confidence:.2f})")
            else:
                print(f"    ❌ No reliable UPC found")
        except Exception as e:
            print(f"    ⚠️ Error: {e}")
    
    # Return best result
    if results:
        best_result = max(results, key=lambda x: x['confidence'])
        return {
            'dabs_code': item['dabs_code'],
            'name': item['name'],
            'upc_found': True,
            'upc': best_result['upc'],
            'verifone_upc': VerifoneFormatter.format_to_verifone(best_result['upc']),
            'confidence': best_result['confidence'],
            'sources': best_result['sources'],
            'search_term_used': best_result['search_term'],
            'product_name_found': best_result['product_name']
        }
    else:
        return {
            'dabs_code': item['dabs_code'],
            'name': item['name'],
            'upc_found': False,
            'reason': 'No UPC found in any database',
            'search_terms_tried': item['search_terms']
        }

async def main():
    """Main UPC lookup process"""
    print("🚀 Starting UPC Lookup for DABS Order 233811 Remaining Items")
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Items to lookup: {len(REMAINING_ITEMS)}")
    
    # Initialize verifier
    verifier = EnhancedUPCVerifier()
    
    # Process each item
    results = []
    for i, item in enumerate(REMAINING_ITEMS, 1):
        print(f"\n{'='*60}")
        print(f"Processing {i}/{len(REMAINING_ITEMS)}: {item['dabs_code']}")
        print(f"{'='*60}")
        
        result = await lookup_item_upc(verifier, item)
        results.append(result)
        
        # Small delay between requests
        await asyncio.sleep(2)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 LOOKUP SUMMARY")
    print(f"{'='*60}")
    
    found_count = sum(1 for r in results if r['upc_found'])
    print(f"✅ UPCs Found: {found_count}/{len(REMAINING_ITEMS)}")
    print(f"❌ UPCs Not Found: {len(REMAINING_ITEMS) - found_count}/{len(REMAINING_ITEMS)}")
    
    # Detailed results
    print(f"\n📋 DETAILED RESULTS:")
    for result in results:
        if result['upc_found']:
            print(f"✅ {result['dabs_code']}: {result['upc']} (confidence: {result['confidence']:.2f})")
            print(f"   Verifone: {result['verifone_upc']}")
            print(f"   Sources: {', '.join(result['sources'])}")
        else:
            print(f"❌ {result['dabs_code']}: {result['reason']}")
    
    # Save results to file
    output_file = f"upc_lookup_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    return results

if __name__ == "__main__":
    try:
        results = asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Lookup interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during lookup: {e}")
        import traceback
        traceback.print_exc()
