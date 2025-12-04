# Quick Render Deployment Guide

This is a quick reference for deploying both Qdrant and your backend on Render.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                    Render                        │
│                                                  │
│  ┌────────────────┐      ┌──────────────────┐  │
│  │  Qdrant        │      │  Backend API     │  │
│  │  (Private      │◄─────┤  (Web Service)   │  │
│  │   Service)     │      │                  │  │
│  │                │      │  Port: 8000      │  │
│  │  Port: 6333    │      │                  │  │
│  │                │      └──────────────────┘  │
│  │  Persistent    │              │             │
│  │  Disk: 10GB    │              │             │
│  └────────────────┘              │             │
│                                   │             │
│                           Public Internet       │
└───────────────────────────────────┼─────────────┘
                                    │
                              Your Users
```

## One-Click Deployment (Easiest)

1. **Push code** to GitHub/GitLab/Bitbucket
2. **Go to Render** → "New +" → "Blueprint"
3. **Connect repository** and select branch
4. **Set secrets** in Render dashboard:
   - `HF_HUB_TOKEN`: Get from https://huggingface.co/settings/tokens
   - `HF_API_TOKEN`: Same value as HF_HUB_TOKEN
5. **Click Apply** - Done!

The `render.yaml` file automatically creates:
- ✅ Qdrant private service with persistent storage
- ✅ Backend web service connected to Qdrant
- ✅ All environment variables configured
- ✅ Internal networking between services

## Manual Setup (If You Prefer)

### Step 1: Deploy Qdrant (Private Service)

Go to Render → "New +" → "Private Service"

| Setting | Value |
|---------|-------|
| Name | `functiomed-qdrant` |
| Image URL | `qdrant/qdrant:latest` |
| Region | `frankfurt` (or your choice) |
| Instance | Starter (512MB minimum) |
| Mount Path | `/qdrant/storage` |
| Disk Size | 10GB |
| Env Var | `QDRANT__SERVICE__GRPC_PORT=6334` |

**Important**: After creation, note the internal hostname: `functiomed-qdrant:6333`

### Step 2: Deploy Backend (Web Service)

Go to Render → "New +" → "Web Service"

| Setting | Value |
|---------|-------|
| Repository | Your Git repo |
| Name | `functiomed-chatbot-backend` |
| Region | Same as Qdrant |
| Branch | `main` |
| Root Directory | `backend` |
| Environment | Docker |
| Dockerfile Path | `backend/Dockerfile` |
| Instance | Starter Plus (2GB RAM minimum) |

**Environment Variables**:

```bash
# Qdrant (Internal Connection - No Auth Needed)
QDRANT_URL=http://functiomed-qdrant:6333
QDRANT_COLLECTION=functiomed_medical_docs
QDRANT_VECTOR_SIZE=1024

# HuggingFace (REQUIRED - Mark as Secret)
HF_HUB_TOKEN=<your_token>
HF_API_TOKEN=<your_token>

# Models
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cpu
LLM_MODEL_NAME=meta-llama/Llama-3.2-1B-Instruct

# Optional - Use Defaults
DEBUG=False
LLM_MAX_TOKENS=512
LLM_TEMPERATURE=0.8
RAG_MAX_CHUNKS=5
RAG_MIN_CHUNK_SCORE=0.5
```

## Verify Deployment

After both services are running:

```bash
# Check health
curl https://your-backend-url.onrender.com/health

# Expected response
{"status":"healthy","service":"functiomed-chatbot-backend"}
```

## Key Points

### Internal Communication
- Qdrant is a **Private Service** (not publicly accessible)
- Backend connects to Qdrant via internal hostname: `functiomed-qdrant:6333`
- No API key needed for internal Render services
- Secure by default (private network)

### Storage
- Qdrant data persists on disk (10GB)
- Backend models cache in container (downloaded on first start)
- Models re-download if container restarts (ephemeral storage)

### Costs (Approximate)
- **Qdrant Private Service**: $7/month (Starter)
- **Backend Web Service**: $7/month (Starter - 512MB) to $21/month (Starter Plus - 2GB)
- **Qdrant Disk**: $0.25/GB/month (10GB = $2.50/month)
- **Total**: ~$16-30/month depending on backend size

### Scaling Recommendations

| Traffic Level | Backend RAM | Qdrant Plan | Total Cost |
|--------------|-------------|-------------|------------|
| Development | 2GB | Starter | ~$16/month |
| Low Traffic | 4GB | Starter | ~$30/month |
| Medium Traffic | 8GB | Standard | ~$60/month |
| High Traffic | 16GB | Standard | ~$120/month |

## Troubleshooting

### Backend can't connect to Qdrant
- ✅ Check Qdrant service is running
- ✅ Verify `QDRANT_URL=http://functiomed-qdrant:6333` (no https)
- ✅ Ensure both services in same region

### Out of Memory (OOM) errors
- ✅ Upgrade backend to at least 2GB RAM
- ✅ Check model loading isn't happening multiple times
- ✅ Consider using lighter models

### Models not loading
- ✅ Verify `HF_HUB_TOKEN` is set correctly
- ✅ Check token has access to Llama models
- ✅ Review application logs for download errors

### Slow cold starts
- ✅ Upgrade to paid plan (keeps service warm)
- ✅ Models download on first start (~2-3GB)
- ✅ Consider pre-building models into Docker image

## Next Steps

After deployment:
1. Initialize Qdrant collection (run document embedding scripts)
2. Test the chat API endpoints
3. Connect your frontend
4. Set up monitoring and alerts
5. Configure custom domain (optional)

## Support

- Render Docs: https://render.com/docs
- Qdrant Docs: https://qdrant.tech/documentation/
- HuggingFace Tokens: https://huggingface.co/settings/tokens
