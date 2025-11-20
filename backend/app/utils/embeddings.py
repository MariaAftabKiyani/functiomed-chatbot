"""
Embedding service using BGE-M3 via sentence-transformers.
Windows-compatible, no build dependencies required.
"""
import logging
import time
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
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

# """
# Embedding service using BGE-M3 via sentence-transformers.
# Windows-compatible, uses .env config, no build dependencies required.
# """
# import logging
# import time
# from typing import List
# import numpy as np
# from sentence_transformers import SentenceTransformer
# from huggingface_hub import login
# import os
# import sys
# from pathlib import Path

# # Import config
# sys.path.insert(0, str(Path(__file__).parent.parent.parent))
# from app.config import settings

# logger = logging.getLogger(__name__)

# # ------------------------------
# # Setup Hugging Face authentication & cache
# # ------------------------------
# if not settings.HF_HUB_TOKEN:
#     raise RuntimeError("HF_HUB_TOKEN not set in .env")

# os.environ["HF_HOME"] = settings.HF_HOME
# os.environ["TRANSFORMERS_CACHE"] = settings.HF_HOME
# os.environ["HF_DATASETS_CACHE"] = settings.HF_HOME

# # Programmatic login
# login(token=settings.HF_HUB_TOKEN)


# class EmbeddingService:
#     """
#     BGE-M3 embedding service with:
#     - Input validation
#     - Error handling with retries
#     - Progress tracking
#     - Windows-compatible
#     """

#     def __init__(self):
#         """Initialize BGE-M3 model"""
#         self.model = None
#         self._initialize()

#     def _initialize(self):
#         """Load model with error handling"""
#         logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL} on {settings.EMBEDDING_DEVICE}...")
#         try:
#             self.model = SentenceTransformer(
#                 settings.EMBEDDING_MODEL,
#                 device=settings.EMBEDDING_DEVICE
#             )

#             # Warmup
#             logger.info("Warming up model...")
#             _ = self.model.encode(
#                 ["warmup"],
#                 batch_size=1,
#                 show_progress_bar=False,
#                 convert_to_numpy=True
#             )
#             logger.info("✓ Model loaded and ready")
#         except Exception as e:
#             logger.error(f"Failed to load model: {e}")
#             raise RuntimeError(f"Model initialization failed: {e}")

#     def embed_documents(self, texts: List[str]) -> np.ndarray:
#         """
#         Embed a list of document texts.

#         Args:
#             texts: List of text strings to embed

#         Returns:
#             numpy array of shape (n, 1024)
#         """
#         # Validate input
#         if not texts:
#             raise ValueError("Text list is empty")

#         if not isinstance(texts, list):
#             raise TypeError(f"Expected list, got {type(texts)}")

#         # Filter out empty strings
#         valid_texts = [t.strip() for t in texts if t and t.strip()]

#         if not valid_texts:
#             raise ValueError("No valid texts after filtering empty strings")

#         if len(valid_texts) < len(texts):
#             logger.warning(f"Filtered out {len(texts) - len(valid_texts)} empty texts")

#         logger.info(f"Embedding {len(valid_texts)} documents (batch_size={settings.EMBEDDING_BATCH_SIZE})...")

#         # Embed with retries
#         for attempt in range(settings.MAX_RETRIES):
#             try:
#                 embeddings = self.model.encode(
#                     valid_texts,
#                     batch_size=settings.EMBEDDING_BATCH_SIZE,
#                     show_progress_bar=True,
#                     convert_to_numpy=True,
#                     normalize_embeddings=settings.EMBEDDING_NORMALIZE
#                 )

#                 # Validate output
#                 self._validate_embeddings(embeddings, len(valid_texts))

#                 logger.info(f"✓ Generated embeddings: {embeddings.shape}")
#                 return embeddings

#             except Exception as e:
#                 if attempt < settings.MAX_RETRIES - 1:
#                     wait_time = settings.RETRY_DELAY * (attempt + 1)
#                     logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
#                     time.sleep(wait_time)
#                 else:
#                     logger.error(f"Embedding failed after {settings.MAX_RETRIES} attempts")
#                     raise RuntimeError(f"Embedding failed: {e}")

#     def _validate_embeddings(self, embeddings: np.ndarray, expected_count: int):
#         """Validate embedding output"""
#         if embeddings is None:
#             raise ValueError("Embeddings are None")

#         if not isinstance(embeddings, np.ndarray):
#             raise TypeError(f"Expected numpy array, got {type(embeddings)}")

#         if embeddings.shape[0] != expected_count:
#             raise ValueError(f"Expected {expected_count} embeddings, got {embeddings.shape[0]}")

#         if embeddings.shape[1] != settings.QDRANT_VECTOR_SIZE:
#             raise ValueError(f"Expected dimension {settings.QDRANT_VECTOR_SIZE}, got {embeddings.shape[1]}")

#         if np.isnan(embeddings).any():
#             raise ValueError("Embeddings contain NaN values")

#         if np.isinf(embeddings).any():
#             raise ValueError("Embeddings contain Inf values")


# # ------------------------------
# # Self-test
# # ------------------------------
# if __name__ == "__main__":
#     from app.config import setup_logging

#     setup_logging("INFO")

#     print("\n" + "="*60)
#     print("EMBEDDING SERVICE TEST")
#     print("="*60)

#     try:
#         service = EmbeddingService()

#         # Test valid texts
#         print("\n[Test 1] Valid texts")
#         texts = [
#             "Dies ist ein deutscher Test.",
#             "This is an English test.",
#             "functiomed bietet medizinische Behandlungen."
#         ]
#         embeddings = service.embed_documents(texts)
#         print(f"✓ Shape: {embeddings.shape}")
#         print(f"✓ Dtype: {embeddings.dtype}")
#         print(f"✓ Sample: {embeddings[0][:5]}")

#         # Test with empty strings
#         print("\n[Test 2] Mixed valid/empty texts")
#         mixed = ["Valid text", "", "Another", "  ", "Last"]
#         embeddings = service.embed_documents(mixed)
#         print(f"✓ Shape: {embeddings.shape}")

#         print("\n" + "="*60)
#         print("✓ All tests passed!")
#         print("="*60 + "\n")

#     except Exception as e:
#         print(f"\n✗ Test failed: {e}")
#         import traceback
#         traceback.print_exc()
#         sys.exit(1)
