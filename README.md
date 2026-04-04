# MediScript — Installation Guide

AI-powered clinical communication system for Hemas Hospitals.

> **Windows 10 / 11 only.**

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Hardware & OS Requirements](#2-hardware--os-requirements)
3. [What Gets Installed](#3-what-gets-installed)
4. [Windows Installation](#4-windows-installation)
5. [Ollama Setup](#5-ollama-setup)
6. [Starting the Services](#6-starting-the-services)
7. [Twilio & ngrok Webhook Setup](#7-twilio--ngrok-webhook-setup)
8. [Environment Configuration Reference](#8-environment-configuration-reference)
9. [Demo Accounts & Test Data](#9-demo-accounts--test-data)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. System Overview

```
┌─────────────────────┐        HTTPS        ┌──────────────────────┐
│  React Frontend     │ ◄──────────────────► │  FastAPI Backend     │
│  Vite dev server    │      port 8000       │  port 8000           │
│  port 5173 (HTTPS)  │                      │                      │
└─────────────────────┘                      │  ┌───────────────┐   │
                                             │  │ SQLite DB     │   │
                                             │  └───────────────┘   │
                                             │  ┌───────────────┐   │
                                             │  │ Whisper       │   │
                                             │  │ (in-process)  │   │
                                             │  └───────────────┘   │
                                             │  ┌───────────────┐   │
                                             │  │ NLLB Model    │   │
                                             │  │ (in-process)  │   │
                                             │  └───────────────┘   │
                                             └──────────┬───────────┘
                                                        │
                              ┌─────────────────────────┼──────────────────┐
                              │                         │                  │
                    ┌─────────▼──────┐        ┌─────────▼──────┐  ┌───────▼──────┐
                    │ Ollama         │        │ ngrok tunnel   │  │ Twilio       │
                    │ phi3 / qwen2   │        │ → public HTTPS │  │ WhatsApp API │
                    │ port 11434     │        │ port 8000      │  │              │
                    └────────────────┘        └────────────────┘  └──────────────┘
```

| Component | Role | Port |
|-----------|------|------|
| React (Vite) | Doctor, pharmacy, and admin UI | 5173 (HTTPS) |
| FastAPI | REST API, business logic | 8000 |
| SQLite | Persistent storage | — (file) |
| Whisper (`faster-whisper`) | Speech-to-text transcription | in-process |
| NLLB (`zaanind/nllb-ensi-v1.6`) | English ↔ Sinhala / Tamil translation | in-process |
| Ollama | AI consultation structuring | 11434 |
| ngrok | Expose backend to internet for Twilio | tunnel |
| Twilio | WhatsApp messaging & sandbox | external API |

---

## 2. Hardware & OS Requirements

| Resource | Requirement |
|----------|-------------|
| OS | Windows 10 (20H2 / build 19042+) or Windows 11 |
| CPU | 4-core, x86-64 |
| RAM | 8 GB minimum — 16 GB recommended (NLLB + Whisper load large models) |
| Disk | 20 GB free (models, node_modules, Python packages) |
| Internet | Required during install and for Twilio / ngrok |

**GPU (optional):** An NVIDIA GPU with CUDA 12.x speeds up Whisper and NLLB significantly but is not required. The system runs fully on CPU.

---

## 3. What Gets Installed

The install script handles everything automatically:

| Tool | Version | Purpose |
|------|---------|---------|
| `uv` | latest | Fast Python package & environment manager |
| Python | 3.13 (via uv) | Backend runtime |
| Node.js | 22 LTS | Frontend build tooling |
| npm | bundled with Node | Frontend package manager |
| ffmpeg | latest | Audio decoding for Whisper |
| Git | latest | Source control |
| ngrok | latest | Tunnel localhost to public HTTPS for Twilio |
| Python packages | `backend/requirements.txt` | All backend libraries |
| npm packages | `frontend/package.json` | React, Vite, Tailwind, etc. |

> **Ollama is installed separately** — see [Section 5](#5-ollama-setup).

**AI models — downloaded on first use, not during install:**

| Model | Size | Trigger |
|-------|------|---------|
| `faster-whisper` small | ~244 MB | First audio transcription |
| `zaanind/nllb-ensi-v1.6` | ~1.2 GB | First translation request |
| `phi3` (Ollama) | ~2.2 GB | `ollama pull phi3` |
| `qwen2:7b` (Ollama) | ~4.4 GB | `ollama pull qwen2:7b` |
| `gpt-oss:120b-cloud` | cloud | `ollama pull gpt-oss:120b-cloud` (requires login) |

---

## 4. Windows Installation

### 4.1 Prerequisites

- Windows 10 (20H2+) or Windows 11
- **winget** (Windows Package Manager) — ships with Windows 11; on Windows 10 install [App Installer](https://aka.ms/getwinget) from the Microsoft Store
- PowerShell 5.1 or later (built into Windows)
- Internet access

> Run PowerShell **as Administrator** to avoid UAC prompts during winget installs.

### 4.2 Allow script execution (one-time)

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 4.3 Clone the repository

```powershell
git clone https://github.com/chamodhk/MediScript.git $env:USERPROFILE\MediScript
cd $env:USERPROFILE\MediScript
```

### 4.4 Run the install script

```powershell
.\scripts\install_windows.ps1
```

With options:

```powershell
# Install to a custom directory
.\scripts\install_windows.ps1 -InstallDir C:\Apps\MediScript

# Skip the frontend build verification step (faster)
.\scripts\install_windows.ps1 -SkipFrontendBuild

# Skip ngrok
.\scripts\install_windows.ps1 -SkipNgrok

# Re-run demo data seed on an existing install
.\scripts\install_windows.ps1 -ForceReseed
```

### 4.5 What the script does, step by step

1. Validates that `winget` is available
2. Installs `Git`, `Node.js 22 LTS`, `ffmpeg` via winget
3. Installs `uv` via the official PowerShell installer
4. Downloads **Python 3.13** via `uv python install`
5. Clones the repository (or pulls latest if already cloned)
6. Creates `backend\.venv` with Python 3.13
7. Installs Python dependencies — strips Windows-incompatible packages (`nvidia-*`, `cuda-*`, `triton`, `uvloop`, `fastar`) and installs PyTorch from the correct CPU or CUDA index
8. Runs Alembic database migrations (`alembic upgrade head`)
9. Seeds demo data (users, pharmacies, patients)
10. Installs **ngrok** via `winget install Ngrok.Ngrok`
11. Installs frontend npm packages and verifies build
12. Writes `.bat` convenience start scripts to `scripts\`

### 4.6 Expected duration

10–20 minutes on a fresh machine depending on internet speed.

### 4.7 PATH note

The script refreshes the current session's PATH from the registry after each winget install. New terminals opened after installation will find all tools immediately.

---

## 5. Ollama Setup

Ollama must be installed and configured manually. Do this **before starting the backend**.

### 5.1 Install Ollama

```powershell
winget install --id Ollama.Ollama --accept-package-agreements --accept-source-agreements
```

**Close and reopen your terminal** after installation so Ollama is on your PATH.

### 5.2 Start the Ollama service

```powershell
ollama serve
```

Leave this terminal open. Or use the convenience script:
```bat
scripts\start_ollama.bat
```

### 5.3 Pull a model (choose one)

| Model | Command | Best for |
|-------|---------|----------|
| `phi3` | `ollama pull phi3` | Fast, lightweight — works on most machines |
| `qwen2:7b` | `ollama pull qwen2:7b` | More accurate — needs a stronger machine |
| `gpt-oss:120b-cloud` | see below | Cloud-hosted, no GPU needed, requires login |

**For the cloud model:**

```powershell
ollama login                         # opens browser to ollama.com — log in and authorise
ollama pull gpt-oss:120b-cloud
```

### 5.4 Activate the model in structure_service.py

Model selection is **not** done via `.env` — it is set directly in `backend\services\structure_service.py`. Open that file and uncomment the line for the model you pulled (keep only one line active):

```python
# model="gpt-oss:120b-cloud",  # cloud — needs ollama login first
model="phi3",                   # fast, lightweight — good for most machines
# model="qwen2:7b"              # more accurate — needs a stronger machine
```

---

## 6. Starting the Services

Start each service in a **separate terminal**, in this order:

### Terminal 1 — Ollama

```powershell
ollama serve
```

### Terminal 2 — Backend API

```powershell
cd $env:USERPROFILE\MediScript\backend
.\.venv\Scripts\activate
python run.py
```

Or:
```bat
scripts\start_backend.bat
```

API: **http://localhost:8000** | Docs: **http://localhost:8000/docs**

### Terminal 3 — Frontend

```powershell
cd $env:USERPROFILE\MediScript\frontend
npm run dev
```

Or:
```bat
scripts\start_frontend.bat
```

App: **https://localhost:5173**

> Accept the self-signed certificate warning: in Chrome click **Advanced → Proceed to localhost (unsafe)**; in Firefox click **Accept the Risk and Continue**.

### Terminal 4 — ngrok (only needed for WhatsApp / Twilio)

```powershell
ngrok http 8000
```

Or:
```bat
scripts\start_ngrok.bat
```

### Application URLs

| URL | Portal |
|-----|--------|
| `https://localhost:5173/doctor` | Doctor portal |
| `https://localhost:5173/pharmacy/1` | Pharmacy 1 queue |
| `https://localhost:5173/pharmacy/2` | Pharmacy 2 queue |
| `https://localhost:5173/admin` | Admin panel |
| `http://localhost:8000/docs` | Swagger API docs |

---

## 7. Twilio & ngrok Webhook Setup

WhatsApp features (prescription notifications, patient reminders, channeling bot) require Twilio to deliver incoming messages to the backend via a public HTTPS webhook. ngrok creates this tunnel.

### 7.1 Start the ngrok tunnel

```bat
scripts\start_ngrok.bat
```

ngrok will display:

```
Forwarding    https://a1b2c3d4e5f6.ngrok-free.app -> http://localhost:8000
```

Copy the `https://...ngrok-free.app` URL.

### 7.2 Register the webhook with Twilio

1. Go to [console.twilio.com](https://console.twilio.com)
2. Navigate to **Messaging → Try it out → Send a WhatsApp message**
3. Click **Sandbox Configuration**
4. Under **WHEN A MESSAGE COMES IN**, enter:
   ```
   https://<your-ngrok-id>.ngrok-free.app/api/twilio/webhook
   ```
5. Set the HTTP method to **POST**
6. Click **Save**

![](https://github.com/chamodhk/MediScript/blob/main/docs/Screenshot%202026-04-04%20053953.png)

### 7.3 Add Twilio credentials to the backend

Edit `backend\.env`:

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

Find these at **https://console.twilio.com/us1/account/keys-credentials/api-keys**. Restart the backend after saving.

### 7.4 Join the Twilio sandbox

Every WhatsApp number that needs to receive messages must join the sandbox once by sending this to **+1 415 523 8886** on WhatsApp:

```
join <your-sandbox-keyword>
```

The keyword is shown on the Twilio sandbox page.

### 7.5 ngrok notes

| Note | Detail |
|------|--------|
| Free tier URL changes | A new random URL is assigned every restart — update the Twilio webhook each time |
| Stable URL | Create a free account at [ngrok.com](https://ngrok.com) and run `ngrok config add-authtoken <token>` |
| Session limit | Free tier allows only one active tunnel — close any other ngrok sessions before starting a new one |
| ERR_NGROK_108 | Another ngrok session is active — kill it with `Stop-Process -Name ngrok` and restart |

---

## 8. Environment Configuration Reference

`backend\.env` is created automatically by the install script. Edit to enable optional features.

```env
# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL=sqlite+aiosqlite:///./mediscript.db

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,https://localhost:5173

# ── Authentication ────────────────────────────────────────────────────────────
JWT_SECRET_KEY=mediscript-local-dev-secret-please-change
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ── Twilio (WhatsApp) ─────────────────────────────────────────────────────────
# Leave blank to disable WhatsApp features.
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# ── Whisper (speech-to-text) ──────────────────────────────────────────────────
# Model size: tiny | base | small | medium | large
WHISPER_MODEL=small

# ── Ollama (consultation structuring) ─────────────────────────────────────────
# OLLAMA_BASE_URL controls where the backend connects to Ollama.
# Model selection is done in backend/services/structure_service.py, not here.
OLLAMA_BASE_URL=http://localhost:11434

# ── Application ───────────────────────────────────────────────────────────────
APP_ENV=development
REMINDER_TIMEZONE=Asia/Colombo
REMINDER_POLL_SECONDS=60
```

`frontend\.env.local`:

```env
# Replace localhost with your LAN IP if accessing from another device on the same network.
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## 9. Demo Accounts & Test Data

All passwords are `password@123`.

### User accounts

| Email | Role | Portal |
|-------|------|--------|
| `admin@mediscript.com` | Admin | `/admin` |
| `doctor1@mediscript.com` | Doctor | `/doctor` |
| `doctor2@mediscript.com` | Doctor | `/doctor` |
| `pharmacy1@mediscript.com` | Pharmacist | `/pharmacy/1` |
| `pharmacy2@mediscript.com` | Pharmacist | `/pharmacy/2` |

### Demo patients

| Name | Phone | Preferred language |
|------|-------|--------------------|
| Kamal Perera | 0771234567 | Sinhala |
| Nimal Silva | 0779876543 | Sinhala |
| Amara Fernando | 0712345678 | Tamil |
| Chamodh Nethsara | +94703086052 | English |
| Didula Jeewandara | +94763596129 | English |

### Pre-seeded pharmacy queue

Pharmacy 1 is pre-loaded with three test prescriptions (`pending`, `preparing`, `ready`) so the pharmacy UI is demonstrable without completing a full consultation flow.

### Re-seeding the database

```powershell
cd $env:USERPROFILE\MediScript\backend
.\.venv\Scripts\python.exe -m core.seed
```

Or via the install script:

```powershell
.\scripts\install_windows.ps1 -ForceReseed
```

---

## 10. Troubleshooting

### Backend won't start — ModuleNotFoundError

Run from the `backend\` directory using the venv Python:

```powershell
cd $env:USERPROFILE\MediScript\backend
.\.venv\Scripts\activate
python run.py
```

---

### `alembic upgrade head` fails — "Can't locate revision"

Delete the database and start fresh:

```powershell
Remove-Item $env:USERPROFILE\MediScript\backend\mediscript.db
cd $env:USERPROFILE\MediScript\backend
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m core.seed
```

---

### Frontend shows blank page or network errors

Check that `VITE_API_BASE_URL` in `frontend\.env.local` points to where the backend is running:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

If accessing from another device on the LAN, replace `localhost` with the host machine's IP (e.g. `http://192.168.1.50:8000/api`).

---

### Audio transcription fails

1. Confirm ffmpeg is installed: `ffmpeg -version`
2. Confirm `backend\temp\` directory exists
3. On first use, Whisper downloads the `small` model (~244 MB) — watch the backend terminal for progress

---

### Ollama / AI structuring returns an error

1. Confirm Ollama is running: open `http://localhost:11434` in a browser — it should show `Ollama is running`
2. Confirm your model is installed: `ollama list`
3. If missing, pull it: `ollama pull phi3`
4. Confirm the correct model line is uncommented in `backend\services\structure_service.py`
5. If Ollama is not installed, run: `winget install --id Ollama.Ollama --accept-package-agreements --accept-source-agreements`

---

### Twilio webhook not receiving messages

1. Confirm ngrok is running and the HTTPS URL is active
2. Confirm the Twilio sandbox webhook URL matches the **current** ngrok URL (changes every restart on the free tier)
3. Confirm `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` are set in `backend\.env` and the backend was restarted after editing
4. Confirm the patient's WhatsApp number has joined the sandbox (sent the join phrase to +1 415 523 8886)

---

### winget not found

Install **App Installer** from the Microsoft Store or download it from [aka.ms/getwinget](https://aka.ms/getwinget). Alternatively install Git and Node.js manually from their official websites, then re-run the PowerShell script.

---

### Script blocked by execution policy

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

---

### ngrok: ERR_NGROK_108 (session limit)

Free ngrok accounts allow only one active tunnel at a time:

```powershell
Stop-Process -Name ngrok -ErrorAction SilentlyContinue
```

Then restart `scripts\start_ngrok.bat`.

---

### ollama not recognised after install

Close the current terminal completely and open a new one. The Ollama installer writes to the user PATH in the registry — the current session won't see it until restarted.
