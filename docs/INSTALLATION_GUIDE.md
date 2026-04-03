# MediScript Installation Guide

This guide covers a full local setup of MediScript from scratch, including:

- Backend setup
- Frontend setup
- Database initialization
- Demo login accounts
- Ollama and LibreTranslate
- Twilio WhatsApp sandbox
- ngrok for public webhook access
- Mobile microphone testing

## 1. Prerequisites

Install these first:

- `git`
- `Python 3.11+`
- `pip`
- `node` and `npm`
- `SQLite`
- `ngrok`
- `Ollama`
- `LibreTranslate`

Recommended OS tools:

- `venv` for Python virtual environments
- a modern browser such as Chrome

## 2. Clone the Project

```bash
git clone <your-repo-url>
cd MediScript
```

## 3. Project Structure

Main app folders:

- `backend/` - FastAPI backend
- `frontend/` - React + Vite frontend
- `docs/` - project documentation

## 4. Backend Setup

Move into the backend folder:

```bash
cd backend
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## 5. Backend Environment Variables

Create `backend/.env` with the following values:

```env
DATABASE_URL=sqlite+aiosqlite:///./mediscript.db
JWT_SECRET_KEY=change-this-in-production
JWT_ALGORITHM=HS256

TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

WHISPER_MODEL=small
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3
LIBRETRANSLATE_URL=http://localhost:5000
APP_ENV=development
REMINDER_TIMEZONE=Asia/Colombo
REMINDER_POLL_SECONDS=60
```

Notes:

- `TWILIO_WHATSAPP_FROM` defaults to the Twilio WhatsApp sandbox number.
- SQLite is the default local database.
- For production, replace `JWT_SECRET_KEY` with a strong secret.

## 6. Database Setup

You can initialize the database in either of these ways.

### Option A: Alembic migrations

```bash
alembic upgrade head
python -m core.seed
```

### Option B: One-shot local bootstrap

```bash
python scripts/setup_database.py
```

If you want a clean reset:

```bash
python scripts/setup_database.py --reset
```

## 7. Seeded Demo Accounts

The seed scripts create demo users with the password:

```text
password@123
```

Available accounts:

- `admin@mediscript.com`
- `doctor1@mediscript.com`
- `doctor2@mediscript.com`
- `pharmacy1@mediscript.com`
- `pharmacy2@mediscript.com`

## 8. Start Required Local Services

Start the supporting services before starting the app.

### LibreTranslate

```bash
libretranslate --host 0.0.0.0 --port 5000
```

### Ollama

Start Ollama:

```bash
ollama serve
```

Pull the model used by the backend:

```bash
ollama pull phi3
```

If your team uses a different model, update `OLLAMA_MODEL` in `backend/.env`.

## 9. Start the Backend

From `backend/`:

```bash
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at:

```text
http://localhost:8000
http://<your-lan-ip>:8000
```

Health endpoint:

```text
GET /api/health
```

## 10. Frontend Setup

Open a new terminal:

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

If you are testing from another device on the same network:

```env
VITE_API_BASE_URL=http://<your-lan-ip>:8000/api
```

## 11. Start the Frontend

From `frontend/`:

```bash
npm run dev
```

The local doctor and pharmacy portals are:

- `https://localhost:5173/doctor`
- `https://localhost:5173/pharmacy/1`
- `https://localhost:5173/pharmacy/2`

If you are opening the app from another device:

- `https://<your-lan-ip>:5173/doctor`
- `https://<your-lan-ip>:5173/pharmacy/1`
- `https://<your-lan-ip>:5173/pharmacy/2`

Important:

- The Vite dev server is configured for HTTPS.
- On first visit, the browser may show a certificate warning for the local dev certificate.
- You must accept the warning before microphone access can work on mobile.

## 12. Twilio WhatsApp Sandbox Setup

This project uses the Twilio WhatsApp sandbox for local development.

### Twilio setup steps

1. Create a Twilio account.
2. Open the WhatsApp Sandbox in the Twilio console.
3. Copy your:
   `Account SID`
4. Copy your:
   `Auth Token`
5. Put both values into `backend/.env`.
6. Keep `TWILIO_WHATSAPP_FROM=whatsapp:+14155238886` unless you are using a real WhatsApp sender.

### Join the sandbox

Each phone number that will receive or send sandbox messages must join the Twilio sandbox first.

In the Twilio console, you will see a join code and instructions such as sending a specific message to the sandbox number. Complete that step from the target phone.

## 13. ngrok Setup for Twilio Webhooks

Twilio needs a public HTTPS URL to reach your local backend webhook.

Start the backend first, then expose port `8000` using ngrok:

```bash
ngrok http 8000
```

ngrok will return a public HTTPS URL, for example:

```text
https://your-subdomain.ngrok-free.app
```

Use this as the Twilio sandbox webhook URL:

```text
https://your-subdomain.ngrok-free.app/api/twilio/webhook
```

The MediScript incoming WhatsApp webhook route is:

```text
POST /api/twilio/webhook
```

## 14. Optional ngrok Setup for Frontend Mobile Testing

If a phone refuses the local HTTPS certificate from the Vite dev server, expose the frontend through ngrok too:

```bash
ngrok http 5173
```

Then set:

```env
VITE_API_BASE_URL=https://your-backend-ngrok-url/api
```

Open the frontend using the ngrok HTTPS URL. This is often the easiest way to test microphone features on mobile devices.

## 15. Twilio Test Flow

After backend, ngrok, and Twilio are configured:

1. Join the WhatsApp sandbox from your phone.
2. Set the sandbox webhook to:
   `https://your-backend-ngrok-url/api/twilio/webhook`
3. Start the backend.
4. Send a WhatsApp message from your phone to the sandbox number.
5. The backend should process the message and reply through Twilio.

The app also has a direct message endpoint:

```text
POST /api/send-transcription
```

Example JSON payload:

```json
{
  "patient_number": "+94703086052",
  "transcription": "Take your medicine after meals for 5 days."
}
```

## 16. Typical Startup Order

Use this order for local development:

1. Start `LibreTranslate`
2. Start `Ollama`
3. Start backend
4. Start ngrok for backend if Twilio is needed
5. Start frontend
6. Start ngrok for frontend if mobile HTTPS testing is needed

## 17. Mobile Microphone Notes

For microphone recording on mobile:

- open the frontend over `HTTPS`
- accept the browser certificate warning if using local Vite HTTPS
- if local HTTPS still fails on mobile, use an `ngrok` HTTPS URL for the frontend

If the site is opened over plain HTTP on a phone, the browser may block microphone access without showing the permission prompt.

## 18. Common Troubleshooting

### Backend starts but login fails

Check:

- database was initialized
- seed data was created
- you are using one of the seeded accounts

### Twilio messages do not arrive

Check:

- `TWILIO_ACCOUNT_SID` is correct
- `TWILIO_AUTH_TOKEN` is correct
- the phone joined the sandbox
- ngrok is running
- Twilio webhook points to `/api/twilio/webhook`
- backend is running when Twilio sends the request

### Mobile microphone does not prompt

Check:

- frontend is opened over HTTPS
- the certificate warning was accepted
- the phone browser supports `getUserMedia`
- the microphone is not already in use by another app

### Frontend cannot reach backend

Check:

- `VITE_API_BASE_URL` points to the correct backend
- backend is listening on `0.0.0.0`
- port `8000` is reachable from the device
- CORS changes are loaded after restarting the backend

## 19. Useful Commands

Backend:

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm run dev
```

Database reset:

```bash
cd backend
source .venv/bin/activate
python scripts/setup_database.py --reset
```

Backend ngrok:

```bash
ngrok http 8000
```

Frontend ngrok:

```bash
ngrok http 5173
```

## 20. Recommended First End-to-End Test

After a fresh setup:

1. Initialize the database
2. Start LibreTranslate
3. Start Ollama
4. Start backend
5. Start frontend
6. Log in with `doctor1@mediscript.com` and `password@123`
7. Open a pharmacy page and verify the queue loads
8. Configure ngrok and Twilio
9. Send a WhatsApp sandbox test message
10. Open the app on a phone over HTTPS and test microphone recording
