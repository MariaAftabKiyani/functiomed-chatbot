"""
Document Retrieval Service for RAG Pipeline
Orchestrates query normalization, embedding, and vector search.
"""
import logging
import time
from typing import List, Optional, Dict, Any
import numpy as np
import sys
from pathlib import Path

# Add backend to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import settings
from app.utils.embeddings import EmbeddingService
from app.utils.qdrant_client import QdrantService
from app.services.query_normalizer import QueryNormalizer, NormalizedQuery
from app.schemas.retrieval import (
    RetrievalRequest,
    RetrievalResult,
    RetrievalResponse,
    RetrievalFilters
)

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Main retrieval service for RAG pipeline.
    
    Pipeline:
    1. Normalize query
    2. Generate query embedding
    3. Search vectors in Qdrant
    4. Apply metadata filters
    5. Format and return results
    """
    
    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        qdrant_service: Optional[QdrantService] = None,
        query_normalizer: Optional[QueryNormalizer] = None
    ):
        """
        Initialize retrieval service.
        
        Args:
            embedding_service: Optional pre-initialized embedding service
            qdrant_service: Optional pre-initialized Qdrant service
            query_normalizer: Optional pre-initialized query normalizer
        """
        # Initialize or use provided services
        self.embedding_service = embedding_service or EmbeddingService()
        self.qdrant_service = qdrant_service or QdrantService()
        self.query_normalizer = query_normalizer or QueryNormalizer(
            max_length=settings.RETRIEVAL_MAX_QUERY_LENGTH
        )
        
        logger.info("RetrievalService initialized")
        logger.info(f"  Default top_k: {settings.RETRIEVAL_TOP_K}")
        logger.info(f"  Min score threshold: {settings.RETRIEVAL_MIN_SCORE}")
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        category: Optional[List[str]] = None,
        language: Optional[str] = None,
        source_type: Optional[str] = None,
        min_score: Optional[float] = None
    ) -> RetrievalResponse:
        """
        Retrieve relevant document chunks for a query.
        
        Args:
            query: User query text
            top_k: Number of results to return (default from config)
            category: Filter by categories (OR logic)
            language: Filter by language (DE/EN)
            source_type: Filter by source type (pdf/text)
            min_score: Minimum similarity score threshold
            
        Returns:
            RetrievalResponse with results and metadata
            
        Raises:
            ValueError: If query is invalid
            RuntimeError: If retrieval pipeline fails
        """
        start_time = time.time()
        
        # Use defaults from config
        top_k = top_k or settings.RETRIEVAL_TOP_K
        min_score = min_score if min_score is not None else settings.RETRIEVAL_MIN_SCORE
        
        logger.info(f"Retrieving for query: '{query[:50]}...'")
        logger.debug(f"  top_k={top_k}, category={category}, language={language}, min_score={min_score}")
        
        try:
            # Step 1: Normalize query
            normalized = self._normalize_query(query)
            logger.debug(f"  Normalized: '{normalized.normalized[:50]}...' (lang: {normalized.detected_language})")
            
            # Auto-detect language if not specified
            if not language and normalized.detected_language:
                language = normalized.detected_language
                logger.debug(f"  Auto-detected language: {language}")
            
            # Step 2: Generate query embedding
            query_embedding = self._embed_query(normalized.normalized)
            logger.debug(f"  Embedding shape: {query_embedding.shape}")
            
            # Step 3: Build filters
            filters = RetrievalFilters(
                category=category,
                language=language,
                source_type=source_type
            )
            logger.debug(f"  Filters: {filters}")
            
            # Step 4: Search in Qdrant
            search_results = self._search_vectors(
                query_vector=query_embedding,
                top_k=top_k,
                filters=filters,
                min_score=min_score
            )
            
            # Step 5: Format results
            formatted_results = self._format_results(search_results)
            
            # Calculate retrieval time
            retrieval_time_ms = (time.time() - start_time) * 1000
            
            # Build response
            response = RetrievalResponse(
                query=query,
                normalized_query=normalized.normalized,
                detected_language=normalized.detected_language,
                results=formatted_results,
                total_results=len(formatted_results),
                filters_applied={
                    "category": category,
                    "language": language,
                    "source_type": source_type,
                    "min_score": min_score
                },
                retrieval_time_ms=retrieval_time_ms
            )
            
            logger.info(
                f"✓ Retrieved {len(formatted_results)} results in {retrieval_time_ms:.1f}ms"
            )
            
            return response
            
        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            raise
        except Exception as e:
            logger.error(f"Retrieval failed: {type(e).__name__}: {e}")
            raise RuntimeError(f"Retrieval pipeline failed: {e}")
    
    def _normalize_query(self, query: str) -> NormalizedQuery:
        """Normalize query using QueryNormalizer"""
        try:
            return self.query_normalizer.normalize(query)
        except Exception as e:
            logger.error(f"Query normalization failed: {e}")
            raise ValueError(f"Invalid query: {e}")
    
    def _embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for normalized query"""
        try:
            # Embed single query (returns shape: (1, 1024))
            embedding = self.embedding_service.embed_documents([query])
            return embedding[0]  # Return single vector
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            raise RuntimeError(f"Failed to embed query: {e}")
    
    def _search_vectors(
        self,
        query_vector: np.ndarray,
        top_k: int,
        filters: RetrievalFilters,
        min_score: float
    ) -> List[Dict[str, Any]]:
        """Search Qdrant for similar vectors"""
        try:
            # Convert filters to Qdrant format
            qdrant_filter = filters.to_qdrant_filter()
            
            # Perform search
            results = self.qdrant_service.search(
                query_vector=query_vector,
                top_k=top_k,
                filters=qdrant_filter,
                score_threshold=min_score if min_score > 0 else None
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise RuntimeError(f"Search failed: {e}")
    
    def _format_results(self, search_results: List[Dict[str, Any]]) -> List[RetrievalResult]:
        """Format Qdrant search results into RetrievalResult objects"""
        formatted = []
        
        for result in search_results:
            payload = result["payload"]
            
            # Extract all fields from payload
            retrieval_result = RetrievalResult(
                text=payload.get("text", ""),
                score=result["score"],
                chunk_id=payload.get("chunk_id", ""),
                source_document=payload.get("source_document", ""),
                category=payload.get("category", ""),
                language=payload.get("language"),
                chunk_index=payload.get("chunk_index", 0),
                total_chunks=payload.get("total_chunks", 1),
                source_type=payload.get("source_type", ""),
                metadata=payload  # Store full payload
            )
            
            formatted.append(retrieval_result)
        
        return formatted
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of retrieval service components.
        
        Returns:
            Health status dictionary
        """
        health = {
            "service": "RetrievalService",
            "status": "healthy",
            "components": {}
        }
        
        # Check Qdrant connection
        try:
            collection_info = self.qdrant_service.get_collection_info()
            health["components"]["qdrant"] = {
                "status": "healthy",
                "collection_exists": collection_info.get("exists", False),
                "vector_count": collection_info.get("points_count", 0)
            }
        except Exception as e:
            health["components"]["qdrant"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health["status"] = "degraded"
        
        # Check embedding service
        try:
            test_embedding = self.embedding_service.embed_documents(["test"])
            health["components"]["embeddings"] = {
                "status": "healthy",
                "model": settings.EMBEDDING_MODEL
            }
        except Exception as e:
            health["components"]["embeddings"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health["status"] = "degraded"
        
        # Check query normalizer
        try:
            self.query_normalizer.normalize("test query")
            health["components"]["normalizer"] = {
                "status": "healthy"
            }
        except Exception as e:
            health["components"]["normalizer"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health["status"] = "degraded"
        
        return health


# Singleton instance for reuse across requests
_retrieval_service_instance = None

def get_retrieval_service() -> RetrievalService:
    """
    Get or create singleton RetrievalService instance.
    
    Returns:
        Initialized RetrievalService
    """
    global _retrieval_service_instance
    
    if _retrieval_service_instance is None:
        logger.info("Creating new RetrievalService instance")
        _retrieval_service_instance = RetrievalService()
    
    return _retrieval_service_instance