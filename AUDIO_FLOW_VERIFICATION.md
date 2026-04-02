# Audio Recording Flow Verification

## Current Audio Flow

### ✅ Frontend → Backend Flow (ACTIVE)

```
1. Doctor starts recording
   └─> MediScriptDashboard.jsx: startRecording()
   └─> useAudioRecorder hook: MediaRecorder starts capturing

2. Doctor stops recording
   └─> MediScriptDashboard.jsx: stopRecording()
   └─> useAudioRecorder hook: Creates audioBlob on onstop event

3. Frontend detects audioBlob is ready
   └─> useEffect hook triggers automatically
   └─> Calls sendAudioToBackend(audioBlob)
   └─> FormData sent to: POST /transcription/transcribe/{consultationId}

4. Backend receives audio
   └─> transcription_router.py: POST /transcribe/{consultation_id}
   └─> Calls TranscriptionController.process_audio()
```

### 📊 Database Storage Process

**Step-by-step in Consultation Table:**

```
STEP 1: Audio Saved to Temp
├─ Controller saves audio bytes to: backend/temp/audio_{consultationId}_{uuid}.wav
├─ audio_file_path = "backend/temp/audio_123_abc123.wav"
├─ Consultation status = IN_PROGRESS
└─ Database updated ✓

STEP 2: Whisper Transcription
├─ Reads audio from audio_file_path
├─ Transcribes to text
├─ Deletes the audio file from disk
├─ consultation.transcript = "raw text here"
├─ consultation.audio_file_path = None (cleared)
├─ Consultation status = TRANSCRIBED
└─ Database updated ✓

STEP 3: Ollama Structuring  
├─ Processes raw_transcript through LLM
├─ Creates structured JSON output
├─ consultation.structured_output = {...structured json...}
├─ Consultation status = STRUCTURED
└─ Database updated ✓
```

---

## Current Implementation Details

### Frontend (MediScriptDashboard.jsx)
- **Audio Hook**: `useAudioRecorder()` (lines 615)
- **Recording Methods**: `startRecording()` / `stopRecording()`
- **Auto-send Logic**: `useEffect` on audioBlob (lines 702-706)
- **Endpoint**: `POST /transcription/transcribe/{consultationId}`
- **Format**: WebM audio blob wrapped in FormData

### Backend (TranscriptionController)
- **Audio Storage**: `backend/temp/` folder (temporary)
- **Database Field**: `consultations.audio_file_path` 
- **Current Behavior**: 
  - Path stored temporarily during processing
  - **Deleted after transcription** (audio_file_path set to NULL)
  - This is by design for privacy/storage

### Database (Consultation Model)
```python
# Audio field in consultation table
audio_file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

# This field contains:
# 1. Temp path during processing
# 2. NULL after transcription completes
# 3. Status updates: IN_PROGRESS → TRANSCRIBED → STRUCTURED
```

---

## ✅ What IS Working

- [x] Audio recorder captures microphone input
- [x] Audio blob created on stop recording
- [x] Automatic POST to backend with audio file
- [x] Backend receives and saves to temp folder
- [x] Audio path stored in consultation.audio_file_path
- [x] Whisper transcription processes the audio
- [x] Ollama structures the transcript
- [x] Consultation status updated through pipeline
- [x] Transcript stored in consultation.transcript
- [x] Structured output stored in consultation.structured_output

---

## 📝 How to Debug/Verify

### Option 1: Check Console Logs
1. Open browser DevTools (F12)
2. Check **Console tab** for:
   - `"Transcription successful: {response.data}"`
   - Error messages if upload fails

### Option 2: Check Backend Logs
1. Watch backend terminal for:
   - `"Raw transcript: ..."`
   - `"Structured output: ..."`

### Option 3: Database Query
Check if audio was stored in consultation:
```python
# In Python terminal
from backend.core.database import SessionLocal
from backend.models.consultation import Consultation

db = SessionLocal()
consultation = db.query(Consultation).filter(Consultation.id == 1).first()
print(f"Audio path: {consultation.audio_file_path}")
print(f"Transcript: {consultation.transcript}")
print(f"Structured: {consultation.structured_output}")
print(f"Status: {consultation.status}")
```

---

## 🔍 Key Consultation Statuses During Flow

```
IDLE → IN_PROGRESS (audio being processed)
     → TRANSCRIBED (transcript complete)
     → STRUCTURED (final output ready)
```

---

## 📌 Important Notes

1. **Audio File Cleanup**: Audio files are deleted after transcription (not kept)
   - This is by design for privacy/storage optimization
   - Only transcript and structured output are permanently stored

2. **Consultation ID Required**: 
   - Must create consultation FIRST via `/consultations` endpoint
   - Only then can audio be uploaded to that consultation_id

3. **Status Flow**:
   - Doctor loads patient → Creates new consultation (status=IN_PROGRESS)
   - Doctor records audio → Audio sent to backend
   - Backend processes → Status goes TRANSCRIBED → STRUCTURED

---

## To Enable Persistent Audio Storage (Optional)

If you want to **keep the audio file** instead of deleting it:

Edit `backend/controllers/transcription_controller.py` line 47-48:
```python
# CURRENT (deletes audio after transcription):
consultation.transcript = raw_text
consultation.audio_file_path = None  # ← This deletes the path

# CHANGE TO (keeps audio):
consultation.transcript = raw_text
# consultation.audio_file_path = audio_path  # ← Keep the path
```

Then move the audio from temp to permanent storage directory.
