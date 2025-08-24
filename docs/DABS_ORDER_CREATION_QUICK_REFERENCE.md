# DABS Order Creation Quick Reference Card
## Fast Reference for AI Agents

**Date**: August 24, 2025 12:08 MDT  
**Validated**: Task ID `91d356e0-7b7d-4bcb-b1d9-0e55a99d9497` ✅  
**Test Case**: Order `234090` - `005232 HIGHLAND PARK 15 YEAR` - 3 cases - `$2,249.82`

---

## 🚨 **CRITICAL CONSTRAINT**
**DABS allows ONLY 1 pending order at a time** - MUST check before creating new orders!

---

## 📋 **8-STEP PROCESS**

### **STEP 1: Create Order** 🆕
```python
await page.click('a.btn.btn-orange.btn-lg[data-bs-toggle="modal"][data-bs-target="#paTypeModal"]')
```

### **STEP 2: Select Warehouse** 🏭
```python
await page.click('a.btn.btn-primary.btn-lg[href="/ProdApps/OnlineOrders/Orders/CreateOrderPAW"]')
```

### **STEP 3: Add To Order Dropdown** 📋
```python
await page.click('button.btn.btn-primary.dropdown-toggle[id="dropdownMenuButton"]')
```

### **STEP 4: Select All Items** 📦
```python
await page.click('text=All Items')
```

### **STEP 5: Search Product** 🔍
```python
await page.fill('input[type="search"].form-control.form-control-sm[placeholder="Item Code or Name"]', 
                 f"{item_code} - {product_name}")
```

### **STEP 6: Set Quantity** 🔢 **CRITICAL**
```python
quantity_selector = 'input.form-control.Normal11[id="quantity"][name="i.QuantityOrdered"]'
await page.click(quantity_selector)  # Focus
await page.evaluate('(selector) => document.querySelector(selector).select()', quantity_selector)  # Select all
await page.type(quantity_selector, str(quantity))  # Type new value
# MUST replace default "0" - never append!
```

### **STEP 7: Add to Order** ➕
```python
await page.click('a.btn.btn-primary.btn-sm[href*="EditOrder"]')
# Extract Order ID from href: orderId=(\d+)
```

### **STEP 8: Return to Orders** 🔙
```python
await page.click('a.btn.button4.btn-sm[href="/ProdApps/OnlineOrders/Orders"]')
```

---

## ⚠️ **CRITICAL SUCCESS FACTORS**

1. **✅ Check Single Pending Order Constraint First**
2. **✅ Replace Quantity (don't append to "0")**  
3. **✅ Wait for networkidle after navigation**
4. **✅ Extract Order ID from href in Step 7**
5. **✅ Validate quantity after setting**

---

## 📊 **VALIDATED RESULTS**
- Order ID: `234090` ✅
- Product: `005232 - HIGHLAND PARK 15 YEAR 750ml (L)` ✅  
- Quantity: `3` cases (replaced "0") ✅
- Extended Price: `$2,249.82` ✅
- Processing Time: `45.67 seconds` ✅

---

**Full Guide**: `docs/DABS_ORDER_CREATION_TECHNICAL_GUIDE_COMPLETE.md`  
**Implementation**: `src/integration/dabs_automated_ordering.py` (Lines 514-678)
