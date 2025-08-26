#!/usr/bin/env python3
"""
Case-to-Unit Conversion Automation
Handles DABS case packaging vs individual unit billing discrepancies

This system prevents pricing errors like those in Order 233808 by automatically
detecting and converting between case and unit pricing based on DABS specifications.

Business Context:
- DABS orders in cases (12 bottles, 24 cans, etc.)
- SSCS billing often requires individual unit pricing
- Manual conversion prone to errors and inconsistencies
- Utah Package Agency requires accurate pricing for compliance
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PackagingRule:
    """Packaging conversion rule"""
    category: str
    container_type: str  # bottle, can, box, etc.
    container_size: str  # 750ml, 355ml, 3000ml, etc.
    units_per_case: int
    conversion_factor: Decimal
    validation_range: Tuple[Decimal, Decimal]  # (min_price, max_price) per unit

@dataclass
class ConversionResult:
    """Result of case-to-unit conversion"""
    original_item_id: str
    original_quantity: int
    original_unit_price: Decimal
    original_total: Decimal
    converted_quantity: int
    converted_unit_price: Decimal
    converted_total: Decimal
    conversion_rule: str
    confidence: float
    warnings: List[str]
    timestamp: str

class CaseUnitConverter:
    """
    Automated case-to-unit conversion system
    
    Prevents Order 233808 type pricing errors by:
    1. Automatically detecting case vs unit packaging
    2. Applying correct conversion factors based on product category
    3. Validating converted prices against expected ranges
    4. Providing audit trail for all conversions
    """
    
    def __init__(self, rules_file: str = "config/packaging_rules.json"):
        self.rules_file = Path(rules_file)
        self.packaging_rules = self._load_packaging_rules()
        self.conversion_history = []
        
    def _load_packaging_rules(self) -> Dict[str, PackagingRule]:
        """Load packaging conversion rules"""
        default_rules = {
            # Spirits (750ml bottles)
            "spirits_750ml": PackagingRule(
                category="Spirits",
                container_type="bottle", 
                container_size="750ml",
                units_per_case=12,
                conversion_factor=Decimal("12"),
                validation_range=(Decimal("15.00"), Decimal("150.00"))
            ),
            # Spirits (1000ml/1L bottles) 
            "spirits_1000ml": PackagingRule(
                category="Spirits",
                container_type="bottle",
                container_size="1000ml", 
                units_per_case=6,
                conversion_factor=Decimal("6"),
                validation_range=(Decimal("20.00"), Decimal("200.00"))
            ),
            # Beer (355ml cans)
            "beer_355ml_can": PackagingRule(
                category="Beer",
                container_type="can",
                container_size="355ml",
                units_per_case=24,
                conversion_factor=Decimal("24"),
                validation_range=(Decimal("1.00"), Decimal("8.00"))
            ),
            # Beer (500ml bottles)
            "beer_500ml_bottle": PackagingRule(
                category="Beer", 
                container_type="bottle",
                container_size="500ml",
                units_per_case=12,
                conversion_factor=Decimal("12"),
                validation_range=(Decimal("2.00"), Decimal("12.00"))
            ),
            # Wine (750ml bottles)
            "wine_750ml": PackagingRule(
                category="Wine",
                container_type="bottle",
                container_size="750ml", 
                units_per_case=12,
                conversion_factor=Decimal("12"),
                validation_range=(Decimal("8.00"), Decimal("80.00"))
            ),
            # Wine (3000ml boxes)
            "wine_3000ml_box": PackagingRule(
                category="Wine",
                container_type="box",
                container_size="3000ml",
                units_per_case=4,
                conversion_factor=Decimal("4"),
                validation_range=(Decimal("12.00"), Decimal("50.00"))
            ),
            # Cider (355ml cans)
            "cider_355ml": PackagingRule(
                category="Cider",
                container_type="can", 
                container_size="355ml",
                units_per_case=24,
                conversion_factor=Decimal("24"),
                validation_range=(Decimal("1.50"), Decimal("6.00"))
            )
        }
        
        # Try to load from file, fall back to defaults
        if self.rules_file.exists():
            try:
                with open(self.rules_file, 'r') as f:
                    rules_data = json.load(f)
                    return {
                        key: PackagingRule(**rule_data) 
                        for key, rule_data in rules_data.items()
                    }
            except Exception as e:
                logger.warning(f"Failed to load packaging rules from {self.rules_file}: {e}")
                logger.info("Using default packaging rules")
        
        # Save default rules for future reference
        self._save_packaging_rules(default_rules)
        return default_rules
    
    def _save_packaging_rules(self, rules: Dict[str, PackagingRule]):
        """Save packaging rules to file"""
        self.rules_file.parent.mkdir(parents=True, exist_ok=True)
        
        rules_data = {
            key: asdict(rule) for key, rule in rules.items()
        }
        
        with open(self.rules_file, 'w') as f:
            json.dump(rules_data, f, indent=2, default=str)
        
        logger.info(f"Packaging rules saved to {self.rules_file}")
    
    def detect_packaging_type(self, item_name: str, category: str, unit_price: Decimal) -> Optional[PackagingRule]:
        """
        Detect packaging type from item description and category
        
        Uses pattern matching and price analysis to determine the most likely
        packaging configuration for accurate conversion.
        """
        item_name_lower = item_name.lower()
        category_lower = category.lower()
        
        # Extract container size from item name
        container_size = None
        if "750ml" in item_name_lower:
            container_size = "750ml"
        elif "1000ml" in item_name_lower or "1l" in item_name_lower:
            container_size = "1000ml"
        elif "355ml" in item_name_lower:
            container_size = "355ml"
        elif "500ml" in item_name_lower:
            container_size = "500ml"
        elif "3000ml" in item_name_lower or "3l" in item_name_lower:
            container_size = "3000ml"
        
        # Match against packaging rules
        for rule_key, rule in self.packaging_rules.items():
            # Check category match
            if rule.category.lower() not in category_lower:
                continue
                
            # Check container size match
            if container_size and rule.container_size != container_size:
                continue
            
            # Check price range validation
            estimated_unit_price = unit_price / rule.conversion_factor
            min_price, max_price = rule.validation_range
            
            if min_price <= estimated_unit_price <= max_price:
                logger.info(f"✅ Packaging detected: {rule_key} for {item_name}")
                logger.info(f"   Estimated unit price: ${estimated_unit_price} (range: ${min_price}-${max_price})")
                return rule
        
        logger.warning(f"⚠️ No packaging rule matched for: {item_name} (${unit_price})")
        return None
    
    def convert_case_to_units(self, 
                             item_id: str,
                             item_name: str,
                             category: str,
                             case_quantity: int,
                             case_price: Decimal) -> ConversionResult:
        """
        Convert case pricing to individual unit pricing
        
        Args:
            item_id: Unique item identifier
            item_name: Product name/description
            category: Product category (Spirits, Beer, Wine, etc.)
            case_quantity: Number of cases ordered
            case_price: Price per case
            
        Returns:
            ConversionResult with unit pricing and validation
        """
        timestamp = datetime.now().isoformat()
        warnings = []
        
        logger.info(f"🔄 Converting case to units: {item_name}")
        logger.info(f"   Input: {case_quantity} cases @ ${case_price}/case")
        
        # Detect packaging type
        packaging_rule = self.detect_packaging_type(item_name, category, case_price)
        
        if not packaging_rule:
            # Fallback to generic conversion based on category
            packaging_rule = self._get_fallback_rule(category)
            warnings.append(f"Using fallback conversion rule for {category}")
        
        # Calculate unit conversion
        total_units = case_quantity * packaging_rule.units_per_case
        unit_price = case_price / packaging_rule.conversion_factor
        total_price = case_quantity * case_price
        
        # Validate unit price is reasonable
        min_price, max_price = packaging_rule.validation_range
        confidence = 1.0
        
        if unit_price < min_price:
            warnings.append(f"Unit price ${unit_price} below expected range (${min_price}-${max_price})")
            confidence = 0.7
        elif unit_price > max_price:
            warnings.append(f"Unit price ${unit_price} above expected range (${min_price}-${max_price})")
            confidence = 0.7
        
        # Round unit price to nearest cent
        unit_price = unit_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        result = ConversionResult(
            original_item_id=item_id,
            original_quantity=case_quantity,
            original_unit_price=case_price,
            original_total=total_price,
            converted_quantity=total_units,
            converted_unit_price=unit_price,
            converted_total=total_price,  # Total should remain the same
            conversion_rule=f"{packaging_rule.category}_{packaging_rule.container_size}",
            confidence=confidence,
            warnings=warnings,
            timestamp=timestamp
        )
        
        logger.info(f"✅ Conversion complete: {total_units} units @ ${unit_price}/unit")
        if warnings:
            for warning in warnings:
                logger.warning(f"⚠️ {warning}")
        
        self.conversion_history.append(result)
        return result
    
    def _get_fallback_rule(self, category: str) -> PackagingRule:
        """Get fallback packaging rule when specific detection fails"""
        category_lower = category.lower()
        
        if "spirit" in category_lower:
            return self.packaging_rules["spirits_750ml"]
        elif "beer" in category_lower:
            return self.packaging_rules["beer_355ml_can"]
        elif "wine" in category_lower:
            return self.packaging_rules["wine_750ml"]
        elif "cider" in category_lower:
            return self.packaging_rules["cider_355ml"]
        else:
            # Generic fallback - assume 12 units per case
            return PackagingRule(
                category="Generic",
                container_type="unit",
                container_size="unknown",
                units_per_case=12,
                conversion_factor=Decimal("12"),
                validation_range=(Decimal("1.00"), Decimal("100.00"))
            )
    
    def validate_conversion(self, result: ConversionResult) -> bool:
        """Validate that conversion maintains mathematical integrity"""
        # Check that total price is preserved
        price_difference = abs(result.original_total - result.converted_total)
        if price_difference > Decimal('0.01'):
            logger.error(f"❌ Conversion failed: Total price changed by ${price_difference}")
            return False
        
        # Check that unit price is reasonable
        if result.confidence < 0.8:
            logger.warning(f"⚠️ Low confidence conversion: {result.confidence}")
        
        # Check for warnings
        if result.warnings:
            logger.warning(f"⚠️ Conversion warnings: {len(result.warnings)} issues")
        
        logger.info(f"✅ Conversion validated: {result.original_item_id}")
        return True
    
    def batch_convert(self, items: List[Dict[str, Any]]) -> List[ConversionResult]:
        """Convert multiple items from case to unit pricing"""
        results = []
        
        logger.info(f"🔄 Batch converting {len(items)} items")
        
        for item in items:
            try:
                result = self.convert_case_to_units(
                    item_id=item['id'],
                    item_name=item['name'],
                    category=item['category'],
                    case_quantity=item['quantity'],
                    case_price=Decimal(str(item['unit_price']))
                )
                
                if self.validate_conversion(result):
                    results.append(result)
                else:
                    logger.error(f"❌ Conversion validation failed for {item['id']}")
                    
            except Exception as e:
                logger.error(f"❌ Conversion error for {item['id']}: {e}")
        
        logger.info(f"✅ Batch conversion complete: {len(results)}/{len(items)} successful")
        return results
    
    def get_conversion_summary(self) -> Dict[str, Any]:
        """Get summary of all conversions performed"""
        if not self.conversion_history:
            return {'status': 'no_conversions', 'total_conversions': 0}
        
        total_conversions = len(self.conversion_history)
        high_confidence = sum(1 for c in self.conversion_history if c.confidence >= 0.9)
        medium_confidence = sum(1 for c in self.conversion_history if 0.7 <= c.confidence < 0.9)
        low_confidence = sum(1 for c in self.conversion_history if c.confidence < 0.7)
        
        return {
            'status': 'complete',
            'total_conversions': total_conversions,
            'high_confidence': high_confidence,
            'medium_confidence': medium_confidence, 
            'low_confidence': low_confidence,
            'average_confidence': sum(c.confidence for c in self.conversion_history) / total_conversions,
            'total_warnings': sum(len(c.warnings) for c in self.conversion_history)
        }

# Example usage and testing
if __name__ == "__main__":
    # Initialize converter
    converter = CaseUnitConverter()
    
    # Example Order 233813 items
    test_items = [
        {
            'id': '917817',
            'name': 'RED ROCK ELEPHINO IPA 500ml',
            'category': 'Beer',
            'quantity': 4,
            'unit_price': 48.48
        },
        {
            'id': '039271', 
            'name': 'SUGAR HOUSE VODKA 1000ml',
            'category': 'Spirits',
            'quantity': 1,
            'unit_price': 131.94
        },
        {
            'id': '419961',
            'name': '19 CRIMES CABERNET SAUVIGNON 750ml',
            'category': 'Wine', 
            'quantity': 3,
            'unit_price': 155.88
        }
    ]
    
    print("🧪 Testing case-to-unit conversion...")
    results = converter.batch_convert(test_items)
    
    print(f"\n📊 Conversion Results:")
    for result in results:
        print(f"  {result.original_item_id}: {result.original_quantity} cases → {result.converted_quantity} units")
        print(f"    ${result.original_unit_price}/case → ${result.converted_unit_price}/unit")
        print(f"    Confidence: {result.confidence:.1%}")
        if result.warnings:
            print(f"    Warnings: {len(result.warnings)}")
    
    print(f"\n📊 Summary:")
    summary = converter.get_conversion_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
