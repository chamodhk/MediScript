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

## Changelog

- **2026-03-29:** Init only (no feature logic). Backend scaffold: `routers/`, `controllers/`, `services/`, `core/`, Alembic async, stubs + `main.py`, `.env`, `requirements.txt`.
- **2026-03-29:** Frontend scaffold: Vite React, Tailwind v3, react-router-dom, axios, fabric; pages/components/hooks + `api.js`; `frontend/.env`.
- **2026-03-29:** Root `README.md` + `PROJECT_MEMORY.md` updated (startup, ports, libs, env vars).
- **2026-03-29:** Demo simplification: receptionist removed; Patient.token pre-seeded. Migrations `3ea0854ac8ee` → `23de54475b85` → `60eabfecebca`. 3 demo patients (T001–T003), 4 users, 2 pharmacies seeded.
- **2026-03-29:** Demystifying theme: Hemas Healthcare brand colors integrated into Tailwind (`tailwind.config.js`) and CSS variables (`src/index.css`).
- **2026-03-29:** UserRole, `ConsultationStatus`, `ReminderType`, `ReminderStatus` enums; prescription `image_data` + `image_mime_type`.
- **2026-03-29:** Auth MVP completed. Login-only JWT auth added (`POST /api/auth/login`, `GET /api/auth/me`), signup removed, role-based `redirectPath` returned (admin/doctor/pharmacist paths).
- **2026-03-29:** Seed data updated to 5 demo auth users with `.com` emails and shared password `password@123` (admin, doctor1, doctor2, pharmacy1, pharmacy2). Non-demo users are removed during re-seed.
- **2026-03-29:** Frontend login implemented with Tailwind-styled form, token storage, and route redirects using backend `redirectPath`. Added `/admin` route/page and protected route wrapper.
- **2026-03-29:** Frontend toolchain stabilized after broken `node_modules` state: `react-router` (v7 package), `vite@5.4.21`, `@vitejs/plugin-react@4.3.4`; production build confirmed.
- **2026-03-29:** Root `.gitignore` updated to ignore `frontend/node_modules/` and stop tracking dependency tree.

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

## Frontend Theme

**Mandatory:** Use Hemas Healthcare brand colors for all UI components.

| Type | Tailwind Classes | Hex |
|---|---|---|
| **Primary** | `bg-hemas-teal`, `text-hemas-teal` | `#025567` |
| **Accent** | `bg-hemas-orange`, `text-hemas-orange` | `#e75424` |
| **Surface** | `bg-hemas-navy`, `bg-hemas-dark` | `#112023`, `#081c20` |

See detailed palette in`tailwind.config.js`.

---

## Database

### Current tables

| Table | Key columns |
|---|---|
| `users` | id, email (unique), password_hash, full_name, role (`UserRole` enum: admin/doctor/pharmacist), is_active |
| `patients` | id, name, phone (unique), preferred_language, date_of_birth, age, token (unique, pre-seeded) |
| `consultations` | id, patient_id (FK), doctor_id (FK → users), transcript, structured_output (JSON), audio_file_path, status (`ConsultationStatus`) |
| `prescriptions` | id, consultation_id (FK, unique), pharmacy_id (FK), image_path (optional), image_data (BLOB), image_mime_type (default `image/png`), status |
| `pharmacies` | id, name, is_available |
| `reminders` | id, patient_id (FK), consultation_id (FK), message, scheduled_at, sent_at, type (`ReminderType`), status (`ReminderStatus`) |

**DB file:** `backend/mediscript.db`

### Running migrations

```bash
# From backend/ directory (use miniconda3 Python until venv is set up)
/home/rumeshchathuranga/miniconda3/bin/alembic revision --autogenerate -m "describe_change"
/home/rumeshchathuranga/miniconda3/bin/alembic upgrade head
```

Migrations: `3ea0854ac8ee` → `23de54475b85` (role + prescription image) → `60eabfecebca` (`ConsultationStatus`, `ReminderType`, `ReminderStatus` enums)

### ⚠️ Migration rules
- Never edit an existing file inside `migrations/versions/`
- Always generate a new migration file for every model change
- Always run `alembic upgrade head` after every `git pull`

### Seeding

Run `python -m core.seed` from `backend/`. Idempotent (safe to re-run).

Seeds: Pharmacy 1, Pharmacy 2, and 5 default users:

| email | password | role |
|---|---|---|
| admin@mediscript.com | password@123 | admin |
| doctor1@mediscript.com | password@123 | doctor |
| doctor2@mediscript.com | password@123 | doctor |
| pharmacy1@mediscript.com | password@123 | pharmacist |
| pharmacy2@mediscript.com | password@123 | pharmacist |

Demo patients (pre-seeded with tokens):

| name | phone | language | token |
|---|---|---|---|
| Kamal Perera | 0771234567 | Sinhala | T001 |
| Nimal Silva | 0779876543 | Sinhala | T002 |
| Amara Fernando | 0712345678 | Tamil | T003 |

---

## API Endpoints

### Authorization

- `POST /api/auth/login` (form-data: `username` as email, `password`) → returns `access_token`, `token_type`, `role`, `redirectPath`
- `GET /api/auth/me` (Bearer token) → returns current user profile (`id`, `email`, `full_name`, `role`, `is_active`)

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

(see `backend/requirements.txt`) FastAPI, uvicorn, SQLAlchemy[asyncio], aiosqlite, pydantic, pydantic-settings, python-multipart, alembic, apscheduler, twilio, openai-whisper, httpx, python-dotenv, passlib[bcrypt], python-jose[cryptography].

### Frontend

(see `frontend/package.json`) react, react-dom, react-router, axios, fabric; dev: vite@5.4.21, @vitejs/plugin-react@4.3.4, tailwindcss@3, postcss, autoprefixer, eslint.

---




## Environment Variables (`.env`)

**Backend** (`backend/.env`): `DATABASE_URL`, `CORS_ORIGINS`, Twilio (`TWILIO_*`), `WHISPER_MODEL`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `LIBRETRANSLATE_URL`, `APP_ENV`.

**Frontend** (`frontend/.env`): `VITE_API_BASE_URL` (default `http://localhost:8000/api`).

---

## MCP Servers 


