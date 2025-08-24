# SSCS CPB Manual Testing Guide
## Test NAXML Upload for Tessa's Automation

### Step 1: Login to SSCS
1. Open browser: https://sscsta.sscsinc.com/TransactionAnalysis.App/#!/merchandisesales/
2. Username: v6242shawn
3. Password: Notone2016!
4. Should redirect to CDB interface

### Step 2: Navigate to Central Price Book
1. Look for "Price Book", "CPB", "Central Price", or "Vendor" links
2. Navigate to CPB section
3. Look for "Vendor Import" or "Import" functionality

### Step 3: Configure DABS Vendor
1. Create new vendor profile named "DABS"
2. Set import type to "NAXML ItemSynch/ItemPrice" (McLane profile)
3. Set file mask to "DABS*.xml"
4. Enable "Apply Vendor List Price"
5. Set vendor zone to "ZONE0_GLOBAL"

### Step 4: Test NAXML Upload
1. Use test file: data/sscs_discovery/DABS_TEST_ItemPrice.xml
2. Upload via vendor import interface
3. Check "Outside Updates" for staged changes
4. Validate price changes match test data

### Step 5: Test DTS (Distribute to Sites)
1. Accept changes in Outside Updates
2. Run "Distribute to Sites" (DTS)
3. Check for Scheduled Task automation options
4. Validate price changes reach POS terminals

### Expected Results:
- CPB processes NAXML file without errors
- Test products appear in Outside Updates
- Price changes match test data (BACARDI MOJITO: $19.99)
- DTS successfully distributes to POS

### Documentation:
- Screenshot each step
- Note any configuration options
- Document error messages (if any)
- Record timing for processing steps
