# RAG Pipeline Testing Guide

## Overview
This guide explains how to test your RAG pipeline using the enhanced test script.

## Prerequisites

1. **Backend running** - Make sure your FastAPI backend is running:
   ```bash
   cd backend
   .venv\Scripts\activate
   uvicorn app.main:app --reload
   ```

2. **Qdrant running** - Vector database must be active
3. **Documents indexed** - Your documents must be in Qdrant
4. **LLM model downloaded** - Llama model cached locally

## Running Tests

### Basic Test Run
```bash
cd scripts
python test_rag_pipeline.py
```

### With Virtual Environment
```bash
cd c:\Users\HomePC\Documents\Workspace\functiomed\Project\functiomed-chatbot
backend\.venv\Scripts\activate
cd scripts
python test_rag_pipeline.py
```

## What the Test Checks

### 1. Service Initialization
- ✅ RAG service loads correctly
- ✅ All components initialized

### 2. Health Check
- ✅ Retrieval service status (Qdrant + Embeddings)
- ✅ LLM service status (Model loaded + inference working)

### 3. Test Cases (3 tests)
Each test includes:
- ❓ **Question** - The input query
- 📝 **Ground Truth** - Expected answer
- 🤖 **LLM Response** - Actual generated answer
- 📊 **Metrics:**
  - ⏱️ Total time
  - 🔍 Retrieval time
  - 💭 Generation time
  - 🎯 Tokens used (restored!)
  - 📚 Retrieved chunks
  - 📖 Citations
  - 💯 Confidence score
  - 🌐 Detected language
- 📄 **Sources** - Top 3 relevant documents

### 4. Summary
- Total tests run
- Passed/Failed count
- Success rate percentage

## Expected Output

```
🚀 Starting RAG Pipeline Tests...

================================================================================
RAG PIPELINE COMPREHENSIVE TEST
================================================================================

[1/3] Initializing RAG service...
✓ RAG service initialized successfully

[2/3] Running health check...
✓ Service Status: healthy
  - Retrieval: healthy
  - LLM: healthy

[3/3] Running test cases...
================================================================================

================================================================================
Test 1/3 - Category: pricing
================================================================================
❓ Question: What are prices of functiomed?
📝 Expected (Ground Truth):
   30min Fr. 108.- 45min Fr. 159.- ...

🤖 LLM Response:
   [Generated answer showing pricing information]

📊 Metrics:
   ⏱️  Total Time: 2.34s (2340ms)
   🔍 Retrieval Time: 340ms
   💭 Generation Time: 2000ms
   🎯 Tokens Used: 456
   📚 Retrieved Chunks: 5
   📖 Citations: [1], [2], [3]
   💯 Confidence: 88.5%
   🌐 Detected Language: EN

📄 Sources (5):
   [1] prices.pdf (score: 0.923)
   [2] services.pdf (score: 0.856)
   [3] info.pdf (score: 0.784)

✅ Test 1 PASSED

[... more tests ...]

================================================================================
TEST SUMMARY
================================================================================
Total Tests: 3
✅ Passed: 3
❌ Failed: 0
Success Rate: 100.0%
================================================================================

✨ All tests completed!
```

## Troubleshooting

### Error: "Failed to initialize RAG service"
- Check if backend is running
- Check if Qdrant is accessible
- Check if LLM model is downloaded

### Error: "Retrieval: unhealthy"
- Verify Qdrant is running: `docker ps`
- Check Qdrant connection in `.env`
- Verify documents are indexed

### Error: "LLM: unhealthy"
- Check if model is downloaded
- Verify HF_HOME path in `.env`
- Check available RAM (model needs ~4-8GB)

### Low Confidence Scores
- Add more relevant documents to Qdrant
- Lower `min_score` threshold
- Check document quality and relevance

## Adding More Tests

Edit `test_rag_pipeline.py` and add to `TEST_CASES`:

```python
TEST_CASES = [
    {
        "question": "Your question here?",
        "answer": "Expected ground truth answer",
        "category": "your_category"
    },
    # ... more tests
]
```

## Performance Benchmarks

**Typical Performance:**
- Retrieval Time: 200-500ms
- Generation Time: 1000-3000ms (CPU) / 200-500ms (GPU)
- Total Time: 1500-3500ms
- Tokens: 300-600 tokens

**Good Performance Indicators:**
- ✅ Confidence > 80%
- ✅ 3+ relevant sources retrieved
- ✅ Citations used in response
- ✅ Language correctly detected

## Notes

- Tests run sequentially (not parallel)
- Each test is independent
- Warmup happens once during initialization
- Token counting now fully restored!
- Embedding cache active (FAQ queries faster on repeat)
