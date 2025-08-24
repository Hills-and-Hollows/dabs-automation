# DABS MCP Tools - Quick Reference Guide
## Essential Information for DABS Order Management

**Updated**: August 24, 2025 09:01 MDT  
**Status**: ✅ **PRODUCTION READY**  

---

## 🔑 **CRITICAL AUTHENTICATION FIX**

### **Issue**: DABS login fails with 405 Method Not Allowed
### **Solution**: Navigate to main page, not `/Login` endpoint

```python
# ❌ WRONG (causes 405 error)
await page.goto(base_url + "Login")

# ✅ CORRECT (works perfectly)
await page.goto(base_url)  # Login form is on main page
```

**Files Updated**: `src/integration/dabs_automated_ordering.py`

---

## 🗑️ **ORDER DELETION - PROVEN SEQUENCE**

### **Two-Step Process** (both steps required):

#### **Step 1**: Click trash icon
```python
await page.click('i.material-icons[data-bs-original-title="Delete"]')
```

#### **Step 2**: Click red Delete button (in confirmation dialog)
```python
await page.click('input[type="submit"][value="Delete"].btn.btn-red')
```

**Files Updated**: `src/mcp/dabs_simple_mcp_server.py`

---

## 📋 **18 DABS MCP TOOLS - ALL WORKING**

### **Quick Tool List**:
- `mcp_dabs-ordering_dabs_login_status` - Check auth
- `mcp_dabs-ordering_dabs_perform_login` - Login  
- `mcp_dabs-ordering_dabs_delete_open_order` - **Delete orders**
- `mcp_dabs-ordering_dabs_get_open_order` - Check pending
- `mcp_dabs-ordering_dabs_create_new_order` - Create new
- `mcp_dabs-ordering_dabs_submit_order` - Submit
- `mcp_dabs-ordering_dabs_search_all_items` - Product search
- ... (15 more tools)

---

## ⚡ **QUICK TROUBLESHOOTING**

### **Problem**: "No tools or prompts" in Cursor
**Solution**: Restart MCP server
```bash
pkill -f dabs_simple_mcp_server.py
python3 src/mcp/dabs_simple_mcp_server.py > dabs.log 2>&1 &
```

### **Problem**: Authentication fails
**Solution**: Check login URL (should be main page, not `/Login`)

### **Problem**: Delete doesn't work
**Solution**: Use two-step sequence (trash icon → red Delete button)

---

## 🎯 **COMMON WORKFLOWS**

### **Delete Pending Order**:
```python
# Check for pending order
open_order = mcp_dabs_ordering_dabs_get_open_order()

# Delete if exists
if order_exists:
    result = mcp_dabs_ordering_dabs_delete_open_order(confirm=True)
```

### **Create New Order**:
```python
# Create new order (requires no pending orders)
new_order = mcp_dabs_ordering_dabs_create_new_order()

# Add items
mcp_dabs_ordering_dabs_add_item_to_order(
    item_code="000159", 
    cases=2
)

# Submit
mcp_dabs_ordering_dabs_submit_order()
```

---

## 🔧 **SERVER MANAGEMENT**

### **Start DABS MCP Server**:
```bash
cd "/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory"
python3 src/mcp/dabs_simple_mcp_server.py > dabs.log 2>&1 &
```

### **Check Server Status**:
```bash
ps aux | grep dabs_simple_mcp_server.py
tail -f dabs.log
```

### **Stop Server**:
```bash
pkill -f dabs_simple_mcp_server.py
```

---

## 📊 **SUCCESS INDICATORS**

### **Authentication Working**:
- Login status returns `"authenticated": true`
- Auth file exists: `dabs_auth.json`
- All tools accessible in Cursor

### **Order Deletion Working**:
- Order disappears from Orders page
- Success message confirms deletion
- New orders can be created

---

## 🚨 **EMERGENCY CONTACTS**

### **DABS System Issues**:
- **URL**: https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/
- **Credentials**: hillshollows / Hills2025!@
- **Manual Backup**: Use web interface directly

### **Technical Support**:
- **Config File**: `.cursor/mcp.json`
- **Log Files**: `dabs.log`, `dabs_mcp.log`  
- **Documentation**: `docs/DABS_AUTHENTICATION_FIX_AND_ORDER_DELETION_COMPLETE.md`

---

**🎉 ALL SYSTEMS OPERATIONAL - READY FOR PRODUCTION USE** ✅
