# MediScript — Tech Stack

## Frontend

- Framework: React 18 + Vite
- Routing: React Router v6
- Styling: Tailwind CSS v3
- Canvas: Fabric.js
- HTTP Client: Axios
- State: useState / custom hooks (no Redux)

## Backend

- Framework: Python FastAPI
- Server: Uvicorn
- ORM: SQLAlchemy (async)
- Database: SQLite (aiosqlite)
- Validation: Pydantic v2
- File Uploads: python-multipart

## AI / ML (all local, no data leaves machine)

- Speech-to-Text: OpenAI Whisper — `small` model (local)
- NLP Structuring: Ollama — `meditron:7b` model
- Ollama Runtime: localhost:11434
- Translation: LibreTranslate — localhost:5000
- Languages: English, Sinhala (`si`), Tamil (`ta`)

## Notifications

- WhatsApp: Twilio WhatsApp Sandbox (free)
- SMS fallback: Twilio SMS
- Scheduler: APScheduler (in-process, FastAPI)

## Infrastructure

- Deployment: localhost only
- Ports: Frontend :5173 · Backend :8000 · Ollama :11434 · LibreTranslate :5000
- Image Storage: `backend/static/prescriptions/` (PNG files)
- Auth: None (MVP)
