from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.enums import UserRole
from models.symptom_triage import ConsultantSuggestion, SymptomTriageResponse
from models.user import User


@dataclass(frozen=True)
class CategoryRule:
    category: str
    keywords: tuple[str, ...]
    doctor_emails: tuple[str, ...]
    reason: str


class SymptomTriageService:
    def __init__(self) -> None:
        self.red_flag_keywords = (
            "chest pain",
            "difficulty breathing",
            "shortness of breath",
            "severe bleeding",
            "passed out",
            "unconscious",
            "stroke",
            "one side weak",
            "seizure",
            "suicidal",
            "cannot breathe",
        )
        self.category_rules = (
            CategoryRule(
                category="ENT",
                keywords=("ear pain", "sore throat", "tonsil", "sinus", "blocked nose", "runny nose"),
                doctor_emails=("doctor2@mediscript.com",),
                reason="Symptoms mainly involve the ear, nose, or throat.",
            ),
            CategoryRule(
                category="Dermatology",
                keywords=("rash", "itching", "itchy", "skin", "eczema", "acne", "hives"),
                doctor_emails=("doctor2@mediscript.com",),
                reason="Symptoms mainly involve the skin.",
            ),
            CategoryRule(
                category="Orthopedics",
                keywords=("back pain", "joint pain", "knee pain", "shoulder pain", "fracture", "sprain"),
                doctor_emails=("doctor2@mediscript.com",),
                reason="Symptoms mainly involve bones, joints, or musculoskeletal pain.",
            ),
            CategoryRule(
                category="Pediatrics",
                keywords=("my child", "my baby", "infant", "toddler", "child has fever"),
                doctor_emails=("doctor1@mediscript.com",),
                reason="The message appears to be about a child.",
            ),
            CategoryRule(
                category="Gynecology",
                keywords=("pregnant", "pregnancy", "period pain", "vaginal bleeding", "missed period"),
                doctor_emails=("doctor2@mediscript.com",),
                reason="Symptoms mainly relate to women's health.",
            ),
            CategoryRule(
                category="Cardiology",
                keywords=("palpitations", "high blood pressure", "heart racing", "swollen legs"),
                doctor_emails=("doctor1@mediscript.com",),
                reason="Symptoms may need heart-related review.",
            ),
            CategoryRule(
                category="Neurology",
                keywords=("headache", "migraine", "numbness", "vertigo", "dizziness", "fainting"),
                doctor_emails=("doctor1@mediscript.com",),
                reason="Symptoms may need nerve or brain-related review.",
            ),
            CategoryRule(
                category="General Medicine",
                keywords=("fever", "cough", "body pain", "fatigue", "vomiting", "diarrhea", "stomach pain"),
                doctor_emails=("doctor1@mediscript.com", "doctor2@mediscript.com"),
                reason="Symptoms fit a general medical consultation best.",
            ),
        )

    async def triage(self, db: AsyncSession, message: str, patient_name: str | None = None) -> SymptomTriageResponse:
        normalized = self._normalize(message)
        extracted_symptoms = self._extract_symptoms(normalized)
        matched_red_flags = self._matched_keywords(normalized, self.red_flag_keywords)

        if matched_red_flags:
            consultants = await self._load_consultants(
                db,
                category="Emergency / Immediate Review",
                preferred_emails=("doctor1@mediscript.com", "doctor2@mediscript.com"),
                fallback_reason="Urgent symptoms were detected and need immediate medical review.",
            )
            return SymptomTriageResponse(
                category="Emergency / Immediate Review",
                urgency="high",
                urgency_message=(
                    "Some symptoms sound urgent. Please seek immediate medical care or go to the emergency unit."
                ),
                extracted_symptoms=extracted_symptoms,
                matched_keywords=list(matched_red_flags),
                channeling_message=(
                    "Urgent symptoms were detected, so normal channeling should be skipped and immediate care is recommended."
                ),
                consultants=consultants,
            )

        best_rule = self._best_rule(normalized)
        consultants = await self._load_consultants(
            db,
            category=best_rule.category,
            preferred_emails=best_rule.doctor_emails,
            fallback_reason=best_rule.reason,
        )
        patient_prefix = f"{patient_name.strip()}, " if patient_name and patient_name.strip() else ""
        return SymptomTriageResponse(
            category=best_rule.category,
            urgency="routine",
            urgency_message="No immediate emergency red flags were detected from this message.",
            extracted_symptoms=extracted_symptoms,
            matched_keywords=list(self._matched_keywords(normalized, best_rule.keywords)),
            channeling_message=(
                f"{patient_prefix}the best consultant category for these symptoms appears to be "
                f"{best_rule.category}. {best_rule.reason}"
            ),
            consultants=consultants,
        )

    def _normalize(self, text: str) -> str:
        cleaned = text.strip().lower()
        return re.sub(r"\s+", " ", cleaned)

    def _extract_symptoms(self, text: str) -> list[str]:
        chunks = re.split(r",| and | with | also | but ", text)
        symptoms: list[str] = []
        for chunk in chunks:
            value = chunk.strip(" .!?")
            if len(value) < 3:
                continue
            if value not in symptoms:
                symptoms.append(value)
        return symptoms[:8]

    def _matched_keywords(self, text: str, keywords: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(keyword for keyword in keywords if keyword in text)

    def _best_rule(self, text: str) -> CategoryRule:
        scored: list[tuple[int, CategoryRule]] = []
        for rule in self.category_rules:
            score = sum(1 for keyword in rule.keywords if keyword in text)
            if score:
                scored.append((score, rule))

        if not scored:
            for rule in self.category_rules:
                if rule.category == "General Medicine":
                    return rule
            return self.category_rules[-1]

        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[0][1]

    async def _load_consultants(
        self,
        db: AsyncSession,
        *,
        category: str,
        preferred_emails: tuple[str, ...],
        fallback_reason: str,
    ) -> list[ConsultantSuggestion]:
        result = await db.execute(
            select(User).where(User.role == UserRole.DOCTOR, User.is_active.is_(True)).order_by(User.full_name.asc())
        )
        doctors = result.scalars().all()
        by_email = {doctor.email: doctor for doctor in doctors}

        selected: list[User] = [by_email[email] for email in preferred_emails if email in by_email]
        if not selected:
            selected = doctors[:2]

        return [
            ConsultantSuggestion(
                doctor_id=doctor.id,
                doctor_name=doctor.full_name,
                category=category,
                reason=fallback_reason,
            )
            for doctor in selected
        ]
