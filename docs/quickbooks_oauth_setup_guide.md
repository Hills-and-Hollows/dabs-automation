# QuickBooks OAuth 2.0 Setup Guide
## Hills & Hollows LLC - DABS Automation System

### Overview
This guide walks through setting up QuickBooks Online OAuth 2.0 integration for the DABS automation system.

### Prerequisites
- QuickBooks Online account (shawn@owenent.com)
- Intuit Developer account access
- Admin access to Hills & Hollows LLC QuickBooks company

### Step 1: Create Intuit Developer Account

1. **Visit Intuit Developer Portal**
   - Go to: https://developer.intuit.com/
   - Sign in with QuickBooks credentials: `shawn@owenent.com`

2. **Create New App**
   - Click "Create an app"
   - Select "QuickBooks Online and Payments"
   - App Name: "Hills & Hollows DABS Automation"
   - Description: "Automated inventory and pricing management system for Utah Package Agency"

3. **Configure App Settings**
   - **Redirect URIs**: `https://localhost:8000/auth/quickbooks/callback`
   - **Scopes**: `com.intuit.quickbooks.accounting`
   - **App Environment**: Production (after testing in Sandbox)

### Step 2: Obtain OAuth Credentials

After creating the app, you'll receive:
- **Client ID**: Copy this value
- **Client Secret**: Copy this value (keep secure)
- **Company ID**: Will be obtained during OAuth flow

### Step 3: Update Configuration Files

1. **Update config/quickbooks_config.env**:
```bash
QB_CLIENT_ID=your_actual_client_id_here
QB_CLIENT_SECRET=your_actual_client_secret_here
QB_REDIRECT_URI=https://localhost:8000/auth/quickbooks/callback
```

2. **Update config/secure_credentials.json**:
```json
{
  "credentials": {
    "quickbooks_online": {
      "oauth_config": {
        "client_id": "your_actual_client_id_here",
        "client_secret": "your_actual_client_secret_here"
      }
    }
  }
}
```

3. **Set Environment Variables**:
```bash
export QB_CLIENT_ID="your_actual_client_id_here"
export QB_CLIENT_SECRET="your_actual_client_secret_here"
export QB_USERNAME="shawn@owenent.com"
export QB_PASSWORD="teymTJWoZr47!"
```

### Step 4: Test OAuth Flow

1. **Run OAuth Manager**:
```bash
cd /Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory
python src/automation/workflows/quickbooks_integration/qb_oauth_manager.py
```

2. **Complete Authorization**:
   - Copy the authorization URL from output
   - Visit URL in browser
   - Sign in to QuickBooks Online
   - Authorize the application
   - Copy authorization code from callback URL

3. **Exchange Code for Tokens**:
   - Use the authorization code to get access/refresh tokens
   - Tokens will be automatically saved and encrypted

### Step 5: Verify Integration

1. **Check Token Storage**:
   - Tokens saved in: `config/quickbooks_tokens.json.encrypted`
   - Verify file exists and has proper permissions

2. **Test API Access**:
   - Run inventory sync test
   - Verify connection to QuickBooks company
   - Confirm item read/write permissions

### Security Considerations

- **Never commit credentials to version control**
- **Use environment variables for sensitive data**
- **Encrypt token storage**
- **Implement proper access controls**
- **Regular token refresh validation**

### Troubleshooting

**Common Issues**:
1. **Invalid Client Credentials**: Verify Client ID/Secret from developer portal
2. **Redirect URI Mismatch**: Ensure exact match in app settings
3. **Scope Permissions**: Verify accounting scope is enabled
4. **Company Access**: Ensure user has admin access to QuickBooks company

**Error Codes**:
- `invalid_client`: Check Client ID/Secret
- `invalid_grant`: Authorization code expired or invalid
- `invalid_scope`: Scope not enabled for app
- `access_denied`: User denied authorization

### Next Steps

After successful OAuth setup:
1. Test inventory synchronization
2. Validate DABS → QuickBooks workflow
3. Configure real-time sync intervals
4. Set up error monitoring and alerts

### Support Resources

- **Intuit Developer Docs**: https://developer.intuit.com/app/developer/qbo/docs/
- **OAuth 2.0 Guide**: https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/oauth-2.0
- **API Explorer**: https://developer.intuit.com/app/developer/qbo/docs/api/accounting/most-commonly-used/item
