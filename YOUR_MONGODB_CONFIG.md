# Your MongoDB Connection String

## ⚠️ IMPORTANT: Replace Password First

Your connection string:
```
mongodb+srv://wangarinjorogekenya_db_user:<db_password>@cluster1.cbqvizr.mongodb.net/?appName=Cluster1
```

**You need to replace `<db_password>` with your ACTUAL MongoDB password.**

---

## Step 1: Get Your MongoDB Password

If you don't remember your password:

1. Go to your MongoDB Atlas: https://cloud.mongodb.com/v2/6919c4e9e667f562f62af4eb
2. Click **"Database Access"** (left menu)
3. Find user: `wangarinjorogekenya_db_user`
4. Click **"Edit"** → **"Edit Password"**
5. Set a new password OR autogenerate one
6. **SAVE THE PASSWORD!**

---

## Step 2: Complete Your Connection String

Replace `<db_password>` with your actual password.

**Example:**
If your password is `MyPassword123`, your connection string becomes:

```
mongodb+srv://wangarinjorogekenya_db_user:MyPassword123@cluster1.cbqvizr.mongodb.net/?appName=Cluster1
```

**⚠️ Important:**
- NO angle brackets `< >`
- NO spaces
- Use your ACTUAL password

---

## Step 3: Add to Render

### Option A: If you already have a Render service

1. Go to your Render dashboard: https://dashboard.render.com
2. Click on your `clipix-backend` service
3. Click **"Environment"** (left sidebar)
4. Find or add these variables:

```
MONGO_URL = mongodb+srv://wangarinjorogekenya_db_user:YOUR_ACTUAL_PASSWORD@cluster1.cbqvizr.mongodb.net/?appName=Cluster1
DB_NAME = clipix_db
CORS_ORIGINS = *
EMERGENT_LLM_KEY = sk-emergent-c743b6eB02958A6886
```

5. Click **"Save Changes"**
6. Service will auto-redeploy

---

### Option B: Creating NEW Render service

If you're creating a NEW service (after deleting the old Node.js one):

1. Dashboard → **"New +"** → **"Web Service"**
2. Connect: **njoroge-mary/clipix-backend**
3. Configure:
   - **Runtime**: **Docker**
   - **Build Command**: (leave blank)
   - **Start Command**: (leave blank)

4. Add environment variables:

| Key | Value |
|-----|-------|
| `MONGO_URL` | `mongodb+srv://wangarinjorogekenya_db_user:YOUR_PASSWORD@cluster1.cbqvizr.mongodb.net/?appName=Cluster1` |
| `DB_NAME` | `clipix_db` |
| `CORS_ORIGINS` | `*` |
| `EMERGENT_LLM_KEY` | `sk-emergent-c743b6eB02958A6886` |

5. Click **"Create Web Service"**

---

## Step 4: Verify Network Access

Make sure Render can connect to your MongoDB:

1. In MongoDB Atlas, click **"Network Access"**
2. Make sure `0.0.0.0/0` is in the list (Allow access from anywhere)
3. If not, click **"Add IP Address"** → **"Allow Access from Anywhere"** → **"Confirm"**

---

## Step 5: Test Connection

After Render deployment completes:

```bash
# Replace with your actual Render URL
curl https://your-service-name.onrender.com/api/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "clipix-backend",
  "database": "connected",
  "timestamp": "2025-11-16T12:45:00.000000+00:00"
}
```

If you see `"database": "connected"` → **MongoDB is working!** ✅

---

## 🚨 Troubleshooting

### "Authentication failed"
- Double-check your password is correct
- Make sure you replaced `<db_password>` with actual password
- No extra spaces or characters

### "Connection timeout"
- Check Network Access allows `0.0.0.0/0`
- Wait 1-2 minutes after adding network access

### "Database not initialized"
- Check MONGO_URL is correctly set in Render
- Redeploy the service
- Check Render logs for errors

### Password has special characters?
If your password has `@`, `#`, `%`, `:`, or `/`, URL encode them:

| Character | Replace with |
|-----------|--------------|
| `@` | `%40` |
| `#` | `%23` |
| `%` | `%25` |
| `/` | `%2F` |
| `:` | `%3A` |

---

## ✅ Quick Checklist

- [ ] Get/reset MongoDB password
- [ ] Replace `<db_password>` in connection string
- [ ] Add `MONGO_URL` to Render environment variables
- [ ] Add other 3 environment variables
- [ ] Verify Network Access allows 0.0.0.0/0
- [ ] Save changes in Render
- [ ] Wait for deployment
- [ ] Test health endpoint

---

## 📝 Your Complete Configuration

**For Render Environment Variables:**

```
MONGO_URL=mongodb+srv://wangarinjorogekenya_db_user:YOUR_ACTUAL_PASSWORD_HERE@cluster1.cbqvizr.mongodb.net/?appName=Cluster1
DB_NAME=clipix_db
CORS_ORIGINS=*
EMERGENT_LLM_KEY=sk-emergent-c743b6eB02958A6886
```

**Replace `YOUR_ACTUAL_PASSWORD_HERE` with your MongoDB password!**

---

**Once you add the connection string with the correct password to Render, your backend will be fully operational! 🚀**
