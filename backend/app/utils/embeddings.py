"""
Embedding service using BGE-M3 via sentence-transformers.
Windows-compatible, no build dependencies required.
"""
import logging
import time
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from functools import lru_cache
import hashlib
import sys
from pathlib import Path

# Import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    BGE-M3 embedding service with:
    - Input validation
    - Error handling with retries
    - Progress tracking
    - Windows-compatible
    """
    
    def __init__(self):
        """Initialize BGE-M3 model"""
        self.model = None
        self._embedding_cache: Dict[str, np.ndarray] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self._initialize()
    
    def _initialize(self):
        """Load model with error handling"""
        logger.info(f"Loading {settings.EMBEDDING_MODEL}...")
        
        try:
            # Use sentence-transformers (Windows-friendly)
            self.model = SentenceTransformer(
                settings.EMBEDDING_MODEL,
                device="cpu"
            )
            
            # Warmup
            logger.info("Warming up model...")
            _ = self.model.encode(
                ["warmup"],
                batch_size=1,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            
            logger.info("✓ Model loaded and ready")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model initialization failed: {e}")
    
    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """
        Embed a list of document texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            numpy array of shape (n, 1024)
            
        Raises:
            ValueError: If input is invalid
            RuntimeError: If embedding fails
        """
        # Validate input
        if not texts:
            raise ValueError("Text list is empty")
        
        if not isinstance(texts, list):
            raise TypeError(f"Expected list, got {type(texts)}")
        
        # Filter out empty strings
        valid_texts = [t.strip() for t in texts if t and t.strip()]
        
        if not valid_texts:
            raise ValueError("No valid texts after filtering empty strings")
        
        if len(valid_texts) < len(texts):
            logger.warning(f"Filtered out {len(texts) - len(valid_texts)} empty texts")
        
        logger.info(f"Embedding {len(valid_texts)} documents (batch_size={settings.EMBEDDING_BATCH_SIZE})...")
        
        # Embed with retries
        for attempt in range(settings.MAX_RETRIES):
            try:
                embeddings = self._embed(valid_texts)
                
                # Validate output
                self._validate_embeddings(embeddings, len(valid_texts))
                
                logger.info(f"✓ Generated embeddings: {embeddings.shape}")
                return embeddings
                
            except Exception as e:
                if attempt < settings.MAX_RETRIES - 1:
                    wait_time = settings.RETRY_DELAY * (attempt + 1)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Embedding failed after {settings.MAX_RETRIES} attempts")
                    raise RuntimeError(f"Embedding failed: {e}")
    
    def _embed(self, texts: List[str]) -> np.ndarray:
        """Internal embedding method"""
        embeddings = self.model.encode(
            texts,
            batch_size=settings.EMBEDDING_BATCH_SIZE,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=settings.EMBEDDING_NORMALIZE
        )
        return embeddings

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a single query with caching for FAQ queries.

        Args:
            query: Query text to embed

        Returns:
            numpy array of shape (1024,)

        Raises:
            ValueError: If input is invalid
            RuntimeError: If embedding fails
        """
        # Validate input
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Normalize query for cache key (lowercase, strip whitespace)
        cache_key = self._get_cache_key(query.strip().lower())

        # Check cache
        if cache_key in self._embedding_cache:
            self._cache_hits += 1
            logger.debug(f"Cache hit for query (hits: {self._cache_hits}, misses: {self._cache_misses})")
            return self._embedding_cache[cache_key]

        # Cache miss - generate embedding
        self._cache_misses += 1
        logger.debug(f"Cache miss for query (hits: {self._cache_hits}, misses: {self._cache_misses})")

        # Use embed_documents for single query
        embedding = self.embed_documents([query])[0]

        # Store in cache (limit cache size to 1000 entries)
        if len(self._embedding_cache) >= 1000:
            # Remove oldest entry (simple FIFO)
            first_key = next(iter(self._embedding_cache))
            del self._embedding_cache[first_key]
            logger.debug("Cache full, removed oldest entry")

        self._embedding_cache[cache_key] = embedding

        return embedding

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text using hash"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "cache_size": len(self._embedding_cache),
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": self._cache_hits / (self._cache_hits + self._cache_misses) if (self._cache_hits + self._cache_misses) > 0 else 0.0
        }

    def clear_cache(self):
        """Clear the embedding cache"""
        self._embedding_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info("Embedding cache cleared")
    
    def _validate_embeddings(self, embeddings: np.ndarray, expected_count: int):
        """Validate embedding output"""
        if embeddings is None:
            raise ValueError("Embeddings are None")
        
        if not isinstance(embeddings, np.ndarray):
            raise TypeError(f"Expected numpy array, got {type(embeddings)}")
        
        if embeddings.shape[0] != expected_count:
            raise ValueError(f"Expected {expected_count} embeddings, got {embeddings.shape[0]}")
        
        if embeddings.shape[1] != settings.QDRANT_VECTOR_SIZE:
            raise ValueError(f"Expected dimension {settings.QDRANT_VECTOR_SIZE}, got {embeddings.shape[1]}")
        
        if np.isnan(embeddings).any():
            raise ValueError("Embeddings contain NaN values")
        
        if np.isinf(embeddings).any():
            raise ValueError("Embeddings contain Inf values")


if __name__ == "__main__":
    # Test
    from config import setup_logging
    setup_logging("INFO")
    
    print("\n" + "="*60)
    print("EMBEDDING SERVICE TEST")
    print("="*60)
    
    try:
        service = EmbeddingService()
        
        # Test valid texts
        print("\n[Test 1] Valid texts")
        texts = [
            "Dies ist ein deutscher Test.",
            "This is an English test.",
            "functiomed bietet medizinische Behandlungen."
        ]
        embeddings = service.embed_documents(texts)
        print(f"✓ Shape: {embeddings.shape}")
        print(f"✓ Dtype: {embeddings.dtype}")
        print(f"✓ Sample: {embeddings[0][:5]}")
        
        # Test with empty strings
        print("\n[Test 2] Mixed valid/empty texts")
        mixed = ["Valid text", "", "Another", "  ", "Last"]
        embeddings = service.embed_documents(mixed)
        print(f"✓ Shape: {embeddings.shape}")
        
        print("\n" + "="*60)
        print("✓ All tests passed!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
