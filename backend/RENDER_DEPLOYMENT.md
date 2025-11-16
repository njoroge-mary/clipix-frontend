# Deploying Clipix Backend to Render

## Issue: requirements.txt not found

This happens when the requirements.txt file wasn't properly pushed to GitHub.

## Solution:

### Step 1: Verify files in your local backend directory

```bash
cd /app/backend
ls -la
```

You should see:
- server.py
- video_processor.py
- caption_generator.py
- requirements.txt
- .env (this should NOT be in git)
- .gitignore
- README.md

### Step 2: Check Git Status

```bash
cd /app/backend
git status
```

### Step 3: Add and Push requirements.txt

```bash
cd /app/backend

# Add requirements.txt explicitly
git add requirements.txt

# Verify it's staged
git status

# Commit
git commit -m "Add requirements.txt for deployment"

# Push to GitHub
git push origin main
```

### Step 4: Verify on GitHub

1. Go to https://github.com/njoroge-mary/clipix-backend
2. Check if `requirements.txt` is visible in the file list
3. Click on it to verify the contents

### Step 5: Trigger Render Redeploy

1. Go to your Render dashboard
2. Select your clipix-backend service
3. Click "Manual Deploy" → "Deploy latest commit"
4. OR push a new commit to trigger auto-deploy

---

## Render Configuration

Make sure your Render service has these settings:

### Build Command:
```bash
pip install -r requirements.txt && apt-get update && apt-get install -y ffmpeg
```

### Start Command:
```bash
uvicorn server:app --host 0.0.0.0 --port $PORT
```

### Environment Variables (Add these in Render Dashboard):
- `MONGO_URL` = your MongoDB connection string
- `DB_NAME` = clipix_db
- `CORS_ORIGINS` = https://your-frontend-url.vercel.app
- `EMERGENT_LLM_KEY` = your actual key

### Python Version:
- Use Python 3.11 (NOT 3.13, as some packages may not be compatible)

---

## Alternative: If requirements.txt still not found

Create a fresh requirements.txt with only essential dependencies:

```bash
cd /app/backend
cat > requirements.txt << 'EOF'
fastapi==0.110.1
uvicorn==0.25.0
python-dotenv==1.2.1
pydantic==2.12.4
motor==3.3.1
pymongo==4.5.0
ffmpeg-python==0.2.0
python-multipart==0.0.20
emergentintegrations==0.1.0
EOF

git add requirements.txt
git commit -m "Add minimal requirements.txt"
git push origin main
```

---

## Render Deployment Steps

### 1. Create New Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository: `njoroge-mary/clipix-backend`
4. Configure:
   - **Name**: clipix-backend
   - **Region**: Choose closest to your users
   - **Branch**: main
   - **Root Directory**: leave blank (or `.` if needed)
   - **Runtime**: Python 3
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     uvicorn server:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type**: Free (or paid for better performance)

### 2. Add Environment Variables

In Render dashboard, add:
```
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=clipix_db
CORS_ORIGINS=*
EMERGENT_LLM_KEY=sk-emergent-c743b6eB02958A6886
```

**Important**: Replace with your actual MongoDB URL.

### 3. Install FFmpeg

Render doesn't have FFmpeg by default. You have two options:

**Option A: Use render.yaml** (Recommended)

Create `/app/backend/render.yaml`:
```yaml
services:
  - type: web
    name: clipix-backend
    env: python
    buildCommand: |
      apt-get update && apt-get install -y ffmpeg
      pip install -r requirements.txt
    startCommand: uvicorn server:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

**Option B: Use Dockerfile** (More control)

Create `/app/backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 4. MongoDB Setup

Use MongoDB Atlas (free tier):
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a free cluster
3. Get connection string
4. Add to Render environment variables

---

## Troubleshooting

### Error: "requirements.txt not found"
- **Solution**: Follow Step 3 above to push requirements.txt

### Error: "FFmpeg not found"
- **Solution**: Use render.yaml or Dockerfile to install FFmpeg

### Error: "Port already in use"
- **Solution**: Render sets $PORT automatically, use it in start command

### Error: "MongoDB connection failed"
- **Solution**: Check MONGO_URL in environment variables
- Whitelist Render's IP (0.0.0.0/0) in MongoDB Atlas

### Error: "emergentintegrations not found"
- **Solution**: Add to requirements.txt:
  ```
  emergentintegrations==0.1.0
  ```

---

## After Successful Deployment

1. Copy your Render URL (e.g., `https://clipix-backend.onrender.com`)
2. Update frontend `.env`:
   ```
   REACT_APP_BACKEND_URL=https://clipix-backend.onrender.com
   ```
3. Update backend CORS:
   ```
   CORS_ORIGINS=https://your-frontend-domain.vercel.app
   ```

---

## Testing Deployment

```bash
# Health check
curl https://clipix-backend.onrender.com/api/health

# Expected response:
# {"status":"healthy","service":"clipix-backend","database":"connected"}
```

---

**Good luck with deployment! 🚀**
