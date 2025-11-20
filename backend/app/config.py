import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field
import logging

class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    APP_NAME: str = "FunctiOMed Chatbot API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Qdrant Vector Database
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY", None)
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "functiomed_medical_docs")
    QDRANT_VECTOR_SIZE: int = int(os.getenv("QDRANT_VECTOR_SIZE", "1024"))
    QDRANT_DISTANCE_METRIC: str = os.getenv("QDRANT_DISTANCE_METRIC", "Cosine")
    QDRANT_TIMEOUT: int = int(os.getenv("QDRANT_TIMEOUT", "30"))

    # Embedding Model (BGE-M3)
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    EMBEDDING_DEVICE: str = os.getenv("EMBEDDING_DEVICE", "cpu")
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "16"))
    EMBEDDING_MAX_LENGTH: int = int(os.getenv("EMBEDDING_MAX_LENGTH", "8192"))
    EMBEDDING_NORMALIZE: bool = os.getenv("EMBEDDING_NORMALIZE", "True").lower() == "true"

    # Hugging Face
    HF_HUB_TOKEN: str = os.getenv("HF_HUB_TOKEN", "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")
    HF_HOME: str = os.getenv(
        "HF_HOME",
        os.path.join(os.path.dirname(__file__), "..", "..", ".hf_cache")
    )

    # Document Processing
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "150"))
    MIN_CHUNK_SIZE: int = int(os.getenv("MIN_CHUNK_SIZE", "200"))

    # Retry Settings
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", "1.0"))
    UPLOAD_BATCH_SIZE: int = int(os.getenv("UPLOAD_BATCH_SIZE", "100"))

    # Data Paths
    DOCUMENTS_DIR: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "documents")
    )

    # ============================================================================
    # Retrieval Settings
    # ============================================================================
    RETRIEVAL_TOP_K: int = Field(
        default=5,
        env="RETRIEVAL_TOP_K",
        description="Default number of chunks to retrieve"
    )

    RETRIEVAL_MIN_SCORE: float = Field(
        default=0.5,
        env="RETRIEVAL_MIN_SCORE",
        description="Minimum similarity score threshold (0-1)"
    )

    RETRIEVAL_MAX_QUERY_LENGTH: int = Field(
        default=512,
        env="RETRIEVAL_MAX_QUERY_LENGTH",
        description="Maximum query length in characters"
    )


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Logging configuration
def setup_logging(level: str = "INFO"):
    """Setup application logging"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("qdrant_client").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


if __name__ == "__main__":
    print("=" * 60)
    print("FUNCTIOMED CONFIGURATION")
    print("=" * 60)
    print(f"Qdrant URL: {settings.QDRANT_URL}")
    print(f"Collection: {settings.QDRANT_COLLECTION}")
    print(f"Vector Size: {settings.QDRANT_VECTOR_SIZE}")
    print(f"Embedding Model: {settings.EMBEDDING_MODEL}")
    print(f"Hugging Face Token: {'SET' if settings.HF_HUB_TOKEN else 'NOT SET'}")
    print(f"HF Cache Dir: {settings.HF_HOME}")
    print("=" * 60)
