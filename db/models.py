from passlib.hash import bcrypt
from db.pool import get_conn, put_conn
import json


def setup_database():
    conn = get_conn()
    cur = conn.cursor()

    # Users table
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );"""
    )

    # Doctors table
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS doctors (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );"""
    )

    # Patients table
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS patients (
        id SERIAL PRIMARY KEY,
        name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );"""
    )

    # Sessions table (with structured summary fields)
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS sessions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        doctor_id INTEGER REFERENCES doctors(id),
        patient_id INTEGER REFERENCES patients(id),
        date TIMESTAMP,
        transcript TEXT,
        patient_complaint TEXT,
        clinical_notes TEXT,
        diagnosis TEXT,
        treatment_plan TEXT,
        audio_path TEXT,
        audio_hash TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (user_id, audio_hash)
    );"""
    )

    conn.commit()
    cur.close()
    put_conn(conn)


def create_user(email: str, password: str) -> int:
    """Hash the password and insert a new user; returns user id."""
    pwd_hash = bcrypt.hash(password)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (email, password_hash) VALUES (%s, %s) ON CONFLICT (email) DO NOTHING",
        (email, pwd_hash),
    )
    conn.commit()
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    user_id = cur.fetchone()[0]
    cur.close()
    put_conn(conn)
    return user_id


def authenticate_user(email: str, password: str) -> bool:
    """Return True if email exists and password matches."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE email = %s", (email,))
    row = cur.fetchone()
    cur.close()
    put_conn(conn)
    if not row:
        return False
    stored_hash = row[0]
    return bcrypt.verify(password, stored_hash)


def insert_doctor(name: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO doctors (name)
        VALUES (%s)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        (name,),
    )

    doctor_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    put_conn(conn)
    return doctor_id


def insert_patient(name: str) -> int:
    """
    Inserts a new patient record and returns its ID.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO patients (name)
        VALUES (%s)
        RETURNING id
        """,
        (name,),
    )
    patient_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    put_conn(conn)
    return patient_id


def insert_session(
    user_id,
    doctor_id,
    patient_id,
    date,
    transcript,
    patient_complaint,
    clinical_notes,
    diagnosis,
    treatment_plan,
    audio_path,
    audio_hash,
):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO sessions (
            user_id, doctor_id, patient_id, date,
            transcript, patient_complaint, clinical_notes,
            diagnosis, treatment_plan,
            audio_path, audio_hash
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
        """,
        (
            user_id,
            doctor_id,
            patient_id,
            date,
            transcript,
            patient_complaint,
            clinical_notes,
            diagnosis,
            treatment_plan,
            audio_path,
            audio_hash,
        ),
    )
    sess_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    put_conn(conn)
    return sess_id


def get_patient_names():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM patients")
    names = [row[0] for row in cur.fetchall()]
    cur.close()
    put_conn(conn)
    return names


def get_recent_sessions(user_id, limit=5):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT s.date, p.name, s.summary
        FROM sessions s
        JOIN patients p ON s.patient_id = p.id
        WHERE s.user_id = %s
        ORDER BY s.date DESC
        LIMIT %s
        """,
        (user_id, limit),
    )
    rows = cur.fetchall()
    cur.close()
    put_conn(conn)
    return rows


def get_user_id(email: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    user_id = cur.fetchone()[0]
    cur.close()
    put_conn(conn)
    return user_id


def user_exists(email: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
    exists = cur.fetchone() is not None
    cur.close()
    put_conn(conn)
    return exists


def get_session_details_by_index(user_id: int, limit: int = 20):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT s.id, s.date, d.name, p.name, s.transcript,
               s.patient_complaint, s.clinical_notes, s.diagnosis, s.treatment_plan
        FROM sessions s
        JOIN doctors d ON s.doctor_id = d.id
        JOIN patients p ON s.patient_id = p.id
        WHERE s.user_id = %s
        ORDER BY s.date DESC
        LIMIT %s
        """,
        (user_id, limit),
    )
    sessions = cur.fetchall()
    cur.close()
    put_conn(conn)

    formatted_sessions = []
    for sess in sessions:
        sess_id, date, doc_name, pat_name, tr, pc, cn, diag, tp = sess
        summary = json.dumps(
            {
                "Patient Complaint": pc or "No readout",
                "Clinical Notes": cn or "No readout",
                "Diagnosis": diag or "No readout",
                "Treatment Plan": tp or "No readout",
            },
            ensure_ascii=False,
        )
        formatted_sessions.append((sess_id, date, doc_name, pat_name, tr, summary))

    return formatted_sessions


def get_existing_session_by_hash(user_id: int, audio_hash: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT transcript, patient_complaint, clinical_notes, diagnosis, treatment_plan, date
        FROM sessions
        WHERE user_id = %s AND audio_hash = %s
        ORDER BY date DESC LIMIT 1
        """,
        (user_id, audio_hash),
    )
    row = cur.fetchone()
    cur.close()
    put_conn(conn)
    if not row:
        return None
    tr, pc, cn, diag, tp, dt = row
    summary = json.dumps(
        {
            "Patient Complaint": pc or "No readout",
            "Clinical Notes": cn or "No readout",
            "Diagnosis": diag or "No readout",
            "Treatment Plan": tp or "No readout",
        },
        ensure_ascii=False,
    )
    return dict(transcript=tr, summary_raw=summary, date=dt)
