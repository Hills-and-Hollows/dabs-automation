# 🚀 WordPress Production Update Guide

## 📋 **IMMEDIATE UPDATES REQUIRED**

Now that the React app is deployed to Netlify, the WordPress iframe needs to be updated to point to the production URLs instead of localhost.

### **🎯 Current Issues:**
- ❌ WordPress iframe points to `localhost:8000`
- ❌ API endpoints use local development URLs
- ❌ Backup links point to localhost

### **✅ Production Updates:**
- ✅ Update iframe src to Netlify deployment
- ✅ Update API endpoints to use proxy
- ✅ Update backup links to production URLs

---

## 🔧 **STEP-BY-STEP UPDATE PROCESS**

### **Step 1: Access WordPress Admin**
1. Go to `https://hillsandhollowsmarket.com/wp-admin`
2. Navigate to Pages → Restaurant Orders
3. Edit the page content

### **Step 2: Replace Iframe Code**
Replace the current iframe code with the production version:

**OLD (localhost):**
```html
<iframe src="http://localhost:8000/restaurant/embed" 
        width="100%" height="1200px">
```

**NEW (production):**
```html
<iframe src="https://dabs-automation.netlify.app/src/web_portal/restaurant_portal_wordpress_embed.html" 
        width="100%" height="1200px">
```

### **Step 3: Update Backup Links**
**OLD:**
```html
<a href="http://localhost:8000/restaurant/embed" target="_blank">
```

**NEW:**
```html
<a href="https://dabs-automation.netlify.app/portal" target="_blank">
```

### **Step 4: Add Admin Dashboard Link**
Add a new button for admin access:
```html
<a href="https://dabs-automation.netlify.app/admin" target="_blank" 
   style="background: #28a745; color: white; padding: 12px 24px;">
   ⚙️ Admin Dashboard
</a>
```

---

## 📄 **COMPLETE PRODUCTION CODE**

Use the complete updated code from: `docs/WORDPRESS_EMBED_CODE_PRODUCTION.html`

### **Key Changes:**
1. **Iframe Source**: `dabs-automation.netlify.app`
2. **API Endpoints**: Use `/api/` proxy paths
3. **Backup Links**: Point to Netlify deployment
4. **Admin Access**: New admin dashboard button

---

## 🧪 **TESTING CHECKLIST**

After updating WordPress:

### **Functionality Tests:**
- [ ] Iframe loads the ordering system
- [ ] Product catalog displays correctly
- [ ] Search functionality works
- [ ] Shopping cart operates properly
- [ ] Order submission functions
- [ ] Admin dashboard accessible

### **Responsive Tests:**
- [ ] Desktop view (1920x1080)
- [ ] Tablet view (768x1024)
- [ ] Mobile view (375x667)
- [ ] Full-screen button works

### **Integration Tests:**
- [ ] WordPress theme compatibility
- [ ] No console errors
- [ ] SSL certificate valid
- [ ] Cross-origin requests work

---

## 🚨 **BACKUP PLAN**

If iframe embedding has issues:

### **Option 1: Direct Redirect**
Replace iframe with direct redirect:
```html
<script>
window.location.href = 'https://dabs-automation.netlify.app/portal';
</script>
```

### **Option 2: External Link**
Replace with external link button:
```html
<a href="https://dabs-automation.netlify.app/portal" 
   target="_blank" 
   style="display: block; background: #007cba; color: white; padding: 20px; text-align: center;">
   🍽️ Access Restaurant Ordering System
</a>
```

---

## 📊 **PRODUCTION URLS REFERENCE**

### **Main Application:**
- **Frontend**: `https://dabs-automation.netlify.app`
- **Admin Hub**: `https://dabs-automation.netlify.app/admin`
- **Restaurant Portal**: `https://dabs-automation.netlify.app/portal`
- **Manager Dashboard**: `https://dabs-automation.netlify.app/dashboard`

### **API Endpoints:**
- **Health Check**: `https://dabs-automation.netlify.app/health`
- **API Status**: `https://dabs-automation.netlify.app/api/status`
- **Product Catalog**: `https://dabs-automation.netlify.app/api/dabs/catalog/products`

### **WordPress Integration:**
- **Embed URL**: `https://dabs-automation.netlify.app/src/web_portal/restaurant_portal_wordpress_embed.html`
- **WordPress Page**: `https://hillsandhollowsmarket.com/restaurant-orders/`

---

## ⚡ **IMMEDIATE ACTION REQUIRED**

1. **Update WordPress iframe** to production URL
2. **Test ordering functionality** 
3. **Verify mobile responsiveness**
4. **Confirm admin access works**

The ordering system is now live and ready for production use! 🎉
