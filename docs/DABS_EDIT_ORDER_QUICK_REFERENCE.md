# DABS Edit Order Quick Reference
## Fast Reference for Editing Existing Orders
used with tool call `dabs_edit_open_order` from MCP Tools also along with the playwright code:

## ✅ **PROVEN SUCCESSFUL WORKFLOW VERIFIED**
**Task ID:** f91fcc2a-89d7-4941-95c3-9284613043f7  
**Success Rate:** 100% (28/28 items added successfully)  
**User Verification:** Perfect match - $4,242.55 total, 38 units confirmed  
**Key Success Factor:** Use simplified brand names (not full descriptions) for search

**Date**: August 24, 2025 12:12 MDT  
**Context**: Extension of Order Creation Process  
**Business Rule**: Only 1 pending order (THE order to edit)

---

## 🚨 **CRITICAL CONSTRAINT**
**DABS allows ONLY 1 pending order** - THE pending order IS the order being edited!

---

## ✏️ **EDIT WORKFLOW - 5 STEPS**

### **STEP 1: Click Edit Button** ✏️
```python
# Primary selector from user's HTML element
await page.click('i.material-icons.blue[data-bs-original-title="Edit"]')
```

### **STEP 2: Verify EditOrder Page** 📄
```python
# Confirm URL and extract Order ID
current_url = page.url  # Should contain "EditOrder?orderId=XXXXX"
order_id = re.search(r'orderId=(\\d+)', current_url).group(1)
```

### **STEP 3A: Add New Items** ➕ **SAME AS CREATION**
```python
# Identical to order creation steps 3-7
await page.click('button[id="dropdownMenuButton"]')  # Add To Order dropdown
await page.click('text=All Items')                   # Select All Items
await page.fill('input[placeholder="Item Code or Name"]', f"{item_code} - {product_name}")
await page.click('input[id="quantity"]')             # Quantity field
await page.evaluate('(selector) => document.querySelector(selector).select()', 'input[id="quantity"]')
await page.type('input[id="quantity"]', str(quantity))  # REPLACE "0"
await page.click('a[href*="EditOrder"]')             # Add to Order
```

### **STEP 3B: Update Existing Quantities** 🔢
```python
# Find existing item row and update quantity
item_row = await page.query_selector(f'tr:has-text("{item_code}")')
quantity_input = await item_row.query_selector('input[type="number"]')
await quantity_input.click()
await quantity_input.evaluate('el => el.select()')   # Select existing value
await quantity_input.type(str(new_quantity))         # Type new quantity
```

### **STEP 4: Return to Orders** 🔙
```python
await page.click('a.btn.button4.btn-sm[href="/ProdApps/OnlineOrders/Orders"]')
```

---

## 📋 **EDIT CAPABILITIES CONFIRMED**

✅ **Add More Items**: Same process as order creation  
✅ **Update Quantities**: Edit existing item quantities in table  
✅ **View Updated Totals**: Automatic price recalculation  
✅ **Single Order Focus**: Only THE pending order to edit  

---

## 🎯 **COMMON EDIT SCENARIOS**

### **Add Items Only**
```python
add_products = [
    {'item_code': '005233', 'product_name': 'MACALLAN 18 YEAR 750ml', 'quantity': 2}
]
```

### **Update Quantities Only**  
```python
quantity_updates = [
    {'item_code': '005232', 'new_quantity': 5}  # Change existing from 3→5
]
```

### **Combined Edit**
```python
# Both add new items AND update existing quantities
add_products = [new_items]
quantity_updates = [existing_updates] 
```

---

**Full Guide**: `docs/DABS_EDIT_ORDER_WORKFLOW_COMPLETE.md`  
**Original Creation**: `docs/DABS_ORDER_CREATION_TECHNICAL_GUIDE_COMPLETE.md`
