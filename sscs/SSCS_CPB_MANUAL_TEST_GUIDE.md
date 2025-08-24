# 🏪 SSCS CPB Manual Upload Test - Complete Guide

## **🎯 OBJECTIVE**
Test NAXML file import into SSCS CPB (Central Price Book) vendor import system to validate the complete DABS automation workflow.

## **📁 TEST FILE**
- **File**: `exports/sscs_cpb/DABS_20250822_ItemPrice.xml`  
- **Size**: 1,063,505 bytes (1MB)
- **Content**: 1,239 DABS SKUs with current pricing
- **Format**: NAXML 2.0 for SSCS CPB vendor import

---

## **🚀 STEP-BY-STEP MANUAL TEST PROCEDURE**

### **STEP 1: SSCS System Access**
1. **Open Browser**: Use Chrome/Firefox for best compatibility
2. **Navigate**: Go to https://sscsta.sscsinc.com/CStore.Web/CDB/
3. **Login**: Enter your SSCS manager credentials
4. **Verify Access**: Confirm you can see the SSCS dashboard

**✅ SUCCESS CRITERIA**: Successfully logged into SSCS CPB system

---

### **STEP 2: DABS Vendor Configuration**
1. **Navigate**: Go to `Setup` → `Vendor Import Setup`
2. **Add Vendor**: Click `Add New Vendor` or `Create Vendor`
3. **Configure DABS Vendor**:
   - **Vendor Name**: `DABS`
   - **Vendor Code**: `DABS` (if required)
   - **Import Type**: `MCLANE` (this supports NAXML format)
   - **File Mask/Pattern**: `DABS_*.xml`
   - **Description**: `Utah DABS Monthly Price Updates`
4. **Save Configuration**
5. **Note EDI Directory**: Record the import directory path shown (needed for automation)

**✅ SUCCESS CRITERIA**: DABS vendor successfully configured in SSCS CPB

---

### **STEP 3: NAXML File Upload**
1. **Locate Upload Section**: Find file upload area in vendor configuration
2. **Browse Files**: Click browse/upload button
3. **Select File**: Choose `DABS_20250822_ItemPrice.xml` from project
4. **Upload File**: Confirm file upload (should show 1MB file uploaded)
5. **Start Import**: Click import/process button

**⏱️ EXPECTED TIME**: 2-5 minutes for 1,239 SKUs

**✅ SUCCESS CRITERIA**: File uploads without errors

---

### **STEP 4: Import Validation**
1. **Monitor Process**: Watch for import progress/completion
2. **Check Results**:
   - **Total Records**: Should show 1,239 items processed
   - **Successful Imports**: Should be 1,239 (100%)
   - **Failed Imports**: Should be 0
   - **Error Messages**: Should be none or minor warnings only
3. **Review Import Log**: Check detailed log for any issues

**✅ SUCCESS CRITERIA**: All 1,239 SKUs imported successfully with no critical errors

---

### **STEP 5: Price Update Verification**
1. **Search Sample Items**:
   - Look up SKU `004356` (BALVENIE DOUBLEWOOD 12 YR SCOTCH)
   - Verify price matches expected value from DABS file
   - Check 2-3 additional random SKUs from the file
2. **Verify Update Timestamps**: Confirm items show today's date/time
3. **Check Status**: Ensure items are marked as active/available

**✅ SUCCESS CRITERIA**: Sample SKUs show correct prices and current timestamps

---

### **STEP 6: POS System Validation**
1. **Navigate to POS Settings**: Find POS/terminal configuration area
2. **Check Sync Status**: Verify items are queued for distribution to sites
3. **DTS Process**: Look for "Distribute to Sites" or similar process
4. **Monitor Completion**: Wait for POS distribution to complete

**⏱️ EXPECTED TIME**: 5-15 minutes for terminal updates

**✅ SUCCESS CRITERIA**: Price updates successfully distributed to POS terminals

---

## **📊 VALIDATION CHECKLIST**

### **Critical Success Indicators:**
- [ ] **File Upload**: NAXML file accepts without format errors
- [ ] **Import Process**: All 1,239 SKUs process successfully  
- [ ] **Price Accuracy**: Sample SKUs show correct pricing
- [ ] **POS Distribution**: Updates propagate to terminals
- [ ] **Processing Time**: Complete process takes <10 minutes total
- [ ] **Error Rate**: Zero critical errors, minimal warnings acceptable

### **Acceptable Minor Issues:**
- ⚠️ SKUs with missing UPC codes (warnings only)
- ⚠️ Items already discontinued (skip, don't fail)
- ⚠️ Price variance warnings (business validation, not errors)

### **Unacceptable Issues (FAIL):**
- ❌ XML format rejected
- ❌ Import process hangs or crashes  
- ❌ Large number of SKUs rejected (>5%)
- ❌ Prices not updating in POS system
- ❌ System performance issues during import

---

## **🚨 TROUBLESHOOTING GUIDE**

### **Common Issues & Solutions:**

**Issue**: "Invalid XML format"
- **Check**: File not corrupted during transfer
- **Fix**: Re-generate NAXML file if needed
- **Contact**: SSCS support for format requirements

**Issue**: "Vendor not configured correctly"  
- **Check**: Import type set to MCLANE
- **Check**: File mask allows DABS_*.xml pattern
- **Fix**: Reconfigure vendor settings

**Issue**: "Import hangs or times out"
- **Check**: File size reasonable (1MB is fine)
- **Check**: Network connectivity stable
- **Wait**: Large imports can take 5-10 minutes

**Issue**: "Prices not updating on terminals"
- **Check**: DTS process completed successfully
- **Check**: Terminals online and communicating
- **Wait**: Terminal updates can take 10-15 minutes

---

## **🎉 SUCCESS COMPLETION**

### **When Test is Successful:**
1. **Document Results**: Record successful import details
2. **Note EDI Directory**: Save the import directory path for automation
3. **Test Sample Transactions**: Verify prices work at POS terminal
4. **Update Project Status**: Mark SSCS integration as complete

### **Next Steps After Success:**
1. **Automation Setup**: Configure automated file drop to EDI directory
2. **Schedule Setup**: Set up monthly automation on 25th at 3:00 AM  
3. **Monitoring**: Implement alerts for import success/failure
4. **Documentation**: Create operator guide for exception handling

---

## **📞 SUPPORT CONTACTS**

**SSCS Technical Support**: 
- Contact your SSCS account manager
- Provide: DABS vendor import questions
- Include: File format and import process support

**Internal Escalation**:
- If test fails: Review error logs and retry once
- If repeated failures: Contact technical team for NAXML format review
- Document: All error messages and import logs for troubleshooting

---

## **🚀 AUTOMATION READY**

Once manual test succeeds, the system is ready for:
- ✅ **Automated Monthly Processing**: 25th at 3:00 AM
- ✅ **File Drop Integration**: Copy NAXML to EDI directory  
- ✅ **90% Time Reduction for Tessa**: 10+ hours → <1 hour monthly
- ✅ **Production Deployment**: Complete DABS automation system

**🎊 This manual test completion enables the full DABS automation benefit!**
