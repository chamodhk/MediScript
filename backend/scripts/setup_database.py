"""
Fully initialize the local MediScript SQLite database.

Run from the backend/ directory:
    python scripts/setup_database.py

Optional flags:
    --db-path mediscript.db
    --reset
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

import bcrypt

PROJECT_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_BACKEND_ROOT))

from core.seed import (  # noqa: E402
    DEFAULT_USERS,
    DEMO_PATIENTS,
    PHARMACIES,
    PLACEHOLDER_PNG_BYTES,
    TEST_PRESCRIPTION_STATUSES,
)

LATEST_ALEMBIC_REVISION = "d157c7b7457c"
DEFAULT_PASSWORD = "password@123"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS alembic_version (
  version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS patients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(200) NOT NULL,
  phone VARCHAR(20) NOT NULL UNIQUE,
  preferred_language VARCHAR(5) NOT NULL DEFAULT 'en',
  date_of_birth DATE,
  age INTEGER,
  token VARCHAR(20) UNIQUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_patients_phone ON patients (phone);
CREATE INDEX IF NOT EXISTS ix_patients_token ON patients (token);

CREATE TABLE IF NOT EXISTS pharmacies (
  id INTEGER PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  is_available BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(200) NOT NULL,
  role VARCHAR(20) NOT NULL,
  is_active BOOLEAN NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS consultations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_id INTEGER NOT NULL,
  doctor_id INTEGER NOT NULL,
  transcript TEXT,
  structured_output JSON,
  audio_file_path VARCHAR(500),
  status VARCHAR(20) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(patient_id) REFERENCES patients(id),
  FOREIGN KEY(doctor_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS ix_consultations_patient_id ON consultations (patient_id);
CREATE INDEX IF NOT EXISTS ix_consultations_doctor_id ON consultations (doctor_id);

CREATE TABLE IF NOT EXISTS reminders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_id INTEGER NOT NULL,
  consultation_id INTEGER NOT NULL,
  message TEXT NOT NULL,
  scheduled_at DATETIME NOT NULL,
  sent_at DATETIME,
  type VARCHAR(20) NOT NULL,
  status VARCHAR(20) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(patient_id) REFERENCES patients(id),
  FOREIGN KEY(consultation_id) REFERENCES consultations(id)
);
CREATE INDEX IF NOT EXISTS ix_reminders_patient_id ON reminders (patient_id);
CREATE INDEX IF NOT EXISTS ix_reminders_consultation_id ON reminders (consultation_id);

CREATE TABLE IF NOT EXISTS prescriptions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  consultation_id INTEGER NOT NULL UNIQUE,
  pharmacy_id INTEGER NOT NULL,
  image_path VARCHAR(500),
  status VARCHAR(20) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  image_data BLOB,
  image_mime_type VARCHAR(64) NOT NULL DEFAULT 'image/png',
  FOREIGN KEY(consultation_id) REFERENCES consultations(id),
  FOREIGN KEY(pharmacy_id) REFERENCES pharmacies(id)
);
CREATE INDEX IF NOT EXISTS ix_prescriptions_consultation_id ON prescriptions (consultation_id);
CREATE INDEX IF NOT EXISTS ix_prescriptions_pharmacy_id ON prescriptions (pharmacy_id);
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create and seed the local MediScript database")
    parser.add_argument(
        "--db-path",
        default="mediscript.db",
        help="Path to the SQLite database file, relative to backend/ by default",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the existing database file before recreating it",
    )
    return parser.parse_args()


def resolve_db_path(raw_path: str) -> Path:
    db_path = Path(raw_path)
    if not db_path.is_absolute():
        db_path = PROJECT_BACKEND_ROOT / db_path
    return db_path


def ensure_parent_dir(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)


def maybe_reset_db(db_path: Path, reset: bool) -> None:
    if reset and db_path.exists():
        db_path.unlink()


def create_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(cur: sqlite3.Cursor) -> None:
    cur.executescript(SCHEMA_SQL)


def seed_pharmacies(cur: sqlite3.Cursor) -> None:
    for pharmacy in PHARMACIES:
        cur.execute(
            """
            INSERT INTO pharmacies (id, name, is_available)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              name = excluded.name,
              is_available = excluded.is_available
            """,
            (pharmacy["id"], pharmacy["name"], int(pharmacy["is_available"])),
        )


def seed_users(cur: sqlite3.Cursor) -> None:
    allowed_emails = [user["email"] for user in DEFAULT_USERS]
    placeholders = ",".join("?" for _ in allowed_emails)
    cur.execute(f"DELETE FROM users WHERE email NOT IN ({placeholders})", allowed_emails)

    password_hash = bcrypt.hashpw(DEFAULT_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    for user in DEFAULT_USERS:
        cur.execute(
            """
            INSERT INTO users (email, password_hash, full_name, role, is_active)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
              password_hash = excluded.password_hash,
              full_name = excluded.full_name,
              role = excluded.role,
              is_active = excluded.is_active
            """,
            (
                user["email"],
                password_hash,
                user["full_name"],
                user["role"].value,
                1,
            ),
        )


def seed_patients(cur: sqlite3.Cursor) -> None:
    for patient in DEMO_PATIENTS:
        cur.execute("SELECT id FROM patients WHERE phone = ?", (patient["phone"],))
        if cur.fetchone() is None:
            cur.execute(
                """
                INSERT INTO patients (
                  name, phone, preferred_language, date_of_birth, age, token
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    patient["name"],
                    patient["phone"],
                    patient["preferred_language"],
                    patient["date_of_birth"].isoformat(),
                    patient["age"],
                    patient["token"],
                ),
            )


def load_doctor_id(cur: sqlite3.Cursor) -> int | None:
    cur.execute("SELECT id FROM users WHERE email = ?", ("doctor1@mediscript.com",))
    row = cur.fetchone()
    return row[0] if row else None


def load_patient_ids(cur: sqlite3.Cursor) -> dict[str, int]:
    ids: dict[str, int] = {}
    for patient in DEMO_PATIENTS:
        cur.execute("SELECT id FROM patients WHERE phone = ?", (patient["phone"],))
        row = cur.fetchone()
        if row:
            ids[patient["phone"]] = row[0]
    return ids


def seed_demo_queue(cur: sqlite3.Cursor) -> None:
    doctor_id = load_doctor_id(cur)
    if doctor_id is None:
        return

    patient_ids = load_patient_ids(cur)
    cur.execute("SELECT COALESCE(MAX(id), 0) FROM consultations")
    next_consultation_id = cur.fetchone()[0] + 1

    for index, status in enumerate(TEST_PRESCRIPTION_STATUSES):
        cur.execute(
            """
            SELECT id, image_data
            FROM prescriptions
            WHERE pharmacy_id = 1 AND status = ?
            ORDER BY id ASC
            LIMIT 1
            """,
            (status,),
        )
        existing = cur.fetchone()
        if existing:
            if existing[1] is None:
                cur.execute(
                    """
                    UPDATE prescriptions
                    SET image_data = ?, image_mime_type = ?
                    WHERE id = ?
                    """,
                    (PLACEHOLDER_PNG_BYTES, "image/png", existing[0]),
                )
            continue

        patient = DEMO_PATIENTS[index % len(DEMO_PATIENTS)]
        patient_id = patient_ids.get(patient["phone"])
        if patient_id is None:
            continue

        cur.execute(
            """
            INSERT INTO consultations (id, patient_id, doctor_id, status)
            VALUES (?, ?, ?, ?)
            """,
            (next_consultation_id, patient_id, doctor_id, "in_progress"),
        )
        cur.execute(
            """
            INSERT INTO prescriptions (
              consultation_id, pharmacy_id, status, image_data, image_mime_type
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (next_consultation_id, 1, status, PLACEHOLDER_PNG_BYTES, "image/png"),
        )
        next_consultation_id += 1


def stamp_revision(cur: sqlite3.Cursor) -> None:
    cur.execute("DELETE FROM alembic_version")
    cur.execute("INSERT INTO alembic_version (version_num) VALUES (?)", (LATEST_ALEMBIC_REVISION,))


def print_summary(cur: sqlite3.Cursor, db_path: Path) -> None:
    print(f"Database ready: {db_path}")
    print("alembic:", cur.execute("SELECT version_num FROM alembic_version").fetchone()[0])
    print("users:", cur.execute("SELECT COUNT(*) FROM users").fetchone()[0])
    print("patients:", cur.execute("SELECT COUNT(*) FROM patients").fetchone()[0])
    print("consultations:", cur.execute("SELECT COUNT(*) FROM consultations").fetchone()[0])
    print("prescriptions:", cur.execute("SELECT COUNT(*) FROM prescriptions").fetchone()[0])


def main() -> None:
    args = parse_args()
    db_path = resolve_db_path(args.db_path)

    ensure_parent_dir(db_path)
    maybe_reset_db(db_path, args.reset)

    conn = create_connection(db_path)
    try:
        cur = conn.cursor()
        create_schema(cur)
        seed_pharmacies(cur)
        seed_users(cur)
        seed_patients(cur)
        seed_demo_queue(cur)
        stamp_revision(cur)
        conn.commit()
        print_summary(cur, db_path)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
