"""
Cross-Encoder Re-ranking Service
Uses cross-encoder models to re-rank retrieval results for improved accuracy.
"""
import logging
import time
from typing import List, Tuple, Optional
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RankedResult:
    """Re-ranked result with cross-encoder score"""
    original_index: int
    text: str
    bi_encoder_score: float
    cross_encoder_score: float
    final_score: float
    metadata: dict


class CrossEncoderReranker:
    """
    Cross-Encoder Re-ranking Service

    Re-ranks retrieval results using a cross-encoder model which considers
    both query and document together for more accurate relevance scoring.

    Pipeline:
    1. Bi-encoder retrieves candidate documents (fast, approximate)
    2. Cross-encoder re-ranks top candidates (slow, accurate)
    3. Return top-K re-ranked results
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        device: str = "cpu",
        batch_size: int = 16
    ):
        """
        Initialize cross-encoder reranker.

        Args:
            model_name: HuggingFace cross-encoder model
            device: Device to use ('cpu' or 'cuda')
            batch_size: Batch size for inference
        """
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.model = None
        self.is_bge_reranker = "bge-reranker" in model_name.lower()

        logger.info(f"Initializing CrossEncoderReranker with model: {model_name}")
        logger.info(f"  Device: {device}")
        logger.info(f"  Batch size: {batch_size}")
        logger.info(f"  Model type: {'BGE Reranker' if self.is_bge_reranker else 'Cross-Encoder'}")

        self._load_model()

    def _load_model(self):
        """Load cross-encoder or BGE reranker model"""
        try:
            logger.info(f"Loading reranker model: {self.model_name}...")
            start_time = time.time()

            if self.is_bge_reranker:
                # BGE reranker uses FlagReranker class
                try:
                    from FlagEmbedding import FlagReranker

                    self.model = FlagReranker(
                        self.model_name,
                        use_fp16=False  # Use FP32 for CPU, FP16 for CUDA if needed
                    )
                    logger.info("  Using FlagReranker (optimized for BGE models)")

                except ImportError:
                    # Fallback to CrossEncoder if FlagEmbedding not available
                    logger.warning("FlagEmbedding not installed, falling back to CrossEncoder")
                    from sentence_transformers import CrossEncoder

                    self.model = CrossEncoder(
                        self.model_name,
                        device=self.device,
                        max_length=512
                    )
                    self.is_bge_reranker = False  # Treat as regular cross-encoder
            else:
                # Standard cross-encoder model
                from sentence_transformers import CrossEncoder

                self.model = CrossEncoder(
                    self.model_name,
                    device=self.device,
                    max_length=512
                )

            load_time = (time.time() - start_time) * 1000
            logger.info(f"✓ Reranker model loaded in {load_time:.0f}ms")

        except ImportError as e:
            logger.error("Required package not installed.")
            logger.error("Run: pip install sentence-transformers")
            logger.error("For BGE reranker, also run: pip install FlagEmbedding")
            raise RuntimeError("sentence-transformers (and optionally FlagEmbedding) required for re-ranking") from e
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            raise RuntimeError(f"Reranker initialization failed: {e}") from e

    def rerank(
        self,
        query: str,
        results: List[dict],
        top_k: int = 3
    ) -> List[RankedResult]:
        """
        Re-rank retrieval results using cross-encoder.

        Args:
            query: User query
            results: List of retrieval results (dicts with 'text' and 'score')
            top_k: Number of top results to return after re-ranking

        Returns:
            List of top-K re-ranked results sorted by cross-encoder score
        """
        if not results:
            logger.warning("No results to re-rank")
            return []

        if len(results) <= top_k:
            logger.info(f"Results ({len(results)}) <= top_k ({top_k}), re-ranking all")

        logger.info(f"Re-ranking {len(results)} results to select top {top_k}")
        start_time = time.time()

        try:
            # Prepare query-document pairs for cross-encoder
            pairs = []
            for result in results:
                # Extract text from result
                text = result.get("text", "")
                if not text:
                    logger.warning(f"Empty text in result: {result}")
                    text = ""

                pairs.append([query, text])

            # Get cross-encoder scores
            logger.debug(f"Computing cross-encoder scores for {len(pairs)} pairs...")

            if self.is_bge_reranker:
                # BGE reranker returns scores directly (already normalized)
                cross_scores = self.model.compute_score(
                    pairs,
                    batch_size=self.batch_size
                )
                # Convert to numpy array if needed
                if not isinstance(cross_scores, np.ndarray):
                    cross_scores = np.array(cross_scores)
                # BGE scores are already in reasonable range, normalize to [0, 1]
                cross_scores_normalized = self._sigmoid(cross_scores)
            else:
                # Standard cross-encoder
                cross_scores = self.model.predict(
                    pairs,
                    batch_size=self.batch_size,
                    show_progress_bar=False
                )
                # Normalize cross-encoder scores to [0, 1] range using sigmoid
                cross_scores_normalized = self._sigmoid(cross_scores)

            # Combine bi-encoder and cross-encoder scores
            ranked_results = []
            for idx, (result, cross_score, cross_score_norm) in enumerate(
                zip(results, cross_scores, cross_scores_normalized)
            ):
                bi_encoder_score = result.get("score", 0.0)

                # Weighted combination: 70% cross-encoder, 30% bi-encoder
                # Cross-encoder is more accurate but bi-encoder provides useful signal
                final_score = 0.7 * cross_score_norm + 0.3 * bi_encoder_score

                ranked_result = RankedResult(
                    original_index=idx,
                    text=result.get("text", ""),
                    bi_encoder_score=bi_encoder_score,
                    cross_encoder_score=float(cross_score_norm),
                    final_score=final_score,
                    metadata=result
                )
                ranked_results.append(ranked_result)

            # Sort by final score (descending)
            ranked_results.sort(key=lambda x: x.final_score, reverse=True)

            # Select top-K
            top_results = ranked_results[:top_k]

            rerank_time = (time.time() - start_time) * 1000
            logger.info(f"✓ Re-ranking completed in {rerank_time:.0f}ms")
            logger.info(f"  Top-{top_k} results selected")

            # Log score improvements
            if top_results:
                avg_bi_score = np.mean([r.bi_encoder_score for r in top_results])
                avg_cross_score = np.mean([r.cross_encoder_score for r in top_results])
                avg_final_score = np.mean([r.final_score for r in top_results])

                logger.debug(f"  Avg bi-encoder score: {avg_bi_score:.4f}")
                logger.debug(f"  Avg cross-encoder score: {avg_cross_score:.4f}")
                logger.debug(f"  Avg final score: {avg_final_score:.4f}")

            # Log top result details
            if top_results:
                top = top_results[0]
                logger.info(
                    f"  Top result: bi={top.bi_encoder_score:.4f}, "
                    f"cross={top.cross_encoder_score:.4f}, "
                    f"final={top.final_score:.4f}"
                )

            return top_results

        except Exception as e:
            logger.error(f"Re-ranking failed: {type(e).__name__}: {e}")
            # Fallback: return original results sorted by bi-encoder score
            logger.warning("Falling back to bi-encoder scores only")
            fallback_results = [
                RankedResult(
                    original_index=idx,
                    text=result.get("text", ""),
                    bi_encoder_score=result.get("score", 0.0),
                    cross_encoder_score=0.0,
                    final_score=result.get("score", 0.0),
                    metadata=result
                )
                for idx, result in enumerate(results)
            ]
            fallback_results.sort(key=lambda x: x.final_score, reverse=True)
            return fallback_results[:top_k]

    @staticmethod
    def _sigmoid(x):
        """Apply sigmoid activation to normalize scores to [0, 1]"""
        return 1 / (1 + np.exp(-np.array(x)))

    def health_check(self) -> dict:
        """Check if reranker is healthy"""
        health = {
            "service": "CrossEncoderReranker",
            "status": "healthy",
            "model": self.model_name,
            "device": self.device
        }

        try:
            # Test inference
            test_pairs = [["test query", "test document"]]
            _ = self.model.predict(test_pairs, show_progress_bar=False)
            health["model_loaded"] = True
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
            health["model_loaded"] = False

        return health


# Singleton instance
_reranker_instance = None

def get_reranker(
    model_name: Optional[str] = None,
    device: Optional[str] = None
) -> CrossEncoderReranker:
    """
    Get or create singleton CrossEncoderReranker instance.

    Args:
        model_name: Optional model name (uses config default if None)
        device: Optional device (uses config default if None)

    Returns:
        Initialized CrossEncoderReranker
    """
    global _reranker_instance

    if _reranker_instance is None:
        from app.config import settings

        model_name = model_name or settings.RERANKER_MODEL
        device = device or settings.EMBEDDING_DEVICE  # Use same device as embeddings

        logger.info("Creating new CrossEncoderReranker instance")
        _reranker_instance = CrossEncoderReranker(
            model_name=model_name,
            device=device,
            batch_size=settings.RERANKER_BATCH_SIZE
        )

    return _reranker_instance
