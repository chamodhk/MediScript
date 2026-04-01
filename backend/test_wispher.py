from services.whisper_service import WhisperService
import urllib.request

# Download a small sample audio file for testing
print("Downloading test audio...")
urllib.request.urlretrieve(
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
    "temp/test_audio.mp3"
)

# Test transcription
service = WhisperService()
result = service.transcribe("temp/test_audio.mp3")

print("Result:", result)
print("Audio deleted:", not __import__('os').path.exists("temp/test_audio.mp3"))