# MediScript

AI-powered clinical communication system for Hemas Hospitals.

> **Windows only.** Run all commands in PowerShell unless stated otherwise.

---

## Quick Install (Windows)

Open PowerShell **as Administrator** and run:

```powershell
# If you haven't set execution policy yet:
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# Clone and install everything
git clone https://github.com/chamodhk/MediScript.git $env:USERPROFILE\MediScript
cd $env:USERPROFILE\MediScript
.\scripts\install_windows.ps1
```

The script installs Git, Node.js, ffmpeg, uv, Python 3.13, ngrok, runs migrations and seeds the database automatically.

---

## Step-by-Step Startup

Run each service in a **separate terminal**, in this order:

### 1. Install & start Ollama

**Install once:**
```powershell
winget install --id Ollama.Ollama --accept-package-agreements --accept-source-agreements
```
Close and reopen your terminal, then:

```powershell
ollama serve
```

**Pull a model (run once — pick one):**
```powershell
ollama pull phi3        # fast, lightweight — good for most machines
ollama pull qwen2:7b    # more accurate — needs a stronger machine
```

**Or use a cloud model (no GPU needed):**
```powershell
ollama login                        # opens browser to log in
ollama pull gpt-oss:120b-cloud
```

Then set `OLLAMA_MODEL` in `backend\.env` to match whichever model you pulled:
```
OLLAMA_MODEL=phi3
```

### 2. Backend API

```powershell
cd $env:USERPROFILE\MediScript\backend
.\.venv\Scripts\activate
python run.py
```

Or use the convenience script:
```powershell
.\scripts\start_backend.bat
```

API runs at **http://localhost:8000** — interactive docs at **http://localhost:8000/docs**

### 3. Frontend

```powershell
cd $env:USERPROFILE\MediScript\frontend
npm run dev
```

Or use the convenience script:
```powershell
.\scripts\start_frontend.bat
```

App runs at **https://localhost:5173** (accept the self-signed certificate warning)

### 4. ngrok (for Twilio WhatsApp webhook)

```powershell
ngrok http 8000
```

Or use the convenience script:
```powershell
.\scripts\start_ngrok.bat
```

Copy the `https://...ngrok-free.app` URL shown, then set it as your Twilio webhook:
- Twilio Console → Messaging → Try it out → Send a WhatsApp message → Sandbox Configuration
- **WHEN A MESSAGE COMES IN:** `https://<your-id>.ngrok-free.app/api/twilio/webhook`
- Method: **POST**

> ngrok free tier gives a new random URL every restart — update the Twilio webhook each time.

---

## Ports

| Service  | Port  | Notes              |
|----------|-------|--------------------|
| Frontend | 5173  | React 18 (Vite)    |
| Backend  | 8000  | Python (FastAPI)   |
| Ollama   | 11434 | Local AI model     |

---

## Portals

| Portal     | URL                            |
|------------|--------------------------------|
| Admin      | https://localhost:5173/admin   |
| Doctor     | https://localhost:5173/doctor  |
| Pharmacy 1 | https://localhost:5173/pharmacy/1 |
| Pharmacy 2 | https://localhost:5173/pharmacy/2 |

---

## Demo Credentials

| Email                       | Password     | Portal      |
|-----------------------------|--------------|-------------|
| admin@mediscript.com        | password@123 | /admin      |
| doctor1@mediscript.com      | password@123 | /doctor     |
| doctor2@mediscript.com      | password@123 | /doctor     |
| pharmacy1@mediscript.com    | password@123 | /pharmacy/1 |
| pharmacy2@mediscript.com    | password@123 | /pharmacy/2 |

---

## Environment Variables

Set in `backend\.env` (created automatically by the install script):

| Variable                    | Description                                          |
|-----------------------------|------------------------------------------------------|
| `DATABASE_URL`              | SQLite async URL (default: `sqlite+aiosqlite:///./mediscript.db`) |
| `CORS_ORIGINS`              | Comma-separated allowed origins                      |
| `JWT_SECRET_KEY`            | JWT signing secret                                   |
| `TWILIO_ACCOUNT_SID`        | Twilio account SID                                   |
| `TWILIO_AUTH_TOKEN`         | Twilio auth token                                    |
| `TWILIO_WHATSAPP_FROM`      | WhatsApp sandbox number                              |
| `WHISPER_MODEL`             | Whisper model size (`small`)                         |
| `OLLAMA_BASE_URL`           | Ollama API endpoint (`http://localhost:11434`)       |
| `OLLAMA_MODEL`              | Ollama model name (`phi3`, `qwen2:7b`, etc.)         |

---

## Architecture

```
Layered MVC: routers → controllers → services
```

| Layer       | Location             | Responsibility                                  |
|-------------|----------------------|-------------------------------------------------|
| Routers     | `backend/routers/`   | HTTP routing, request parsing                   |
| Controllers | `backend/controllers/` | Business logic orchestration                  |
| Services    | `backend/services/`  | External integrations (Whisper, Ollama, Twilio) |
| Models      | `backend/models/`    | SQLAlchemy ORM definitions                      |
| Core        | `backend/core/`      | Config, DB engine, shared deps                  |

---

## Migration Rules

- **Never** edit files inside `migrations/versions/`
- Generate a new migration for every model change:
  ```powershell
  cd backend
  .\.venv\Scripts\activate
  alembic revision --autogenerate -m "description"
  alembic upgrade head
  ```
- Always run `alembic upgrade head` after every `git pull`
