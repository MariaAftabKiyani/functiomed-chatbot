"""
Setup script for Fish Speech 1.5 TTS
Downloads model weights and sets up reference voices
"""
import os
import sys
from pathlib import Path
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

try:
    from app.config import settings
except ImportError:
    print("Error: Could not import settings. Make sure you're running from the project root.")
    sys.exit(1)

def download_model():
    """Download Fish Speech 1.5 model from HuggingFace"""
    print("=" * 60)
    print("FISH SPEECH 1.5 SETUP")
    print("=" * 60)

    model_path = Path(settings.TTS_MODEL_PATH)

    if model_path.exists():
        print(f"✓ Model directory exists: {model_path}")
        choice = input("Re-download model? (y/n): ").lower()
        if choice != 'y':
            print("Skipping model download")
            return
    else:
        model_path.mkdir(parents=True, exist_ok=True)

    print(f"\nDownloading Fish Speech 1.5 to: {model_path}")
    print("This may take 10-30 minutes depending on your connection...")

    try:
        # Check if huggingface-cli is available
        result = subprocess.run(["huggingface-cli", "--version"], capture_output=True)
        if result.returncode != 0:
            print("\n⚠ huggingface-cli not found. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-U", "huggingface_hub[cli]"], check=True)

        # Download using huggingface-cli
        print("\nDownloading model files...")
        subprocess.run([
            "huggingface-cli",
            "download",
            "fishaudio/fish-speech-1.5",
            "--local-dir",
            str(model_path),
            "--local-dir-use-symlinks",
            "False"
        ], check=True)

        print("\n✓ Model downloaded successfully")

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Download failed: {e}")
        print("\nManual download instructions:")
        print("1. Install huggingface-cli: pip install -U huggingface_hub[cli]")
        print(f"2. Run: huggingface-cli download fishaudio/fish-speech-1.5 --local-dir {model_path}")
        print("\nAlternatively, the TTS service will use gTTS as a fallback.")
        return False

    return True

def setup_reference_voices():
    """Create reference voice directory and instructions"""
    print("\n" + "=" * 60)
    print("REFERENCE VOICE SETUP")
    print("=" * 60)

    ref_dir = Path(settings.TTS_REFERENCE_DIR)
    ref_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nReference voice directory: {ref_dir}")
    print("\nRequired files:")
    print("  - female_de.wav (German female voice, 10-30 seconds)")
    print("  - female_en.wav (English female voice, 10-30 seconds)")
    print("  - female_fr.wav (French female voice, 10-30 seconds)")

    print("\nReference voice requirements:")
    print("  • Duration: 10-30 seconds")
    print("  • Format: WAV, 44.1kHz, mono")
    print("  • Quality: Clear speech, no background noise")
    print("  • Content: Natural conversational speech")

    print("\nWhere to get reference voices:")
    print("  1. Record your own using professional microphone")
    print("  2. Use Fish Audio platform: https://fish.audio (voice library)")
    print("  3. Use royalty-free voice samples from voice actors")
    print("  4. Generate using TTS services and clone")

    # Check if files exist
    print("\nCurrent status:")
    for lang, filename in [("DE", "female_de.wav"), ("EN", "female_en.wav"), ("FR", "female_fr.wav")]:
        filepath = ref_dir / filename
        status = "✓ EXISTS" if filepath.exists() else "✗ MISSING"
        print(f"  {lang}: {status}")

    print("\n" + "=" * 60)

def setup_cache_directory():
    """Create TTS cache directory"""
    cache_dir = Path(settings.TTS_CACHE_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ TTS cache directory created: {cache_dir}")

def install_dependencies():
    """Install TTS dependencies"""
    print("\n" + "=" * 60)
    print("INSTALLING TTS DEPENDENCIES")
    print("=" * 60)

    print("\nInstalling required packages...")
    print("This may take a few minutes...\n")

    try:
        # Install gTTS for fallback
        subprocess.run([sys.executable, "-m", "pip", "install", "gTTS>=2.5.0"], check=True)
        print("✓ gTTS installed")

        # Install audio processing libraries
        subprocess.run([sys.executable, "-m", "pip", "install", "pydub>=0.25.1"], check=True)
        print("✓ pydub installed")

        print("\n✓ All dependencies installed")
        print("\n⚠ Note: You also need FFmpeg installed on your system:")
        print("  Windows: choco install ffmpeg")
        print("  Linux: sudo apt-get install ffmpeg")

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Installation failed: {e}")
        print("\nPlease install manually:")
        print("  pip install gTTS>=2.5.0 pydub>=0.25.1")
        return False

    return True

def test_tts_service():
    """Test the TTS service"""
    print("\n" + "=" * 60)
    print("TESTING TTS SERVICE")
    print("=" * 60)

    try:
        from app.services.tts_service import TTSService
        from app.config import setup_logging

        setup_logging("INFO")

        service = TTSService()

        # Health check
        print("\n[Test] Health check...")
        health = service.health_check()
        print(f"  Status: {health['status']}")
        print(f"  Models loaded: {health['models_loaded']}")
        print(f"  Reference voices: {health['reference_voices']}")

        # Test generation
        print("\n[Test] Generating test audio (EN)...")
        result = service.generate_speech(
            text="Hello, this is a test.",
            language="EN"
        )
        print(f"  ✓ Audio generated: {result['audio_path']}")
        print(f"  ✓ Duration: {result['duration_sec']}s")
        print(f"  ✓ Generation time: {result['generation_time_ms']}ms")

        print("\n✓ TTS service is working!")
        return True

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        print("\nThe TTS service will use gTTS as fallback.")
        return False

if __name__ == "__main__":
    print("\n")

    # Step 1: Install dependencies
    if not install_dependencies():
        print("\n⚠ Warning: Could not install all dependencies")

    # Step 2: Download model (optional, gTTS fallback available)
    print("\n")
    choice = input("Download Fish Speech 1.5 model? (~2GB, optional - gTTS fallback available) (y/n): ").lower()
    if choice == 'y':
        download_model()
    else:
        print("Skipping model download. TTS will use gTTS fallback.")

    # Step 3: Setup reference voices
    setup_reference_voices()

    # Step 4: Setup cache directory
    setup_cache_directory()

    # Step 5: Test TTS service
    print("\n")
    choice = input("Test TTS service now? (y/n): ").lower()
    if choice == 'y':
        test_tts_service()

    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. (Optional) Add reference voice files to:", settings.TTS_REFERENCE_DIR)
    print("2. Start API server: uvicorn app.main:app --reload")
    print("3. Open chatbot UI and test the speaker button")
    print("\nThe TTS service is ready to use with gTTS fallback!")
    print("Fish Speech 1.5 will be used automatically if models are downloaded.\n")
