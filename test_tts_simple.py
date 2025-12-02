"""
Simple TTS test using gTTS fallback
"""
import tempfile
from gtts import gTTS

# Test TTS generation
text = "Hello, this is a test of the text to speech system."
language = "en"

print("Generating audio with gTTS...")
tts = gTTS(text=text, lang=language, slow=False)

# Save to temporary file
temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
tts.save(temp_file.name)

print(f"[SUCCESS] Audio saved to: {temp_file.name}")
print("[SUCCESS] TTS is working!")
print("\nYou can play this file to verify audio was generated correctly.")
