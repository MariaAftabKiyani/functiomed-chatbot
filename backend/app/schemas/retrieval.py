"""
Schemas for retrieval pipeline requests and responses.
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator


# ============================================================================
# Request Schemas (Pydantic for validation)
# ============================================================================

class RetrievalRequest(BaseModel):
    """Request schema for document retrieval"""
    query: str = Field(..., min_length=1, max_length=512, description="User query text")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")
    category: Optional[List[str]] = Field(default=None, description="Filter by categories")
    language: Optional[str] = Field(default=None, pattern="^(DE|EN|FR)$", description="Filter by language")
    source_type: Optional[str] = Field(default=None, pattern="^(pdf|text)$", description="Filter by source type")
    min_score: Optional[float] = Field(default=0.0, ge=0.0, le=1.0, description="Minimum similarity score")
    
    @validator('category')
    def validate_categories(cls, v):
        """Ensure categories are valid"""
        if v:
            valid_categories = {
                'angebote', 'ernaehrung', 'notices', 'patient_info',
                'praxis-info', 'therapien', 'therapy', 'training'
            }
            invalid = set(v) - valid_categories
            if invalid:
                raise ValueError(f"Invalid categories: {invalid}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Welche Therapien bietet functiomed an?",
                "top_k": 3,
                "category": ["angebote", "therapy"],
                "language": "DE",
                "min_score": 0.5
            }
        }


# ============================================================================
# Response Schemas (Dataclasses for internal use)
# ============================================================================

@dataclass
class RetrievalResult:
    """Single retrieval result with relevance score"""
    text: str
    score: float
    chunk_id: str
    source_document: str
    category: str
    language: Optional[str]
    chunk_index: int
    total_chunks: int
    source_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self):
        return (
            f"RetrievalResult(score={self.score:.3f}, source={self.source_document}, "
            f"chunk={self.chunk_index}/{self.total_chunks})"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "text": self.text,
            "score": round(self.score, 4),
            "chunk_id": self.chunk_id,
            "source_document": self.source_document,
            "category": self.category,
            "language": self.language,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "source_type": self.source_type,
            "metadata": self.metadata
        }


@dataclass
class RetrievalResponse:
    """Complete retrieval response with metadata"""
    query: str
    normalized_query: str
    detected_language: Optional[str]
    results: List[RetrievalResult]
    total_results: int
    filters_applied: Dict[str, Any]
    retrieval_time_ms: float
    
    def __repr__(self):
        return (
            f"RetrievalResponse(results={self.total_results}, "
            f"time={self.retrieval_time_ms:.1f}ms)"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "query": self.query,
            "normalized_query": self.normalized_query,
            "detected_language": self.detected_language,
            "results": [r.to_dict() for r in self.results],
            "total_results": self.total_results,
            "filters_applied": self.filters_applied,
            "retrieval_time_ms": round(self.retrieval_time_ms, 2)
        }
    
    def get_context_for_llm(self, max_tokens: Optional[int] = None) -> str:
        """
        Format results as context string for LLM.
        
        Args:
            max_tokens: Optional token limit (approximate by chars)
            
        Returns:
            Formatted context string
        """
        if not self.results:
            return ""
        
        context_parts = []
        total_chars = 0
        max_chars = max_tokens * 4 if max_tokens else None  # Rough estimate
        
        for idx, result in enumerate(self.results, 1):
            # Format: [1] Source: filename (score: 0.85)
            # Text content here...
            part = (
                f"[{idx}] Source: {result.source_document} "
                f"(score: {result.score:.2f})\n"
                f"{result.text}\n"
            )
            
            if max_chars and (total_chars + len(part)) > max_chars:
                break
            
            context_parts.append(part)
            total_chars += len(part)
        
        return "\n---\n".join(context_parts)


# ============================================================================
# Filter Builder Helper
# ============================================================================

@dataclass
class RetrievalFilters:
    """Helper class for building Qdrant filters"""
    category: Optional[List[str]] = None
    language: Optional[str] = None
    source_type: Optional[str] = None
    
    def to_qdrant_filter(self) -> Optional[Dict[str, Any]]:
        """
        Convert to Qdrant filter format.
        
        Returns:
            Qdrant-compatible filter dict or None if no filters
        """
        conditions = []
        
        if self.category:
            # OR logic for categories
            conditions.append({
                "key": "category",
                "match": {"any": self.category}
            })
        
        if self.language:
            conditions.append({
                "key": "language",
                "match": {"value": self.language}
            })
        
        if self.source_type:
            conditions.append({
                "key": "source_type",
                "match": {"value": self.source_type}
            })
        
        if not conditions:
            return None
        
        # Combine with AND logic
        return {
            "must": conditions
        }
    
    def __repr__(self):
        active = []
        if self.category:
            active.append(f"category={self.category}")
        if self.language:
            active.append(f"language={self.language}")
        if self.source_type:
            active.append(f"source_type={self.source_type}")
        return f"RetrievalFilters({', '.join(active) if active else 'none'})"