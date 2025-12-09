"""
Chat API endpoint with RAG integration.
Add this to your existing chat.py or create new endpoint.
"""
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from typing import Optional, List, AsyncGenerator
from pydantic import BaseModel, Field
import logging
import json
import asyncio

from app.services.rag_service import get_rag_service, RAGService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


# ============================================================================
# Request/Response Schemas
# ============================================================================

class ChatRequest(BaseModel):
    """Chat request with RAG parameters"""
    query: str = Field(..., min_length=1, max_length=512, description="User question")
    category: Optional[List[str]] = Field(default=None, description="Filter by categories")
    language: Optional[str] = Field(default=None, pattern="^(DE|EN|FR)$", description="Response language")
    source_type: Optional[str] = Field(default=None, description="Filter by source type")
    top_k: Optional[int] = Field(default=5, ge=1, le=10, description="Number of context chunks")
    min_score: Optional[float] = Field(default=0.5, ge=0.0, le=1.0, description="Minimum similarity")
    style: Optional[str] = Field(default="standard", pattern="^(standard|concise)$", description="Response style")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Welche Therapien bietet functiomed an?",
                "category": ["angebote", "therapy"],
                "language": "DE",
                "top_k": 5,
                "min_score": 0.5,
                "style": "standard"
            }
        }


class ChatResponse(BaseModel):
    """Chat response with answer and metadata"""
    answer: str
    sources: List[dict]
    query: str
    detected_language: Optional[str]
    retrieval_results: int
    citations: List[str]
    confidence_score: float
    metrics: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "functiomed bietet verschiedene Therapien an, darunter Osteopathie, Physiotherapie und Ernährungsberatung [1]. Diese Behandlungen sind darauf ausgerichtet, Ihre Gesundheit ganzheitlich zu unterstützen [2].",
                "sources": [
                    {
                        "index": 1,
                        "document": "angebote.pdf",
                        "category": "angebote",
                        "score": 0.92,
                        "chunk": "1/3"
                    }
                ],
                "query": "Welche Therapien bietet functiomed an?",
                "detected_language": "DE",
                "retrieval_results": 3,
                "citations": ["[1]", "[2]"],
                "confidence_score": 0.88,
                "metrics": {
                    "total_time_ms": 1245.67,
                    "retrieval_time_ms": 234.56,
                    "generation_time_ms": 1011.11,
                    "tokens_used": 456
                }
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    service: str
    status: str
    components: dict


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat endpoint with RAG-based response generation.
    
    This endpoint:
    1. Retrieves relevant document chunks
    2. Generates contextual response with LLM
    3. Includes source citations
    4. Returns confidence score and metrics
    """
    try:
        logger.info(f"Chat request: '{request.query[:50]}...', language={request.language}")

        # Get RAG service
        rag_service: RAGService = get_rag_service()

        # Generate answer
        response = rag_service.generate_answer(
            query=request.query,
            top_k=request.top_k,
            category=request.category,
            language=request.language,
            source_type=request.source_type,
            min_score=request.min_score,
            response_style=request.style
        )
        
        # Convert to API response
        return ChatResponse(**response.to_dict())
        
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Chat failed: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request. Please try again."
        )


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Health check endpoint for RAG service.
    
    Checks:
    - Retrieval service (Qdrant connection, embeddings)
    - LLM service (model loaded, inference working)
    """
    try:
        rag_service: RAGService = get_rag_service()
        health_status = rag_service.health_check()
        return HealthResponse(**health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service health check failed: {str(e)}"
        )


@router.post("/quick", response_model=dict)
async def quick_chat(query: str) -> dict:
    """
    Quick chat endpoint with minimal parameters.

    Simplified endpoint for basic questions without filtering.
    """
    try:
        logger.info(f"Quick chat: '{query[:50]}...'")

        rag_service: RAGService = get_rag_service()

        response = rag_service.generate_answer(
            query=query,
            top_k=3,
            style="concise"
        )

        # Return simplified response
        return {
            "answer": response.answer,
            "confidence": response.confidence_score,
            "sources": len(response.sources)
        }

    except Exception as e:
        logger.error(f"Quick chat failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred. Please try again."
        )


@router.post("/stream")
async def chat_stream(request_body: ChatRequest, request: Request):
    """
    Streaming chat endpoint - allows real-time response generation with ability to stop.

    This endpoint streams the response word-by-word and can be cancelled mid-generation
    by the client closing the connection.

    Returns: Server-Sent Events (SSE) stream with JSON chunks
    """

    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate streaming response with cancellation support"""
        try:
            logger.info(f"Streaming chat request: '{request_body.query[:50]}...'")

            # Get RAG service
            rag_service: RAGService = get_rag_service()

            # Generate answer (non-streaming for now, we'll chunk it)
            # In a production system, you'd modify RAG service to support true streaming
            response = rag_service.generate_answer(
                query=request_body.query,
                top_k=request_body.top_k or 5,
                category=request_body.category,
                language=request_body.language,
                source_type=request_body.source_type,
                min_score=request_body.min_score or 0.5,
                response_style=request_body.style or "standard"
            )

            # Send metadata first
            metadata = {
                "type": "metadata",
                "query": response.query,
                "sources": response.sources,  # sources are already dictionaries
                "confidence_score": response.confidence_score,
                "detected_language": response.detected_language
            }
            yield f"data: {json.dumps(metadata)}\n\n"

            # Check if client disconnected
            if await request.is_disconnected():
                logger.info("Client disconnected before streaming answer")
                return

            # Stream the answer word by word
            words = response.answer.split()
            for i, word in enumerate(words):
                # Check for client disconnect
                if await request.is_disconnected():
                    logger.info(f"Client disconnected at word {i}/{len(words)}")
                    yield f"data: {json.dumps({'type': 'cancelled', 'partial_text': ' '.join(words[:i])})}\n\n"
                    return

                # Send word chunk
                chunk = {
                    "type": "chunk",
                    "text": word + (" " if i < len(words) - 1 else ""),
                    "index": i,
                    "total": len(words)
                }
                yield f"data: {json.dumps(chunk)}\n\n"

                # Small delay to simulate streaming (adjust as needed)
                await asyncio.sleep(0.03)

            # Send completion signal
            completion = {
                "type": "done",
                "full_text": response.answer,
                "metrics": response.to_dict()["metrics"]
            }
            yield f"data: {json.dumps(completion)}\n\n"

            logger.info("Streaming completed successfully")

        except asyncio.CancelledError:
            logger.info("Stream cancelled by client")
            yield f"data: {json.dumps({'type': 'cancelled'})}\n\n"

        except Exception as e:
            logger.error(f"Streaming failed: {type(e).__name__}: {e}")
            error_msg = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_msg)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


# ============================================================================
# Example curl commands:
# ============================================================================

"""
# Standard chat request
curl -X POST "http://localhost:8000/api/v1/chat/" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "Welche Therapien bietet functiomed an?",
    "category": ["angebote"],
    "language": "DE",
    "top_k": 5
  }'

# Quick chat
curl -X POST "http://localhost:8000/api/v1/chat/quick?query=Was%20kostet%20Osteopathie?"

# Health check
curl -X GET "http://localhost:8000/api/v1/chat/health"
"""