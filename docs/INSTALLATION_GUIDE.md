# MediScript — Installation Guide

MediScript is an AI-powered clinical communication system built for Hemas Hospitals. This guide walks through installing the full stack on a fresh **Ubuntu/Debian**, **Arch Linux**, or **Windows 10/11** machine from scratch.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Hardware & OS Requirements](#2-hardware--os-requirements)
3. [What Gets Installed](#3-what-gets-installed)
4. [Ubuntu / Debian Installation](#4-ubuntu--debian-installation)
5. [Arch Linux Installation](#5-arch-linux-installation)
6. [Windows Installation](#6-windows-installation)
7. [Starting the Services](#7-starting-the-services)
8. [Twilio & ngrok Webhook Setup](#8-twilio--ngrok-webhook-setup)
9. [Environment Configuration Reference](#9-environment-configuration-reference)
10. [Demo Accounts & Test Data](#10-demo-accounts--test-data)
11. [Troubleshooting](#11-troubleshooting)

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
                    │ phi3 model     │        │ → public HTTPS │  │ WhatsApp API │
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
| Ollama (`phi3`) | AI consultation structuring | 11434 |
| ngrok | Expose backend to internet for Twilio | tunnel |
| Twilio | WhatsApp messaging & sandbox | external API |

---

## 2. Hardware & OS Requirements

### Minimum

| Resource | Requirement |
|----------|-------------|
| OS | Ubuntu 20.04+ / Debian 11+ / Arch Linux (rolling) / Windows 10 (20H2+) or Windows 11 |
| CPU | 4-core, x86-64 |
| RAM | 8 GB (16 GB recommended — NLLB + Whisper load large models) |
| Disk | 20 GB free (models, node_modules, Python packages) |
| Internet | Required during install and for Twilio / ngrok |

### GPU (Optional)

An NVIDIA GPU with CUDA 12.x speeds up Whisper transcription and NLLB translation significantly but is **not required**. The system runs fully on CPU.

---

## 3. What Gets Installed

The install scripts handle everything automatically:

| Tool | Version | Purpose |
|------|---------|---------|
| `uv` | latest | Fast Python package & environment manager |
| Python | 3.13 (via uv) | Backend runtime |
| Node.js | 22 LTS (Ubuntu) / rolling (Arch) | Frontend build tooling |
| npm | bundled with Node | Frontend package manager |
| ffmpeg | latest | Audio decoding for Whisper |
| Git | latest | Source control |
| ngrok | latest | Tunnel localhost to public HTTPS for Twilio |
| Ollama | latest | Local LLM runtime (phi3 model) |
| Python packages | `backend/requirements.txt` | All backend libraries |
| npm packages | `frontend/package.json` | React, Vite, Tailwind, etc. |

**AI models — downloaded on first use, not during install:**

| Model | Size | Trigger |
|-------|------|---------|
| `faster-whisper` small | ~244 MB | First audio transcription |
| `zaanind/nllb-ensi-v1.6` | ~1.2 GB | First translation request |
| `phi3` (Ollama) | ~2.2 GB | Pulled by install script or `ollama pull phi3` |

---

## 4. Ubuntu / Debian Installation

### 4.1 Prerequisites

- Ubuntu 20.04+ or Debian 11+ with `apt`
- `sudo` privileges
- Internet access

### 4.2 Run the install script

```bash
# Clone the repository
git clone https://github.com/chamodhk/MediScript.git
cd MediScript

# Run the installer
bash scripts/install_fresh_local.sh
```

To install into a custom directory:

```bash
bash scripts/install_fresh_local.sh /opt/MediScript
```

### 4.3 Environment overrides

```bash
# Skip Ollama (if already installed)
INSTALL_OLLAMA=0 bash scripts/install_fresh_local.sh

# Skip ngrok
INSTALL_NGROK=0 bash scripts/install_fresh_local.sh

# Skip the frontend build verification step (faster)
SKIP_FRONTEND_BUILD=1 bash scripts/install_fresh_local.sh

# Check out a specific branch
BRANCH=develop bash scripts/install_fresh_local.sh

# Re-run the demo data seed on an existing database
FORCE_RESEED=1 bash scripts/install_fresh_local.sh
```

### 4.4 What the script does, step by step

1. Installs system packages: `git`, `curl`, `ffmpeg`, `build-essential`, `python3-dev`
2. Installs **Node.js 22 LTS** via NodeSource (the apt default is too old)
3. Installs `uv` via the official installer
4. Downloads **Python 3.13** via `uv python install`
5. Clones the repository (or pulls latest if the directory already exists)
6. Creates `backend/.venv` with Python 3.13
7. Installs all Python dependencies from `requirements.txt`
   - Detects NVIDIA GPU; installs CPU-only PyTorch on machines without CUDA
   - Strips CUDA-only packages (`nvidia-*`, `cuda-*`, `triton`) automatically on CPU machines
8. Runs Alembic database migrations (`alembic upgrade head`)
9. Seeds the database with demo users, pharmacies, and patients (idempotent)
10. Installs **ngrok** via the official apt repository
11. Installs **Ollama** and pulls the `phi3` model
12. Installs frontend npm packages and verifies with `npm run build`
13. Writes convenience start scripts to `scripts/`

### 4.5 Expected duration

10–20 minutes on a fresh machine depending on internet speed and whether a GPU is present.

---

## 5. Arch Linux Installation

### 5.1 Prerequisites

- Arch Linux or any Arch-based distro (Manjaro, EndeavourOS, CachyOS, etc.)
- `sudo` privileges
- Internet access
- Optionally `yay` or `paru` (AUR helper) — the script falls back to direct binary downloads if neither is present

### 5.2 Run the install script

```bash
# Clone the repository
git clone https://github.com/chamodhk/MediScript.git
cd MediScript

# Run the Arch-specific installer
bash scripts/install_arch.sh
```

To install into a custom directory:

```bash
bash scripts/install_arch.sh /opt/MediScript
```

### 5.3 Environment overrides

```bash
# Skip Ollama (if already installed)
INSTALL_OLLAMA=0 bash scripts/install_arch.sh

# Skip ngrok
INSTALL_NGROK=0 bash scripts/install_arch.sh

# Skip the frontend build verification step (faster)
SKIP_FRONTEND_BUILD=1 bash scripts/install_arch.sh

# Force a specific AUR helper (yay | paru | none)
AUR_HELPER=paru bash scripts/install_arch.sh

# Skip AUR entirely — uses direct binary downloads for ngrok/Ollama
AUR_HELPER=none bash scripts/install_arch.sh

# Check out a specific branch
BRANCH=develop bash scripts/install_arch.sh

# Re-run the demo data seed on an existing database
FORCE_RESEED=1 bash scripts/install_arch.sh
```

### 5.4 What the script does, step by step

1. Validates that `pacman` is available (fails fast if not on Arch)
2. Auto-detects `yay` or `paru` as the AUR helper
3. Installs system packages via `pacman`: `git`, `curl`, `ffmpeg`, `base-devel`, `nodejs`, `npm`, `unzip`
4. Installs `uv` via the official installer
5. Downloads **Python 3.13** via `uv python install` (pinned regardless of what Arch currently ships)
6. Clones the repository (or pulls latest if the directory already exists)
7. Creates `backend/.venv` with Python 3.13
8. Installs all Python dependencies from `requirements.txt`
   - Detects NVIDIA GPU; installs CPU-only PyTorch on machines without CUDA
   - Strips CUDA-only packages (`nvidia-*`, `cuda-*`, `triton`) automatically on CPU machines
9. Runs Alembic database migrations (`alembic upgrade head`)
10. Seeds the database with demo users, pharmacies, and patients (idempotent)
11. Installs **ngrok** — via AUR (`yay`/`paru`) if available, otherwise downloads the official binary directly to `/usr/local/bin`
12. Installs **Ollama** — via `pacman -S ollama` (in the `extra` repo), AUR fallback, or official install script
13. Pulls the `phi3` model
14. Installs frontend npm packages and verifies with `npm run build`
15. Writes convenience start scripts to `scripts/`

### 5.5 AUR helper behaviour

| Situation | What the script does |
|-----------|---------------------|
| `yay` or `paru` found | Uses it for AUR packages (ngrok, Ollama if not in official repos) |
| Neither found | ngrok: downloads official binary to `/usr/local/bin`; Ollama: tries `pacman` then official install script |
| `AUR_HELPER=none` | Forces direct downloads, never touches AUR |

### 5.6 Expected duration

10–20 minutes on a fresh machine. Arch's rolling release means `nodejs` and most packages are always current, so no NodeSource workaround is needed.

---

## 6. Windows Installation

### 6.1 Prerequisites

- Windows 10 (20H2 / build 19042) or Windows 11
- **winget** (Windows Package Manager) — ships with Windows 11; on Windows 10 install [App Installer](https://aka.ms/getwinget) from the Microsoft Store
- PowerShell 5.1 or later (built into Windows)
- Internet access

> Run PowerShell **as Administrator** to avoid UAC prompts on every winget install.

### 6.2 Allow script execution (one-time)

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 6.3 Run the install script

```powershell
# From inside the cloned repository
.\scripts\install_windows.ps1
```

With options:

```powershell
# Install to a custom directory and pull the Ollama model
.\scripts\install_windows.ps1 -InstallDir C:\Apps\MediScript -InstallOllama

# Skip the frontend build verification
.\scripts\install_windows.ps1 -SkipFrontendBuild

# Skip ngrok
.\scripts\install_windows.ps1 -SkipNgrok

# Re-run demo data seed on an existing install
.\scripts\install_windows.ps1 -ForceReseed
```

### 6.4 What the script does, step by step

1. Validates that `winget` is available
2. Installs `Git`, `Node.js 22 LTS`, `ffmpeg` via winget
3. Installs `uv` via the official PowerShell installer
4. Downloads **Python 3.13** via `uv python install`
5. Clones the repository (or pulls latest)
6. Creates `backend\.venv` with Python 3.13
7. Installs Python dependencies — strips Windows-incompatible packages (`nvidia-*`, `cuda-*`, `triton`, `uvloop`, `fastar`) and installs PyTorch from the PyTorch CPU or CUDA index
8. Runs Alembic database migrations
9. Seeds demo data
10. Installs **ngrok** via `winget install Ngrok.Ngrok`
11. Installs **Ollama** via winget and pulls `phi3` (only if `-InstallOllama` is passed)
12. Installs frontend npm packages and verifies build
13. Writes `.bat` start scripts to `scripts\`

### 6.5 PATH note

The script refreshes the current session's PATH from the registry after each winget install, so you do not need to restart PowerShell mid-install. New terminals opened after installation will find all tools immediately.

---

## 7. Starting the Services

Start each service in a **separate terminal**. Start Ollama first so it is ready when the backend initialises.

### Ubuntu / Debian and Arch Linux

```bash
# Terminal 1 — Ollama (AI structuring)
ollama serve

# Terminal 2 — Backend API  (http://localhost:8000)
bash ~/MediScript/scripts/start_backend.sh

# Terminal 3 — Frontend  (https://localhost:5173)
bash ~/MediScript/scripts/start_frontend.sh

# Terminal 4 — ngrok tunnel (only needed for WhatsApp / Twilio features)
bash ~/MediScript/scripts/start_ngrok.sh
```

### Windows

```bat
REM Terminal 1 — Ollama
scripts\start_ollama.bat

REM Terminal 2 — Backend API
scripts\start_backend.bat

REM Terminal 3 — Frontend
scripts\start_frontend.bat

REM Terminal 4 — ngrok (only needed for WhatsApp / Twilio features)
scripts\start_ngrok.bat
```

### Application URLs

| URL | Portal | Login role |
|-----|--------|------------|
| `https://localhost:5173/doctor` | Doctor portal | Doctor |
| `https://localhost:5173/pharmacy/1` | Pharmacy 1 queue | Pharmacist 1 |
| `https://localhost:5173/pharmacy/2` | Pharmacy 2 queue | Pharmacist 2 |
| `https://localhost:5173/admin` | Admin panel | Admin |
| `http://localhost:8000/docs` | Swagger API docs | Developers |

> **Self-signed certificate warning:** The frontend runs on HTTPS with a self-signed cert. In Chrome click **Advanced → Proceed to localhost (unsafe)**; in Firefox click **Accept the Risk and Continue**.

---

## 8. Twilio & ngrok Webhook Setup

WhatsApp features (prescription notifications, patient reminders, channeling bot) require Twilio to deliver incoming messages to the backend via a public HTTPS webhook. ngrok creates this tunnel from your local machine.

### 8.1 Start the ngrok tunnel

```bash
# Linux (Ubuntu/Debian or Arch)
bash ~/MediScript/scripts/start_ngrok.sh
```
```bat
REM Windows
scripts\start_ngrok.bat
```

ngrok will display output similar to:

```
Session Status    online
Forwarding        https://a1b2c3d4e5f6.ngrok-free.app -> http://localhost:8000
```

Copy the `https://...ngrok-free.app` URL.

### 8.2 Register the webhook with Twilio

1. Go to [console.twilio.com](https://console.twilio.com)
2. Navigate to **Messaging → Try it out → Send a WhatsApp message**
3. Click **Sandbox Configuration**
4. Under **WHEN A MESSAGE COMES IN**, enter:
   ```
   https://<your-ngrok-id>.ngrok-free.app/api/twilio/webhook
   ```
5. Set the HTTP method to **POST**
6. Click **Save**
7. ![](https://github.com/chamodhk/MediScript/blob/main/docs/Screenshot%202026-04-04%20053953.png)

### 8.3 Add Twilio credentials to the backend

Edit `backend/.env`:

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

Find these values in **https://console.twilio.com/us1/account/keys-credentials/api-keys**. Restart the backend after saving.

### 8.4 Join the Twilio sandbox

Every WhatsApp number that needs to receive messages must join the sandbox once by sending this message to **+1 415 523 8886** on WhatsApp:

```
join <your-sandbox-keyword>
```

The keyword is shown on the Twilio sandbox page under **Send a WhatsApp message**.

### 8.5 ngrok important notes

| Note | Detail |
|------|--------|
| Free tier URL changes | The ngrok free tier assigns a new random URL every restart. Update the Twilio webhook URL each time. |
| Stable URL | Create a free ngrok account at [ngrok.com](https://ngrok.com), then run `ngrok config add-authtoken <your-token>`. Paid accounts get reserved domains. |
| Multiple tunnels | Free tier allows only one active tunnel. Close any other ngrok sessions before starting a new one. |
| Session limit error | If you see `ERR_NGROK_108`, another ngrok session is active. Kill it and restart. |

---

## 9. Environment Configuration Reference

The backend reads all configuration from `backend/.env`. This file is created automatically by the install script with safe defaults. Edit it to enable optional features.

```env
# ── Database ──────────────────────────────────────────────────────────────────
# SQLite is used for local development. The file is created automatically.
DATABASE_URL=sqlite+aiosqlite:///./mediscript.db

# ── CORS ──────────────────────────────────────────────────────────────────────
# Comma-separated list of allowed frontend origins.
# Private LAN IP ranges (10.x, 192.168.x, 172.16-31.x) are always allowed via
# a regex rule in main.py — you do not need to list individual LAN IPs here.
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,https://localhost:5173

# ── Authentication ────────────────────────────────────────────────────────────
# Change JWT_SECRET_KEY to a long random string in any shared/production environment.
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
# "small" is the default — good speed/accuracy balance on CPU.
WHISPER_MODEL=small

# ── Ollama (consultation structuring) ─────────────────────────────────────────
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3

# ── Application ───────────────────────────────────────────────────────────────
APP_ENV=development

# ── Reminder scheduler ────────────────────────────────────────────────────────
REMINDER_TIMEZONE=Asia/Colombo
REMINDER_POLL_SECONDS=60
```

`frontend/.env.local`:

```env
# Backend API base URL. Replace localhost with the LAN IP if accessing
# the frontend from a different device on the same network.
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## 10. Demo Accounts & Test Data

The install script seeds the database with demo accounts and patients. All passwords are `password@123`.

### User accounts

| Email | Password | Role | Portal |
|-------|----------|------|--------|
| `admin@mediscript.com` | `password@123` | Admin | `/admin` |
| `doctor1@mediscript.com` | `password@123` | Doctor | `/doctor` |
| `doctor2@mediscript.com` | `password@123` | Doctor | `/doctor` |
| `pharmacy1@mediscript.com` | `password@123` | Pharmacist | `/pharmacy/1` |
| `pharmacy2@mediscript.com` | `password@123` | Pharmacist | `/pharmacy/2` |

### Demo patients

| Name | Phone | Preferred language | Token |
|------|-------|--------------------|-------|
| Kamal Perera | 0771234567 | Sinhala | T001 |
| Nimal Silva | 0779876543 | Sinhala | T002 |
| Amara Fernando | 0712345678 | Tamil | T003 |
| Chamodh Nethsara | +94703086052 | English | T004 |
| Didula Jeewandara | +94763596129 | English | T005 |

### Pre-seeded pharmacy queue

Pharmacy 1 is pre-loaded with three test prescriptions (statuses: `pending`, `preparing`, `ready`) so the pharmacy UI is demonstrable immediately without completing a full consultation flow.

### Re-seeding the database

The seed script is fully idempotent — running it again updates existing records without creating duplicates.

```bash
# Linux (Ubuntu/Debian or Arch)
cd ~/MediScript/backend
./.venv/bin/python -m core.seed

# Windows
cd %USERPROFILE%\MediScript\backend
.venv\Scripts\python.exe -m core.seed
```

Or pass the reseed flag to the relevant install script:

```bash
# Ubuntu / Debian
FORCE_RESEED=1 bash scripts/install_fresh_local.sh

# Arch Linux
FORCE_RESEED=1 bash scripts/install_arch.sh
```
```powershell
# Windows
.\scripts\install_windows.ps1 -ForceReseed
```

---

## 11. Troubleshooting

### Backend won't start — ModuleNotFoundError

Make sure you are running from the `backend/` directory using the venv Python, not a system Python:

```bash
# Linux (Ubuntu/Debian or Arch)
cd ~/MediScript/backend
./.venv/bin/python run.py

# Windows
cd %USERPROFILE%\MediScript\backend
.venv\Scripts\python.exe run.py
```

---

### `alembic upgrade head` fails — "Can't locate revision"

The database may be in an inconsistent state. Delete it and start fresh:

```bash
rm ~/MediScript/backend/mediscript.db
cd ~/MediScript/backend
./.venv/bin/alembic upgrade head
./.venv/bin/python -m core.seed
```

---

### Frontend shows blank page or network errors

Check that `VITE_API_BASE_URL` in `frontend/.env.local` points to where the backend is actually running:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

If accessing the frontend from another device on the LAN, replace `localhost` with the host machine's IP address (e.g. `http://192.168.1.50:8000/api`).

---

### Audio transcription fails

1. Confirm ffmpeg is installed: `ffmpeg -version`
2. Confirm `backend/temp/` directory exists and is writable
3. On first use, Whisper downloads the `small` model (~244 MB) — watch the backend terminal for download progress or errors

---

### Ollama / AI structuring returns an error

1. Check Ollama is running: `curl http://localhost:11434/api/tags`
2. Check phi3 is installed: `ollama list` — it should show `phi3`
3. If missing: `ollama pull phi3`
4. If Ollama is not installed: re-run the relevant install script (sections 4, 5, or 6)

---

### Twilio webhook not receiving messages

1. Confirm ngrok is running and the HTTPS URL is active
2. Confirm the Twilio sandbox webhook URL matches the **current** ngrok URL (it changes on every restart with the free tier)
3. Confirm `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` are set in `backend/.env` and the backend was restarted after editing
4. Confirm the patient's WhatsApp number has joined the sandbox (sent the join phrase to +1 415 523 8886)

---

### CUDA package errors on Linux (CPU machine)

The `requirements.txt` was generated on a GPU machine and includes CUDA-specific packages. The install scripts strip these automatically, but if you ran pip manually it may fail. Use the install script, or strip them yourself:

```bash
grep -vE '^(nvidia-|cuda-|triton==)' backend/requirements.txt > /tmp/cpu_req.txt
uv pip install --python backend/.venv/bin/python \
  --extra-index-url https://download.pytorch.org/whl/cpu \
  -r /tmp/cpu_req.txt
```

---

### Arch Linux: pacman database is out of date

If pacman fails with signature errors or "package not found":

```bash
sudo pacman -Syu   # full system upgrade + db sync
```

Then re-run the install script. Arch requires a fully up-to-date system before installing new packages.

---

### Arch Linux: ngrok not available in AUR

If your AUR helper can't find ngrok, the script falls back to downloading the binary directly. You can also do this manually:

```bash
curl -Lo /tmp/ngrok.zip \
  "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.zip"
unzip /tmp/ngrok.zip -d /tmp/ngrok-bin
sudo mv /tmp/ngrok-bin/ngrok /usr/local/bin/ngrok
sudo chmod +x /usr/local/bin/ngrok
```

---

### Windows: winget not found

Install the **App Installer** from the Microsoft Store or download it from [aka.ms/getwinget](https://aka.ms/getwinget). Alternatively install Git and Node.js manually from their official websites, then re-run the PowerShell script.

---

### Windows: script blocked by execution policy

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

---

### ngrok: ERR_NGROK_108 (session limit)

Free ngrok accounts allow only one active tunnel. Kill all other ngrok processes:

```bash
# Linux (Ubuntu/Debian or Arch)
pkill ngrok

# Windows (PowerShell)
Stop-Process -Name ngrok -ErrorAction SilentlyContinue
```

Then restart the ngrok start script.
