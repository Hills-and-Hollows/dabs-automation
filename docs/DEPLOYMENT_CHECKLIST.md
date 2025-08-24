# 🚀 **PRODUCTION DEPLOYMENT CHECKLIST**
## Hills & Hollows LLC - DABS Automation System

**Target Timeline**: 1-2 hours total deployment time  
**Deployment Strategy**: Railway (Backend) + Netlify (Frontend) + Supabase (Database)

---

## 📋 **PRE-DEPLOYMENT CHECKLIST**

### **✅ Prerequisites Verification**
- [ ] **Supabase**: ✅ Already configured and working
- [ ] **Local Services**: ✅ Archon system running locally
- [ ] **Environment Files**: ✅ All credentials documented
- [ ] **GitHub Repository**: Ready for deployment

### **🔑 Credentials Collection**
- [ ] **Railway Account**: Access to dashboard
- [ ] **Netlify Account**: Access to dashboard
- [ ] **Host Papa Account**: DNS management access
- [ ] **GitHub Repository**: Push access for auto-deployment

---

## 🎯 **PHASE 1: RAILWAY BACKEND DEPLOYMENT (30 minutes)**

### **Step 1: Railway Project Setup (10 minutes)**
- [ ] **Login to Railway**: https://railway.app
- [ ] **Create New Project**: "Hills Hollows DABS Backend"
- [ ] **Connect GitHub**: Link your repository
- [ ] **Select Service Type**: Web Service
- [ ] **Choose Branch**: main/master

### **Step 2: Environment Variables Configuration (10 minutes)**
Copy these variables to Railway dashboard:

**Database Configuration:**
- [ ] `SUPABASE_URL=https://zwbvfnpaimdpjyuotals.supabase.co`
- [ ] `SUPABASE_SERVICE_KEY=[your-service-key]`

**Application Configuration:**
- [ ] `ENV=production`
- [ ] `LOG_LEVEL=INFO`
- [ ] `PYTHONPATH=/app`
- [ ] `PYTHONUNBUFFERED=1`

**SSCS Integration:**
- [ ] `SSCS_LOGIN_URL=https://sscsta.sscsinc.com/TransactionAnalysis.App/#!/merchandisesales/`
- [ ] `SSCS_USERNAME=v6242shawn`
- [ ] `SSCS_PASSWORD=Notone2016!`

**QuickBooks OAuth:**
- [ ] `QB_CLIENT_ID=AB1HJvz2KjreJxLEhZCV2KwNE2jU8V84nnE4EoITbsj2jzy8SF`
- [ ] `QB_CLIENT_SECRET=Mwl0thaufwcxyP69FMn1G8eTjiVP0KvviD6qXxtH`
- [ ] `QB_REDIRECT_URI=https://api.hillsandhollowsmarket.com/auth/quickbooks/callback`

**Security Configuration:**
- [ ] `ALLOWED_ORIGINS=https://orders.hillsandhollowsmarket.com,https://hillsandhollowsmarket.com`

### **Step 3: Deploy and Verify (10 minutes)**
- [ ] **Trigger Deployment**: Push to GitHub or manual deploy
- [ ] **Monitor Build Logs**: Check for errors
- [ ] **Get Railway URL**: Copy the generated URL (e.g., `your-app.railway.app`)
- [ ] **Test Health Endpoint**: `curl https://your-app.railway.app/health`
- [ ] **Verify API Endpoints**: Test key endpoints

---

## 🎯 **PHASE 2: NETLIFY FRONTEND DEPLOYMENT (15 minutes)**

### **Step 1: Build Preparation (5 minutes)**
- [ ] **Navigate to Frontend**: `cd archon-mcp/archon-ui-main`
- [ ] **Install Dependencies**: `npm install`
- [ ] **Update Environment**: Set `VITE_API_URL` to Railway URL
- [ ] **Build for Production**: `npm run build`
- [ ] **Verify Build**: Check `dist` folder created

### **Step 2: Netlify Deployment (5 minutes)**
- [ ] **Login to Netlify**: https://netlify.com
- [ ] **Create New Site**: "Hills Hollows DABS Frontend"
- [ ] **Deploy Method**: Drag & drop `dist` folder OR connect GitHub
- [ ] **Get Netlify URL**: Copy the generated URL (e.g., `amazing-name-123456.netlify.app`)

### **Step 3: Environment Configuration (5 minutes)**
In Netlify dashboard, add environment variables:
- [ ] `VITE_API_URL=https://your-app.railway.app` (or custom domain)
- [ ] `VITE_APP_NAME=Hills & Hollows DABS System`
- [ ] `VITE_ENVIRONMENT=production`

---

## 🎯 **PHASE 3: DNS CONFIGURATION (15 minutes)**

### **Step 1: Host Papa DNS Setup (10 minutes)**
Login to Host Papa control panel and add DNS records:

**For Frontend (Netlify):**
- [ ] **Record Type**: CNAME
- [ ] **Name**: `orders`
- [ ] **Value**: `amazing-name-123456.netlify.app`
- [ ] **TTL**: 300 (5 minutes)

**For Backend (Railway):**
- [ ] **Record Type**: CNAME  
- [ ] **Name**: `api`
- [ ] **Value**: `your-app.railway.app`
- [ ] **TTL**: 300 (5 minutes)

### **Step 2: SSL Certificate Verification (5 minutes)**
- [ ] **Netlify SSL**: Should be automatic (check site settings)
- [ ] **Railway SSL**: Should be automatic (check deployment logs)
- [ ] **Test HTTPS**: Verify both domains work with https://

---

## 🎯 **PHASE 4: PRODUCTION VALIDATION (20 minutes)**

### **Step 1: System Health Checks (10 minutes)**
- [ ] **Frontend Access**: https://orders.hillsandhollowsmarket.com
- [ ] **Backend Health**: https://api.hillsandhollowsmarket.com/health
- [ ] **Database Connection**: Verify Supabase connectivity
- [ ] **API Endpoints**: Test key functionality

### **Step 2: Integration Testing (10 minutes)**
- [ ] **Restaurant Portal**: Verify ordering interface works
- [ ] **Admin Dashboard**: Check management interface
- [ ] **WordPress Integration**: Test iframe embedding
- [ ] **Mobile Responsiveness**: Test on mobile devices

---

## 🎯 **PHASE 5: MONITORING SETUP (10 minutes)**

### **Built-in Monitoring**
- [ ] **Railway Monitoring**: Enable in dashboard
- [ ] **Netlify Analytics**: Enable in site settings
- [ ] **Supabase Monitoring**: Check database metrics
- [ ] **Health Check URLs**: Bookmark for regular checks

### **Custom Monitoring**
- [ ] **Uptime Monitoring**: Set up external service (optional)
- [ ] **Error Tracking**: Configure error reporting
- [ ] **Performance Monitoring**: Set up metrics collection

---

## ✅ **POST-DEPLOYMENT VERIFICATION**

### **Functional Testing**
- [ ] **User Registration**: Test new user signup
- [ ] **Order Placement**: Complete test order
- [ ] **Admin Functions**: Verify management features
- [ ] **Automated Tasks**: Check scheduled jobs

### **Performance Testing**
- [ ] **Load Time**: < 3 seconds for main pages
- [ ] **API Response**: < 2 seconds for API calls
- [ ] **Mobile Performance**: Smooth on mobile devices
- [ ] **Concurrent Users**: Test multiple simultaneous users

### **Security Verification**
- [ ] **HTTPS Enforcement**: All traffic redirected to HTTPS
- [ ] **CORS Configuration**: Proper cross-origin settings
- [ ] **API Security**: Authentication working correctly
- [ ] **Data Protection**: Sensitive data properly secured

---

## 🚨 **ROLLBACK PLAN**

### **If Issues Occur:**
1. **Railway Issues**: 
   - Check deployment logs
   - Verify environment variables
   - Rollback to previous deployment

2. **Netlify Issues**:
   - Check build logs
   - Verify environment variables  
   - Redeploy from working build

3. **DNS Issues**:
   - Verify DNS records in Host Papa
   - Check TTL settings (may take time to propagate)
   - Use DNS checker tools

4. **Database Issues**:
   - Check Supabase dashboard
   - Verify connection strings
   - Check service status

---

## 🎊 **SUCCESS CRITERIA**

### **Deployment Complete When:**
- [ ] ✅ **Frontend**: https://orders.hillsandhollowsmarket.com loads correctly
- [ ] ✅ **Backend**: https://api.hillsandhollowsmarket.com/health returns healthy
- [ ] ✅ **Database**: Supabase connection working
- [ ] ✅ **SSL**: Both domains have valid certificates
- [ ] ✅ **Functionality**: Core features working end-to-end
- [ ] ✅ **Performance**: Meeting speed requirements
- [ ] ✅ **Monitoring**: Health checks and alerts configured

### **Business Impact Achieved:**
- [ ] ✅ **24/7 Availability**: System accessible around the clock
- [ ] ✅ **Public Access**: Restaurants can access ordering system
- [ ] ✅ **WordPress Integration**: Iframe embedding working
- [ ] ✅ **Cost Effective**: ~$25/month operational cost
- [ ] ✅ **Scalable**: Ready for increased usage

---

**🎯 Total Estimated Time: 1.5-2 hours**  
**💰 Monthly Cost: ~$25**  
**🚀 Result: Production-ready 24/7 DABS automation system**
