import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def setup_database():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS doctors (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS patients (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS sessions (
        id SERIAL PRIMARY KEY,
        doctor_id INTEGER REFERENCES doctors(id),
        patient_id INTEGER REFERENCES patients(id),
        date TIMESTAMP,
        transcript TEXT,
        summary TEXT,
        audio_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    conn.commit()
    cur.close()
    conn.close()

def insert_doctor(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO doctors (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (name,))
    conn.commit()
    cur.execute("SELECT id FROM doctors WHERE name = %s", (name,))
    doctor_id = cur.fetchone()[0]
    cur.close()
    conn.close()
    return doctor_id

def insert_patient(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO patients (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (name,))
    conn.commit()
    cur.execute("SELECT id FROM patients WHERE name = %s", (name,))
    patient_id = cur.fetchone()[0]
    cur.close()
    conn.close()
    return patient_id

def insert_session(doctor_id, patient_id, date, transcript, summary, audio_path):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sessions (doctor_id, patient_id, date, transcript, summary, audio_path)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (doctor_id, patient_id, date, transcript, summary, audio_path))
    conn.commit()
    cur.close()
    conn.close()

def get_patient_names():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM patients")
    names = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return names

def get_recent_sessions(limit=5):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.date, p.name, s.summary
        FROM sessions s
        JOIN doctors d ON s.doctor_id = d.id
        JOIN patients p ON s.patient_id = p.id
        ORDER BY s.date DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
