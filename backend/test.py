# test_setup.py

print("Testing Whisper...")
import whisper
model = whisper.load_model("small")
print(" Whisper loaded successfully!")

print("\nTesting Ollama...")
import ollama
response = ollama.chat(
    model="phi3",
    messages=[{"role": "user", "content": "say hello in one word"}]
)
print("Ollama response:", response["message"]["content"])

print("\n All good! Ready to start coding.")
