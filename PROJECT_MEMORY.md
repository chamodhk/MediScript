# MediScript — Project Memory

> Update this file every time you finish a feature, add an endpoint, change the DB, install a library, or make a technical decision.
> Rule: Before starting work each day — read this file top to bottom first.

---

## Team

| Person | Domain | Slices |
|---|---|---|
| Person A | Setup + Pharmacy portal | Auth, DB, Migrations, Pharmacy routing |
| Person B | Full AI / ML pipeline | Whisper transcription, Ollama NLP structuring |
| Person C | Full doctor experience | Doctor portal UI flow, Prescription canvas |
| Person D | Notifications pipeline | Translation, WhatsApp, Reminders |

---

## How to Update This File

1. Pull latest `main` before editing
2. Add your update under the correct section
3. Always include the date
4. Commit with message: `docs: update project memory`
5. Push immediately — don't batch updates

---


## Running the Project

### Startup order (run in this exact order)

1. LibreTranslate 
2. Ollama 
3. Backend: `cd backend && pip install -r requirements.txt && alembic upgrade head && uvicorn main:app --reload --port 8000`
4. Frontend: `cd frontend && npm install && npm run dev`

### Ports

| Service | Port |
|---------|------|
| Frontend (Vite) | 5173 |
| Backend (FastAPI) | 8000 |
| Ollama | 11434 |
| LibreTranslate | 5000 |

---

## Architecture

- **Pattern:** Layered MVC — routers → controllers → services

---

## Database

### Current tables



### Running migrations



### ⚠️ Migration rules
- Never edit an existing file inside `migrations/versions/`
- Always generate a new migration file for every model change
- Always run `alembic upgrade head` after every `git pull`

### Seeding

---

## API Endpoints

### Authorization


---

### Patients 

---

### Transcription

---

### NLP Structuring

---

### Prescription

---

### Consultation

---

### Pharmacy 

---

### Translation 

---

### Notifications 

---

## Installed Libraries

### Backend

(see `backend/requirements.txt`) FastAPI, uvicorn, SQLAlchemy[asyncio], aiosqlite, pydantic, pydantic-settings, python-multipart, alembic, apscheduler, twilio, openai-whisper, httpx, python-dotenv.

### Frontend

(see `frontend/package.json`) react, react-dom, vite; react-router-dom, axios, fabric; dev: tailwindcss@3, postcss, autoprefixer, eslint.

---




## Environment Variables (`.env`)

**Backend** (`backend/.env`): `DATABASE_URL`, `CORS_ORIGINS`, Twilio (`TWILIO_*`), `WHISPER_MODEL`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `LIBRETRANSLATE_URL`, `APP_ENV`.

**Frontend** (`frontend/.env`): `VITE_API_BASE_URL` (default `http://localhost:8000/api`).

---

## MCP Servers 


