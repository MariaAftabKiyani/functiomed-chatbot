# Deployment Guide for Render

This guide will help you deploy the FunctioMed Chatbot application to Render using Docker.

## Prerequisites

1. A [Render](https://render.com) account
2. A [HuggingFace](https://huggingface.co) account and API token (for LLM models)
3. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)

## Deployment Steps

### Option A: One-Click Deployment with render.yaml (Recommended)

The easiest way to deploy is using the included `render.yaml` file:

1. **Push your code** to GitHub/GitLab/Bitbucket
2. **Log in to Render** and click "New +" → "Blueprint"
3. **Connect your repository** and select the branch
4. **Render will automatically**:
   - Create a Private Service for Qdrant (vector database)
   - Create a Web Service for your backend API
   - Set up persistent storage for Qdrant data
   - Configure internal networking between services

5. **Set required secrets** in Render dashboard:
   - `HF_HUB_TOKEN`: Your HuggingFace API token
   - `HF_API_TOKEN`: Same as HF_HUB_TOKEN

6. **Deploy**: Click "Apply" and Render will provision both services

That's it! The `render.yaml` handles all the configuration automatically.

---

### Option B: Manual Deployment

If you prefer manual setup or need more control:

#### 1. Prepare Your Repository

Ensure these files are in your repository:
- `backend/Dockerfile` - Docker configuration for the application
- `backend/.dockerignore` - Files to exclude from Docker build
- `docker-compose.yml` - Local development configuration (not used by Render)
- `render.yaml` - Blueprint configuration (optional)

#### 2. Deploy Qdrant Database

1. Log in to your Render dashboard
2. Click "New +" and select "Private Service"
3. Configure the service:
   - **Name**: `functiomed-qdrant`
   - **Image URL**: `qdrant/qdrant:latest`
   - **Region**: Choose closest to your users (same as backend)
   - **Instance Type**: Starter (512MB) minimum
   - **Add Persistent Disk**:
     - Mount Path: `/qdrant/storage`
     - Size: 10GB (adjust based on your needs)
   - **Environment Variables**:
     - `QDRANT__SERVICE__GRPC_PORT`: `6334`

4. Click "Create Private Service"
5. **Note the internal URL** (e.g., `functiomed-qdrant:6333`) - you'll use this for the backend

#### 3. Deploy Backend API

1. Click "New +" and select "Web Service"
2. Connect your Git repository
3. Configure the service:

   **Basic Settings:**
   - Name: `functiomed-chatbot-backend`
   - Region: Choose closest to your users
   - Branch: `main` (or your default branch)
   - Root Directory: `backend`
   - Environment: `Docker`
   - Docker Build Context Directory: `backend`
   - Dockerfile Path: `backend/Dockerfile`

   **Instance Type:**
   - Start with at least **2GB RAM** (required for ML models)
   - Recommended: 4GB or higher for better performance

#### 4. Configure Environment Variables

Add these environment variables in the backend web service:

```bash
# Application
DEBUG=False

# Qdrant Vector Database (use the internal URL from step 2)
QDRANT_URL=http://functiomed-qdrant:6333
# Note: No QDRANT_API_KEY needed for internal Render services
QDRANT_COLLECTION=functiomed_medical_docs
QDRANT_VECTOR_SIZE=1024

# HuggingFace Authentication (REQUIRED - use secrets)
HF_HUB_TOKEN=your_huggingface_token_here
HF_API_TOKEN=your_huggingface_token_here

# Embedding Model
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cpu

# LLM Configuration
LLM_MODEL_NAME=meta-llama/Llama-3.2-1B-Instruct
LLM_MAX_TOKENS=512
LLM_TEMPERATURE=0.8

# RAG Settings
RAG_MAX_CHUNKS=5
RAG_MIN_CHUNK_SCORE=0.5
RAG_ENABLE_CITATIONS=true
```

#### 5. Deploy

1. Click "Create Web Service"
2. Render will automatically:
   - Build your Docker image
   - Deploy the container
   - Provide a URL for your service (e.g., `https://functiomed-chatbot-backend.onrender.com`)

### 6. Verify Deployment

Once deployed, test these endpoints:

```bash
# Health check
curl https://your-app.onrender.com/health

# Root endpoint
curl https://your-app.onrender.com/
```

## Important Notes

### Memory Requirements
- **Minimum**: 2GB RAM
- **Recommended**: 4GB+ RAM
- The application loads ML models (embeddings + LLM) which require significant memory

### Cold Starts
- Render free tier services sleep after inactivity
- First request after sleep takes 1-2 minutes (model loading)
- Paid plans keep services always active

### Storage Considerations
- Models are downloaded on first start (~2-3GB)
- Cached in the container
- Redownloaded if container restarts
- Consider using Render's persistent disks for model caching

### Scaling
- Vertical: Increase instance RAM for better performance
- Horizontal: Not recommended (stateful model loading)

## Troubleshooting

### Build Failures
- Check Docker logs in Render dashboard
- Verify all dependencies in `requirements.txt` are compatible
- Ensure sufficient disk space for model downloads

### Runtime Errors
- Check application logs in Render dashboard
- Verify HuggingFace token is valid and has model access
- Ensure Qdrant connection details are correct
- Check memory usage (OOM kills are common with insufficient RAM)

### Slow Performance
- Increase instance RAM
- Check EMBEDDING_DEVICE and LLM device settings (should be 'cpu' on Render)
- Reduce RAG_MAX_CHUNKS if responses are slow

## Cost Optimization

1. **Use lighter models** if performance allows:
   ```
   LLM_MODEL_NAME=meta-llama/Llama-3.2-1B-Instruct  # Current (lightest)
   ```

2. **Optimize batch sizes**:
   ```
   EMBEDDING_BATCH_SIZE=8  # Reduce if memory constrained
   ```

3. **Use Qdrant Cloud free tier** for vector database

4. **Monitor usage** and adjust instance size as needed

## Local Testing

Before deploying, test locally with Docker:

```bash
# Build the image
cd backend
docker build -t functiomed-backend .

# Run the container
docker run -p 8000:8000 \
  -e HF_HUB_TOKEN=your_token \
  -e QDRANT_URL=http://localhost:6333 \
  functiomed-backend

# Or use docker-compose
cd ..
docker-compose up
```

## Updates and Redeployment

Render automatically redeploys when you push to your connected branch:
1. Make changes to your code
2. Commit and push to your repository
3. Render detects changes and rebuilds
4. Zero-downtime deployment

## Support

For Render-specific issues:
- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com)

For application issues:
- Check application logs
- Review configuration settings
- Verify external service connections (Qdrant, HuggingFace)
