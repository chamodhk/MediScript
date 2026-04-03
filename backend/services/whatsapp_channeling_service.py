from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.consultation import Consultation
from models.enums import ConsultationStatus, UserRole
from models.patient import Patient
from models.user import User
from services.symptom_triage_service import SymptomTriageService


@dataclass
class ChannelingSession:
    phone_number: str
    category: str
    prompt: str
    doctor_options: list[User]
    state: str = "awaiting_doctor"
    slot_options: list[str] = field(default_factory=list)
    selected_doctor_id: int | None = None
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RegistrationSession:
    phone_number: str
    state: str = "awaiting_name"
    patient_id: int | None = None
    name: str | None = None
    preferred_language: str | None = None
    date_of_birth: date | None = None
    age: int | None = None
    recording_consent: bool = True
    pending_prompt: str | None = None
    updated_at: datetime = field(default_factory=datetime.utcnow)


class WhatsAppChannelingService:
    SESSION_TTL = timedelta(minutes=30)

    def __init__(self) -> None:
        self._sessions: dict[str, ChannelingSession] = {}
        self._registration_sessions: dict[str, RegistrationSession] = {}
        self._triage = SymptomTriageService()
        self._specialty_keywords = {
            "Cardiology": ("cardiologist", "cardiology", "heart doctor", "heart specialist"),
            "Neurology": ("neurologist", "neurology"),
            "ENT": ("ent", "ear doctor", "nose doctor", "throat doctor", "sore throat doctor"),
            "Dermatology": ("dermatologist", "dermatology", "skin doctor"),
            "Orthopedics": ("orthopedic", "orthopaedic", "bone doctor", "joint doctor"),
            "Gynecology": ("gynecologist", "gynaecologist", "gynecology", "gynaecology"),
            "Pediatrics": ("pediatrician", "paediatrician", "child doctor"),
            "General Medicine": ("doctor", "consultant", "physician", "general doctor"),
        }
        self._doctor_specialties = {
            "doctor1@mediscript.com": ("Cardiology", "Neurology", "General Medicine"),
            "doctor2@mediscript.com": ("ENT", "Dermatology", "Orthopedics", "Gynecology", "Pediatrics", "General Medicine"),
        }

    async def handle_message(
        self,
        db: AsyncSession,
        *,
        from_number: str,
        body: str,
    ) -> str | None:
        text = (body or "").strip()
        if not text:
            return None

        normalized = self._normalize(text)
        self._cleanup_sessions()

        registration_session = self._registration_sessions.get(from_number)
        if registration_session is not None:
            return await self._handle_registration_session(db, from_number, text, normalized, registration_session)

        session = self._sessions.get(from_number)
        if session is not None:
            return await self._handle_active_session(db, from_number, normalized, session)

        patient = await self._get_patient_by_phone(db, from_number)
        if patient is None:
            return self._start_registration(
                from_number,
                pending_prompt=text,
            )

        if self._profile_needs_completion(patient):
            return self._start_registration(
                from_number,
                pending_prompt=text,
                patient=patient,
            )

        if not self._looks_like_channeling_intent(normalized):
            return None

        return await self._start_channeling_flow(
            db,
            from_number=from_number,
            prompt_text=normalized,
        )

    async def _start_channeling_flow(
        self,
        db: AsyncSession,
        *,
        from_number: str,
        prompt_text: str,
    ) -> str:
        category, prompt = await self._resolve_category(db, prompt_text)
        doctor_options = await self._load_doctors_for_category(db, category)
        if not doctor_options:
            return f"Sorry, we could not find an available {category} consultant right now."

        self._sessions[from_number] = ChannelingSession(
            phone_number=from_number,
            category=category,
            prompt=prompt,
            doctor_options=doctor_options,
        )
        return self._doctor_selection_message(category, prompt, doctor_options)

    def _start_registration(
        self,
        from_number: str,
        pending_prompt: str | None,
        patient: Patient | None = None,
    ) -> str:
        session = RegistrationSession(
            phone_number=from_number,
            pending_prompt=pending_prompt,
        )
        if patient is not None:
            session.patient_id = patient.id
            session.name = patient.name
            session.preferred_language = patient.preferred_language
            session.date_of_birth = patient.date_of_birth
            session.age = patient.age
            session.recording_consent = patient.recording_consent
            session.state = self._next_registration_state(session)
            self._registration_sessions[from_number] = session
            return self._prompt_for_state(session, patient_name=patient.name, existing=True)

        self._registration_sessions[from_number] = session
        return (
            "Welcome to MediScript. I could not find your patient record, so let's register you first.\n"
            "Please reply with your full name."
        )

    async def _handle_active_session(
        self,
        db: AsyncSession,
        from_number: str,
        normalized: str,
        session: ChannelingSession,
    ) -> str:
        if normalized in {"cancel", "stop", "exit"}:
            self._sessions.pop(from_number, None)
            return "Channeling request cancelled. Send another message any time if you want to start again."

        if session.state == "awaiting_doctor":
            if not normalized.isdigit():
                return self._doctor_selection_message(session.category, session.prompt, session.doctor_options)

            index = int(normalized) - 1
            if index < 0 or index >= len(session.doctor_options):
                return self._doctor_selection_message(session.category, session.prompt, session.doctor_options)

            doctor = session.doctor_options[index]
            session.selected_doctor_id = doctor.id
            session.slot_options = self._slot_options()
            session.state = "awaiting_slot"
            session.updated_at = datetime.utcnow()
            return self._slot_selection_message(doctor.full_name, session.slot_options)

        if session.state == "awaiting_slot":
            if not normalized.isdigit():
                doctor = self._selected_doctor(session)
                return self._slot_selection_message(doctor.full_name if doctor else "the selected doctor", session.slot_options)

            index = int(normalized) - 1
            if index < 0 or index >= len(session.slot_options):
                doctor = self._selected_doctor(session)
                return self._slot_selection_message(doctor.full_name if doctor else "the selected doctor", session.slot_options)

            patient = await self._get_patient_by_phone(db, from_number)
            doctor = self._selected_doctor(session)
            if patient is None or doctor is None:
                self._sessions.pop(from_number, None)
                return "We could not complete the channeling request. Please try again."

            slot_label = session.slot_options[index]
            consultation = Consultation(
                patient_id=patient.id,
                doctor_id=doctor.id,
                status=ConsultationStatus.SUBMITTED,
                structured_output={
                    "channeling_request": {
                        "source": "whatsapp",
                        "category": session.category,
                        "slot_label": slot_label,
                        "doctor_name": doctor.full_name,
                        "doctor_id": doctor.id,
                    }
                },
            )
            db.add(consultation)
            await db.commit()
            await db.refresh(consultation)
            self._sessions.pop(from_number, None)
            return (
                f"Your channeling request is confirmed.\n"
                f"Consultant: {doctor.full_name}\n"
                f"Category: {session.category}\n"
                f"Requested slot: {slot_label}\n"
                f"Reference: CH-{consultation.id}\n"
                f"We will use this request to proceed with the consultation."
            )

        self._sessions.pop(from_number, None)
        return "The channeling session expired. Please send your request again."

    async def _handle_registration_session(
        self,
        db: AsyncSession,
        from_number: str,
        text: str,
        normalized: str,
        session: RegistrationSession,
    ) -> str:
        if normalized in {"cancel", "stop", "exit"}:
            self._registration_sessions.pop(from_number, None)
            return "Registration cancelled. Send a message any time if you want to start again."

        session.updated_at = datetime.utcnow()

        if session.state == "awaiting_name":
            session.name = text.strip()
            if len(session.name) < 3:
                return "Please reply with your full name."
            session.state = "awaiting_language"
            return (
                f"Thanks, {session.name}.\n"
                "Reply with your preferred language:\n"
                "1. English\n"
                "2. Sinhala\n"
                "3. Tamil"
            )

        if session.state == "awaiting_language":
            language = self._parse_language_choice(normalized)
            if language is None:
                return self._prompt_for_state(session)
            session.preferred_language = language
            session.state = "awaiting_date_of_birth"
            return self._prompt_for_state(session)

        if session.state == "awaiting_date_of_birth":
            parsed_date = self._parse_date_of_birth(text.strip())
            if parsed_date is None:
                return self._prompt_for_state(session)
            session.date_of_birth = parsed_date
            session.age = self._calculate_age(parsed_date)
            session.state = "awaiting_age"
            return self._prompt_for_state(session)

        if session.state == "awaiting_age":
            age = self._parse_age(normalized)
            if age is None:
                return self._prompt_for_state(session)
            session.age = age
            session.state = "awaiting_consent"
            return self._prompt_for_state(session)

        if session.state == "awaiting_consent":
            consent = self._parse_yes_no(normalized)
            if consent is None:
                return self._prompt_for_state(session)

            session.recording_consent = consent
            patient = await self._save_patient_profile(db, from_number, session)
            await db.commit()
            await db.refresh(patient)
            self._registration_sessions.pop(from_number, None)

            if session.pending_prompt and self._looks_like_channeling_intent(self._normalize(session.pending_prompt)):
                follow_up = await self._start_channeling_flow(
                    db,
                    from_number=from_number,
                    prompt_text=self._normalize(session.pending_prompt),
                )
                return (
                    f"Registration complete, {patient.name}.\n\n"
                    f"{follow_up}"
                )

            return (
                f"Registration complete, {patient.name}.\n"
                "You can now tell me your symptoms or the specialist you want to see."
            )

        self._registration_sessions.pop(from_number, None)
        return "The registration session expired. Please send your message again."

    async def _resolve_category(self, db: AsyncSession, normalized: str) -> tuple[str, str]:
        direct_category = self._match_specialty(normalized)
        if direct_category is not None:
            return direct_category, f"You asked for a {direct_category} consultant."

        triage = await self._triage.triage(db, normalized)
        return triage.category, triage.channeling_message

    def _match_specialty(self, normalized: str) -> str | None:
        for category, keywords in self._specialty_keywords.items():
            if any(keyword in normalized for keyword in keywords):
                return category
        return None

    async def _load_doctors_for_category(self, db: AsyncSession, category: str) -> list[User]:
        result = await db.execute(
            select(User).where(User.role == UserRole.DOCTOR, User.is_active.is_(True)).order_by(User.full_name.asc())
        )
        doctors = result.scalars().all()
        matched = [
            doctor
            for doctor in doctors
            if category in self._doctor_specialties.get(doctor.email, ())
        ]
        if matched:
            return matched
        return doctors

    async def _get_patient_by_phone(self, db: AsyncSession, phone_number: str) -> Patient | None:
        normalized = self._normalize_phone(phone_number)
        result = await db.execute(select(Patient).where(Patient.phone == normalized))
        patient = result.scalar_one_or_none()
        if patient is not None:
            return patient

        raw_result = await db.execute(select(Patient).where(Patient.phone == phone_number))
        return raw_result.scalar_one_or_none()

    def _normalize_phone(self, phone_number: str) -> str:
        text = phone_number.strip()
        if text.startswith("whatsapp:"):
            text = text.replace("whatsapp:", "", 1)
        return text

    def _looks_like_channeling_intent(self, normalized: str) -> bool:
        channel_words = (
            "channel",
            "appointment",
            "book",
            "see a",
            "want to chat",
            "want to see",
            "consult",
            "specialist",
            "doctor",
        )
        if any(word in normalized for word in channel_words):
            return True
        if self._match_specialty(normalized) is not None:
            return True
        symptom_words = ("pain", "fever", "cough", "breathing", "rash", "headache", "vomiting")
        return any(word in normalized for word in symptom_words)

    def _normalize(self, text: str) -> str:
        cleaned = text.strip().lower()
        return re.sub(r"\s+", " ", cleaned)

    def _parse_language_choice(self, normalized: str) -> str | None:
        mapping = {
            "1": "en",
            "english": "en",
            "en": "en",
            "2": "si",
            "sinhala": "si",
            "sinhalese": "si",
            "si": "si",
            "3": "ta",
            "tamil": "ta",
            "ta": "ta",
        }
        return mapping.get(normalized)

    def _parse_date_of_birth(self, value: str) -> date | None:
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            return None
        if parsed > date.today():
            return None
        if parsed.year < 1900:
            return None
        return parsed

    def _parse_age(self, normalized: str) -> int | None:
        if not normalized.isdigit():
            return None
        age = int(normalized)
        if age <= 0 or age > 120:
            return None
        return age

    def _parse_yes_no(self, normalized: str) -> bool | None:
        if normalized in {"yes", "y", "1"}:
            return True
        if normalized in {"no", "n", "2"}:
            return False
        return None

    def _calculate_age(self, born: date) -> int:
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    def _profile_needs_completion(self, patient: Patient) -> bool:
        return patient.date_of_birth is None or patient.token is None

    def _next_registration_state(self, session: RegistrationSession) -> str:
        if not session.name:
            return "awaiting_name"
        if not session.preferred_language:
            return "awaiting_language"
        if session.date_of_birth is None:
            return "awaiting_date_of_birth"
        if session.age is None:
            return "awaiting_age"
        return "awaiting_consent"

    def _prompt_for_state(
        self,
        session: RegistrationSession,
        *,
        patient_name: str | None = None,
        existing: bool = False,
    ) -> str:
        if session.state == "awaiting_name":
            return "Please reply with your full name."
        if session.state == "awaiting_language":
            prefix = f"Thanks, {patient_name or session.name}.\n" if not existing else ""
            return (
                f"{prefix}Reply with your preferred language:\n"
                "1. English\n"
                "2. Sinhala\n"
                "3. Tamil"
            )
        if session.state == "awaiting_date_of_birth":
            if existing:
                return "Please reply with your date of birth in YYYY-MM-DD format so we can complete your patient profile."
            return "Please reply with your date of birth in YYYY-MM-DD format."
        if session.state == "awaiting_age":
            return "Please reply with your age in years."
        return (
            "Do you consent to storing your details for consultation coordination?\n"
            "Reply YES or NO."
        )

    async def _save_patient_profile(
        self,
        db: AsyncSession,
        from_number: str,
        session: RegistrationSession,
    ) -> Patient:
        if session.patient_id is not None:
            patient = await db.get(Patient, session.patient_id)
            if patient is None:
                session.patient_id = None
                return await self._save_patient_profile(db, from_number, session)
            patient.name = session.name or patient.name
            patient.phone = from_number
            patient.preferred_language = session.preferred_language or patient.preferred_language
            patient.date_of_birth = session.date_of_birth
            patient.age = session.age
            patient.recording_consent = session.recording_consent
            if not patient.token:
                patient.token = await self._generate_patient_token(db)
            return patient

        patient = Patient(
            name=session.name or "Unknown Patient",
            phone=from_number,
            preferred_language=session.preferred_language or "en",
            date_of_birth=session.date_of_birth,
            age=session.age,
            token=await self._generate_patient_token(db),
            recording_consent=session.recording_consent,
        )
        db.add(patient)
        return patient

    async def _generate_patient_token(self, db: AsyncSession) -> str:
        while True:
            candidate = f"T{uuid.uuid4().hex[:4].upper()}"
            result = await db.execute(select(Patient).where(Patient.token == candidate))
            if result.scalar_one_or_none() is None:
                return candidate

    def _doctor_selection_message(self, category: str, prompt: str, doctors: list[User]) -> str:
        lines = [
            prompt,
            "",
            f"Available {category} consultants:",
        ]
        for index, doctor in enumerate(doctors, start=1):
            lines.append(f"{index}. {doctor.full_name}")
        lines.extend(
            [
                "",
                "Reply with the number of the consultant you want.",
                "Reply CANCEL to stop this channeling flow.",
            ]
        )
        return "\n".join(lines)

    def _slot_selection_message(self, doctor_name: str, slots: list[str]) -> str:
        lines = [
            f"You selected {doctor_name}.",
            "",
            "Available channeling slots:",
        ]
        for index, slot in enumerate(slots, start=1):
            lines.append(f"{index}. {slot}")
        lines.extend(
            [
                "",
                "Reply with the slot number you want.",
                "Reply CANCEL to stop this channeling flow.",
            ]
        )
        return "\n".join(lines)

    def _slot_options(self) -> list[str]:
        return [
            "Today 4:00 PM",
            "Tomorrow 10:00 AM",
            "Tomorrow 4:30 PM",
        ]

    def _selected_doctor(self, session: ChannelingSession) -> User | None:
        if session.selected_doctor_id is None:
            return None
        for doctor in session.doctor_options:
            if doctor.id == session.selected_doctor_id:
                return doctor
        return None

    def _cleanup_sessions(self) -> None:
        cutoff = datetime.utcnow() - self.SESSION_TTL
        expired = [phone for phone, session in self._sessions.items() if session.updated_at < cutoff]
        for phone in expired:
            self._sessions.pop(phone, None)
        expired_registrations = [
            phone for phone, session in self._registration_sessions.items() if session.updated_at < cutoff
        ]
        for phone in expired_registrations:
            self._registration_sessions.pop(phone, None)
