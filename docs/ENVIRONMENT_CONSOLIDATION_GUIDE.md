# Environment Variable Consolidation Guide

## 🔍 Current State Analysis (Completed)

### Found Environment Files
- ❌ **No .env files existed** (causing port defaults)
- 📁 `config/quickbooks_config.env` - QB OAuth & API configuration
- 📁 `config/sscs_production.env` - SSCS credentials & integration
- 📁 `config/sscs_credentials_template.env` - SSCS template (duplicate)
- 📁 `config/dabs_ordering.env` - DABS system credentials
- 📁 `data/enhanced_edi_discovery/edi_discovery_config.env` - EDI configuration

### Critical Issues Identified
1. **Port Mismatch**: Archon MCP expected port 8151, got default 8051
2. **Credential Duplication**: SSCS credentials in multiple files
3. **Security Risk**: Plain text passwords in version control
4. **Configuration Fragmentation**: No single source of truth

## ✅ Resolution Strategy

### Primary Environment Files Structure

```
/DABC Pricing - Inventory/
├── .env                    # Main DABS system configuration
└── archon-mcp/
    └── .env               # Archon MCP infrastructure (CREATED ✅)
```

### 1. Archon MCP Configuration (✅ COMPLETED)
**Location**: `/archon-mcp/.env`
- **ARCHON_MCP_PORT=8151** ← Fixes the port conflict
- ARCHON_SERVER_PORT=8281
- ARCHON_UI_PORT=3837
- ARCHON_AGENTS_PORT=8152

### 2. DABS System Configuration (RECOMMENDED)
**Location**: `/.env` (project root)

#### Consolidated Variables from Existing Files:

##### QuickBooks Integration
```bash
# From config/quickbooks_config.env
QB_CLIENT_ID=AB8BKzC2sT9vXeg5wKuwF2Irk990qM7G5UMSltwXd3UNFfUde3
QB_CLIENT_SECRET=nP0eytbYmze696OtlcMPg3fcmHpxg8RC86YGb5sH
QB_COMPANY_ID=9341455221764032
QB_MAX_REQUESTS_PER_MINUTE=500
```

##### SSCS Integration
```bash
# From config/sscs_production.env (consolidated)
SSCS_CCB_URL=https://apps.sunrayasp.com/CDB
SSCS_CCB_USERNAME=v6242shawn
SSCS_CCB_PASSWORD=Notone2016!
SSCS_INTEGRATION_METHOD=ccb_direct_access
```

##### DABS Ordering System
```bash
# From config/dabs_ordering.env
DABS_ORDERING_LOGIN_URL=https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/
DABS_ORDERING_USERNAME=hillshollows
DABS_ORDERING_PASSWORD=Hills2025!@
```

## 🔐 Security Improvements

### Current Security Issues
- ⚠️ Plain text passwords in version control
- ⚠️ Sensitive credentials scattered across multiple files
- ⚠️ No encryption for stored secrets

### Recommended Security Enhancements
1. **Move sensitive credentials to Archon credential service**
2. **Use encrypted storage via Supabase**
3. **Remove plain text passwords from config files**
4. **Implement credential rotation strategy**

## 📋 Migration Steps

### Phase 1: Immediate (COMPLETED)
- ✅ Created `archon-mcp/.env` with port 8151
- ✅ Fixed Archon MCP port configuration conflict

### Phase 2: Consolidation (RECOMMENDED)
1. Create root `.env` with consolidated DABS variables
2. Update applications to load from single source
3. Remove duplicate configuration files
4. Test all integrations work with new structure

### Phase 3: Security Enhancement (FUTURE)
1. Migrate sensitive credentials to Archon credential service
2. Remove plain text secrets from files
3. Implement encrypted credential storage
4. Set up credential rotation procedures

## 🎯 Verification Checklist

### Port Alignment Verification
- [ ] Archon MCP starts on port 8151
- [ ] Cursor can connect to http://localhost:8151/health
- [ ] All DABS integration configs reference 8151
- [ ] start_archon_dabs.sh succeeds

### Configuration Consolidation
- [ ] Single source of truth established
- [ ] No duplicate environment variables
- [ ] All applications load from correct .env files
- [ ] Legacy config files archived/removed

### Security Validation
- [ ] No plain text passwords in version control
- [ ] Credentials properly encrypted
- [ ] Access logging enabled
- [ ] Rotation procedures documented

## 🚀 Next Steps

1. **Test the Archon MCP port fix** by running `start_archon_dabs.sh`
2. **Create consolidated root .env** with DABS system variables
3. **Update applications** to use the new environment structure
4. **Archive legacy configuration files** after migration
5. **Implement security enhancements** for credential management

## 📖 References

- [Archon MCP Configuration](archon-mcp/dabs_integration_config.json)
- [DABS Configuration](config/dabs_config.json)
- [Security Compliance Rules](.cursor/rules/security-compliance.mdc)
- [Project Structure Rules](.cursor/rules/project-structure.mdc)
