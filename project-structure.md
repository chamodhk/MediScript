MediScript/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env
│   ├── .gitignore
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── patient.py
│   │   ├── consultation.py
│   │   ├── prescription.py
│   │   ├── pharmacy.py
│   │   └── reminder.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth_router.py
│   │   ├── transcription_router.py
│   │   ├── nlp_router.py
│   │   ├── prescription_router.py
│   │   ├── consultation_router.py
│   │   ├── pharmacy_router.py
│   │   ├── translation_router.py
│   │   └── notification_router.py
│   │
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── auth_controller.py
│   │   ├── transcription_controller.py
│   │   ├── nlp_controller.py
│   │   ├── prescription_controller.py
│   │   ├── consultation_controller.py
│   │   ├── pharmacy_controller.py
│   │   ├── routing_controller.py
│   │   ├── translation_controller.py
│   │   └── notification_controller.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── whisper_service.py
│   │   ├── ollama_service.py
│   │   ├── translate_service.py
│   │   ├── twilio_service.py
│   │   └── scheduler_service.py
│   │
│   ├── migrations/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   │
│   ├── alembic.ini
│   │
│   └── static/
│       └── prescriptions/
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── tailwind.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       │
│       ├── pages/
│       │   ├── LoginPage.jsx
│       │   ├── DoctorPortal.jsx
│       │   └── PharmacyPortal.jsx
│       │
│       ├── components/
│       │   ├── shared/
│       │   │   ├── Navbar.jsx
│       │   │   ├── Toast.jsx
│       │   │   └── LoadingSpinner.jsx
│       │   ├── doctor/
│       │   │   ├── PatientSetup.jsx
│       │   │   ├── AudioRecorder.jsx
│       │   │   ├── TranscriptDisplay.jsx
│       │   │   ├── StructuredOutput.jsx
│       │   │   ├── PrescriptionCanvas.jsx
│       │   │   └── ReviewSubmit.jsx
│       │   └── pharmacy/
│       │       ├── PrescriptionQueue.jsx
│       │       ├── PrescriptionCard.jsx
│       │       └── StatusBadge.jsx
│       │
│       ├── hooks/
│       │   ├── useAudioRecorder.js
│       │   ├── useConsultation.js
│       │   └── usePharmacyQueue.js
│       │
│       └── services/
│           └── api.js
│
└── README.md