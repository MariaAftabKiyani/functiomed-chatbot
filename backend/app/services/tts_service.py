"""
TTS Service - Google Text-to-Speech (gTTS) Integration
Handles text-to-speech generation using Google's free TTS API.
"""
import logging
import time
import os
import tempfile
from typing import Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)


class TTSService:
    """
    Google TTS service with:
    - Free, unlimited usage
    - Multilingual support (DE, EN, FR)
    - No API tokens required
    - Direct MP3 output
    - Single audio caching (memory efficient)

    Uses Google's Text-to-Speech API via gTTS library.
    """

    # Language code mapping (uppercase to lowercase)
    LANGUAGE_CODES = {
        "DE": "de",  # German
        "EN": "en",  # English
        "FR": "fr"   # French
    }

    def __init__(self):
        """Initialize gTTS service (no setup required)"""
        self.current_audio_file = None  # Track single cached audio

    def generate_speech(
        self,
        text: str,
        language: str = "EN",
        output_format: str = "mp3",
        bitrate: str = "128k"
    ) -> Dict[str, Any]:
        """
        Generate speech from text using Google TTS.

        Args:
            text: Text to convert to speech
            language: Language code (DE, EN, FR)
            output_format: Audio format (mp3 only)
            bitrate: Ignored (gTTS uses default bitrate)

        Returns:
            Dict with 'audio_path', 'duration_sec', 'generation_time_ms'

        Raises:
            ValueError: If language not supported or text invalid
            RuntimeError: If generation fails
        """
        # Validation
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if language not in self.LANGUAGE_CODES:
            raise ValueError(
                f"Unsupported language: {language}. "
                f"Supported: {', '.join(self.LANGUAGE_CODES.keys())}"
            )

        if len(text) > settings.TTS_MAX_CHARS:
            raise ValueError(
                f"Text too long. Maximum {settings.TTS_MAX_CHARS} characters."
            )

        logger.info(f"Generating TTS for {language}: '{text[:50]}...'")
        start_time = time.time()

        try:
            # Generate audio using gTTS (cleanup happens inside after new file is created)
            audio_path = self._generate_audio(text, language)

            # Calculate metrics
            generation_time_ms = (time.time() - start_time) * 1000

            # Estimate duration (rough approximation: 150 words per minute)
            word_count = len(text.split())
            duration_sec = (word_count / 150) * 60

            logger.info(
                f"✓ Generated ~{duration_sec:.2f}s audio in {generation_time_ms:.0f}ms"
            )

            return {
                "audio_path": audio_path,
                "duration_sec": round(duration_sec, 2),
                "generation_time_ms": round(generation_time_ms, 2),
                "language": language,
                "format": "mp3"
            }

        except Exception as e:
            logger.error(f"TTS generation failed: {type(e).__name__}: {e}")
            raise RuntimeError(f"Failed to generate speech: {e}")

    def _generate_audio(self, text: str, language: str) -> str:
        """
        Generate audio using Google TTS (gTTS)

        Args:
            text: Text to convert
            language: Language code (DE, EN, FR)

        Returns:
            Path to generated MP3 file
        """
        try:
            from gtts import gTTS

            # Get lowercase language code for gTTS
            lang_code = self.LANGUAGE_CODES[language]
            logger.info(f"Using gTTS with language: {lang_code}")

            # Create gTTS object
            tts = gTTS(text=text, lang=lang_code, slow=False)

            # Create cache directory if needed
            os.makedirs(settings.TTS_CACHE_DIR, exist_ok=True)

            # Save old audio file path BEFORE creating new one
            old_audio_file = self.current_audio_file

            # Save to temporary MP3 file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".mp3",
                delete=False,
                dir=settings.TTS_CACHE_DIR
            )

            # Generate and save audio
            tts.save(temp_file.name)
            logger.info(f"Audio saved: {temp_file.name}")

            # Update current audio file reference
            self.current_audio_file = temp_file.name

            # NOW delete the OLD audio file (after new one is ready)
            if old_audio_file and old_audio_file != temp_file.name and os.path.exists(old_audio_file):
                try:
                    os.unlink(old_audio_file)
                    logger.debug(f"Deleted old audio: {old_audio_file}")
                except Exception as e:
                    logger.warning(f"Failed to delete old audio file: {e}")

            return temp_file.name

        except ImportError:
            logger.error("gTTS library not installed")
            raise RuntimeError("gTTS library not found. Install with: pip install gtts")
        except Exception as e:
            logger.error(f"gTTS generation failed: {e}")
            raise RuntimeError(f"Failed to generate audio with gTTS: {e}")

    def _cleanup_current_audio(self):
        """Delete current cached audio file"""
        if self.current_audio_file and os.path.exists(self.current_audio_file):
            try:
                os.unlink(self.current_audio_file)
                logger.debug(f"Deleted previous audio: {self.current_audio_file}")
            except Exception as e:
                logger.warning(f"Failed to delete audio file: {e}")
            finally:
                self.current_audio_file = None

    def health_check(self) -> Dict[str, Any]:
        """Check TTS service health"""
        health = {
            "service": "TTSService",
            "status": "healthy",
            "provider": "Google TTS (gTTS)",
            "supported_languages": list(self.LANGUAGE_CODES.keys()),
        }

        # Check if gTTS is available
        try:
            import gtts
            health["gtts_version"] = gtts.__version__
        except ImportError:
            health["status"] = "degraded"
            health["warning"] = "gTTS library not installed"

        return health


# Singleton instance
_tts_service_instance = None

def get_tts_service() -> TTSService:
    """Get or create singleton TTSService instance"""
    global _tts_service_instance

    if _tts_service_instance is None:
        logger.info("Creating new TTSService instance")
        _tts_service_instance = TTSService()

    return _tts_service_instance


if __name__ == "__main__":
    # Self-test
    import sys
    from app.config import setup_logging

    setup_logging("INFO")

    print("\n" + "="*60)
    print("TTS SERVICE TEST (Google TTS - gTTS)")
    print("="*60)

    try:
        service = TTSService()

        # Health check
        print("\n[Test] Health check...")
        health = service.health_check()
        print(f"  Status: {health['status']}")
        print(f"  Provider: {health['provider']}")
        print(f"  Languages: {health['supported_languages']}")

        # Test generation for English
        print("\n[Test] Generating EN speech...")
        result = service.generate_speech(
            text="Hello, this is a test of the Google text to speech system.",
            language="EN"
        )
        print(f"  ✓ Audio file: {result['audio_path']}")
        print(f"  ✓ Duration: {result['duration_sec']}s")
        print(f"  ✓ Generation time: {result['generation_time_ms']}ms")

        # Test German
        print("\n[Test] Generating DE speech...")
        result = service.generate_speech(
            text="Hallo, dies ist ein Test des Google Text-to-Speech-Systems.",
            language="DE"
        )
        print(f"  ✓ Audio file: {result['audio_path']}")
        print(f"  ✓ Duration: {result['duration_sec']}s")
        print(f"  ✓ Generation time: {result['generation_time_ms']}ms")

        print("\n" + "="*60)
        print("✓ All tests passed!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
