# MediScript

AI-powered clinical communication system for Hemas Hospitals.

---

## Portals

| Portal | URL |
|---|---|
| Doctor Portal | http://localhost:5173/doctor |
| Pharmacy 1 | http://localhost:5173/pharmacy/1 |
| Pharmacy 2 | http://localhost:5173/pharmacy/2 |

---

## Ports

| Service | Port | Notes |
|---|---|---|
| Frontend (Vite) | 5173 | React 18 |
| Backend (FastAPI) | 8000 | Python |
| Ollama | 11434 | meditron:7b |
| LibreTranslate | 5000 | local instance |

---

## Startup Order

Start services in this exact order:

### 1. LibreTranslate (local)
```bash
libretranslate --host 0.0.0.0 --port 5000
```

### 2. Ollama
```bash
ollama serve
# In another terminal, pull the model if not already downloaded:
ollama pull meditron:7b
```

### 3. Backend
```bash
cd backend
pip install -r requirements.txt
# First time — run migrations:
alembic upgrade head
# Start the server:
uvicorn main:app --reload --port 8000
```

### 4. Frontend
```bash
cd frontend
npm install   # only needed first time
npm run dev
```

---

## Architecture

```
Layered MVC: routers → controllers → services
```

| Layer | Location | Responsibility |
|---|---|---|
| Routers | `backend/routers/` | HTTP routing, request parsing |
| Controllers | `backend/controllers/` | Business logic orchestration |
| Services | `backend/services/` | External integrations (Whisper, Ollama, Twilio) |
| Models | `backend/models/` | SQLAlchemy ORM definitions |
| Core | `backend/core/` | Config, DB engine, shared deps |

---

## Environment Variables

Copy and fill in `backend/.env`:

| Variable | Description |
|---|---|
| `DATABASE_URL` | SQLite async URL (default: `sqlite+aiosqlite:///./mediscript.db`) |
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_WHATSAPP_FROM` | WhatsApp sandbox number |
| `WHISPER_MODEL` | Whisper model size (`small`) |
| `OLLAMA_BASE_URL` | Ollama API endpoint |
| `OLLAMA_MODEL` | Ollama model name |
| `LIBRETRANSLATE_URL` | LibreTranslate endpoint |

---

## Team Slices

| Person | Domain |
|---|---|
| A | Setup, DB, Migrations, Pharmacy portal |
| B | Whisper transcription, Ollama NLP |
| C | Doctor portal UI, Prescription canvas |
| D | Translation, WhatsApp notifications, Reminders |

---

## Migration Rules

- **Never** edit files inside `migrations/versions/`
- Always generate a new file for every model change: `alembic revision --autogenerate -m "description"`
- Always run `alembic upgrade head` after every `git pull`
