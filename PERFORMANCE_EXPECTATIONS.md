# Performance Expectations - Render Starter Plan (512MB RAM)

## Current Deployment Specs

**Backend**: Render Starter Plan (512MB RAM, 0.1 CPU)
**Database**: Qdrant Private Service (512MB RAM)
**Models**: BGE-M3 embeddings (~1GB) + Llama-3.2-1B (~2.5GB)

## Expected Performance

### Memory Constraints
**Critical**: 512MB RAM is insufficient for ML models. The backend will likely crash with Out of Memory (OOM) errors during:
- Model loading (embedding + LLM = ~3.5GB total)
- First inference request
- Concurrent requests

**Recommendation**: Upgrade to Starter Plus (2GB) or Standard (4GB) immediately.

### Response Times (If It Runs)

**Cold Start**: 10-15 minutes
- Container wake-up: 30s
- Model downloads: 5-8 min (first deploy only)
- Model loading: 3-5 min

**Warm Requests**:
- FAQ (hardcoded): <100ms
- Simple chat (no RAG): 3-5 seconds
- RAG-enabled chat: 5-10 seconds
- TTS generation: 2-4 seconds

**Throughput**: 1 concurrent request maximum (single CPU)

## What Can Be Tested

### ✅ Likely Works (No ML Models)
- Health endpoint (`/health`)
- Root endpoint (`/`)
- API documentation (`/docs`)
- FAQ endpoint (hardcoded responses)
- Frontend static site (all features)

### ⚠️ May Work (Light ML)
- Chat without RAG (LLM only, short responses)
- Embedding generation (small batches)
- Single-turn conversations

### ❌ Will Fail (Heavy ML)
- RAG-enabled chat (embedding + retrieval + LLM)
- Multi-turn conversations with history
- Concurrent requests
- Long context processing
- TTS with simultaneous chat

## Current LLM Configuration

**Prompt Template**: Configured for short, concise responses
- No markdown formatting (headers, bullets)
- Plain text only
- Maximum 512 tokens per response
- Temperature: 0.8 (balanced creativity)

**Limitations**:
- Cannot generate structured content
- Limited context understanding (1024 tokens max)
- No conversation memory beyond current session
- No citations or references in responses

## Recommended Upgrades

### Minimal Working Setup
**Backend**: Starter Plus (2GB RAM) - $21/month
**Qdrant**: Starter (512MB) - $7/month
**Total**: ~$28/month

### Production Ready
**Backend**: Standard (4GB RAM) - $85/month
**Qdrant**: Standard (2GB) - $25/month
**Total**: ~$110/month

### Performance Improvements
**4GB RAM** enables:
- Reliable model loading
- 2-3 concurrent requests
- Faster response times (2-3s)
- RAG with multiple document chunks
- Better formatted responses

**8GB RAM** enables:
- 5-10 concurrent users
- Sub-2s response times
- Full context windows
- Batch processing
- TTS + chat simultaneously

## Testing Strategy

1. **Start with health checks** - Verify backend is alive
2. **Test hardcoded FAQs** - No ML, should always work
3. **Try simple chat** - Send single message, expect OOM or slow response
4. **Monitor logs** - Watch for memory errors
5. **Upgrade if needed** - Move to 2GB+ before full testing

## Reality Check

**Current 512MB setup is for demo/development only.** Production use requires minimum 2GB RAM. Expect frequent crashes and timeouts with current configuration.
