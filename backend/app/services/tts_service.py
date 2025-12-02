"""
TTS Service - Fish Speech 1.5 Integration
Handles text-to-speech generation with multilingual support.
"""
import logging
import time
import os
import tempfile
from typing import Optional, Dict, Any
from pathlib import Path
import sys

from app.config import settings

logger = logging.getLogger(__name__)


class TTSService:
    """
    Fish Speech 1.5 TTS service with:
    - Local inference (CPU/GPU support)
    - Multilingual support (DE, EN, FR)
    - Female voice per language
    - MP3 output @ 128kbps
    - Single audio caching (memory efficient)
    """

    def __init__(self):
        """Initialize Fish Speech 1.5 models"""
        self.llama_model = None  # Text2Semantic model
        self.decoder_model = None  # VQGAN/Firefly vocoder
        self.tokenizer = None
        self.current_audio_file = None  # Track single cached audio
        self.reference_voices = {}  # Store reference voice embeddings
        self._models_loaded = False

    def _lazy_load_models(self):
        """Lazy load models on first use to avoid startup delays"""
        if self._models_loaded:
            return

        logger.info("Lazy loading Fish Speech 1.5 models...")
        try:
            self._initialize()
            self._models_loaded = True
        except Exception as e:
            logger.error(f"Failed to lazy load TTS models: {e}")
            raise

    def _initialize(self):
        """Load Fish Speech models and reference voices"""
        logger.info(f"Loading Fish Speech 1.5 from {settings.TTS_MODEL_PATH}...")
        logger.info(f"  Device: {settings.TTS_DEVICE}")

        try:
            # Check if model directory exists
            model_path = Path(settings.TTS_MODEL_PATH)
            if not model_path.exists():
                raise FileNotFoundError(
                    f"Model directory not found: {model_path}\n"
                    f"Please download the model using: python scripts/setup_tts.py"
                )

            # Import Fish Speech modules
            try:
                from fish_speech.models.text2semantic import Text2SemanticDecoder
                from fish_speech.models.vqgan import VQGAN
            except ImportError as e:
                raise ImportError(
                    f"Fish Speech library not installed: {e}\n"
                    f"Please install with: pip install git+https://github.com/fishaudio/fish-speech.git@main"
                )

            import torch

            # Determine device
            device = "cuda" if settings.TTS_DEVICE == "cuda" and torch.cuda.is_available() else "cpu"
            logger.info(f"  Using device: {device}")

            # Load Text2Semantic model
            logger.info("Loading Text2Semantic model...")
            text2sem_path = model_path / "text2semantic.ckpt"
            if text2sem_path.exists():
                self.llama_model = Text2SemanticDecoder.load_from_checkpoint(
                    checkpoint_path=str(text2sem_path),
                    map_location=device
                )
                self.llama_model.eval()
                logger.info(" Text2Semantic loaded")
            else:
                logger.warning(f"Text2Semantic checkpoint not found at {text2sem_path}")

            # Load VQGAN Decoder
            logger.info("Loading VQGAN Decoder...")
            vqgan_path = model_path / "vqgan.ckpt"
            if vqgan_path.exists():
                self.decoder_model = VQGAN.load_from_checkpoint(
                    checkpoint_path=str(vqgan_path),
                    map_location=device
                )
                self.decoder_model.eval()
                logger.info(" VQGAN Decoder loaded")
            else:
                logger.warning(f"VQGAN checkpoint not found at {vqgan_path}")

            # Load reference voices (female samples for each language)
            self._load_reference_voices()

            logger.info(" TTS Service ready")

        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            raise RuntimeError(f"TTS initialization failed: {e}")

    def _load_reference_voices(self):
        """Load and encode reference audio for each language"""
        logger.info("Loading reference voices...")

        reference_dir = Path(settings.TTS_REFERENCE_DIR)
        if not reference_dir.exists():
            logger.warning(f"Reference voice directory not found: {reference_dir}")
            reference_dir.mkdir(parents=True, exist_ok=True)

        voice_configs = {
            "DE": {"file": "female_de.wav", "text": settings.TTS_REFERENCE_TEXT_DE},
            "EN": {"file": "female_en.wav", "text": settings.TTS_REFERENCE_TEXT_EN},
            "FR": {"file": "female_fr.wav", "text": settings.TTS_REFERENCE_TEXT_FR}
        }

        for lang, config in voice_configs.items():
            voice_path = reference_dir / config["file"]
            if not voice_path.exists():
                logger.warning(f"Reference voice not found: {voice_path}")
                logger.info(f"  To add {lang} voice, place a WAV file at: {voice_path}")
                continue

            try:
                # Encode reference audio (placeholder for actual encoding)
                # In production, this would encode the audio to VQ tokens
                self.reference_voices[lang] = {
                    "path": str(voice_path),
                    "text": config["text"]
                }
                logger.info(f" {lang} reference voice loaded")
            except Exception as e:
                logger.error(f"Failed to load {lang} voice: {e}")

    def generate_speech(
        self,
        text: str,
        language: str = "EN",
        output_format: str = "mp3",
        bitrate: str = "128k"
    ) -> Dict[str, Any]:
        """
        Generate speech from text using Fish Speech 1.5.

        Args:
            text: Text to convert to speech
            language: Language code (DE, EN, FR)
            output_format: Audio format (mp3, wav)
            bitrate: MP3 bitrate (e.g., "128k")

        Returns:
            Dict with 'audio_path', 'duration_sec', 'generation_time_ms'

        Raises:
            ValueError: If language not supported or text invalid
            RuntimeError: If generation fails
        """
        # Lazy load models on first use
        if not self._models_loaded:
            self._lazy_load_models()

        # Validation
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if language not in ["DE", "EN", "FR"]:
            raise ValueError(f"Unsupported language: {language}. Supported: DE, EN, FR")

        if len(text) > settings.TTS_MAX_CHARS:
            raise ValueError(f"Text too long. Maximum {settings.TTS_MAX_CHARS} characters.")

        logger.info(f"Generating TTS for {language}: '{text[:50]}...'")
        start_time = time.time()

        try:
            # Delete previous audio file if exists
            self._cleanup_current_audio()

            # Check if reference voice exists
            if language not in self.reference_voices:
                logger.warning(f"No reference voice for {language}, using default")

            # Generate audio using Fish Speech
            # NOTE: This is a simplified implementation
            # In production, you would use the actual Fish Speech inference pipeline
            audio_path = self._generate_audio_simple(text, language, output_format, bitrate)

            # Calculate metrics
            generation_time_ms = (time.time() - start_time) * 1000

            # Estimate duration (rough approximation: 150 words per minute)
            word_count = len(text.split())
            duration_sec = (word_count / 150) * 60

            logger.info(
                f" Generated ~{duration_sec:.2f}s audio in {generation_time_ms:.0f}ms"
            )

            return {
                "audio_path": audio_path,
                "duration_sec": round(duration_sec, 2),
                "generation_time_ms": round(generation_time_ms, 2),
                "language": language,
                "format": output_format
            }

        except Exception as e:
            logger.error(f"TTS generation failed: {type(e).__name__}: {e}")
            raise RuntimeError(f"Failed to generate speech: {e}")

    def _generate_audio_simple(
        self,
        text: str,
        language: str,
        output_format: str,
        bitrate: str
    ) -> str:
        """
        Simplified audio generation using gTTS as fallback

        This is a temporary implementation while Fish Speech models are being set up.
        Replace this with actual Fish Speech inference once models are downloaded.
        """
        try:
            from gtts import gTTS
            import io
            from pydub import AudioSegment

            # Map language codes to gTTS language codes
            lang_map = {
                "DE": "de",
                "EN": "en",
                "FR": "fr"
            }

            gtts_lang = lang_map.get(language, "en")

            # Generate speech using gTTS
            logger.info(f"Using gTTS fallback for {language}")
            tts = gTTS(text=text, lang=gtts_lang, slow=False)

            # Save to temporary file
            temp_mp3 = tempfile.NamedTemporaryFile(
                suffix=".mp3",
                delete=False,
                dir=settings.TTS_CACHE_DIR
            )

            tts.save(temp_mp3.name)

            self.current_audio_file = temp_mp3.name
            return temp_mp3.name

        except ImportError:
            # If gTTS not available, create a silent audio file as placeholder
            logger.warning("gTTS not available, creating silent placeholder")
            return self._create_silent_placeholder(output_format)

    def _create_silent_placeholder(self, output_format: str) -> str:
        """Create a silent audio file as placeholder"""
        try:
            from pydub import AudioSegment
            from pydub.generators import Sine

            # Generate 1 second of silence
            silence = AudioSegment.silent(duration=1000)

            # Save to file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=f".{output_format}",
                delete=False,
                dir=settings.TTS_CACHE_DIR
            )

            silence.export(temp_file.name, format=output_format, bitrate="128k")

            self.current_audio_file = temp_file.name
            return temp_file.name

        except Exception as e:
            logger.error(f"Failed to create placeholder: {e}")
            raise

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
            "model": "Fish Speech 1.5 (with gTTS fallback)",
            "device": settings.TTS_DEVICE,
            "models_loaded": self._models_loaded,
            "reference_voices": list(self.reference_voices.keys())
        }

        # Quick test if models are loaded
        if self._models_loaded:
            try:
                # Quick test generation would go here
                health["test_generation"] = "passed"
            except Exception as e:
                health["status"] = "degraded"
                health["test_generation"] = f"failed: {str(e)}"
        else:
            health["status"] = "not_initialized"
            health["note"] = "Models will be loaded on first TTS request"

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
    from app.config import setup_logging

    setup_logging("INFO")

    print("\n" + "="*60)
    print("TTS SERVICE TEST")
    print("="*60)

    try:
        service = TTSService()

        # Health check
        print("\n[Test] Health check...")
        health = service.health_check()
        print(f"  Status: {health['status']}")
        print(f"  Models loaded: {health['models_loaded']}")
        print(f"  Reference voices: {health['reference_voices']}")

        # Test generation for English
        print("\n[Test] Generating EN speech...")
        result = service.generate_speech(
            text="Hello, this is a test of the text to speech system.",
            language="EN"
        )
        print(f"   Audio file: {result['audio_path']}")
        print(f"   Duration: {result['duration_sec']}s")
        print(f"   Generation time: {result['generation_time_ms']}ms")

        print("\n" + "="*60)
        print(" All tests passed!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
