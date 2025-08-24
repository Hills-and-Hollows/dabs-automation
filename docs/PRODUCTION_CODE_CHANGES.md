# 🔧 PRODUCTION CODE CHANGES - Implementation Guide

## 📋 **REQUIRED CODE MODIFICATIONS FOR PRODUCTION**

**Date**: August 23, 2025  
**Purpose**: Specific code changes needed to deploy DABS system to production  
**Status**: Ready for implementation  

---

## 🔄 **1. FastAPI Application Updates**

### **Update `src/api/enhanced_main.py`**

```python
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPSRedirectMiddleware
import logging

# Production environment detection
ENV = os.getenv("ENV", "development")
DOMAIN = os.getenv("DOMAIN", "localhost")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Production logging configuration
if ENV == "production":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("/var/log/dabs-ordering.log"),
            logging.StreamHandler()
        ]
    )

# FastAPI app configuration
app_kwargs = {
    "title": "DABS Restaurant Ordering System",
    "description": "Hills & Hollows LLC - Utah Package Agency",
    "version": "1.0.0"
}

# Disable docs in production
if ENV == "production":
    app_kwargs.update({
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None
    })

app = FastAPI(**app_kwargs)

# Production CORS configuration
if ENV == "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
else:
    # Development CORS (permissive)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Production middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    
    if ENV == "production":
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"  # Allow embedding in same origin
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Allow embedding from WordPress domain
        if "hillsandhollowsmarket.com" in str(request.headers.get("referer", "")):
            response.headers["X-Frame-Options"] = "ALLOW-FROM https://hillsandhollowsmarket.com"
    
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    """Production health check endpoint"""
    return {
        "status": "healthy",
        "environment": ENV,
        "domain": DOMAIN,
        "timestamp": datetime.utcnow().isoformat()
    }

# Production error handlers
@app.exception_handler(500)
async def internal_server_error(request, exc):
    if ENV == "production":
        # Log error but don't expose details
        logging.error(f"Internal server error: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    else:
        # Development: show full error
        raise exc

# Your existing endpoints here...
# (Keep all existing routes)
```

---

## 🌐 **2. Production Environment Configuration**

### **Create `.env.production`**
```bash
# Production environment variables
ENV=production
DOMAIN=orders.hillsandhollowsmarket.com
ALLOWED_ORIGINS=https://hillsandhollowsmarket.com,https://www.hillsandhollowsmarket.com

# Database configuration
DATABASE_URL=sqlite:///opt/dabs/data/production.db

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/dabs-ordering.log

# Feature flags
ENABLE_DEBUG=false
ENABLE_DOCS=false
```

### **Update `requirements.txt`**
```txt
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
jinja2>=3.1.2
python-dotenv>=1.0.0
pandas>=2.1.0
openpyxl>=3.1.0
aiofiles>=23.2.1
httpx>=0.25.0
pydantic>=2.5.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
gunicorn>=21.2.0
```

---

## 📋 **3. Systemd Service Configuration**

### **Create `/etc/systemd/system/dabs-ordering.service`**
```ini
[Unit]
Description=DABS Restaurant Ordering System
After=network.target

[Service]
Type=exec
User=dabs
Group=dabs
WorkingDirectory=/opt/dabs
Environment=PATH=/opt/dabs/venv/bin
EnvironmentFile=/opt/dabs/.env.production
ExecStart=/opt/dabs/venv/bin/uvicorn src.api.enhanced_main:app --host 0.0.0.0 --port 8000 --workers 2
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 🔒 **4. Nginx Configuration**

### **Create `/etc/nginx/sites-available/dabs-ordering`**
```nginx
server {
    listen 80;
    server_name orders.hillsandhollowsmarket.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name orders.hillsandhollowsmarket.com;

    # SSL configuration (managed by certbot)
    ssl_certificate /etc/letsencrypt/live/orders.hillsandhollowsmarket.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/orders.hillsandhollowsmarket.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Allow embedding from WordPress
    location / {
        # Check if request is from WordPress domain
        if ($http_referer ~* "^https://.*\.?hillsandhollowsmarket\.com") {
            add_header X-Frame-Options "ALLOW-FROM https://hillsandhollowsmarket.com" always;
        }
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Security: block common attack paths
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ ^/(wp-|admin|config|\.env) {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

---

## 🗄️ **5. Database & Data Management**

### **Production Data Directory Structure**
```bash
# Create production data structure
sudo mkdir -p /opt/dabs/{data,logs,backups,config}
sudo chown -R dabs:dabs /opt/dabs

# Data structure
/opt/dabs/
├── data/
│   ├── production.db          # SQLite database
│   ├── dabs_backups/         # DABS Excel backups
│   └── exports/              # Generated exports
├── logs/
│   ├── application.log       # Application logs
│   ├── nginx-access.log      # Nginx access logs
│   └── nginx-error.log       # Nginx error logs
├── backups/
│   └── daily/                # Daily automated backups
└── config/
    ├── .env.production       # Environment variables
    └── dabs_config.json      # Application config
```

### **Database Migration Script**
```python
# scripts/migrate_to_production.py
import os
import shutil
from pathlib import Path

def migrate_data_to_production():
    """Migrate development data to production structure"""
    
    # Source paths (development)
    dev_data = Path("data/")
    dev_config = Path("config/")
    
    # Production paths
    prod_base = Path("/opt/dabs/")
    prod_data = prod_base / "data"
    prod_config = prod_base / "config"
    
    # Create production directories
    prod_data.mkdir(parents=True, exist_ok=True)
    prod_config.mkdir(parents=True, exist_ok=True)
    
    # Copy DABS backup files
    if (dev_data / "dabs_backups").exists():
        shutil.copytree(
            dev_data / "dabs_backups",
            prod_data / "dabs_backups",
            dirs_exist_ok=True
        )
    
    # Copy exports
    if (dev_data / "exports").exists():
        shutil.copytree(
            dev_data / "exports", 
            prod_data / "exports",
            dirs_exist_ok=True
        )
    
    # Copy configuration
    if dev_config.exists():
        for config_file in dev_config.glob("*.json"):
            shutil.copy2(config_file, prod_config)
    
    print("✅ Data migration to production complete!")

if __name__ == "__main__":
    migrate_data_to_production()
```

---

## 🔄 **6. Deployment Scripts**

### **Create `scripts/deploy.sh`**
```bash
#!/bin/bash
# Production deployment script

set -e

# Configuration
APP_DIR="/opt/dabs"
SERVICE_NAME="dabs-ordering"
BACKUP_DIR="/opt/dabs/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "🚀 Starting DABS deployment..."

# Create backup before deployment
echo "📦 Creating pre-deployment backup..."
mkdir -p "$BACKUP_DIR/pre-deploy-$TIMESTAMP"
cp -r "$APP_DIR/data" "$BACKUP_DIR/pre-deploy-$TIMESTAMP/"
cp -r "$APP_DIR/config" "$BACKUP_DIR/pre-deploy-$TIMESTAMP/"

# Update application code
echo "📥 Updating application code..."
cd "$APP_DIR"
git pull origin main

# Update dependencies
echo "📋 Updating dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Run database migrations if any
echo "🗄️ Running database migrations..."
python scripts/migrate_to_production.py

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl restart nginx

# Wait for service to start
sleep 5

# Health check
echo "🏥 Performing health check..."
HEALTH_URL="https://orders.hillsandhollowsmarket.com/health"
if curl -f "$HEALTH_URL" > /dev/null 2>&1; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed!"
    echo "🔄 Rolling back..."
    
    # Rollback data
    cp -r "$BACKUP_DIR/pre-deploy-$TIMESTAMP/data/"* "$APP_DIR/data/"
    cp -r "$BACKUP_DIR/pre-deploy-$TIMESTAMP/config/"* "$APP_DIR/config/"
    
    # Restart with old data
    sudo systemctl restart "$SERVICE_NAME"
    
    exit 1
fi

# Cleanup old backups (keep last 10)
echo "🧹 Cleaning up old backups..."
cd "$BACKUP_DIR"
ls -t | tail -n +11 | xargs -d '\n' rm -rf --

echo "🎉 Deployment completed successfully!"
echo "🌐 Service available at: https://orders.hillsandhollowsmarket.com"
echo "📊 Health check: $HEALTH_URL"
```

### **Create `scripts/backup.sh`**
```bash
#!/bin/bash
# Daily backup script

set -e

# Configuration
APP_DIR="/opt/dabs"
BACKUP_BASE="/opt/dabs/backups"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_BASE/daily-$DATE-$TIMESTAMP"

echo "📦 Starting daily backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup application data
echo "🗄️ Backing up data..."
cp -r "$APP_DIR/data" "$BACKUP_DIR/"
cp -r "$APP_DIR/config" "$BACKUP_DIR/"
cp -r "$APP_DIR/logs" "$BACKUP_DIR/"

# Create compressed archive
echo "🗜️ Compressing backup..."
cd "$BACKUP_BASE"
tar -czf "daily-backup-$DATE-$TIMESTAMP.tar.gz" "daily-$DATE-$TIMESTAMP"
rm -rf "daily-$DATE-$TIMESTAMP"

# Upload to cloud storage (optional)
# aws s3 cp "daily-backup-$DATE-$TIMESTAMP.tar.gz" s3://your-backup-bucket/

# Cleanup old backups (keep last 30 days)
echo "🧹 Cleaning up old backups..."
find "$BACKUP_BASE" -name "daily-backup-*.tar.gz" -mtime +30 -delete

echo "✅ Backup completed: daily-backup-$DATE-$TIMESTAMP.tar.gz"
```

---

## 📊 **7. Monitoring & Alerting**

### **Create `scripts/health_monitor.py`**
```python
#!/usr/bin/env python3
"""Health monitoring script for DABS ordering system"""

import requests
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
HEALTH_URL = "https://orders.hillsandhollowsmarket.com/health"
ALERT_EMAIL = "hillshollowsmanager@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def check_health():
    """Check application health"""
    try:
        response = requests.get(HEALTH_URL, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return False

def send_alert(subject, message):
    """Send alert email"""
    try:
        msg = MIMEMultipart()
        msg['From'] = "alerts@hillsandhollowsmarket.com"
        msg['To'] = ALERT_EMAIL
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        # Use environment variables for credentials
        server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASS'))
        server.send_message(msg)
        server.quit()
        
        logging.info("Alert email sent successfully")
    except Exception as e:
        logging.error(f"Failed to send alert: {e}")

def main():
    """Main monitoring function"""
    logging.basicConfig(level=logging.INFO)
    
    if not check_health():
        subject = "🚨 DABS Ordering System - Health Check Failed"
        message = f"""
        Health check failed for DABS Ordering System.
        
        Time: {datetime.now().isoformat()}
        URL: {HEALTH_URL}
        
        Please check the system immediately.
        """
        send_alert(subject, message)
        
        # Try to restart service
        import subprocess
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', 'dabs-ordering'], check=True)
            logging.info("Service restart attempted")
        except subprocess.CalledProcessError as e:
            logging.error(f"Service restart failed: {e}")
    
    else:
        logging.info("Health check passed")

if __name__ == "__main__":
    main()
```

---

## 🔧 **8. WordPress Integration Updates**

### **Production WordPress Embed Code**
```html
<!-- WordPress Page: /restaurant-orders/ -->
<!-- PRODUCTION VERSION -->

<style>
.restaurant-ordering-fullwidth {
    width: 100vw !important;
    max-width: none !important;
    margin-left: calc(50% - 50vw) !important;
    margin-right: calc(50% - 50vw) !important;
    background: #f8f9fa;
    padding: 20px 0;
}

.restaurant-ordering-fullwidth iframe {
    width: 100% !important;
    min-height: 1200px !important;
    height: 1200px !important;
    border: none !important;
    border-radius: 8px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}

@media (max-width: 768px) {
    .restaurant-ordering-fullwidth iframe {
        min-height: 800px !important;
        height: 800px !important;
    }
}
</style>

<div class="restaurant-ordering-fullwidth">
    <div style="max-width: 1400px; margin: 0 auto; padding: 0 20px;">
        <h2>🍽️ DABS Ordering Portal for Restaurants</h2>
        <p>
            <strong>🚀 Automated Ordering System!</strong> Browse 1,244+ DABS products with live pricing!<br>
            <em>Professional restaurant ordering made simple.</em>
        </p>
        
        <div style="text-align: center; margin-bottom: 20px;">
            <a href="https://orders.hillsandhollowsmarket.com/restaurant/embed" 
               target="_blank" 
               style="display: inline-block; background: #007cba; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                🖥️ Open Full-Screen Version
            </a>
        </div>
    </div>
    
    <!-- PRODUCTION IFRAME - UPDATE THIS URL -->
    <iframe 
        src="https://orders.hillsandhollowsmarket.com/restaurant/embed" 
        width="100%" 
        height="1200px"
        frameborder="0"
        loading="lazy"
        allow="fullscreen">
        <p>Your browser doesn't support iframes. 
           <a href="https://orders.hillsandhollowsmarket.com/restaurant/embed" target="_blank">
           Click here to access the ordering system directly</a>
        </p>
    </iframe>
    
    <div style="max-width: 1400px; margin: 0 auto; padding: 0 20px;">
        <div style="margin-top: 25px; padding: 15px; background: white; border-radius: 8px; border-left: 4px solid #007cba;">
            <h4>📋 Ordering Information</h4>
            <ul style="line-height: 1.8;">
                <li><strong>Delivery Schedule:</strong> Every other Tuesday</li>
                <li><strong>Order Deadline:</strong> Thursday evening before delivery</li>
                <li><strong>Support:</strong> 435-335-7349 or hillshollowsmanager@gmail.com</li>
            </ul>
        </div>
    </div>
</div>
```

---

## ✅ **DEPLOYMENT READINESS CHECKLIST**

### **Code Changes**
- [ ] Update `src/api/enhanced_main.py` with production configuration
- [ ] Create `.env.production` with production variables
- [ ] Update `requirements.txt` with all dependencies
- [ ] Create systemd service file
- [ ] Create Nginx configuration
- [ ] Create deployment scripts (`deploy.sh`, `backup.sh`)
- [ ] Create monitoring script (`health_monitor.py`)

### **WordPress Updates**
- [ ] Update iframe URL from localhost to production domain
- [ ] Test full-width CSS in production environment
- [ ] Verify all external links work correctly
- [ ] Test mobile responsiveness

### **Testing Checklist**
- [ ] Health check endpoint responds correctly
- [ ] All 4 restaurant customers can access system
- [ ] DABS product catalog loads properly
- [ ] Order submission works end-to-end
- [ ] Manager dashboard accessible
- [ ] SSL certificate valid and A+ rated
- [ ] WordPress embedding works without errors

---

## 🎊 **PRODUCTION READY STATUS**

Once all code changes are implemented and tested:

✅ **Application is production-ready**  
✅ **Security headers configured**  
✅ **Performance optimized**  
✅ **Monitoring and alerting enabled**  
✅ **WordPress integration optimized**  
✅ **Backup and recovery systems in place**  

**Ready for production deployment! 🚀**

---

*Hills & Hollows LLC - Utah Package Agency*  
*DABS Restaurant Ordering System - Production Implementation*
