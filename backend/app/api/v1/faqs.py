"""
FAQ API endpoint - Provides instant responses for common questions
"""
from fastapi import APIRouter, HTTPException, Response
from typing import List, Optional
from pydantic import BaseModel, Field
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/faqs", tags=["faqs"])


# ============================================================================
# Schemas
# ============================================================================

class FAQQuestion(BaseModel):
    """FAQ question in multiple languages"""
    DE: str
    EN: str
    FR: str


class FAQAnswer(BaseModel):
    """FAQ answer in multiple languages"""
    DE: str
    EN: str
    FR: str


class FAQ(BaseModel):
    """FAQ item with question and answer"""
    id: str
    question: FAQQuestion
    answer: FAQAnswer
    category: str
    confidence_score: float = 1.0

    class Config:
        json_schema_extra = {
            "example": {
                "id": "services",
                "question": {
                    "DE": "Welche Leistungen bieten Sie an?",
                    "EN": "What services do you provide?",
                    "FR": "Quels services proposez-vous?"
                },
                "answer": {
                    "DE": "Wir bieten Osteopathie, Physiotherapie...",
                    "EN": "We offer osteopathy, physiotherapy...",
                    "FR": "Nous offrons ostéopathie, physiothérapie..."
                },
                "category": "services",
                "confidence_score": 1.0
            }
        }


class FAQResponse(BaseModel):
    """Response for single FAQ"""
    id: str
    question: str
    answer: str
    category: str
    confidence_score: float
    language: str


class FAQListResponse(BaseModel):
    """Response with list of FAQs"""
    faqs: List[FAQ]
    total: int
    supported_languages: List[str]
    version: str


# ============================================================================
# Helper Functions
# ============================================================================

def load_faqs() -> dict:
    """Load FAQs from JSON file"""
    try:
        # Get FAQ file path
        faq_file = Path(__file__).parent.parent.parent / "data" / "faqs.json"

        if not faq_file.exists():
            logger.error(f"FAQ file not found: {faq_file}")
            raise FileNotFoundError(f"FAQ file not found: {faq_file}")

        # Load FAQs (no caching - always fresh)
        with open(faq_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.debug(f"Loaded {len(data.get('faqs', []))} FAQs from file")
        return data

    except Exception as e:
        logger.error(f"Failed to load FAQs: {e}")
        raise


def get_faq_by_id(faq_id: str, language: str = "DE") -> Optional[FAQResponse]:
    """Get a specific FAQ by ID"""
    try:
        data = load_faqs()

        for faq in data.get("faqs", []):
            if faq["id"] == faq_id:
                return FAQResponse(
                    id=faq["id"],
                    question=faq["question"][language],
                    answer=faq["answer"][language],
                    category=faq["category"],
                    confidence_score=faq["confidence_score"],
                    language=language
                )

        return None

    except Exception as e:
        logger.error(f"Error getting FAQ {faq_id}: {e}")
        raise


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/", response_model=FAQListResponse)
async def get_all_faqs(response: Response, language: Optional[str] = "DE") -> FAQListResponse:
    """
    Get all FAQs in the specified language.

    This endpoint returns fresh FAQ data on every request.
    No LLM processing required - responses are pre-generated.

    Args:
        language: Language code (DE, EN, FR). Default: DE

    Returns:
        List of all FAQs with metadata
    """
    # Prevent browser caching
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    try:
        data = load_faqs()
        metadata = data.get("metadata", {})

        # Validate language
        supported_languages = metadata.get("supported_languages", ["DE", "EN", "FR"])
        if language not in supported_languages:
            language = "DE"

        return FAQListResponse(
            faqs=[FAQ(**faq) for faq in data.get("faqs", [])],
            total=len(data.get("faqs", [])),
            supported_languages=supported_languages,
            version=metadata.get("version", "1.0.0")
        )

    except Exception as e:
        logger.error(f"Failed to get FAQs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load FAQs: {str(e)}"
        )


@router.get("/{faq_id}", response_model=FAQResponse)
async def get_faq(faq_id: str, response: Response, language: Optional[str] = "DE") -> FAQResponse:
    """
    Get a specific FAQ by ID.

    This provides instant fresh responses for common questions.
    Perfect for FAQ buttons/cards on the frontend.

    Args:
        faq_id: FAQ identifier (e.g., "services", "pricing")
        language: Language code (DE, EN, FR). Default: DE

    Returns:
        FAQ question and answer in specified language
    """
    # Prevent browser caching
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    try:
        faq = get_faq_by_id(faq_id, language)

        if faq is None:
            raise HTTPException(
                status_code=404,
                detail=f"FAQ with ID '{faq_id}' not found"
            )

        return faq

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get FAQ {faq_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load FAQ: {str(e)}"
        )


@router.get("/category/{category}", response_model=List[FAQResponse])
async def get_faqs_by_category(category: str, response: Response, language: Optional[str] = "DE") -> List[FAQResponse]:
    """
    Get all FAQs in a specific category.

    Args:
        category: Category name (e.g., "services", "pricing", "booking")
        language: Language code (DE, EN, FR). Default: DE

    Returns:
        List of FAQs in the specified category
    """
    # Prevent browser caching
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    try:
        data = load_faqs()
        results = []

        for faq in data.get("faqs", []):
            if faq["category"] == category:
                results.append(FAQResponse(
                    id=faq["id"],
                    question=faq["question"][language],
                    answer=faq["answer"][language],
                    category=faq["category"],
                    confidence_score=faq["confidence_score"],
                    language=language
                ))

        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No FAQs found for category '{category}'"
            )

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get FAQs for category {category}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load FAQs: {str(e)}"
        )


@router.post("/reload")
async def reload_faqs() -> dict:
    """
    Check FAQ file status.

    Note: FAQs are no longer cached - they are loaded fresh on each request.
    This endpoint is kept for backward compatibility.

    Returns:
        Status message with number of FAQs available
    """
    try:
        data = load_faqs()

        return {
            "status": "success",
            "message": "FAQs are loaded fresh on each request (no caching)",
            "total_faqs": len(data.get("faqs", [])),
            "version": data.get("metadata", {}).get("version", "unknown")
        }

    except Exception as e:
        logger.error(f"Failed to load FAQs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load FAQs: {str(e)}"
        )


# ============================================================================
# Example curl commands:
# ============================================================================

"""
# Get all FAQs in German (default)
curl -X GET "http://localhost:8000/api/v1/faqs/"

# Get all FAQs in English
curl -X GET "http://localhost:8000/api/v1/faqs/?language=EN"

# Get specific FAQ by ID
curl -X GET "http://localhost:8000/api/v1/faqs/services?language=DE"

# Get FAQs by category
curl -X GET "http://localhost:8000/api/v1/faqs/category/pricing?language=EN"

# Reload FAQ cache
curl -X POST "http://localhost:8000/api/v1/faqs/reload"
"""
