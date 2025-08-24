# 🗄️ GET SUPABASE CREDENTIALS - 2-MINUTE SETUP

## **STEP 1: Create Free Supabase Account**
1. Go to: https://supabase.com
2. Click "Sign Up" 
3. Use GitHub, Google, or email signup
4. **No credit card required** - free tier is sufficient

## **STEP 2: Create New Project**
1. Click "New Project"
2. Choose organization (personal is fine)
3. **Project Name**: "Archon DABS"
4. **Database Password**: Create a strong password (you'll need this)
5. **Region**: Choose closest to you
6. Click "Create new project"
7. **Wait 2-3 minutes** for project initialization

## **STEP 3: Get Required Credentials**

### **🔗 SUPABASE_URL:**
```
📍 Location: Project Dashboard → Settings → API
📋 Copy: "Project URL" 
📝 Format: https://your-unique-id.supabase.co
📎 Example: https://abcdefghijklmnop.supabase.co
```

### **🔑 SUPABASE_SERVICE_KEY:**
```
📍 Location: Project Dashboard → Settings → API  
📋 Copy: "service_role secret" (the LONG key)
⚠️ IMPORTANT: Use the LONGER key (service_role), not the shorter one
📝 Format: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6...
📎 This key is ~200+ characters long
```

## **STEP 4: Database Migration**
1. **Go to**: Project Dashboard → SQL Editor
2. **Copy contents** from: `archon-mcp/migration/complete_setup.sql`
3. **Paste and execute** in SQL Editor
4. **Wait for completion** (should show "Success")

## **✅ CREDENTIALS READY**
You now have:
- ✅ SUPABASE_URL
- ✅ SUPABASE_SERVICE_KEY  
- ✅ Database initialized

**Total time: 2-3 minutes**
**Cost: $0 (free tier)**
