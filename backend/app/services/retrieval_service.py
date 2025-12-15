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
from app.utils.reranker import CrossEncoderReranker, get_reranker
from app.utils.bm25_search import BM25, HybridSearchFusion, get_bm25_search
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
        query_normalizer: Optional[QueryNormalizer] = None,
        reranker: Optional[CrossEncoderReranker] = None,
        bm25_search: Optional[BM25] = None
    ):
        """
        Initialize retrieval service.

        Args:
            embedding_service: Optional pre-initialized embedding service
            qdrant_service: Optional pre-initialized Qdrant service
            query_normalizer: Optional pre-initialized query normalizer
            reranker: Optional pre-initialized cross-encoder reranker
            bm25_search: Optional pre-initialized BM25 search
        """
        # Initialize or use provided services
        self.embedding_service = embedding_service or EmbeddingService()
        self.qdrant_service = qdrant_service or QdrantService()
        self.query_normalizer = query_normalizer or QueryNormalizer(
            max_length=settings.RETRIEVAL_MAX_QUERY_LENGTH
        )

        # Initialize reranker if enabled
        self.reranker_enabled = settings.RERANKER_ENABLED
        self.reranker = None
        if self.reranker_enabled:
            try:
                self.reranker = reranker or get_reranker()
                logger.info("  Cross-encoder re-ranking: ENABLED")
                logger.info(f"    Model: {settings.RERANKER_MODEL}")
                logger.info(f"    Re-rank top-K: {settings.RERANKER_TOP_K}")
            except Exception as e:
                logger.warning(f"Failed to initialize reranker: {e}")
                logger.warning("Re-ranking will be disabled")
                self.reranker_enabled = False
        else:
            logger.info("  Cross-encoder re-ranking: DISABLED")

        # Initialize BM25 hybrid search if enabled
        self.hybrid_search_enabled = settings.HYBRID_SEARCH_ENABLED
        self.bm25_search = None
        if self.hybrid_search_enabled:
            try:
                bm25_index_path = Path(settings.DOCUMENTS_DIR).parent / "bm25_index.pkl"
                self.bm25_search = bm25_search or get_bm25_search(index_path=str(bm25_index_path))
                if self.bm25_search.num_docs > 0:
                    logger.info("  Hybrid BM25 + Semantic search: ENABLED")
                    logger.info(f"    BM25 index: {self.bm25_search.num_docs} documents")
                    logger.info(f"    Hybrid alpha: {settings.HYBRID_ALPHA} (semantic weight)")
                else:
                    logger.warning("BM25 index is empty - hybrid search disabled")
                    self.hybrid_search_enabled = False
            except Exception as e:
                logger.warning(f"Failed to initialize BM25 search: {e}")
                logger.warning("Hybrid search will be disabled - using semantic only")
                self.hybrid_search_enabled = False
        else:
            logger.info("  Hybrid search: DISABLED (semantic only)")

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

        Pipeline with re-ranking:
        1. Retrieve larger candidate set with bi-encoder (fast)
        2. Re-rank candidates with cross-encoder (accurate)
        3. Return top-K re-ranked results

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

        # Determine candidate retrieval size
        # If re-ranking is enabled, retrieve more candidates (10x top_k or at least 15)
        if self.reranker_enabled and self.reranker:
            candidate_top_k = max(top_k * 10, 15)
            rerank_top_k = min(top_k, settings.RERANKER_TOP_K)  # Re-rank top 3 (or user's top_k if smaller)
            logger.info(f"Re-ranking enabled: retrieving {candidate_top_k} candidates, re-ranking top {rerank_top_k}")
        else:
            candidate_top_k = top_k
            rerank_top_k = 0
            logger.info(f"Re-ranking disabled: retrieving {candidate_top_k} results directly")

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

            # Step 4: Search (Hybrid or Semantic only)
            if self.hybrid_search_enabled and self.bm25_search:
                # Hybrid search: BM25 + Semantic
                search_results = self._hybrid_search(
                    query=normalized.normalized,
                    query_vector=query_embedding,
                    top_k=candidate_top_k,
                    filters=filters,
                    min_score=min_score
                )
            else:
                # Semantic search only
                search_results = self._search_vectors(
                    query_vector=query_embedding,
                    top_k=candidate_top_k,
                    filters=filters,
                    min_score=min_score
                )

            # Step 5: Re-rank results if enabled
            if self.reranker_enabled and self.reranker and len(search_results) > 0:
                logger.info(f"[Re-ranking] Processing {len(search_results)} candidates...")
                rerank_start = time.time()

                # Re-rank using cross-encoder
                reranked = self.reranker.rerank(
                    query=normalized.normalized,
                    results=search_results,
                    top_k=rerank_top_k
                )

                rerank_time_ms = (time.time() - rerank_start) * 1000
                logger.info(f"[Re-ranking] Completed in {rerank_time_ms:.0f}ms, selected top {len(reranked)}")

                # Convert reranked results back to search result format
                search_results = [r.metadata for r in reranked]

                # Update scores with cross-encoder scores
                for i, ranked_result in enumerate(reranked):
                    search_results[i]["score"] = ranked_result.final_score
                    search_results[i]["original_score"] = ranked_result.bi_encoder_score
                    search_results[i]["cross_encoder_score"] = ranked_result.cross_encoder_score

            # Step 6: Format results
            formatted_results = self._format_results(search_results)

            # Take only top_k results (in case re-ranking returned more)
            formatted_results = formatted_results[:top_k]

            # Calculate total retrieval time
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
                    "min_score": min_score,
                    "reranking_enabled": self.reranker_enabled
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
        """Generate embedding for normalized query with caching"""
        try:
            # Use embed_query for single query with caching support
            embedding = self.embedding_service.embed_query(query)
            return embedding
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

    def _hybrid_search(
        self,
        query: str,
        query_vector: np.ndarray,
        top_k: int,
        filters: RetrievalFilters,
        min_score: float
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining BM25 and semantic search.

        Args:
            query: Normalized query text
            query_vector: Query embedding vector
            top_k: Number of results to return
            filters: Metadata filters
            min_score: Minimum score threshold

        Returns:
            Fused results from both search methods
        """
        logger.info("[Hybrid Search] Combining BM25 + Semantic search...")

        # Step 1: BM25 keyword search
        bm25_start = time.time()
        bm25_filter_dict = {}
        if filters.category:
            bm25_filter_dict['category'] = filters.category
        if filters.language:
            bm25_filter_dict['language'] = filters.language

        bm25_results = self.bm25_search.search(
            query=query,
            top_k=top_k * 2,  # Get more candidates for fusion
            filters=bm25_filter_dict if bm25_filter_dict else None
        )
        bm25_time = (time.time() - bm25_start) * 1000
        logger.info(f"  BM25: {len(bm25_results)} results in {bm25_time:.0f}ms")

        # Step 2: Semantic vector search
        semantic_start = time.time()
        semantic_results = self._search_vectors(
            query_vector=query_vector,
            top_k=top_k * 2,  # Get more candidates for fusion
            filters=filters,
            min_score=min_score
        )
        semantic_time = (time.time() - semantic_start) * 1000
        logger.info(f"  Semantic: {len(semantic_results)} results in {semantic_time:.0f}ms")

        # Step 3: Fuse results using weighted scoring
        fusion_start = time.time()
        fused_results = HybridSearchFusion.weighted_fusion(
            bm25_results=bm25_results,
            semantic_results=semantic_results,
            alpha=settings.HYBRID_ALPHA
        )
        fusion_time = (time.time() - fusion_start) * 1000

        # Take top-k after fusion
        fused_results = fused_results[:top_k]

        logger.info(
            f"  Fusion: {len(fused_results)} results in {fusion_time:.0f}ms "
            f"(alpha={settings.HYBRID_ALPHA})"
        )

        return fused_results
    
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

        # Check reranker (if enabled)
        if self.reranker_enabled and self.reranker:
            try:
                reranker_health = self.reranker.health_check()
                health["components"]["reranker"] = reranker_health
                if reranker_health["status"] != "healthy":
                    health["status"] = "degraded"
            except Exception as e:
                health["components"]["reranker"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health["status"] = "degraded"
        else:
            health["components"]["reranker"] = {
                "status": "disabled",
                "enabled": False
            }

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