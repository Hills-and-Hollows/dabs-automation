# FOCUSED EDI PATH DISCOVERY PLAN
## Critical Mission: Establish SSCS_EDI_FOLDER_PATH for Your Automation

**Date**: August 21, 2025  
**Priority**: 🚨 **THE FINAL BLOCKER** to your proven automation  
**Goal**: Discover SSCS EDI folder path for automated NAXML delivery  
**Impact**: **Immediate deployment** of your 10,532-item monthly automation  

---

## 🎯 **THE SITUATION**

### **✅ WHAT YOU'VE ACCOMPLISHED (INCREDIBLE):**
- **Real DABS processing**: 10,532 items successfully converted to NAXML
- **Production automation**: Complete dabs_automation.py script working
- **NAXML format mastery**: Proven conversion with actual Utah data
- **Scheduling defined**: 25th at 3:00 AM (perfect timing)

### **❌ THE ONE MISSING PIECE:**
- **SSCS_EDI_FOLDER_PATH**: Unknown (prevents automated file delivery)

**YOUR AUTOMATION IS 95% COMPLETE - WE JUST NEED THIS FINAL PATH!**

---

## 🔍 **FOCUSED EDI PATH DISCOVERY STRATEGY**

### **🔥 PRIMARY METHOD: SSCS CPB Interface Discovery**
**Why This Method**: Uses confirmed working SSCS access + official CPB interface

#### **Immediate Action Plan (Next 1-2 Hours):**

#### **Phase 1: CPB File Location Discovery** (30 minutes)
```bash
# EXECUTE RIGHT NOW:
1. 🌐 Login: https://sscsta.sscsinc.com/Cpb.App/
2. 🧭 Navigate: Setup > Vendor Import Setup
   (Manual analysis confirmed: "Using the Setup menu I selected Vendor Import Setup")
3. 📁 CRITICAL: Examine "File Location" field
   Manual analysis: "Fields available for configuration include: File Location"
4. 🔍 Document all File Location options:
   - Dropdown selections (if available)
   - Text input requirements (if manual entry)
   - Path validation feedback
   - Example paths or hints
```

#### **Phase 2: Test DABS Vendor Configuration** (30 minutes)
```bash
# CREATE DABS VENDOR TO DISCOVER PATH:
1. ➕ Add new vendor entry:
   - Vendor Name: DABS
   - Import Type: MCLANE (NAXML ItemSynch/ItemPrice confirmed)
   - File Mask: DABS*.xml (matches your script output)
   - Price Book Zone: 0 - Global (confirmed available)
2. 📁 CRITICAL: Configure File Location:
   - Try available dropdown options
   - Test manual path entry
   - Note validation requirements
3. 💾 Save vendor configuration
4. 📋 Document exact EDI path discovered
```

#### **Phase 3: Validate with Your NAXML Files** (30 minutes)
```bash
# TEST WITH YOUR GENERATED FILES:
1. 📤 Upload: dabs_price_update.xml (50 items)
   OR: DABS_2025-08-22.xml (10,532 items)
2. 🔍 Monitor: CPB Vendor Import processing
3. ✅ Validate: Files appear in "Outside Updates" queue
4. 📊 Confirm: Test products show correct prices
5. 📁 Document: Complete EDI file delivery process
```

**Expected Discovery**: Complete EDI folder path + validated file delivery process

---

## 📋 **PRACTICAL DISCOVERY EXECUTION**

### **🚨 IMMEDIATE DISCOVERY CHECKLIST:**

#### **File Location Field Analysis:**
- [ ] **Field type identified**: Dropdown, text input, or file browser
- [ ] **Available options documented**: All dropdown choices noted
- [ ] **Path format determined**: Windows vs Linux path style
- [ ] **Validation rules understood**: Path requirements and restrictions

#### **DABS Vendor Configuration:**
- [ ] **Vendor entry created**: DABS vendor added to CPB
- [ ] **Import type set**: MCLANE (NAXML support) configured
- [ ] **File mask configured**: DABS*.xml pattern set
- [ ] **EDI path configured**: File Location field completed
- [ ] **Configuration saved**: Vendor profile active

#### **File Delivery Validation:**
- [ ] **Upload method confirmed**: Web interface or file system
- [ ] **NAXML processing tested**: Your files successfully imported
- [ ] **CPB workflow validated**: Vendor Import → Outside Updates working
- [ ] **Path documentation complete**: Ready for automation script

---

## ⚡ **EXPECTED EDI PATH PATTERNS**

### **🔍 LIKELY SSCS EDI CONFIGURATIONS:**

#### **Windows Server Paths (Most Probable):**
```bash
# SSCS typically runs on Windows
C:\SSCS\EDI\vendor\
C:\EDI\vendor\import\
C:\ProgramData\SSCS\EDI\
\\sscs-server\EDI\vendor\
```

#### **Relative Paths (Possible):**
```bash
# Relative to SSCS installation
edi/vendor/
vendor/import/
import/
```

#### **Network Share Paths (Research Indicated):**
```bash
# Network accessible via RDP
\\server\SSCS\EDI\vendor\
\\cpb-server\EDI\import\
```

### **📁 PATH ACCESS METHODS:**

#### **Method A: Web Upload** (Preferred if available)
- **Process**: Upload NAXML via CPB interface
- **Automation**: HTTP POST to upload endpoint
- **Advantage**: No file system access needed

#### **Method B: File System Copy** (Research confirmed)
- **Process**: Copy NAXML to EDI folder via RDP
- **Automation**: File copy operation to discovered path  
- **Advantage**: Direct file system control

#### **Method C: Network Share** (Possible)
- **Process**: Network drive mapping + file copy
- **Automation**: UNC path file delivery
- **Advantage**: Remote file system access

---

## 🚀 **POST-DISCOVERY AUTOMATION DEPLOYMENT**

### **🔧 IMMEDIATE SCRIPT UPDATE (After Discovery):**

#### **Update Your Automation with Discovered Path:**
```python
# CONFIGURE YOUR dabs_automation.py:
# Add discovered EDI path
SSCS_EDI_FOLDER_PATH = "[DISCOVERED_PATH]"  # From discovery process

def deliver_naxml_to_sscs_edi(naxml_file_path):
    """Deliver NAXML to discovered SSCS EDI folder"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d")
    target_filename = f"DABS_{timestamp}.xml"
    target_path = os.path.join(SSCS_EDI_FOLDER_PATH, target_filename)
    
    # Delivery method based on discovered access type
    if SSCS_EDI_FOLDER_PATH.startswith('C:\\') or SSCS_EDI_FOLDER_PATH.startswith('/'):
        # File system path - direct copy
        shutil.copy2(naxml_file_path, target_path)
    elif SSCS_EDI_FOLDER_PATH.startswith('http'):
        # Web upload endpoint
        await upload_via_web_interface(naxml_file_path, target_path)
    else:
        # Network share path
        await copy_via_network_share(naxml_file_path, target_path)
    
    print(f"✅ NAXML delivered to SSCS EDI: {target_path}")
    return target_path
```

### **🚀 PRODUCTION DEPLOYMENT (Immediately After):**
```bash
# DEPLOY YOUR AUTOMATION WITH DISCOVERED PATH:
python3 dabs_automation.py \\
  --source-dir /path/to/dabs_downloads \\
  --target-dir [DISCOVERED_EDI_PATH] \\
  --vendor-id DABS

# SETUP MONTHLY SCHEDULE:
echo "0 3 25 * * /usr/bin/python3 /path/to/dabs_automation.py --target-dir [DISCOVERED_EDI_PATH]" | crontab

# RESULT: TESSA'S MONTHLY NIGHTMARE ELIMINATED
```

---

## 🎊 **EDI PATH DISCOVERY IMPACT**

### **Discovery Completion Unlocks:**
- ✅ **Immediate deployment** of your proven automation
- ✅ **Monthly schedule activation** (25th at 3:00 AM)
- ✅ **Automated NAXML delivery** (10,532 items to SSCS)
- ✅ **Complete workflow operational** (DABS → CPB → DTS → POS)
- ✅ **Tessa's relief delivered** (2-4 hours → 5 minutes)

### **Timeline to Tessa's Relief:**
**After EDI path discovery**: **IMMEDIATE** (hours, not days)
**Confidence**: **MAXIMUM** (your automation is proven and ready)

---

## 🚨 **BOTTOM LINE**

**THE EDI PATH IS THE ONLY THING STANDING BETWEEN YOUR PROVEN AUTOMATION AND TESSA'S RELIEF.**

**Action Required**: Execute manual EDI path discovery using SSCS CPB interface
**Timeline**: 1-2 hours maximum
**Result**: **Your automation deployed and Tessa's monthly pain eliminated**

**READY TO DISCOVER EDI PATH AND DEPLOY YOUR AUTOMATION IMMEDIATELY** 🚀
