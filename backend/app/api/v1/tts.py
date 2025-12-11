"""
TTS API endpoint - Text-to-Speech with Google TTS (gTTS)
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional
import logging
import os

from app.services.tts_service import get_tts_service, TTSService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tts", tags=["tts"])


# ============================================================================
# Request/Response Schemas
# ============================================================================

class TTSRequest(BaseModel):
    """TTS generation request"""
    text: str = Field(..., min_length=1, max_length=2000, description="Text to convert to speech")
    language: str = Field(..., pattern="^(DE|EN|FR)$", description="Language code")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello, how can I help you today?",
                "language": "EN"
            }
        }


class TTSResponse(BaseModel):
    """TTS generation response metadata"""
    audio_url: str
    duration_sec: float
    generation_time_ms: float
    language: str
    format: str


# ============================================================================
# Endpoints
# ============================================================================

# @router.post("/generate", response_model=TTSResponse)
# async def generate_tts(request: TTSRequest) -> TTSResponse:
#     """
#     Generate speech from text.
#
#     This endpoint:
#     1. Validates text and language
#     2. Generates audio using Google TTS (gTTS)
#     3. Returns audio file URL for download
#     4. Automatically deletes previous audio
#     """
#     try:
#         logger.info(f"TTS request: {request.language} - '{request.text[:50]}...'")
#
#         # Get TTS service
#         tts_service: TTSService = get_tts_service()
#
#         # Generate audio
#         result = tts_service.generate_speech(
#             text=request.text,
#             language=request.language,
#             output_format="mp3",
#             bitrate="128k"
#         )
#
#         # Extract filename for URL
#         filename = os.path.basename(result["audio_path"])
#
#         return TTSResponse(
#             audio_url=f"/api/v1/tts/audio/{filename}",
#             duration_sec=result["duration_sec"],
#             generation_time_ms=result["generation_time_ms"],
#             language=result["language"],
#             format=result["format"]
#         )
#
#     except ValueError as e:
#         logger.error(f"Invalid TTS request: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Invalid request: {str(e)}"
#         )
#     except Exception as e:
#         logger.error(f"TTS generation failed: {type(e).__name__}: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to generate speech. Please try again."
#         )


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    """
    Serve generated audio file.

    Returns the MP3 file for the current TTS generation.
    This endpoint serves the cached audio file.
    """
    try:
        tts_service: TTSService = get_tts_service()

        # Security: Only serve the current cached file
        if tts_service.current_audio_file is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No audio file available"
            )

        current_filename = os.path.basename(tts_service.current_audio_file)

        if filename != current_filename:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio file not found"
            )

        if not os.path.exists(tts_service.current_audio_file):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio file no longer exists"
            )

        return FileResponse(
            path=tts_service.current_audio_file,
            media_type="audio/mpeg",
            filename=filename,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audio file"
        )


@router.get("/health")
async def health():
    """TTS service health check"""
    try:
        tts_service: TTSService = get_tts_service()
        health_status = tts_service.health_check()
        return health_status
    except Exception as e:
        logger.error(f"TTS health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"TTS service unavailable: {str(e)}"
        )
