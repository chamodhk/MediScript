# 🎤 Audio Recording Debug Guide

## Quick Verification Steps

### Step 1️⃣ Check Frontend Console Logs
1. Start your app: select patient, click "Start Recording"
2. Record something, then "Stop Recording"
3. Open DevTools: **F12 → Console tab**
4. You should see logs like:

```
🎙️ RECORDING STARTED - Requesting microphone access...
✅ Microphone access granted {audioTracks: 1, deviceName: "Built-in Microphone"}
▶️ MediaRecorder started
🛑 RECORDING STOPPED {audioFormat: "audio/webm", audioSize: "250.45 KB", chunks: 10, ...}
📤 Sending audio to backend...
🎤 AUDIO UPLOAD STARTED {consultationId: 1, audioFormat: "audio/webm", audioSize: "0.24 MB", ...}
```

---

### Step 2️⃣ Check Backend Logs
Watch your backend terminal for:

```
============================================================
🎤 [STEP 1] Consultation Found
   Consultation ID: 1
   Patient ID: 5
   Doctor ID: 1
   Current Status: IN_PROGRESS
============================================================

💾 [STEP 2] Audio Saved to Temp
   Path: /path/to/backend/temp/audio_1_abc123xyz.wav
   Size: 250.45 KB

📝 [STEP 3] Audio Path Saved to Database
   consultation.audio_file_path = /path/to/backend/temp/audio_1_abc123xyz.wav
   consultation.status = IN_PROGRESS

⏳ [STEP 4] Transcription In Progress...
✅ Transcription Complete!
   Length: 245 characters
   Preview: "The patient presents with complaints of..."

📚 [STEP 5] Transcript Stored in Database
   consultation.transcript = 'The patient presents with complaints of...'
   consultation.audio_file_path = None (audio deleted)
   consultation.status = TRANSCRIBED

🤖 [STEP 6] Structuring With Ollama...
✅ Structuring Complete!
   Output Type: <class 'dict'>
   Output Keys: ['chief_complaint', 'history', 'vitals', ...]

✨ [STEP 7] Structured Output Saved to Database
   consultation.structured_output = {'chief_complaint': '...', 'history': '...', ...}
   consultation.status = STRUCTURED

🎉 [STEP 8] Returning Response to Frontend

✅ BACKEND RESPONSE RECEIVED {status: 200, hasTranscript: true, transcriptLength: 245, ...}
✨ Transcription successful
📝 Raw Transcript: "The patient presents with complaints of..."
📊 Structured Output: {chief_complaint: "...", history: "...", ...}
```

---

### Step 3️⃣ Verify Data in Database

Run this in Python to check what's stored:

```python
from backend.core.database import SessionLocal
from backend.models.consultation import Consultation
from backend.models.enums import ConsultationStatus

# Create session
db = SessionLocal()

# Get the latest consultation
consultation = db.query(Consultation).order_by(Consultation.id.desc()).first()

# Print all audio/transcript data
print(f"Consultation ID: {consultation.id}")
print(f"Patient ID: {consultation.patient_id}")
print(f"Doctor ID: {consultation.doctor_id}")
print(f"Status: {consultation.status}")
print(f"\n--- AUDIO FILE ---")
print(f"audio_file_path: {consultation.audio_file_path}")
print(f"   Note: Should be NULL after processing (file was deleted)")
print(f"\n--- TRANSCRIPTION ---")
print(f"transcript: {consultation.transcript[:200] if consultation.transcript else 'NO TRANSCRIPT'}")
print(f"\n--- STRUCTURED OUTPUT ---")
print(f"structured_output: {consultation.structured_output}")

db.close()
```

---

## 🔍 Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND (Browser)                                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ useAudioRecorder Hook                                  │ │
│  │ • startRecording()  → 🎙️ RECORDING STARTED           │ │
│  │ • stopRecording()   → 🛑 RECORDING STOPPED            │ │
│  │ • Creates audioBlob → 📦 WebM audio file created      │ │
│  └────────────────────────────────────────────────────────┘ │
│  ▼                                                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ MediScriptDashboard.jsx                                │ │
│  │ • detectAudioBlob (useEffect)                          │ │
│  │ • sendAudioToBackend()                                 │ │
│  │ • POST /transcription/transcribe/{consultationId}      │ │
│  │ • FormData with audio blob → 📤 AUDIO UPLOAD STARTED │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP POST (FormData with WebM audio)
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  BACKEND (FastAPI)                                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ transcription_router.py                                │ │
│  │ POST /transcribe/{consultation_id}                     │ │
│  │ • Receives UploadFile (audio blob)                    │ │
│  │ • Calls TranscriptionController.process_audio()       │ │
│  └────────────────────────────────────────────────────────┘ │
│  ▼                                                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ TranscriptionController                                │ │
│  │                                                         │ │
│  │ [STEP 1] Get consultation from DB                     │ │
│  │ 🎤 Consultation Found                                  │ │
│  │                                                         │ │
│  │ [STEP 2] Save audio to temp folder                    │ │
│  │ 💾 backend/temp/audio_{id}_{uuid}.wav                │ │
│  │                                                         │ │
│  │ [STEP 3] Update DB: audio_file_path                   │ │
│  │ 📝 status = IN_PROGRESS                               │ │
│  │                                                         │ │
│  │ [STEP 4] Whisper transcription                        │ │
│  │ ⏳ Processing audio...                                │ │
│  │ ✅ raw_text = "patient's words..."                    │ │
│  │                                                         │ │
│  │ [STEP 5] Update DB: transcript                        │ │
│  │ 📚 status = TRANSCRIBED                               │ │
│  │ 🗑️ audio_file_path = NULL (file deleted)            │ │
│  │                                                         │ │
│  │ [STEP 6] Ollama structuring (LLM)                     │ │
│  │ 🤖 Processing transcript...                           │ │
│  │ ✅ structured = {...JSON...}                         │ │
│  │                                                         │ │
│  │ [STEP 7] Update DB: structured_output                │ │
│  │ ✨ status = STRUCTURED                                │ │
│  │                                                         │ │
│  │ [STEP 8] Return to frontend                           │ │
│  │ 🎉 Response with transcript + structured data        │ │
│  └────────────────────────────────────────────────────────┘ │
│                      ▼                                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ DATABASE (SQLite/PostgreSQL)                           │ │
│  │ ┌──────────────────────────────────────────────────┐  │ │
│  │ │ consultations table                              │  │ │
│  │ ├──────────────────────────────────────────────────┤  │ │
│  │ │ id: 1                                            │  │ │
│  │ │ patient_id: 5                                    │  │ │
│  │ │ doctor_id: 1                                     │  │ │
│  │ │ status: STRUCTURED                              │  │ │
│  │ │ audio_file_path: NULL ✓ (deleted after use)     │  │ │
│  │ │ transcript: "patient's words..." ✓              │  │ │
│  │ │ structured_output: {...JSON...} ✓              │  │ │
│  │ │ created_at: 2024-01-15 10:30:00                │  │ │
│  │ └──────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
                       │
                       │ HTTP Response
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  FRONTEND (Browser)                                          │
│  • Receives {transcript, structured}                       │ │
│  ✅ BACKEND RESPONSE RECEIVED                              │ │
│  • Displays results to doctor                             │ │
└────────────────────────────────────────────────────────────┘
```

---

## ❓ Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "audioData or consultationId missing" | No consultation created | Select patient first to create consultation |
| No backend logs shown | Backend not running | Ensure `python main.py` is running in backend |
| "Consultation not found" error | Wrong consultation ID | Check console for correct consultationId value |
| Audio file not saved | Incorrect temp folder path | Check `backend/temp/` exists, create if needed |
| Whisper transcription fails | Model not loaded | Check internet, first run may take time |
| Empty audio blob | Microphone not recording | Check browser permissions (Settings > Privacy) |

---

## 📊 What Gets Stored Where

| Data | Location | When | Status |
|------|----------|------|--------|
| **audio_file_path** | `consultations.audio_file_path` | During processing | ❌ Deleted after done |
| **raw_transcript** | `consultations.transcript` | After Whisper | ✅ Permanent |
| **structured_output** | `consultations.structured_output` | After Ollama | ✅ Permanent |
| **status** | `consultations.status` | Throughout flow | ✅ Permanent |

---

## 🛠️ Test the Entire Flow

```python
# backend/test_audio_flow.py

import asyncio
from pathlib import Path
from backend.core.database import SessionLocal
from backend.models.consultation import Consultation
from backend.controllers.transcription_controller import TranscriptionController

async def test_audio_flow():
    # Get sample audio (or create one from actual mic)
    # This assumes you have a test WAV file
    test_audio_path = "backend/test_audio.wav"
    
    with open(test_audio_path, "rb") as f:
        audio_bytes = f.read()
    
    db = SessionLocal()
    controller = TranscriptionController()
    
    # Create a test consultation
    consultation_id = 1  # Adjust to existing consultation
    
    # Process audio
    result = await controller.process_audio(
        audio_bytes=audio_bytes,
        consultation_id=consultation_id,
        db=db
    )
    
    print("\n✅ TEST RESULT:")
    print(f"Transcript: {result['raw_transcript']}")
    print(f"Structured: {result['structured']}")
    
    # Verify DB
    consultation = db.query(Consultation).filter(
        Consultation.id == consultation_id
    ).first()
    
    print(f"\n📚 DATABASE STATE:")
    print(f"Stored Transcript: {consultation.transcript}")
    print(f"Stored Structured: {consultation.structured_output}")
    print(f"Status: {consultation.status}")
    print(f"Audio Path: {consultation.audio_file_path}")
    
    db.close()

# Run test
if __name__ == "__main__":
    asyncio.run(test_audio_flow())
```

Run with: `python backend/test_audio_flow.py`
