import os
from typing import ClassVar, Optional, List, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import logging

class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    APP_NAME: str = "FunctiOMed Chatbot API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # CORS settings
    ALLOWED_ORIGINS: Union[List[str], str] = "*"

    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(',')]
        return v

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
    HF_HUB_TOKEN: str = os.getenv("HF_HUB_TOKEN", "")
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
        default=1,
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

    # ============================================================================
    # LLM Configuration (CPU-only inference)
    # ============================================================================

    # Model settings
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "meta-llama/Llama-3.2-1B-Instruct")

    # Generation settings
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS","512"))  # Max tokens for responses
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.5"))  # Sampling temperature (lower = more focused)
    LLM_TOP_P: float = float(os.getenv("LLM_TOP_P", "0.9"))
    LLM_CONTEXT_WINDOW: int = int(os.getenv("LLM_CONTEXT_WINDOW", "8192"))  # Llama-3.2-1B context window (128K capable, but limiting for performance) 

    # ============================================================================
    # RAG (Retrieval-Augmented Generation) Configuration
    # ============================================================================

    # Context settings
    RAG_MAX_CONTEXT_TOKENS: int = int(os.getenv("RAG_MAX_CONTEXT_TOKENS", "1024"))  # Reserve space for response (prompt + context)
    RAG_MAX_CHUNKS: int = int(os.getenv("RAG_MAX_CHUNKS", "5"))  # Number of chunks to retrieve
    RAG_MIN_CHUNK_SCORE: float = float(os.getenv("RAG_MIN_CHUNK_SCORE", "0.5"))  # Minimum similarity

    # Response settings
    RAG_ENABLE_CITATIONS: bool = os.getenv("RAG_ENABLE_CITATIONS", "true").lower() == "true"
    RAG_FALLBACK_RESPONSE_DE: str = os.getenv(
        "RAG_FALLBACK_RESPONSE_DE",
        "Entschuldigung, ich habe keine relevanten Informationen zu Ihrer Frage. "
        "Für weitere Unterstützung können Sie uns gerne kontaktieren:\n\n"
        "**Telefon**: +41 (0)44 401 15 15\n"
        "**Email**: functiomed@hin.ch\n\n"
        "Wir antworten in der Regel innerhalb von 24 Stunden an Werktagen."
    )
    RAG_FALLBACK_RESPONSE_EN: str = os.getenv(
        "RAG_FALLBACK_RESPONSE_EN",
        "I apologize, but I don't have relevant information available regarding this. "
        "For further assistance, you can contact us:\n\n"
        "**Phone**: +41 (0)44 401 15 15\n"
        "**Email**: functiomed@hin.ch\n\n"
        "We usually respond to inquiries within 24 hours on weekdays."
    )
    RAG_FALLBACK_RESPONSE_FR: str = os.getenv(
        "RAG_FALLBACK_RESPONSE_FR",
        "Je m'excuse, mais je n'ai pas d'informations pertinentes disponibles à ce sujet. "
        "Pour une assistance supplémentaire, vous pouvez nous contacter :\n\n"
        "**Téléphone** : +41 (0)44 401 15 15\n"
        "**Email** : functiomed@hin.ch\n\n"
        "Nous répondons généralement aux demandes dans les 24 heures les jours ouvrables."
    )

    # ============================================================================
    # HuggingFace Settings
    # ============================================================================

    # Authentication and caching
    HF_HUB_TOKEN: str = os.getenv("HF_HUB_TOKEN", "")  # Required for Llama models
    HF_HOME: str = os.getenv("HF_HOME", "./models/huggingface")  # Model cache directory

    # ============================================================================
    # TTS Configuration (HuggingFace Inference API)
    # ============================================================================

    # HuggingFace API authentication
    HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", os.getenv("HF_HUB_TOKEN", ""))

    # Audio cache directory
    TTS_CACHE_DIR: str = os.getenv(
        "TTS_CACHE_DIR",
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "tts_cache")
    )

    # Generation settings
    TTS_MAX_CHARS: int = int(os.getenv("TTS_MAX_CHARS", "2000"))
    TTS_TIMEOUT: int = int(os.getenv("TTS_TIMEOUT", "30"))  # seconds


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
