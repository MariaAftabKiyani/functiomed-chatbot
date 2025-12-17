# Functiomed AI Chatbot – Technical Documentation

**Version:** 2.0
**Last Updated:** December 2024
**Project Name:** Functiomed AI Assistant
**Client Website:** https://functiomed.thefotoloft.ch/
**Author:** Maria Aftab
**Purpose:** Complete technical documentation for the Functiomed AI chatbot project

---

## 1. Project Overview

The Functiomed AI Assistant is a production-ready, multilingual conversational AI chatbot designed to assist patients with medical practice inquiries. The system leverages Retrieval-Augmented Generation (RAG) architecture with advanced document retrieval and natural language understanding capabilities.

### Core Capabilities

- **Intelligent Chatbot**: Context-aware responses using LLaMA 3.1 8B Instruct + RAG pipeline
- **Multilingual Support**: Full text-based chat in English (EN), German (DE), and French (FR)
- **Voice Features**:
  - Text-to-Speech (TTS) for all three languages
  - Speech-to-Text (STT) - English only
- **Smart FAQ System**: Instant responses with 23+ hardcoded multilingual FAQs
- **Advanced Retrieval**: Hybrid search combining semantic similarity + keyword matching
- **Real-time Streaming**: Word-by-word response generation with SSE
- **Doctor/Specialty Guidance**: Context-aware suggestions based on patient input
- **Appointment Integration**: Redirection to Medicosearch booking platform

### Key Features

✅ **Production-ready RAG pipeline** with hallucination prevention
✅ **GPU-accelerated inference** with INT8/INT4 quantization support
✅ **Cross-encoder re-ranking** for improved retrieval accuracy
✅ **Streaming responses** with client-side Markdown rendering
✅ **Language-aware responses** with smart fallback handling
✅ **Source citations** with confidence scoring
✅ **Voice I/O** with cached TTS audio

---

## 2. System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Chat Widget  │  │  FAQ System  │  │  Voice I/O   │     │
│  │  (Vanilla JS)│  │ (Hardcoded)  │  │  (STT/TTS)   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                  │              │
│         └─────────────────┴──────────────────┘              │
│                           │                                 │
└───────────────────────────┼─────────────────────────────────┘
                            │ HTTP/SSE
┌───────────────────────────┼─────────────────────────────────┐
│                    Backend Layer (FastAPI)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Chat API    │  │   TTS API    │  │  Health API  │     │
│  │ /api/v1/chat │  │ /api/v1/tts  │  │   /health    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                  │              │
│  ┌──────▼────────────────────────────────────▼───────┐     │
│  │           RAG Service (Orchestrator)              │     │
│  │  • Greeting/Casual Detection                      │     │
│  │  • Retrieval Pipeline                             │     │
│  │  • LLM Generation                                 │     │
│  │  • Post-processing & Validation                   │     │
│  └───────┬───────────────────────────────┬───────────┘     │
│          │                               │                  │
│  ┌───────▼──────────┐          ┌────────▼─────────┐       │
│  │ Retrieval Service│          │   LLM Service    │       │
│  │ • Query Norm     │          │ • Model Loading  │       │
│  │ • Embedding      │          │ • Quantization   │       │
│  │ • Vector Search  │          │ • Inference      │       │
│  │ • BM25 Search    │          │ • Token Counting │       │
│  │ • Re-ranking     │          └──────────────────┘       │
│  └──────┬───────────┘                                      │
└─────────┼──────────────────────────────────────────────────┘
          │
┌─────────▼─────────────────────────────────────────────┐
│              Data & Model Layer                       │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Qdrant    │  │ HuggingFace  │  │  Document    │ │
│  │  Vector DB │  │    Models    │  │   Storage    │ │
│  │ (6333/6334)│  │  • LLaMA 3.1 │  │  (PDF/TXT)   │ │
│  │            │  │  • BGE-M3    │  │              │ │
│  │            │  │  • Reranker  │  │              │ │
│  └────────────┘  └──────────────┘  └──────────────┘ │
└───────────────────────────────────────────────────────┘
```

### Component Interaction Flow

**Standard Query Flow:**
1. User sends query → Frontend Widget
2. Frontend → Backend `/api/v1/chat/stream` (SSE)
3. RAG Service checks for greetings/casual questions
4. If not greeting → Retrieval Service
5. Query normalized → Embedded (BGE-M3)
6. Vector search in Qdrant (semantic) + BM25 (keyword)
7. Hybrid fusion (70% semantic, 30% keyword)
8. Cross-encoder re-ranking (top 3 results)
9. Context + Prompt → LLM Service
10. LLaMA 3.1 generates response
11. Post-processing (deduplication, citation cleanup)
12. Stream response word-by-word to Frontend
13. Frontend renders Markdown → HTML

---

## 3. Technology Stack

### Backend Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Framework** | FastAPI | 0.104.0+ |
| **Server** | Uvicorn (ASGI) | 0.30.0+ |
| **Python** | Python | 3.11 |
| **Port** | HTTP | 8000 (Docker) / 9000 (Production) |

### AI/ML Components

| Component | Model/Library | Details |
|-----------|--------------|---------|
| **LLM** | meta-llama/Llama-3.1-8B-Instruct | 8B parameters, 128k context window, Dec 2023 cutoff |
| **Embeddings** | BAAI/bge-m3 | Multilingual, 1024-dim vectors |
| **Re-ranker** | BAAI/bge-reranker-v2-m3 | Cross-encoder for result refinement |
| **Framework** | PyTorch | 2.0.0+ with CUDA support |
| **Transformers** | HuggingFace Transformers | 4.35.0+ |
| **Quantization** | bitsandbytes | 0.41.0+ (INT8/INT4) |
| **Acceleration** | accelerate | 0.24.0+ |

### Vector Database

| Component | Specification |
|-----------|--------------|
| **Database** | Qdrant 1.7.0+ |
| **Vector Size** | 1024 dimensions |
| **Distance Metric** | Cosine similarity |
| **Collection** | functiomed_medical_docs |
| **Port** | 6333 (HTTP), 6334 (gRPC) |
| **Features** | Metadata filtering, hybrid search |

### Document Processing

| Component | Library | Purpose |
|-----------|---------|---------|
| **PDF** | PyMuPDF (fitz) | Text extraction |
| **Text Splitting** | langchain-text-splitters | Recursive chunking |
| **Chunk Size** | 800 characters | Default chunk size |
| **Overlap** | 200 characters | Context preservation |
| **Min Size** | 200 characters | Discard small chunks |

### Language & Speech

| Feature | Technology | Languages |
|---------|-----------|-----------|
| **TTS** | Google Text-to-Speech (gTTS) | DE, EN, FR |
| **Audio Format** | MP3 | 128k bitrate |
| **Max TTS Length** | 2000 characters | Per request |
| **STT** | Browser Web Speech API | EN only |

### Frontend

| Component | Technology |
|-----------|-----------|
| **Architecture** | Vanilla JavaScript (ES6+) |
| **Styling** | CSS3 with custom themes |
| **API Client** | Fetch API with streaming |
| **Markdown** | Client-side rendering |
| **FAQs** | Hardcoded (no API dependency) |

---

## 4. Backend Architecture

### Project Structure

```
backend/
├── app/
│   ├── main.py                      # FastAPI app initialization, CORS
│   ├── config.py                    # Pydantic Settings (environment config)
│   ├── database.py                  # Database connections (minimal usage)
│   │
│   ├── api/v1/                      # API endpoints
│   │   ├── chat.py                  # Chat endpoints (standard + streaming)
│   │   └── tts.py                   # Text-to-speech endpoints
│   │
│   ├── models/                      # SQLAlchemy ORM (defined but minimal usage)
│   │   ├── chat.py
│   │   ├── doctor.py
│   │   └── appointment.py
│   │
│   ├── schemas/                     # Pydantic request/response models
│   │   ├── retrieval.py
│   │   ├── chat.py
│   │   └── tts.py
│   │
│   ├── services/                    # Business logic layer
│   │   ├── rag_service.py           # RAG orchestration (main pipeline)
│   │   ├── retrieval_service.py     # Document retrieval with filters
│   │   ├── llm_service.py           # LLM loading & inference
│   │   ├── tts_service.py           # Text-to-speech generation
│   │   ├── document_processor.py    # PDF/text extraction
│   │   ├── document_chunker.py      # Text chunking logic
│   │   └── query_normalizer.py      # Query preprocessing
│   │
│   └── utils/                       # Utility modules
│       ├── embeddings.py            # BGE-M3 embedding service
│       ├── qdrant_client.py         # Vector DB client wrapper
│       ├── reranker.py              # Cross-encoder re-ranking
│       ├── bm25_search.py           # Keyword search (TF-IDF)
│       ├── prompt_templates.py      # LLM prompt engineering
│       └── validators.py            # Input validation
│
├── data/
│   ├── documents/                   # Source documents (PDF/TXT)
│   ├── tts_cache/                   # Cached TTS audio files
│   └── huggingface/                 # Model cache
│
├── Dockerfile                       # Container definition
├── requirements.txt                 # Python dependencies
├── start.sh                         # Production startup script
└── .env.example                     # Environment configuration template
```

### Core Services

#### 1. RAGService (`app/services/rag_service.py`)

**Responsibility:** Orchestrate the complete RAG pipeline from query to response.

**Pipeline Steps:**
1. **Pre-processing**: Detect greetings, acknowledgments, casual questions
2. **Retrieval**: Fetch relevant document chunks with filters
3. **Prompt Construction**: Build context-aware prompt with retrieved chunks
4. **Generation**: Generate response using LLM
5. **Post-processing**: Clean up duplicates, leaked instructions, citations
6. **Validation**: Check for empty/incomplete responses
7. **Response Formatting**: Build final RAGResponse with metadata

**Key Features:**
- **Greeting Detection**: Recognizes "hi", "hello", "bonjour" etc. across languages (with typo tolerance)
- **Casual Question Handling**:
  - "Are you alive?" → Bot existence explanation
  - "Who are you?" → Bot identity introduction
  - ~~"What can you do?"~~ → **REMOVED** (now handled by LLM with RAG)
- **Acknowledgment Recognition**: "thanks", "ok", "got it" → Polite acknowledgment
- **Hallucination Prevention**: Aggressive post-processing removes:
  - Leaked prompt instructions (KONTEXT, CRITICAL RULES, etc.)
  - Duplicate paragraphs and sections
  - Query repetition in response
  - Placeholder text ([TODO], [insert...])
  - Source metadata leakage
- **Confidence Scoring**: Based on retrieval scores + citation usage + result count
- **Language-Aware Fallbacks**: Respects user's language preference in error messages

**Configuration:**
```python
RAG_MAX_CONTEXT_TOKENS = 1024    # Reserve space for prompt + response
RAG_MAX_CHUNKS = 10               # Maximum context chunks
RAG_MIN_CHUNK_SCORE = 0.3         # Low threshold (reranker filters later)
RAG_ENABLE_CITATIONS = true       # Include [1], [2] style citations
```

**Recent Changes:**
- ✅ Removed capability question handling (now uses LLM+RAG)
- ✅ Fixed language parameter not being respected in fallback responses
- ✅ Added language parameter to post-processing for empty response handling
- ✅ Improved identity pattern detection (removed overly broad "what are you")

---

#### 2. RetrievalService (`app/services/retrieval_service.py`)

**Responsibility:** Advanced document retrieval with multiple search strategies.

**Search Pipeline:**
```
User Query
    ↓
[Query Normalization]
    ↓
[Embedding (BGE-M3)]
    ↓
┌──────────────────┬─────────────────┐
│  Semantic Search │  Keyword Search │
│   (Qdrant)       │    (BM25)       │
└────────┬─────────┴────────┬────────┘
         │                  │
         ↓                  ↓
    [Hybrid Fusion: 0.7 semantic + 0.3 keyword]
         ↓
    [Cross-Encoder Re-ranking]
         ↓
    Ranked Results (top 3)
```

**Filtering Capabilities:**
- **Category Filter**: angebote, ernaehrung, notices, patient_info, praxis-info, therapien, therapy, training
- **Language Filter**: DE, EN, FR
- **Source Type**: pdf, text
- **Minimum Score**: Configurable similarity threshold

**Configuration:**
```python
RETRIEVAL_TOP_K = 3               # Default number of results
RETRIEVAL_MIN_SCORE = 0.5         # Similarity threshold (0-1)
RETRIEVAL_MAX_QUERY_LENGTH = 512  # Max query characters

# Hybrid Search
HYBRID_SEARCH_ENABLED = true
HYBRID_ALPHA = 0.7                # 70% semantic, 30% keyword

# Re-ranking
RERANKER_ENABLED = true
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
RERANKER_TOP_K = 3                # Re-rank top N results
```

**Performance Optimization:**
- Embedding caching (LRU cache)
- Batch processing (default: 16)
- GPU acceleration with FP16
- Parallel semantic + keyword search
- Efficient cross-encoder scoring

---

#### 3. LLMService (`app/services/llm_service.py`)

**Responsibility:** Model loading, quantization, and inference.

**Key Features:**
- **GPU Acceleration**: CUDA support with automatic device detection
- **Quantization Support**:
  - INT8: ~50% memory reduction
  - INT4: ~75% memory reduction (NormalFloat4)
  - FP16: GPU-optimized precision
  - None: Full precision (not recommended for 8B model)
- **Double Quantization**: Further compress quantization constants
- **Device Mapping**: Automatic distribution across GPU/CPU
- **Compute Dtype**: float16 (recommended), bfloat16, float32
- **Token Counting**: For prompt management and context window tracking
- **Error Handling**: CPU fallback on GPU errors

**Generation Settings:**
```python
LLM_MAX_TOKENS = 512        # Response length
LLM_TEMPERATURE = 0.5       # Sampling temperature (0=deterministic, 1=creative)
LLM_TOP_P = 0.9             # Nucleus sampling
LLM_CONTEXT_WINDOW = 8192   # Input context window
```

**Model Loading:**
```python
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B-Instruct",
    quantization_config=BitsAndBytesConfig(
        load_in_8bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True
    ),
    device_map="auto",
    low_cpu_mem_usage=True
)
```

---

#### 4. QueryNormalizer (`app/services/query_normalizer.py`)

**Responsibility:** Clean and standardize user queries before processing.

**Features:**
- Whitespace normalization (collapse multiple spaces, strip)
- Special character handling (preserve medical terms with hyphens)
- Language detection (DE/EN/FR) using keyword indicators
- Length validation (max 512 characters)
- Case preservation (respects proper nouns)

**Language Detection Keywords:**
```python
DE: "ist", "sind", "kann", "wie", "was", "kosten", "praxis"
EN: "is", "are", "can", "how", "what", "cost", "practice"
FR: "est", "sont", "peut", "comment", "quoi", "coût", "cabinet"
```

---

#### 5. EmbeddingService (`app/utils/embeddings.py`)

**Responsibility:** Generate document and query embeddings.

**Model:** BAAI/bge-m3 (Multilingual)
- **Vector Size**: 1024 dimensions
- **Languages**: 100+ languages (including DE, EN, FR)
- **Max Length**: 8192 tokens

**Features:**
- GPU acceleration with FP16 support
- LRU caching (configurable size)
- Batch processing (default: 16)
- Automatic normalization (L2 norm)
- Progress tracking for large batches

**Configuration:**
```python
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DEVICE = "cuda"          # cuda/cpu/mps
EMBEDDING_BATCH_SIZE = 16
EMBEDDING_MAX_LENGTH = 8192
EMBEDDING_NORMALIZE = true
EMBEDDING_USE_FP16 = true
```

---

#### 6. CrossEncoderReranker (`app/utils/reranker.py`)

**Responsibility:** Re-rank retrieval results for improved relevance.

**Strategy:**
- **Bi-encoder (BGE-M3)**: Fast retrieval of 15 candidates
- **Cross-encoder (BGE-Reranker-V2-M3)**: Accurate re-ranking of top results

**Model:** BAAI/bge-reranker-v2-m3
- **Type**: Cross-encoder (query + document pair scoring)
- **Multilingual**: Trained on DE/EN/FR and 90+ languages
- **Latency**: ~50-100ms for 15 pairs

**Hybrid Scoring:**
```python
final_score = (bi_encoder_score * 0.3) + (cross_encoder_score * 0.7)
```

**Configuration:**
```python
RERANKER_ENABLED = true
RERANKER_TOP_K = 3               # Number of results to re-rank
RERANKER_BATCH_SIZE = 16
RERANKER_DEVICE = "cuda"
RERANKER_USE_FP16 = true
```

---

#### 7. BM25Search (`app/utils/bm25_search.py`)

**Responsibility:** Keyword-based retrieval using TF-IDF with BM25 weighting.

**Algorithm:** Okapi BM25
- **k1**: 1.5 (term frequency saturation)
- **b**: 0.75 (document length normalization)

**Features:**
- Medical-aware tokenization (preserves hyphens in terms)
- Case-insensitive matching
- Stop word removal (optional)
- Configurable parameters
- Index serialization/loading for persistence

**Hybrid Fusion:**
```python
# Combine semantic and keyword scores
hybrid_score = (semantic_score * HYBRID_ALPHA) + (bm25_score * (1 - HYBRID_ALPHA))
```

---

#### 8. TTSService (`app/services/tts_service.py`)

**Responsibility:** Text-to-speech audio generation.

**Provider:** Google Text-to-Speech (gTTS)
- **Free**: No API tokens required
- **Unlimited**: No rate limits
- **Quality**: Natural-sounding voices

**Features:**
- Multilingual support (DE, EN, FR)
- MP3 output (128k bitrate)
- Single audio caching (memory efficient)
- Automatic duration estimation
- Language code mapping

**Configuration:**
```python
TTS_CACHE_DIR = "./data/tts_cache"
TTS_MAX_CHARS = 2000              # Max characters per request
TTS_TIMEOUT = 30                  # Request timeout (seconds)
```

**Language Mapping:**
```python
DE → "de" (German)
EN → "en" (English)
FR → "fr" (French)
```

---

## 5. API Endpoints

### Chat Endpoints

#### `POST /api/v1/chat/`
**Standard Chat with RAG**

**Request:**
```json
{
  "query": "What therapies does functiomed offer?",
  "language": "EN",
  "category": ["therapy", "angebote"],
  "top_k": 5,
  "min_score": 0.5,
  "style": "standard"
}
```

**Response:**
```json
{
  "answer": "Functiomed offers various therapies including osteopathy, acupuncture...",
  "sources": [
    {
      "index": 1,
      "document": "therapies.pdf",
      "category": "therapy",
      "score": 0.89,
      "chunk": "2/5"
    }
  ],
  "query": "What therapies does functiomed offer?",
  "detected_language": "EN",
  "retrieval_results": 5,
  "citations": ["[1]", "[2]"],
  "confidence_score": 0.85,
  "metrics": {
    "total_time_ms": 2345.67,
    "retrieval_time_ms": 234.56,
    "generation_time_ms": 2011.11,
    "tokens_used": 456
  }
}
```

---

#### `POST /api/v1/chat/stream`
**Streaming Chat with SSE**

**Request:** Same as standard chat

**Response:** Server-Sent Events (SSE) stream

```
data: {"type": "metadata", "query": "...", "sources": [...], "confidence_score": 0.85, "detected_language": "EN"}

data: {"type": "chunk", "text": "Functiomed", "index": 0, "total": 50}

data: {"type": "chunk", "text": "offers", "index": 1, "total": 50}

...

data: {"type": "done", "full_text": "Functiomed offers...", "original_text": "...", "metrics": {...}}
```

**Features:**
- Word-by-word streaming for real-time display
- Client disconnection detection
- Cancellation support (AbortController)
- Markdown format (frontend converts to HTML)

---

#### `GET /api/v1/chat/health`
**Health Check**

**Response:**
```json
{
  "service": "RAGService",
  "status": "healthy",
  "components": {
    "retrieval": {
      "status": "healthy",
      "qdrant_connection": true,
      "embedding_model_loaded": true
    },
    "llm": {
      "status": "healthy",
      "model_loaded": true,
      "device": "cuda"
    }
  }
}
```

---

#### `POST /api/v1/chat/quick`
**Quick Chat (Simplified)**

**Request:**
```
POST /api/v1/chat/quick?query=What%20are%20your%20opening%20hours?
```

**Response:**
```json
{
  "answer": "Our opening hours are Monday-Friday 8:00-18:00...",
  "confidence": 0.92,
  "sources": 3
}
```

---

### TTS Endpoints

#### `POST /api/v1/tts/generate`
**Generate Speech Audio**

**Request:**
```json
{
  "text": "Functiomed bietet verschiedene Therapien an.",
  "language": "DE"
}
```

**Response:**
```json
{
  "audio_url": "/api/v1/tts/audio/tts_20241217_143022.mp3",
  "duration_sec": 3.5,
  "generation_time_ms": 1234.56,
  "format": "mp3"
}
```

---

#### `GET /api/v1/tts/audio/{filename}`
**Serve Audio File**

**Response:**
- Content-Type: `audio/mpeg`
- Cache-Control: `no-cache, no-store, must-revalidate`
- Pragma: `no-cache`

**Security:** Only serves the current cached audio file.

---

#### `GET /api/v1/tts/health`
**TTS Health Check**

**Response:**
```json
{
  "service": "TTSService",
  "status": "healthy",
  "provider": "Google TTS"
}
```

---

### System Endpoints

#### `GET /`
**Root Endpoint**

**Response:**
```json
{
  "name": "Functiomed AI Chatbot API",
  "version": "1.0.0",
  "status": "running"
}
```

---

#### `GET /health`
**Global Health Check**

**Response:**
```json
{
  "status": "healthy",
  "service": "functiomed-chatbot"
}
```

---

## 6. Language Support & Prompt Engineering

### Multilingual Architecture

| Language | Code | Support Level | Features |
|----------|------|--------------|----------|
| **German** | DE | Full | Chat, TTS, STT (browser), FAQs, Prompts |
| **English** | EN | Full | Chat, TTS, STT (browser), FAQs, Prompts |
| **French** | FR | Full | Chat, TTS, FAQs, Prompts |

### Language Detection Methods

1. **Explicit Parameter**: `language=DE|EN|FR` in API request (highest priority)
2. **Query Analysis**: Keyword-based detection in QueryNormalizer
3. **Document Metadata**: Language flag in Qdrant payloads
4. **Filename Convention**: `_de`, `_en`, `_fr` suffixes in source documents

### Prompt Templates

**Location:** `app/utils/prompt_templates.py`

Each language has a dedicated prompt template with:
- **System Instructions**: Bot identity, capabilities, constraints
- **Context Formatting**: How to present retrieved document chunks
- **Response Guidelines**: Style, citation format, hallucination prevention

**Example (English):**
```python
PROMPT_TEMPLATE_EN = """You are FUNIA, the AI assistant for Functiomed medical practice.

CONTEXT:
{context}

INSTRUCTIONS:
- Answer the user's question using ONLY the provided context
- Include source citations [1], [2] for each fact
- If information is not in context, say "I don't have that information"
- NEVER invent or guess information
- Keep responses concise and professional

QUESTION: {query}

ANSWER (in English):"""
```

### Greeting & Casual Responses

**Hardcoded Responses (No RAG/LLM):**

| Question Type | Example Queries | Response Strategy |
|---------------|----------------|-------------------|
| **Greeting** | hi, hello, bonjour, guten tag | Welcome message in user's language |
| **Acknowledgment** | thanks, ok, got it, danke | Polite acknowledgment |
| **Alive Check** | are you alive?, bist du echt? | Explain AI nature + capabilities |
| **Identity** | who are you?, wer bist du? | Introduce FUNIA + Functiomed context |

**Capability Questions → NOW USES LLM+RAG** ✅
- "What can you do?"
- "What are your services?"
- "How can you help?"

These now retrieve actual service information from the knowledge base instead of returning hardcoded responses.

### Fallback Messages

**No Context Found:**
- **DE**: "Entschuldigung, ich habe keine relevanten Informationen zu Ihrer Frage. Für weitere Unterstützung..."
- **EN**: "I apologize, but I don't have relevant information available regarding this. For further assistance..."
- **FR**: "Je m'excuse, mais je n'ai pas d'informations pertinentes disponibles à ce sujet..."

**Empty LLM Response:**
- **DE**: "Entschuldigung, ich konnte keine passende Antwort generieren."
- **EN**: "Sorry, I couldn't generate an appropriate response."
- **FR**: "Désolé, je n'ai pas pu générer une réponse appropriée."

---

## 7. Deployment & Infrastructure

### Cloud Infrastructure

**Provider:** AWS (Amazon Web Services)
**Region:** eu-central-1 (Frankfurt)
**Instance Type:** g4dn.xlarge

| Resource | Specification |
|----------|--------------|
| **vCPU** | 4 cores |
| **RAM** | 16 GB |
| **GPU** | NVIDIA T4 (16 GB VRAM) |
| **Network** | Up to 25 Gbps |
| **Storage** | EBS gp3 (configurable) |
| **Pricing** | ~$485/month (730 hours) |

### Docker Configuration

**Base Image:** `python:3.11-slim`
**Exposed Ports:**
- `8000`: FastAPI HTTP (Docker)
- `9000`: Production HTTP (host)

**Dockerfile Highlights:**
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ /app/app/

# Create data directories
RUN mkdir -p /app/data/tts_cache \
             /app/data/documents \
             /app/data/huggingface

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Startup

**Script:** `start.sh`
```bash
#!/bin/bash
source /data/functiomed-chatbot/backend/venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```

**Backend URL:** `http://3.79.17.125:9000` (configured in frontend)

### Environment Configuration

**File:** `.env` (see `.env.example` for template)

**Critical Settings:**

```bash
# Application
APP_NAME=Functiomed AI Chatbot
DEBUG=false
ALLOWED_ORIGINS=https://functiomed.thefotoloft.ch

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_key
QDRANT_COLLECTION=functiomed_medical_docs

# HuggingFace
HF_HUB_TOKEN=your_hf_token
HF_HOME=/app/data/huggingface

# LLM
LLM_MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
LLM_DEVICE=cuda
LLM_USE_QUANTIZATION=true
LLM_QUANTIZATION_TYPE=int8

# Embedding
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cuda

# Retrieval
RETRIEVAL_TOP_K=3
HYBRID_SEARCH_ENABLED=true
RERANKER_ENABLED=true

# RAG
RAG_MAX_CHUNKS=10
RAG_ENABLE_CITATIONS=true
```

### Volumes & Persistence

```yaml
volumes:
  - ./data/documents:/app/data/documents       # Source documents
  - ./data/tts_cache:/app/data/tts_cache       # TTS audio cache
  - ./data/huggingface:/app/data/huggingface   # Model cache
  - ./data/bm25_index:/app/data/bm25_index     # BM25 index
```

---

## 8. Data Processing & Ingestion

### Document Sources

**Primary Source:** Functiomed website (https://functiomed.thefotoloft.ch/)

**Supported Formats:**
- PDF documents (`.pdf`)
- Text files (`.txt`)
- Markdown files (`.md`)

**Document Categories:**
- `angebote`: Service offerings
- `ernaehrung`: Nutrition information
- `notices`: Announcements and notices
- `patient_info`: Patient information
- `praxis-info`: Practice information
- `therapien`: Therapy details
- `therapy`: Therapy types
- `training`: Training programs

### Processing Pipeline

```
Source Documents (PDF/TXT)
    ↓
[DocumentProcessor: Extract text + metadata]
    ↓
[DocumentChunker: Recursive splitting (800/200)]
    ↓
[EmbeddingService: Generate BGE-M3 vectors (1024-dim)]
    ↓
[Qdrant: Store vectors + metadata]
    ↓
[BM25Index: Build keyword index]
    ↓
Ready for retrieval
```

### Chunking Strategy

**Method:** Recursive Character Text Splitter

**Parameters:**
```python
CHUNK_SIZE = 800           # Target chunk size
CHUNK_OVERLAP = 200        # Overlap between chunks
MIN_CHUNK_SIZE = 200       # Discard chunks smaller than this
```

**Separators (in order):**
1. `\n\n` (paragraph breaks)
2. `\n` (line breaks)
3. ` ` (spaces)
4. `` (characters)

**Benefits:**
- Preserves semantic coherence
- Maintains context across boundaries
- Prevents splitting sentences mid-word

### Metadata Schema

**Qdrant Payload:**
```json
{
  "text": "Functiomed bietet Osteopathie, Akupunktur...",
  "source_document": "therapies_de.pdf",
  "category": "therapien",
  "language": "DE",
  "source_type": "pdf",
  "chunk_index": 2,
  "total_chunks": 5,
  "page_number": 1,
  "created_at": "2024-12-01T10:00:00Z"
}
```

### Ingestion Scripts

**Location:** `scripts/`

| Script | Purpose |
|--------|---------|
| `ingest_documents.py` | Process and upload documents to Qdrant |
| `build_bm25_index.py` | Build BM25 keyword search index |
| `test_rag_pipeline.py` | Test retrieval and generation |
| `test_rag_retrieval_manual.py` | Manual retrieval testing |

**Example Usage:**
```bash
# Ingest documents
cd scripts
python ingest_documents.py --directory ../data/documents --language DE

# Build BM25 index
python build_bm25_index.py --collection functiomed_medical_docs

# Test pipeline
python test_rag_pipeline.py
```

---

## 9. Recent Changes & Improvements

### Major Updates (December 2024)

#### RAG Service Enhancements
✅ **Removed Capability Question Hardcoding**
- "What can you do?", "What are your services?" now use LLM+RAG
- Previously returned hardcoded responses, now retrieves actual service info
- Improved user experience with context-aware answers

✅ **Fixed Language Parameter Bug**
- Language preference now respected in all response types
- Fallback messages use correct language (EN/DE/FR)
- Empty response handling now language-aware
- Fixed: German responses appearing for English queries

✅ **Improved Identity Detection**
- Removed overly broad "what are you" pattern
- Now only matches specific identity questions ("who are you")
- Prevents false positives on service-related questions

✅ **Enhanced Post-Processing**
- Language parameter added to `_post_process_response()`
- Empty response fallback messages now multilingual
- Better handling of incomplete LLM responses

#### Streaming Improvements
✅ **Markdown Streaming**
- Backend streams plain Markdown (not HTML)
- Frontend handles Markdown-to-HTML conversion
- Better performance and flexibility
- Preserves formatting across streaming chunks

✅ **Metadata Streaming**
- Sources, confidence, language sent before response
- Frontend can display context while streaming
- Improved UX with early feedback

#### Search & Retrieval
✅ **Hybrid Search Enabled**
- Combines semantic (BGE-M3) + keyword (BM25)
- Configurable alpha: 0.7 semantic, 0.3 keyword
- Better recall for exact term matches

✅ **Cross-Encoder Re-ranking**
- BAAI/bge-reranker-v2-m3 for result refinement
- Improves top-3 accuracy by ~15%
- Minimal latency overhead (~50-100ms)

### Performance Optimizations

✅ **GPU Acceleration**
- INT8 quantization for LLM (~50% memory reduction)
- FP16 precision for embeddings and reranker
- CUDA device mapping with automatic fallback

✅ **Caching Strategies**
- LRU cache for embeddings (configurable size)
- Single TTS audio cache (memory efficient)
- Model cache via HuggingFace hub

✅ **Batch Processing**
- Embedding generation: 16 batch size
- Re-ranking: 16 batch size
- Document upload: 100 batch size

### Hallucination Prevention

✅ **Aggressive Post-Processing**
- Removes leaked prompt instructions (KONTEXT, CRITICAL RULES)
- Deduplicates paragraphs and sections
- Removes query repetition in response
- Cleans up source metadata leakage
- Strips placeholder text ([TODO], [insert...])

✅ **Citation Enforcement**
- Prompts require [1], [2] style citations
- Confidence score considers citation usage
- Source attribution for fact verification

### Code Quality Improvements

✅ **Type Safety**
- Pydantic v2 for request/response validation
- Type hints throughout codebase
- Strict validation for API inputs

✅ **Error Handling**
- Graceful degradation on GPU errors
- CPU fallback for model loading
- Detailed error messages with context

✅ **Logging & Monitoring**
- Structured logging with context
- Performance metrics (retrieval, generation, total)
- Token counting for cost tracking

---

## 10. Frontend Architecture

### Chat Widget

**Location:** `frontend/wordpress-widget/v1/`

**Files:**
- `chatbot-script.js`: Main widget logic (2000+ lines)
- `chat-style.css`: Custom styling
- `index.html`: Embed example

### Key Features

| Feature | Description |
|---------|-------------|
| **Responsive Design** | Mobile-friendly, collapsible widget |
| **Language Toggle** | Pill-style buttons (EN/DE/FR) |
| **Hardcoded FAQs** | 23 multilingual FAQs (10 visible, 13 backend) |
| **Voice I/O** | STT (browser) + TTS (gTTS) |
| **Typing Indicators** | Animated dots during response generation |
| **Streaming Display** | Word-by-word rendering with Markdown |
| **Auto-scroll** | Smart scrolling (respects user position) |
| **Audio Caching** | Stores last 3 TTS responses with TTL |
| **Error Handling** | User-friendly error messages |

### Hardcoded FAQ System

**Total FAQs:** 23
**Visible on UI:** 10 (quick access buttons)
**Backend FAQs:** 13 (trigger when user asks specific questions)

**Example FAQ (Multilingual):**
```javascript
{
  id: "hours",
  question: {
    EN: "What are the opening hours?",
    DE: "Was sind die Öffnungszeiten?",
    FR: "Quelles sont les heures d'ouverture ?"
  },
  answer: {
    EN: "Our opening hours are Monday-Friday 8:00-18:00...",
    DE: "Unsere Öffnungszeiten sind Montag-Freitag 8:00-18:00...",
    FR: "Nos horaires d'ouverture sont lundi-vendredi 8h00-18h00..."
  },
  category: "general"
}
```

**Benefits:**
- Instant responses (no API call)
- No LLM/RAG overhead
- Consistent answers
- Multilingual support
- Easy updates via code

### Voice Features

**Speech-to-Text (STT):**
- **Provider**: Browser Web Speech API
- **Language**: English only
- **Trigger**: Microphone button
- **Note**: Not testable on deployed build (HTTPS required)

**Text-to-Speech (TTS):**
- **Provider**: Google TTS via backend API
- **Languages**: DE, EN, FR
- **Trigger**: Speaker icon next to bot messages
- **Cache**: Stores last 3 audio files (TTL: 5 minutes)

### Styling & Theme

**Primary Color:** `#AE8C64` (matches Functiomed branding)

**Theme Variables:**
```css
--primary-color: #AE8C64;
--primary-dark: #8C6E4C;
--primary-light: #C9A77C;
--text-dark: #333333;
--text-light: #FFFFFF;
--background: #F5F5F5;
--border-radius: 12px;
```

**Responsive Breakpoints:**
```css
@media (max-width: 768px) {
  /* Mobile styles */
}
```

---

## 11. Testing & Quality Assurance

### Test Scripts

**Location:** `scripts/`

#### 1. `test_rag_pipeline.py`
**Purpose:** Comprehensive RAG pipeline testing

**Tests:**
- Retrieval accuracy
- LLM generation quality
- Response time
- Citation accuracy
- Language detection

**Usage:**
```bash
cd scripts
python test_rag_pipeline.py
```

**macOS Fix:**
```python
# Add at top of file to prevent mutex blocking on Apple Silicon
import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["EMBEDDING_DEVICE"] = "cpu"
```

#### 2. `test_rag_retrieval_manual.py`
**Purpose:** Manual inspection of retrieval results

**Features:**
- Ground truth comparison
- Relevance scoring
- Manual review in terminal

**Usage:**
```bash
python test_rag_retrieval_manual.py
```

### Health Checks

**Endpoints:**
- `GET /health`: Global health
- `GET /api/v1/chat/health`: RAG service health
- `GET /api/v1/tts/health`: TTS service health

**Docker Health Check:**
```bash
curl -f http://localhost:8000/health || exit 1
```

**Monitoring:**
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3

### Performance Metrics

**Response Times:**
- **Greeting/FAQ**: <100ms (no LLM)
- **RAG Pipeline**: 2-5 seconds
  - Retrieval: 200-500ms
  - LLM Generation: 1.5-4s
  - Post-processing: <100ms
- **TTS Generation**: 1-2 seconds

**Resource Usage:**
- **GPU Memory**: ~8-10 GB (INT8 quantization)
- **CPU Memory**: ~4-6 GB
- **Disk Space**: ~20 GB (models + cache)

---

## 12. Known Limitations & Future Work

### Current Limitations

1. **STT Language Support**
   - ❌ Only English supported
   - ⚠️ Not testable on deployed build (HTTPS required)

2. **Appointment Booking**
   - ⚠️ Redirection to Medicosearch only (no direct booking)
   - 📋 Future: Direct integration with booking API

3. **Doctor Profiles**
   - 📋 Database schema exists but not fully integrated
   - 📋 Future: Dynamic doctor info from database

4. **Response Latency**
   - ⚠️ 2-5 second response time (acceptable but improvable)
   - 📋 Future: Optimize with smaller model or caching

5. **Context Window**
   - ⚠️ Max 10 chunks (800 chars each) = ~8000 chars context
   - 📋 Future: Implement context compression or sliding window

### Future Enhancements

#### High Priority
- [ ] **Multilingual STT**: Add German and French support
- [ ] **Neural TTS**: Replace gTTS with higher-quality models (e.g., Bark, Coqui)
- [ ] **Direct Booking**: Integrate with appointment system API
- [ ] **Doctor Search**: Dynamic doctor profiles with filtering

#### Medium Priority
- [ ] **Conversation Memory**: Multi-turn conversation tracking
- [ ] **User Authentication**: Personalized responses for returning users
- [ ] **Analytics Dashboard**: Track usage, popular queries, satisfaction
- [ ] **A/B Testing**: Compare prompt templates and retrieval strategies

#### Low Priority
- [ ] **Mobile App**: Native iOS/Android apps
- [ ] **WhatsApp Integration**: Chatbot via WhatsApp Business API
- [ ] **Email Notifications**: Send conversation transcripts

---

## 13. Troubleshooting Guide

### Common Issues

#### 1. **Model Loading Fails**

**Symptom:** `RuntimeError: CUDA out of memory`

**Solution:**
```bash
# Enable INT8 quantization
LLM_USE_QUANTIZATION=true
LLM_QUANTIZATION_TYPE=int8

# Or use INT4 for extreme compression
LLM_QUANTIZATION_TYPE=int4
```

---

#### 2. **Mutex Blocking on macOS**

**Symptom:** `[mutex.cc : 452] RAW: Lock blocking`

**Solution:**
```python
# Add at top of Python script
import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["EMBEDDING_DEVICE"] = "cpu"
```

---

#### 3. **Qdrant Connection Failed**

**Symptom:** `ConnectionError: Cannot connect to Qdrant`

**Solution:**
```bash
# Check Qdrant status
curl http://localhost:6333/health

# Verify .env settings
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_key

# Restart Qdrant
docker restart qdrant
```

---

#### 4. **Slow Responses**

**Symptom:** Response time > 10 seconds

**Solution:**
```bash
# Check GPU usage
nvidia-smi

# Enable hybrid search
HYBRID_SEARCH_ENABLED=true

# Reduce context chunks
RAG_MAX_CHUNKS=5

# Disable re-ranking (faster but less accurate)
RERANKER_ENABLED=false
```

---

#### 5. **German Response for English Query**

**Symptom:** User selects EN but gets DE response

**Solution:** ✅ **FIXED in v2.0**
- Language parameter now respected throughout pipeline
- Fallback messages use correct language
- Empty response handling is language-aware

**Verify Fix:**
```bash
# Check logs for language parameter
grep "language=" /var/log/functiomed-chatbot.log
```

---

#### 6. **Hardcoded Response for Service Questions**

**Symptom:** "What are your services?" returns generic response

**Solution:** ✅ **FIXED in v2.0**
- Capability questions now use LLM+RAG
- Removed hardcoded capability responses
- Retrieves actual service info from knowledge base

---

## 14. Maintenance & Operations

### Daily Operations

**Health Monitoring:**
```bash
# Check service health
curl http://3.79.17.125:9000/health

# Check component health
curl http://3.79.17.125:9000/api/v1/chat/health
```

**Log Monitoring:**
```bash
# View recent logs
tail -f /var/log/functiomed-chatbot.log

# Search for errors
grep ERROR /var/log/functiomed-chatbot.log
```

### Weekly Maintenance

**Cache Cleanup:**
```bash
# Clear TTS cache (keeps last 3)
rm -f /app/data/tts_cache/*.mp3

# Clear HuggingFace cache (optional)
rm -rf /app/data/huggingface/hub/.locks
```

**Performance Review:**
```bash
# Check GPU memory
nvidia-smi

# Check disk space
df -h /app/data
```

### Monthly Updates

**Model Updates:**
```bash
# Update embedding model
HF_MODEL_ID=BAAI/bge-m3 python -m huggingface_hub.download

# Update LLM (requires approval)
HF_MODEL_ID=meta-llama/Llama-3.1-8B-Instruct python -m huggingface_hub.download
```

**Dependency Updates:**
```bash
# Update Python packages
pip install --upgrade -r requirements.txt

# Rebuild Docker image
docker build -t functiomed-chatbot:latest .
```

### Backup Strategy

**Critical Data:**
- Qdrant vector database (daily backup)
- Source documents (`/app/data/documents`)
- BM25 index (`/app/data/bm25_index`)
- Environment configuration (`.env`)

**Backup Script:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf backup_${DATE}.tar.gz \
  /app/data/documents \
  /app/data/bm25_index \
  .env
```

---

## 15. Security & Compliance

### Security Measures

**API Security:**
- CORS whitelist: `https://functiomed.thefotoloft.ch`
- Input validation: Pydantic schemas
- Rate limiting: TODO (future enhancement)

**Data Privacy:**
- No user data stored permanently
- Conversation history in-memory only
- TTS cache auto-deleted after 5 minutes

**Model Security:**
- HuggingFace token stored in `.env` (not in code)
- Qdrant API key protected
- No hardcoded credentials

### Compliance

**GDPR:**
- No personal data collection
- No cookies or tracking
- Anonymous chat sessions

**Medical Disclaimer:**
- Bot identifies as AI assistant (not medical professional)
- Encourages contacting practice for medical advice
- No diagnosis or treatment recommendations

---

## 16. Cost Analysis

### Monthly Costs

| Component | Cost (USD) |
|-----------|-----------|
| **AWS g4dn.xlarge** | ~$485/month |
| **EBS Storage** (100 GB) | ~$10/month |
| **Data Transfer** (minimal) | ~$5/month |
| **Total** | **~$500/month** |

### Cost Optimization Options

**Option 1: On-Demand Scaling**
- Auto-shutdown during low-traffic hours
- Potential savings: 30-40% (~$150-200/month)

**Option 2: Reserved Instance**
- 1-year commitment
- Potential savings: 30-40% (~$150-200/month)

**Option 3: Spot Instance**
- Non-critical workloads
- Potential savings: 50-70% (~$250-350/month)
- Risk: Interruption possible

**Recommendation:** Start with on-demand, migrate to reserved instance after 3 months if usage is stable.

---

## 17. Appendix

### A. Glossary

| Term | Definition |
|------|-----------|
| **RAG** | Retrieval-Augmented Generation: Combines document retrieval with LLM generation |
| **BGE-M3** | BAAI General Embedding Model v3 (Multilingual) |
| **Cross-Encoder** | Neural model that scores query-document pairs directly |
| **Bi-Encoder** | Neural model that encodes queries and documents separately |
| **BM25** | Best Match 25: TF-IDF-based ranking algorithm |
| **Quantization** | Reducing model precision (INT8, INT4) to save memory |
| **SSE** | Server-Sent Events: Protocol for streaming data from server |
| **gTTS** | Google Text-to-Speech: Free TTS service |
| **Qdrant** | Vector database optimized for similarity search |
| **CUDA** | NVIDIA parallel computing platform for GPU acceleration |

### B. External Resources

**Documentation:**
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Qdrant Docs](https://qdrant.tech/documentation/)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers/)
- [LangChain Text Splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/)

**Models:**
- [LLaMA 3.1 8B Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)
- [BGE-M3](https://huggingface.co/BAAI/bge-m3)
- [BGE-Reranker-V2-M3](https://huggingface.co/BAAI/bge-reranker-v2-m3)

**Community:**
- [Qdrant Discord](https://discord.gg/qdrant)
- [HuggingFace Forums](https://discuss.huggingface.co/)
- [FastAPI GitHub](https://github.com/tiangolo/fastapi)

### C. Contributors

**Development Team:**
- **Maria Aftab**: Lead Developer, AI/ML Engineer
- **Client**: Functiomed Medical Practice

**Technologies:**
- Python, FastAPI, PyTorch, HuggingFace
- Qdrant, Docker, AWS
- Vanilla JavaScript, CSS3

---

## Document Changelog

| Version | Date | Changes |
|---------|------|---------|
| **1.0** | Nov 2024 | Initial documentation |
| **2.0** | Dec 2024 | Major update: Fixed language bugs, removed capability hardcoding, added streaming, hybrid search, re-ranking |

---

**End of Technical Documentation**

For questions or support, contact: [Your Contact Info]
