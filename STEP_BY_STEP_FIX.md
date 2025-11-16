# ⚠️ URGENT: Follow These Exact Steps

## The Problem
Render has already detected your service as Node.js. You CANNOT change this without deleting and recreating.

---

## ✅ STEP-BY-STEP FIX (Do This NOW)

### Step 1: DELETE the Old Service ❌

1. Go to: https://dashboard.render.com
2. Find your **clipix-backend** service
3. Click on it
4. On the left sidebar, scroll down and click **"Settings"**
5. Scroll ALL the way to the bottom
6. Find **"Delete Web Service"** button (red button)
7. Click it and confirm deletion

**👉 THIS IS MANDATORY - You cannot skip this step!**

---

### Step 2: Create BRAND NEW Service ✨

1. Go back to Render Dashboard
2. Click the big **"New +"** button (top right)
3. Select **"Web Service"**
4. Click **"Build and deploy from a Git repository"**
5. Find and click **"njoroge-mary/clipix-backend"**
6. Click **"Connect"**

---

### Step 3: Configure Service (IMPORTANT!)

Now you'll see a configuration form. Fill it EXACTLY like this:

#### Basic Info:
- **Name**: `clipix-backend` (or any name you want)
- **Region**: Choose any (Oregon recommended)
- **Branch**: `main`
- **Root Directory**: *(LEAVE THIS BLANK)*

#### Build Settings:
- **Runtime**: Click dropdown and select **"Docker"** ⚠️ **THIS IS CRITICAL!**

#### Commands:
- **Build Command**: *(LEAVE BLANK - Docker handles it)*
- **Start Command**: *(LEAVE BLANK - Docker handles it)*

#### Instance:
- **Instance Type**: Select **"Free"**

---

### Step 4: Add Environment Variables 🔑

Click **"Add Environment Variable"** button and add these ONE BY ONE:

1. **MONGO_URL**
   - Value: `mongodb+srv://your-username:your-password@cluster.mongodb.net/`
   - ⚠️ Replace with your ACTUAL MongoDB URL

2. **DB_NAME**
   - Value: `clipix_db`

3. **CORS_ORIGINS**
   - Value: `*`

4. **EMERGENT_LLM_KEY**
   - Value: `sk-emergent-c743b6eB02958A6886`

---

### Step 5: Create Service 🚀

1. Click the big **"Create Web Service"** button at the bottom
2. Wait for deployment (5-10 minutes)
3. Watch the logs - you should see Docker building

---

## 🎯 What You Should See in Logs

**CORRECT (Docker):**
```
==> Building with Docker
==> Building image from Dockerfile
Step 1/10 : FROM python:3.11-slim
Step 2/10 : RUN apt-get update && apt-get install -y ffmpeg
...
==> Build successful
```

**WRONG (Node.js) - If you see this, you did NOT select Docker:**
```
==> Using Node.js version
==> Running build command 'yarn'
❌ THIS MEANS YOU SELECTED WRONG RUNTIME
```

---

## 🆘 If You Don't Have MongoDB Yet

### Quick MongoDB Setup:

1. Go to: https://www.mongodb.com/cloud/atlas/register
2. Sign up (free)
3. Create a **free cluster** (M0 - FREE FOREVER)
4. Wait 2-3 minutes for cluster to create
5. Click **"Connect"**
6. Select **"Drivers"**
7. Copy the connection string
8. Replace `<password>` with your database password
9. Use this in Render's `MONGO_URL` environment variable

**Example MongoDB URL:**
```
mongodb+srv://myuser:mypassword123@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
```

---

## ✅ How to Verify Success

After deployment completes:

1. Go to your service dashboard
2. Copy your service URL (looks like: `https://clipix-backend-xyz.onrender.com`)
3. Test it:
   ```bash
   curl https://YOUR-URL.onrender.com/api/health
   ```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "clipix-backend",
  "database": "connected"
}
```

---

## 🚨 Common Mistakes to Avoid

1. ❌ **NOT deleting the old service first**
   - You MUST delete it completely

2. ❌ **Selecting "Python" instead of "Docker"**
   - Select **"Docker"** from the Runtime dropdown

3. ❌ **Leaving Root Directory filled**
   - Keep it BLANK

4. ❌ **Adding build/start commands**
   - Leave them BLANK when using Docker

5. ❌ **Wrong MongoDB URL**
   - Must start with `mongodb+srv://` or `mongodb://`
   - Must have correct password

---

## 📞 Still Having Issues?

If after following ALL steps above you still see Node.js errors:

1. Take a screenshot of your Render service settings page
2. Verify on GitHub that Dockerfile exists: https://github.com/njoroge-mary/clipix-backend
3. Make sure you selected **Docker** runtime
4. Try creating service from scratch one more time

---

## ⏱️ Timeline

- Delete old service: **30 seconds**
- Create new service: **2 minutes**
- First deployment: **5-10 minutes**
- Total time: **~12 minutes**

---

**START WITH STEP 1 NOW - DELETE THE OLD SERVICE!**

Then come back and do steps 2-5 carefully.
