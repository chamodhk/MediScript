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



### Ports


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

### Frontend 

---




## Environment Variables (`.env`)



---

## MCP Servers 


