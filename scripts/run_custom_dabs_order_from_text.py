#!/usr/bin/env python3
"""
Create a new DABS order from a custom item list (parsed from embedded text)
Leaves the order in Pending state for review.

Usage: python3 scripts/run_custom_dabs_order_from_text.py
"""

import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from integration.dabs_automated_ordering import DABSAutomatedOrdering  # noqa: E402


RAW_ORDER_TEXT = """
Description - Item Code	Unit Price	Quantity	Extended Price
DENTED BRICK CRAFT GIN 1000ml - 029911	$113.94	1	$113.94
UTOG RED EYE ALE 473 ml - 900821	$95.76	1	$95.76
EPIC SPACE DEBRIS IPA 355ml - 923201	$65.28	1	$65.28
EPIC CHASING GHOSTS HAZY DIPA CANS 473ml - 900286	$68.40	1	$68.40
CASTLE ROCK CHARDONNAY CNTRL C 750ml - 552500	$143.88	1	$143.88
PENDLETON CANADIAN WHISKY 375ml - 014194	$179.88	1	$179.88
ICEHOUSE BEER 355ml - 989177	$17.82	5	$89.10
BONTERRA CABERNET 750ml - 464685	$203.88	1	$203.88
ODELL BIG SIPPIN IMPERIAL SOUR ALE 355ml - 927491	$71.76	1	$71.76
TITOS HANDMADE VODKA 1000ml - 038177	$299.88	1	$299.88
GRAND TETON SWEETGRASS APA 355 ml - 989396	$38.88	1	$38.88
DESCHUTES FRESH SQUEEZED CAN 355ml - 919043	$71.76	1	$71.76
WOODCHUCK HARD CIDER PEARSECCO 355ml - 900888	$60.00	1	$60.00
PRODIGY BREWING THREE AMIGOS TRIPEL473ml - 924828	$95.76	1	$95.76
SIERRA NEVADA PALE ALE 355ml - 989206	$47.76	1	$47.76
UINTA TROP NOSH IPA 355 ml - 918916	$51.60	1	$51.60
JOSH CELLARS HEARTH CABERNET 750ml - 478138	$143.88	1	$143.88
LAGUNITAS IPA CAN 355 ml - 917389	$52.56	1	$52.56
SPATEN PREMIUM LAGER 355ml - 989240	$54.00	1	$54.00
DESCHUTES TROPICAL FRESH IPA 355ml - 929703	$71.76	1	$71.76
BELLS TWO HEARTED IPA 355ml - 925376	$56.40	1	$56.40
MTN WEST DESOLATION CIDER CAN 473ml - 921273	$126.96	1	$126.96
FIELD RECORDINGS SKINS'22/23 750ml - 954341	$239.88	1	$239.88
SEGURA VIUDAS BRUT 750ml - 733238	$167.88	1	$167.88
HELPER BEER SLOW FADE 473ml - 926273	$108.00	1	$108.00
RUTH LEWANDOWSKI ROSE'23 750ml - 949335	$275.88	1	$275.88
PRODIGY BREWING INVERSION NE IPA 473ml - 924827	$83.76	1	$83.76
LAGUNITAS IPA 355ml - 919658	$52.56	1	$52.56
ODELL IPA 355 ml - 953843	$59.76	1	$59.76
NEW BELGIUM VOODOO FRUIT FORCE - 925378	$56.40	1	$56.40
MTN WEST COTTONWOOD DRY HOP CANS 473ml - 953985	$126.96	1	$126.96
LEVEL CROSSING SUSS IT OUT RYE IPA 473ml - 955767	$84.00	1	$84.00
SALTFIRE HEAVY METAL PARKING LOT 473ml - 922388	$94.80	1	$94.80
NEW BELGIUM VOO RANGER IPA CANS 355 ml - 947400	$49.20	2	$98.40
SALTFIRE FURY KOLSCH CAN 473ml - 901976	$71.76	1	$71.76
OSKAR BLUES DALES PALE ALE 355ml - 949961	$48.96	2	$97.92
LEVEL CROSSING DALLAS ALICE BELGIAN473ml - 900567	$75.60	1	$75.60
MTN WEST RUBY HARD CIDER CANS 473ml - 953984	$126.96	1	$126.96
TITOS HANDMADE VODKA 200 ml - 038179	$191.76	1	$191.76
DENTED BRICK CRAFT RUM 1000 ml - 046206	$113.94	1	$113.94
FOUNDERS BREWING BREAKFAST STOUT 355ml - 900269	$85.20	1	$85.20
BROADBENT VINHO VERDE 750ml - 403760	$155.88	1	$155.88
ESPOLON BLANCO TEQUILA 750ml - 087619	$383.88	1	$383.88
NATTY DADDY 355 ml - 918885	$16.35	5	$81.75
DESCHUTES FRESH HAZE IPA CAN 355 ml - 948026	$71.76	1	$71.76
GILBEYS GIN PET 1750ml - 030238	$107.94	1	$107.94
ELYSIAN SPACE DUST IPA 355 ml - 918765	$63.60	2	$127.20
NEW BELGIUM VOODOO JUICE FORCE 355 ml - 918778	$56.40	1	$56.40
GRUET BRUT NV 750ml - 771052	$263.88	1	$263.88
OSKAR BLUES DOUBLE DALES 355 ml - 904445	$48.96	2	$97.92
MODELO NEGRA DARK ALE 355 ml - 989012	$49.20	1	$49.20
SIERRA NEVADA TORPEDO EXTRA IP 355ml - 907923	$57.36	1	$57.36
MTN WEST SWEET ALICE CAN 473ml - 902702	$126.96	1	$126.96
SIERRA NEVADA PALE ALE CANS 355ml - 919867	$47.76	1	$47.76
HIGH WEST BOURBON 375 ml - 018603	$239.88	1	$239.88
BEEHIVE/DESOLATION GIN RICKEY 355 ml - 955762	$86.16	2	$172.32
EPIC LOS LOCOS LAGER 355 ml - 918705	$47.76	1	$47.76
BEEHIVE/DESOLATION MOSCOW MULE 355 ml - 955763	$86.16	2	$172.32
LAGUNITAS LIL SUMPIN SUMPIN CANS 355 ml - 919158	$52.56	1	$52.56
LEFFE BLONDE ALE 330ml - 989359	$57.36	1	$57.36
DESCHUTES BLACK BUTTE PORTER 355ml - 989261	$50.40	1	$50.40
HORNITOS REPOSADO TEQUILA 750ml - 089836	$311.88	1	$311.88
NEW BELGIUM VOODOO JUICY HAZE CAN 355 ml - 953285	$56.40	1	$56.40
BEWILDER GECKO FINGERS - 925479	$90.96	1	$90.96
ORIGINAL SIN BLACK WIDOW CIDER 355ml - 902930	$63.60	1	$63.60
LEVEL CROSSING JAZZ LOON PILSNER 473 - 900566	$71.76	1	$71.76
"""


def parse_items(raw: str) -> List[Dict[str, object]]:
    items: List[Dict[str, object]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.lower().startswith("description"):
            continue
        # Expect pattern: <desc> - <code> $price <qty> $extended
        m = re.search(r"^(.*?)\s-\s(\d{6})\s+\$[\d,]+\.?\d*\s+(\d+)\s+\$[\d,]+\.?\d*", line)
        if not m:
            # Try variant without decimals in first price
            m = re.search(r"^(.*?)\s-\s(\d{6})\s+\$[\d,.]+\s+(\d+)\s+\$[\d,.]+", line)
        if m:
            product_name = m.group(1).strip()
            code = m.group(2).strip()
            qty = int(m.group(3))
            items.append({
                "item_code": code,
                "product_name": product_name,
                "quantity": qty,
            })
    return items


async def run():
    print("🎯 CUSTOM DABS ORDER CREATION (Headless)")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")

    order_items = parse_items(RAW_ORDER_TEXT)
    if not order_items:
        print("❌ Failed to parse any items from the provided text")
        sys.exit(1)

    print(f"📦 Parsed {len(order_items)} items (total qty: {sum(i['quantity'] for i in order_items)})")

    processor = None
    try:
        processor = DABSAutomatedOrdering(headless=True, timeout=120000)
        await processor.initialize_automation_system()

        # Use saved auth if present; otherwise perform login
        auth_file = Path("dabs_auth.json")
        if not auth_file.exists():
            print("🔐 Performing headless login...")
            ok = await processor.perform_dabs_login()
            if not ok:
                print("❌ Authentication failed")
                sys.exit(2)

        print("🚀 Creating new DABS order and adding items (will remain Pending)...")
        result = await processor.create_dabs_order_with_products(order_items)

        print("\n" + "=" * 70)
        print("📊 RESULT")
        print("=" * 70)
        print(json.dumps(result, indent=2))

        if result.get("success"):
            print("\n✅ Order created and left Pending for review")
            print(f"📋 Order ID: {result.get('order_id')}")
        else:
            print("\n❌ Order creation failed")
            sys.exit(3)

    finally:
        if processor:
            await processor.cleanup()


if __name__ == "__main__":
    asyncio.run(run())


