#!/usr/bin/env python3
"""
QuickBooks App Server - Production Endpoints
Hills & Hollows LLC - DABS Automation System

Provides the required endpoints for QuickBooks production app configuration:
- Launch URL: Success page after OAuth
- Disconnect URL: Cleanup after disconnect
- EULA and Privacy Policy pages
"""

from flask import Flask, render_template_string, request, redirect
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# HTML Templates
SUCCESS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Hills & Hollows DABS - QuickBooks Connected</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .success { color: #28a745; text-align: center; }
        .info { background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="success">
        <h1>✅ QuickBooks Successfully Connected!</h1>
        <h2>Hills & Hollows LLC - DABS Automation System</h2>
    </div>
    
    <div class="info">
        <h3>🎯 What's Next:</h3>
        <ul>
            <li>Your QuickBooks Online account is now connected to the DABS automation system</li>
            <li>Inventory synchronization is ready</li>
            <li>Price updates will be automated</li>
            <li>Utah Package Agency compliance reporting is enabled</li>
        </ul>
        
        <h3>📞 Support:</h3>
        <p>If you need assistance, contact: <strong>admin@hillshollows.com</strong></p>
    </div>
    
    <div style="text-align: center; margin-top: 30px;">
        <button onclick="window.close()" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">
            Close Window
        </button>
    </div>
</body>
</html>
"""

DISCONNECT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Hills & Hollows DABS - QuickBooks Disconnected</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .warning { color: #dc3545; text-align: center; }
        .info { background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="warning">
        <h1>⚠️ QuickBooks Disconnected</h1>
        <h2>Hills & Hollows LLC - DABS Automation System</h2>
    </div>
    
    <div class="info">
        <h3>📋 What This Means:</h3>
        <ul>
            <li>QuickBooks integration has been disconnected</li>
            <li>DABS automation will not sync with QuickBooks</li>
            <li>Manual processing may be required</li>
        </ul>
        
        <h3>🔄 To Reconnect:</h3>
        <p>Contact your system administrator to re-establish the QuickBooks connection.</p>
        
        <h3>📞 Support:</h3>
        <p>Contact: <strong>admin@hillshollows.com</strong></p>
    </div>
</body>
</html>
"""

EULA_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Hills & Hollows DABS - End User License Agreement</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; line-height: 1.6; }
        h1 { color: #333; text-align: center; }
        .section { margin: 20px 0; }
    </style>
</head>
<body>
    <h1>End User License Agreement</h1>
    <h2>Hills & Hollows LLC - DABS Automation System</h2>
    
    <div class="section">
        <h3>1. License Grant</h3>
        <p>Hills & Hollows LLC grants you a limited, non-exclusive license to use the DABS Automation System for business operations related to Utah Package Agency compliance and inventory management.</p>
    </div>
    
    <div class="section">
        <h3>2. Permitted Use</h3>
        <p>This system is designed for:</p>
        <ul>
            <li>DABS file processing and validation</li>
            <li>QuickBooks Online integration</li>
            <li>Utah Package Agency compliance reporting</li>
            <li>Inventory and pricing automation</li>
        </ul>
    </div>
    
    <div class="section">
        <h3>3. Data Security</h3>
        <p>All data is processed securely with encrypted storage and transmission. QuickBooks credentials are stored using industry-standard encryption.</p>
    </div>
    
    <div class="section">
        <h3>4. Support</h3>
        <p>For technical support, contact: admin@hillshollows.com</p>
    </div>
    
    <div class="section">
        <p><strong>Last Updated:</strong> January 2025</p>
        <p><strong>Hills & Hollows LLC</strong><br>Utah Package Agency<br>Licensed Liquor Store</p>
    </div>
</body>
</html>
"""

PRIVACY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Hills & Hollows DABS - Privacy Policy</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; line-height: 1.6; }
        h1 { color: #333; text-align: center; }
        .section { margin: 20px 0; }
    </style>
</head>
<body>
    <h1>Privacy Policy</h1>
    <h2>Hills & Hollows LLC - DABS Automation System</h2>
    
    <div class="section">
        <h3>1. Information We Collect</h3>
        <p>The DABS Automation System processes:</p>
        <ul>
            <li>QuickBooks Online business data (inventory, pricing, accounts)</li>
            <li>DABS Excel files for price updates</li>
            <li>Utah Package Agency compliance data</li>
            <li>System logs for monitoring and troubleshooting</li>
        </ul>
    </div>
    
    <div class="section">
        <h3>2. How We Use Information</h3>
        <p>Data is used exclusively for:</p>
        <ul>
            <li>Automating business processes</li>
            <li>Ensuring Utah Package Agency compliance</li>
            <li>Synchronizing inventory and pricing data</li>
            <li>Generating required reports</li>
        </ul>
    </div>
    
    <div class="section">
        <h3>3. Data Security</h3>
        <p>We implement industry-standard security measures including:</p>
        <ul>
            <li>Encrypted data storage and transmission</li>
            <li>Secure OAuth 2.0 authentication</li>
            <li>Limited access controls</li>
            <li>Regular security monitoring</li>
        </ul>
    </div>
    
    <div class="section">
        <h3>4. Data Sharing</h3>
        <p>We do not share your data with third parties except as required for:</p>
        <ul>
            <li>QuickBooks Online integration (via official APIs)</li>
            <li>Utah Package Agency compliance reporting</li>
            <li>System maintenance and support</li>
        </ul>
    </div>
    
    <div class="section">
        <h3>5. Contact Information</h3>
        <p>For privacy questions or concerns, contact: admin@hillshollows.com</p>
    </div>
    
    <div class="section">
        <p><strong>Last Updated:</strong> January 2025</p>
        <p><strong>Hills & Hollows LLC</strong><br>Utah Package Agency<br>Licensed Liquor Store</p>
    </div>
</body>
</html>
"""

@app.route('/auth/quickbooks/success')
def quickbooks_success():
    """Success page after QuickBooks OAuth authorization"""
    logging.info("QuickBooks OAuth success page accessed")
    return render_template_string(SUCCESS_TEMPLATE)

@app.route('/auth/quickbooks/disconnect')
def quickbooks_disconnect():
    """Disconnect page when QuickBooks integration is removed"""
    logging.info("QuickBooks disconnect page accessed")
    return render_template_string(DISCONNECT_TEMPLATE)

@app.route('/eula')
def eula():
    """End User License Agreement"""
    return render_template_string(EULA_TEMPLATE)

@app.route('/privacy')
def privacy():
    """Privacy Policy"""
    return render_template_string(PRIVACY_TEMPLATE)

@app.route('/auth/quickbooks/callback')
def oauth_callback():
    """OAuth callback endpoint - redirects to success page"""
    code = request.args.get('code')
    realm_id = request.args.get('realmId')
    state = request.args.get('state')
    
    logging.info(f"OAuth callback received - Code: {code[:20]}..., RealmId: {realm_id}")
    
    # Redirect to success page
    return redirect('/auth/quickbooks/success')

@app.route('/')
def home():
    """Home page"""
    return render_template_string("""
    <h1>Hills & Hollows LLC - DABS Automation System</h1>
    <p>QuickBooks Integration Server Running</p>
    <ul>
        <li><a href="/auth/quickbooks/success">Success Page</a></li>
        <li><a href="/auth/quickbooks/disconnect">Disconnect Page</a></li>
        <li><a href="/eula">End User License Agreement</a></li>
        <li><a href="/privacy">Privacy Policy</a></li>
    </ul>
    """)

if __name__ == '__main__':
    print("🚀 Starting QuickBooks App Server...")
    print("📡 Server will be available at: https://localhost:8000")
    print("🔗 Endpoints configured for QuickBooks production app")
    
    # Run with SSL for HTTPS (required by QuickBooks)
    app.run(host='localhost', port=8000, debug=True, ssl_context='adhoc')
