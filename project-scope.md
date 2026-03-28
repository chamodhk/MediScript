# MediScript — Project Scope (MVP)

## Product
AI-powered clinical communication system for Hemas Hospitals.

## Portals
- **Doctor Portal** — consultation, recording, prescription
- **Pharmacy Portal** — incoming prescription queue

## Core Features
-  Patient registration (name, phone, preferred language)
### Doctor Portal
-  Start Consultation → triggers consent
-  Audio recording via browser mic (MediaRecorder API)
-  Whisper transcription (local, batch after stop)
-  Ollama NLP structuring → medications, dosages, follow-ups, reminders
-  Structured output display (doctor can review)
-  Prescription drawing canvas (Fabric.js, mouse/stylus)
-  Review & Submit screen
-  On submit → dispatch to pharmacy, send WhatsApp

### Pharmacy Portal
-  Two pharmacy portals — /pharmacy/1 and /pharmacy/2
-  Live queue of incoming prescriptions (per pharmacy)
-  View prescription image 
-  Status update: Pending → Preparing → Ready → Collected
-  "Mark as Busy / Available" toggle button

### Notifications (Twilio WhatsApp Sandbox)
-  Immediate post-consultation message to patient (structured instructions in their language)
-  Prescription forwarded to pharmacy
-  Scheduled medication reminders (APScheduler)
-  Follow-up test / appointment reminders
-  Hemas promotional message (static template, sent once)

### Translation
-  English → Sinhala / Tamil / English (LibreTranslate, local)

- More than 2 pharmacies
- Dynamic wait-time prediction (queue count is used as proxy)
- Patient history / EHR access
- Mobile app
- Real-time streaming transcription
- Verified Meta WhatsApp Business account
- Dynamic promotional content engine

