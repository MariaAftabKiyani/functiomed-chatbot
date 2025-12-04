# Troubleshooting "Failed Deploy" on Render

## Current Status
Your deployment shows "Failed deploy" - let's fix this.

## Most Likely Causes

### 1. Deployed Without Using Blueprint
If you manually created a Web Service, it won't have Qdrant running, causing the backend to fail.

**Solution: Deploy Using Blueprint**

1. **Delete the failed service** (if it exists):
   - Click on "functiomed-chatbot"
   - Settings → Delete Service

2. **Deploy with Blueprint instead**:
   - Render Dashboard → "New +" → **"Blueprint"**
   - Connect your Git repository
   - Select branch: `main`
   - Render reads `render.yaml` and creates:
     - ✅ Qdrant Private Service
     - ✅ Backend Web Service

3. **Set required secrets**:
   - After services are created, go to Backend service
   - Environment tab
   - Add these as **Secret Files** or **Environment Variables**:
     - `HF_HUB_TOKEN`: Your HuggingFace token
     - `HF_API_TOKEN`: Same value

4. **Trigger Manual Deploy**:
   - Click "Manual Deploy" → "Deploy latest commit"

---

### 2. Missing HuggingFace Token

The backend needs a HuggingFace token to download the Llama model.

**How to Fix:**
1. Get token from: https://huggingface.co/settings/tokens
2. Create a **Write** token (Read tokens won't work for Llama)
3. Accept Llama model license: https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct
4. Add to Render:
   - Backend service → Environment
   - Add: `HF_HUB_TOKEN` = your_token
   - Add: `HF_API_TOKEN` = your_token

---

### 3. Incorrect Dockerfile Path

**Symptoms**: Build fails, can't find Dockerfile

**Fix:**
- Root Directory: `backend`
- Docker Build Context: `backend`
- Dockerfile Path: `backend/Dockerfile`

---

### 4. Out of Memory During Build

**Symptoms**: Build succeeds but service crashes immediately

**Fix:**
- Upgrade to **Starter Plus** (2GB RAM minimum)
- Free tier (512MB) is too small for ML models

---

### 5. Qdrant Not Running

**Symptoms**: Backend logs show "Connection refused" to Qdrant

**Fix:**
- Check Qdrant service is running (should be Private Service)
- Verify `QDRANT_URL=http://functiomed-qdrant:6333`
- Both services must be in same region

---

## Step-by-Step: Fresh Deployment

### Prerequisites Checklist
- [ ] Code pushed to GitHub/GitLab/Bitbucket
- [ ] HuggingFace account created
- [ ] Llama model access granted: https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct
- [ ] HuggingFace Write token created: https://huggingface.co/settings/tokens

### Deployment Steps

1. **Go to Render Dashboard**
   - https://dashboard.render.com

2. **Click "New +" → "Blueprint"**

3. **Connect Repository**
   - Select your Git provider
   - Choose: `functiomed-chatbot` repo
   - Branch: `main`

4. **Review Blueprint**
   - Render shows 2 services will be created:
     - `functiomed-qdrant` (Private Service)
     - `functiomed-chatbot-backend` (Web Service)
   - Click **"Apply"**

5. **Wait for Creation** (1-2 minutes)
   - Qdrant service creates first
   - Backend service creates second

6. **Set Secrets**
   - Click on `functiomed-chatbot-backend`
   - Go to "Environment" tab
   - Find `HF_HUB_TOKEN` → Click "Generate" or add manually
   - Paste your HuggingFace token
   - Find `HF_API_TOKEN` → Add same token
   - Click "Save Changes"

7. **Trigger Deploy**
   - Go to "Manual Deploy"
   - Click "Deploy latest commit"

8. **Monitor Logs**
   - Click "Logs" tab
   - Watch for:
     - ✅ "Downloading model..."
     - ✅ "Model loaded successfully"
     - ✅ "Application startup complete"

9. **Test Deployment**
   ```bash
   curl https://your-service-url.onrender.com/health
   ```

---

## Checking Logs for Specific Errors

Click on your failed service → "Logs" tab. Look for these patterns:

### Error: "Connection refused" or "Qdrant connection failed"
**Cause**: Qdrant not running
**Fix**: Deploy Qdrant Private Service first

### Error: "401 Unauthorized" from HuggingFace
**Cause**: Invalid or missing HF token
**Fix**: Add valid HuggingFace token with Llama access

### Error: "Killed" or "OOMKilled"
**Cause**: Out of memory
**Fix**: Upgrade to 2GB+ RAM instance

### Error: "No such file or directory: Dockerfile"
**Cause**: Wrong paths
**Fix**: Set Root Directory to `backend`

### Error: "Module not found"
**Cause**: Dependencies not installed
**Fix**: Check `requirements.txt` is in `backend/` folder

---

## Quick Test: Local Docker Build

Before deploying, test locally:

```bash
# Navigate to project
cd "c:\Users\HomePC\Documents\Workspace\functiomed\Project\functiomed-chatbot"

# Build backend image
cd backend
docker build -t functiomed-test .

# If build succeeds, the Dockerfile is correct
# If it fails, fix errors before deploying to Render
```

---

## Still Not Working?

Share the error logs:
1. Click on failed service
2. Go to "Logs" tab
3. Copy the last 50 lines
4. Check for the specific error message

Common log locations:
- Build logs: Shows Dockerfile execution
- Deploy logs: Shows startup errors
- Service logs: Shows runtime errors

---

## Need Help?

1. **Check service logs** in Render dashboard
2. **Review environment variables** - make sure HF tokens are set
3. **Verify Qdrant is running** - check Private Services
4. **Test locally first** - use `docker-compose up`

## Contact
- Render Support: https://render.com/docs
- Render Community: https://community.render.com
