# EDI Processing Troubleshooting Guide
**Comprehensive Problem Resolution for DABS-SSCS Integration**

**Document Version**: 1.0  
**Last Updated**: August 26, 2025  
**Target Audience**: System Operators, Technical Support, Administrators  
**Business Context**: Prevents processing failures that could impact $28,000 annual automation value

## 🚨 Emergency Response Procedures

### **CRITICAL: Data Loss Detected**
**Immediate Actions (Execute within 5 minutes)**:

1. **STOP ALL PROCESSING** 
   ```bash
   # Kill all running DABS processes
   pkill -f "dabs_processor"
   pkill -f "edi_generator"
   ```

2. **Assess Damage**
   ```python
   # Check validation logs
   validator = SourceDataValidator("data/audit")
   recent_validations = validator.get_recent_validations(24)  # Last 24 hours
   
   for validation in recent_validations:
       if not validation.success:
           print(f"FAILURE: {validation.stage} - Missing: {validation.missing_items}")
   ```

3. **Initiate Recovery**
   ```python
   # Use rollback system
   rollback_system = RollbackRecoverySystem()
   recent_transactions = rollback_system.get_transaction_history(10)
   
   # Find last successful transaction
   last_good = next(txn for txn in recent_transactions if txn['state'] == 'committed')
   
   # Rollback to safe state
   rollback_system.rollback_to_checkpoint(last_good['transaction_id'])
   ```

4. **Alert Stakeholders**
   - Notify DABS system administrator immediately
   - Contact Utah Package Agency if compliance affected
   - Document incident for post-mortem analysis

## 🔍 Diagnostic Procedures

### **System Health Check**
```bash
#!/bin/bash
# Complete system diagnostic script

echo "=== DABS System Health Check ==="
echo "Timestamp: $(date)"
echo

# Check prevention framework components
echo "1. Prevention Framework Status:"
python3 -c "
from src.monitoring.prevention_dashboard import PreventionDashboard
dashboard = PreventionDashboard()
status = dashboard.get_system_status()
for component, health in status.items():
    print(f'   {component}: {health}')
"

# Check database connections
echo "2. Database Status:"
python3 -c "
from src.validation.vendor_mapping_system import VendorMappingSystem
mapper = VendorMappingSystem()
stats = mapper.get_mapping_statistics()
print(f'   Mappings: {stats[\"total_mappings\"]} total')
print(f'   Success Rate: {stats[\"success_rate\"]:.1f}%')
"

# Check disk space
echo "3. Storage Status:"
df -h | grep -E "(data|logs|exports)"

# Check recent errors
echo "4. Recent Errors:"
tail -n 20 logs/error.log | grep -E "(ERROR|CRITICAL)"

echo "=== Health Check Complete ==="
```

### **Performance Analysis**
```python
# Performance diagnostic script
import time
from datetime import datetime, timedelta
from src.validation.prevention_framework_orchestrator import PreventionFrameworkOrchestrator

def diagnose_performance():
    """Diagnose system performance issues"""
    orchestrator = PreventionFrameworkOrchestrator()
    
    # Test processing time with sample data
    test_data = [
        {'id': 'PERF_001', 'name': 'Test Item', 'category': 'Test', 
         'quantity': 1, 'unit_price': 10.00, 'total_price': 10.00}
    ]
    
    start_time = time.time()
    result = await orchestrator.process_order_with_prevention(test_data, "test_output.xml")
    processing_time = time.time() - start_time
    
    print(f"Processing Time: {processing_time:.2f}s")
    print(f"Success: {result.success}")
    print(f"Stage Reached: {result.stage}")
    
    if processing_time > 30:
        print("⚠️  WARNING: Processing time exceeds expected performance")
        
    return result

# Run performance diagnosis
import asyncio
asyncio.run(diagnose_performance())
```

## 🛠️ Common Issues and Solutions

### **Issue 1: NAXML Validation Failures**

**Symptoms**:
- EDI files rejected by SSCS
- Validation errors in logs
- Processing stops at SSCS validation stage

**Diagnostic Steps**:
```python
from src.validation.sscs_validator import SSCSValidator

validator = SSCSValidator()
result = validator.validate_naxml_file("path/to/file.xml")

if not result.valid:
    print("Validation Issues:")
    for issue in result.issues:
        print(f"  - {issue['severity']}: {issue['message']}")
        print(f"    Location: {issue.get('xpath', 'N/A')}")
```

**Common Causes and Fixes**:

1. **Missing Required Elements**
   ```xml
   <!-- WRONG -->
   <VendorInfo>
     <VendorID>DABS</VendorID>
     <!-- Missing VendorName, InvoiceNumber, etc. -->
   </VendorInfo>
   
   <!-- CORRECT -->
   <VendorInfo>
     <VendorID>DABS</VendorID>
     <VendorName>Utah Division of Alcoholic Beverage Control</VendorName>
     <InvoiceNumber>DABS_20250826_123456</InvoiceNumber>
     <InvoiceDate>2025-08-26</InvoiceDate>
     <TotalItems>13</TotalItems>
   </VendorInfo>
   ```

2. **Invalid Price Formats**
   ```xml
   <!-- WRONG -->
   <Price>$19.99</Price>
   
   <!-- CORRECT -->
   <Price>19.99</Price>
   ```

3. **Character Encoding Issues**
   ```xml
   <!-- Ensure proper encoding declaration -->
   <?xml version="1.0" encoding="utf-8"?>
   ```

### **Issue 2: Case-to-Unit Conversion Errors**

**Symptoms**:
- Incorrect unit prices in output
- Low confidence scores in conversion results
- Mathematical integrity failures

**Diagnostic Steps**:
```python
from src.validation.case_unit_converter import CaseUnitConverter

converter = CaseUnitConverter()
result = converter.convert_case_to_units(
    item_id="917817",
    item_name="RED ROCK ELEPHINO IPA 500ml",
    category="Beer",
    case_quantity=4,
    case_price=Decimal("48.48")
)

print(f"Confidence: {result.confidence}")
print(f"Detected Case Size: {result.detected_case_size}")
print(f"Unit Price: ${result.converted_unit_price}")

if result.confidence < 0.8:
    print("⚠️  Low confidence conversion - manual review required")
```

**Common Causes and Fixes**:

1. **Unrecognized Package Size**
   ```python
   # Add manual packaging rule
   converter.add_packaging_rule(
       pattern="500ml.*beer",
       case_size=12,
       confidence=1.0,
       category="Beer"
   )
   ```

2. **Category Mismatch**
   ```python
   # Verify category mapping
   category_map = {
       "Spirits": ["vodka", "whiskey", "rum", "gin", "tequila"],
       "Beer": ["beer", "ale", "lager", "ipa", "stout"],
       "Wine": ["wine", "champagne", "prosecco", "chardonnay"]
   }
   ```

3. **Price Range Validation Failure**
   ```python
   # Check if unit price is reasonable
   if result.converted_unit_price < Decimal("0.50"):
       print("⚠️  Unit price suspiciously low - check conversion logic")
   elif result.converted_unit_price > Decimal("200.00"):
       print("⚠️  Unit price suspiciously high - check conversion logic")
   ```

### **Issue 3: Vendor Mapping Failures**

**Symptoms**:
- High percentage of unmapped items
- EDI processing blocked due to missing vendor codes
- SSCS import failures

**Diagnostic Steps**:
```python
from src.validation.vendor_mapping_system import VendorMappingSystem

mapper = VendorMappingSystem()
stats = mapper.get_mapping_statistics()

print(f"Total Mappings: {stats['total_mappings']}")
print(f"Success Rate: {stats['success_rate']:.1f}%")
print(f"Recent Failures: {stats['recent_failures']}")

# Check specific item
result = mapper.lookup_vendor_code("917817", "RED ROCK ELEPHINO IPA 500ml")
if not result.success:
    print(f"Mapping failed: {result.error_message}")
    if result.suggestions:
        print("Suggestions:")
        for suggestion in result.suggestions:
            print(f"  - {suggestion.dabs_name} -> {suggestion.vendor_item_code}")
```

**Common Causes and Fixes**:

1. **Missing Mappings for New Items**
   ```python
   # Add manual mapping
   success = mapper.add_mapping(VendorMapping(
       dabs_plu="917817",
       dabs_name="RED ROCK ELEPHINO IPA 500ml",
       vendor_item_code="RR-ELEPHINO-500ML",
       vendor_name="Red Rock Brewing",
       category="Beer",
       size="500ml",
       confidence=1.0,
       verification_source="manual_entry"
   ))
   ```

2. **Fuzzy Matching Threshold Too High**
   ```python
   # Adjust fuzzy matching sensitivity
   mapper.set_fuzzy_threshold(0.7)  # Lower threshold for more matches
   ```

3. **Vendor Code Format Issues**
   ```python
   # Validate vendor code format
   valid, message = mapper.validate_vendor_code_format("RR-ELEPHINO-500ML")
   if not valid:
       print(f"Invalid format: {message}")
       # Fix format: remove spaces, special characters, etc.
   ```

### **Issue 4: Source Data Validation Failures**

**Symptoms**:
- Processing stops at validation stage
- Missing items detected in extraction
- Total value discrepancies

**Diagnostic Steps**:
```python
from src.validation.source_data_validator import SourceDataValidator

validator = SourceDataValidator("data/audit")

# Check recent validation
recent = validator.get_recent_validations(1)[0]
if not recent.success:
    print(f"Validation failed at stage: {recent.stage}")
    print(f"Missing items: {len(recent.missing_items)}")
    print(f"Total expected: ${recent.total_expected}")
    print(f"Total found: ${recent.total_found}")
    
    for item in recent.missing_items:
        print(f"  Missing: {item.name} (${item.total_price})")
```

**Common Causes and Fixes**:

1. **PDF Extraction Incomplete**
   ```python
   # Re-run extraction with enhanced settings
   extractor = DABSExtractor()
   extractor.set_extraction_mode("comprehensive")  # More thorough extraction
   
   # Verify extraction against source
   extracted_data = extractor.extract_from_pdf("source.pdf")
   validator.validate_extraction_completeness(source_data, extracted_data, "retry")
   ```

2. **Data Format Inconsistencies**
   ```python
   # Normalize data formats before validation
   normalized_data = []
   for item in raw_data:
       normalized_item = DataItem(
           id=str(item.get('id', item.get('sku', ''))),
           name=item.get('name', item.get('product_name', '')),
           quantity=int(item.get('quantity', 1)),
           unit_price=Decimal(str(item.get('unit_price', 0))),
           total_price=Decimal(str(item.get('total_price', 0))),
           category=item.get('category', 'Unknown')
       )
       normalized_data.append(normalized_item)
   ```

### **Issue 5: Rollback System Failures**

**Symptoms**:
- Transaction rollback not triggered on failures
- Partial processing states persist
- Data corruption after failed operations

**Diagnostic Steps**:
```python
from src.validation.rollback_recovery_system import RollbackRecoverySystem

rollback_system = RollbackRecoverySystem()

# Check transaction history
history = rollback_system.get_transaction_history(10)
for txn in history:
    if txn['state'] == 'failed':
        print(f"Failed transaction: {txn['transaction_id']}")
        print(f"  Metadata: {txn['metadata']}")
        print(f"  Checkpoints: {len(txn.get('checkpoints', []))}")
```

**Common Causes and Fixes**:

1. **Transaction Context Not Used**
   ```python
   # WRONG - No transaction protection
   def process_order(data):
       validate_data(data)
       convert_data(data)
       generate_output(data)
   
   # CORRECT - With transaction protection
   async def process_order(data):
       async with rollback_system.transaction({'order': data}) as txn:
           await txn.checkpoint('validation', validate_data(data))
           await txn.checkpoint('conversion', convert_data(data))
           await txn.checkpoint('output', generate_output(data))
   ```

2. **Rollback Actions Not Defined**
   ```python
   # Add rollback actions for cleanup
   async with rollback_system.transaction(metadata) as txn:
       # Create temporary file
       temp_file = create_temp_file()
       txn.add_rollback_action(lambda: temp_file.unlink())
       
       # Process data
       result = process_data()
   ```

## 📊 Monitoring and Alerts

### **Dashboard Monitoring**
Access the prevention dashboard at: http://localhost:5001

**Key Metrics to Monitor**:
- **Processing Success Rate**: Should be >99.9%
- **Validation Pass Rate**: Should be >99.5%
- **Average Processing Time**: Should be <15 minutes for 1,239 SKUs
- **Component Health**: All components should show "Healthy"

### **Alert Thresholds**
```python
# Configure alert thresholds
ALERT_THRESHOLDS = {
    'processing_time': 900,        # 15 minutes in seconds
    'validation_failure_rate': 0.1, # 0.1% failure rate
    'missing_items_count': 0,      # Zero tolerance for missing items
    'conversion_confidence': 0.8,   # Minimum confidence score
    'mapping_success_rate': 0.95   # 95% mapping success rate
}
```

### **Log Analysis**
```bash
# Monitor critical errors
tail -f logs/error.log | grep -E "(CRITICAL|ERROR)"

# Check validation failures
grep "validation.*failed" logs/application.log | tail -20

# Monitor processing times
grep "processing_time" logs/performance.log | awk '{print $NF}' | sort -n
```

## 🔧 Maintenance Procedures

### **Daily Maintenance**
```bash
#!/bin/bash
# Daily maintenance script

echo "=== Daily DABS Maintenance ==="
date

# 1. Check system health
python3 scripts/health_check.py

# 2. Clean up old logs (keep 30 days)
find logs/ -name "*.log" -mtime +30 -delete

# 3. Backup validation database
cp data/audit/validations.db data/backups/validations_$(date +%Y%m%d).db

# 4. Check disk space
df -h | awk '$5 > 80 {print "WARNING: " $0 " is over 80% full"}'

# 5. Verify prevention framework
python3 -c "
from src.monitoring.prevention_dashboard import PreventionDashboard
dashboard = PreventionDashboard()
status = dashboard.run_health_check()
if not status['healthy']:
    print('ALERT: Prevention framework health check failed')
    exit(1)
print('✅ Prevention framework healthy')
"

echo "=== Daily Maintenance Complete ==="
```

### **Weekly Maintenance**
```bash
#!/bin/bash
# Weekly maintenance script

echo "=== Weekly DABS Maintenance ==="

# 1. Run comprehensive tests
python -m pytest tests/prevention_framework/ -v

# 2. Update vendor mappings
python3 scripts/update_vendor_mappings.py

# 3. Analyze performance trends
python3 scripts/performance_analysis.py --days 7

# 4. Generate maintenance report
python3 scripts/generate_maintenance_report.py --week

echo "=== Weekly Maintenance Complete ==="
```

## 📞 Escalation Procedures

### **Level 1: Operator Response**
**Timeframe**: Immediate (0-15 minutes)
- Check dashboard for obvious issues
- Review recent logs for errors
- Attempt standard troubleshooting procedures
- Document all actions taken

### **Level 2: Technical Support**
**Timeframe**: 15-60 minutes
- Escalate if Level 1 cannot resolve
- Perform advanced diagnostics
- Contact system administrator if needed
- Coordinate with Utah Package Agency if compliance affected

### **Level 3: Emergency Response**
**Timeframe**: Critical (immediate)
- Data loss detected
- System completely down
- Utah compliance deadline at risk
- Contact all stakeholders immediately

### **Contact Information**
```
Level 1 Support: [Phone/Email]
Level 2 Technical: [Phone/Email]
System Administrator: [Phone/Email]
Utah Package Agency: [Phone/Email]
Emergency Escalation: [Phone/Email]
```

## 📋 Troubleshooting Checklist

### **Before Starting Troubleshooting**
- [ ] Document current system state
- [ ] Identify affected components
- [ ] Estimate business impact
- [ ] Notify appropriate stakeholders
- [ ] Backup current state if possible

### **During Troubleshooting**
- [ ] Follow systematic diagnostic procedures
- [ ] Document all actions and results
- [ ] Test fixes in isolation before applying
- [ ] Verify fixes don't break other components
- [ ] Monitor system stability after changes

### **After Resolution**
- [ ] Verify complete system functionality
- [ ] Update documentation with lessons learned
- [ ] Conduct post-incident review
- [ ] Implement preventive measures
- [ ] Update monitoring and alerts

---

**Remember**: The goal is to maintain 100% data integrity and Utah Package Agency compliance while protecting the $28,000 annual automation value. When in doubt, err on the side of caution and escalate appropriately.
