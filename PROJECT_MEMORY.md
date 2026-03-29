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

<<<<<<< Updated upstream
=======
## Changelog

- **2026-03-29:** Init only (no feature logic). Backend scaffold: `routers/`, `controllers/`, `services/`, `core/`, Alembic async, stubs + `main.py`, `.env`, `requirements.txt`.
- **2026-03-29:** Frontend scaffold: Vite React, Tailwind v3, react-router-dom, axios, fabric; pages/components/hooks + `api.js`; `frontend/.env`.
- **2026-03-29:** Root `README.md` + `PROJECT_MEMORY.md` updated (startup, ports, libs, env vars).
- **2026-03-29:** DB models: Patient, Consultation, Prescription, Pharmacy, Reminder + User + Appointment. Pharmacies + 5 users seeded.
- **2026-03-29:** Demo simplification: Appointment model removed, receptionist role removed. Patient.token restored (pre-seeded). Migration reset to `3ea0854ac8ee_001_initial_schema`. 3 demo patients seeded (T001/T002/T003).
- **2026-03-29:** `UserRole` enum (`models/enums.py`). Prescription stores `image_data` (BLOB) + `image_mime_type`; migration `23de54475b85`.
- **2026-03-29:** `ConsultationStatus`, `ReminderType`, `ReminderStatus` enums; migration `60eabfecebca`.
- **2026-03-29:** Database: models defined, migration `8950a33e1831_001_initial_schema` generated + applied, pharmacies seeded.

---

>>>>>>> Stashed changes
## Running the Project

### Startup order (run in this exact order)



### Ports


---

## Architecture

- **Pattern:** Layered MVC — routers → controllers → services

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
| admin@mediscript.lk | Admin@1234 | admin |
| doctor@mediscript.lk | Doctor@1234 | doctor |
| pharmacy1@mediscript.lk | Pharma@1234 | pharmacist |
| pharmacy2@mediscript.lk | Pharma@1234 | pharmacist |

Demo patients (pre-seeded with tokens):

| name | phone | language | token |
|---|---|---|---|
| Kamal Perera | 0771234567 | Sinhala | T001 |
| Nimal Silva | 0779876543 | Sinhala | T002 |
| Amara Fernando | 0712345678 | Tamil | T003 |

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

<<<<<<< Updated upstream
### Frontend 
=======
(see `backend/requirements.txt`) FastAPI, uvicorn, SQLAlchemy[asyncio], aiosqlite, pydantic, pydantic-settings, python-multipart, alembic, apscheduler, twilio, openai-whisper, httpx, python-dotenv, passlib[bcrypt], python-jose[cryptography].

### Frontend

(see `frontend/package.json`) react, react-dom, vite; react-router-dom, axios, fabric; dev: tailwindcss@3, postcss, autoprefixer, eslint.
>>>>>>> Stashed changes

---




## Environment Variables (`.env`)



---

## MCP Servers 


