# MongoDB Atlas Setup for Clipix Backend

## Your MongoDB Atlas URL
https://cloud.mongodb.com/v2/6919c4e9e667f562f62af4eb#/overview

---

## Step-by-Step Setup

### Step 1: Create Database User

1. In your MongoDB Atlas dashboard, click **"Database Access"** (left sidebar)
2. Click **"Add New Database User"** button
3. Fill in:
   - **Authentication Method**: Password
   - **Username**: `clipix_user` (or any name you want)
   - **Password**: Click "Autogenerate Secure Password" OR create your own
   - **⚠️ SAVE THIS PASSWORD - You'll need it later!**
4. **Database User Privileges**: Select **"Read and write to any database"**
5. Click **"Add User"**

**Save your credentials:**
```
Username: clipix_user
Password: [YOUR_PASSWORD_HERE]
```

---

### Step 2: Whitelist IP Addresses (Network Access)

1. Click **"Network Access"** (left sidebar)
2. Click **"Add IP Address"** button
3. Click **"Allow Access from Anywhere"**
   - This will add `0.0.0.0/0`
   - This is needed for Render to connect
4. Click **"Confirm"**

**Wait 1-2 minutes** for the changes to apply.

---

### Step 3: Get Connection String

1. Go back to **"Database"** (left sidebar)
2. You should see your cluster (usually called "Cluster0")
3. Click **"Connect"** button
4. Select **"Drivers"**
5. Select:
   - **Driver**: Python
   - **Version**: 3.12 or later
6. **Copy the connection string** - it looks like:

```
mongodb+srv://clipix_user:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

7. **Replace `<password>`** with your actual password from Step 1

---

### Step 4: Format Connection String

Your final connection string should look like:

```
mongodb+srv://clipix_user:YOUR_ACTUAL_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

**Example with password "MyPass123":**
```
mongodb+srv://clipix_user:MyPass123@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
```

**⚠️ Important Notes:**
- NO spaces in the connection string
- NO angle brackets `< >`
- Replace `<password>` with your ACTUAL password
- If your password has special characters, you may need to URL encode them

---

### Step 5: Add to Render

Now use this connection string in Render:

1. Go to your Render service
2. Go to **"Environment"** tab (left sidebar)
3. Find or add **`MONGO_URL`** variable
4. Paste your complete connection string
5. Click **"Save Changes"**

**Your Render environment variables should be:**
```
MONGO_URL = mongodb+srv://clipix_user:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
DB_NAME = clipix_db
CORS_ORIGINS = *
EMERGENT_LLM_KEY = sk-emergent-c743b6eB02958A6886
```

---

### Step 6: Create Database (Optional)

MongoDB will auto-create the database on first use, but you can create it manually:

1. In MongoDB Atlas, go to **"Database"** → **"Browse Collections"**
2. Click **"Create Database"**
3. Database Name: `clipix_db`
4. Collection Name: `videos` (or any name)
5. Click **"Create"**

---

## 🧪 Testing Connection

After setting up MongoDB and deploying on Render, test:

```bash
curl https://your-render-url.onrender.com/api/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "clipix-backend",
  "database": "connected",
  "timestamp": "2025-11-16T12:30:00.000000+00:00"
}
```

If `"database": "connected"` appears, MongoDB is working! ✅

---

## 🚨 Troubleshooting

### "Authentication failed"
- Check your username and password are correct
- Make sure you replaced `<password>` with actual password
- Check for spaces or special characters

### "Connection timeout"
- Make sure you added `0.0.0.0/0` to Network Access
- Wait 1-2 minutes for changes to apply

### "Database not initialized"
- Check `MONGO_URL` environment variable in Render
- Make sure connection string is correct
- Redeploy your service

### Password has special characters
If your password has special characters like `@`, `#`, `%`, etc., you need to URL encode them:

| Character | URL Encoded |
|-----------|-------------|
| `@` | `%40` |
| `#` | `%23` |
| `%` | `%25` |
| `:` | `%3A` |
| `/` | `%2F` |

**Example:** Password `My@Pass#123` becomes `My%40Pass%23123`

---

## ✅ Quick Checklist

- [ ] Create database user with password
- [ ] Save username and password
- [ ] Whitelist `0.0.0.0/0` in Network Access
- [ ] Get connection string
- [ ] Replace `<password>` with actual password
- [ ] Add to Render as `MONGO_URL` environment variable
- [ ] Redeploy service
- [ ] Test health endpoint

---

## 📝 Summary

**What you need for Render:**

```
MONGO_URL=mongodb+srv://USERNAME:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

Replace:
- `USERNAME` → Your MongoDB user (e.g., `clipix_user`)
- `PASSWORD` → Your actual password
- `cluster0.xxxxx` → Your actual cluster address (from connection string)

---

**Once you have the connection string, add it to Render and redeploy! 🚀**
