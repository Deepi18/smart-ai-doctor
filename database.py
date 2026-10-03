import sqlite3
import os
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

def get_db_connection():
    """Establishes connection to SQLite database."""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes database schemas for users, assessments, doctors, prescriptions, and knowledge base."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'patient',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Patient Diagnostic Assessments Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            patient_name TEXT NOT NULL,
            patient_age INTEGER,
            patient_gender TEXT,
            symptoms TEXT NOT NULL,
            ml_predictions_json TEXT,
            ai_summary TEXT,
            overall_urgency TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # 3. Specialist Doctors & Medical Institutions Directory Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            experience_years INTEGER,
            hospital TEXT,
            rating REAL,
            phone TEXT,
            email TEXT,
            location TEXT,
            availability TEXT,
            source_url TEXT,
            source_type TEXT,
            last_verified TEXT
        )
    ''')

    # 4. Medical Knowledge Base Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            condition_name TEXT NOT NULL UNIQUE,
            category TEXT,
            description TEXT NOT NULL,
            symptoms TEXT,
            precautions TEXT,
            risk_factors TEXT,
            specialist TEXT
        )
    ''')

    # 5. Doctor Appointment Bookings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            doctor_id INTEGER,
            doctor_name TEXT,
            patient_name TEXT NOT NULL,
            patient_email TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(doctor_id) REFERENCES doctors(id)
        )
    ''')

    # 6. Prescription Safety Checks Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prescription_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            patient_name TEXT,
            prescribed_medicine TEXT NOT NULL,
            status TEXT NOT NULL,
            status_label TEXT,
            flags_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Auto-migrate existing SQLite tables if missing columns
    doctor_cols = [row['name'] for row in cursor.execute("PRAGMA table_info(doctors)").fetchall()]
    if 'source_url' not in doctor_cols:
        cursor.execute("ALTER TABLE doctors ADD COLUMN source_url TEXT")
    if 'source_type' not in doctor_cols:
        cursor.execute("ALTER TABLE doctors ADD COLUMN source_type TEXT")
    if 'last_verified' not in doctor_cols:
        cursor.execute("ALTER TABLE doctors ADD COLUMN last_verified TEXT")

    assessment_cols = [row['name'] for row in cursor.execute("PRAGMA table_info(assessments)").fetchall()]
    if 'user_id' not in assessment_cols:
        cursor.execute("ALTER TABLE assessments ADD COLUMN user_id INTEGER")

    appointment_cols = [row['name'] for row in cursor.execute("PRAGMA table_info(appointments)").fetchall()]
    if 'user_id' not in appointment_cols:
        cursor.execute("ALTER TABLE appointments ADD COLUMN user_id INTEGER")

    conn.commit()

    # Seed Admin User if not exists
    cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', ('admin', 'admin@smartdoctor.ai'))
    if not cursor.fetchone():
        admin_hash = generate_password_hash('AdminSecurePass2026!')
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        ''', ('admin', 'admin@smartdoctor.ai', admin_hash, 'admin'))
        conn.commit()

    conn.close()

# User Management Functions
def create_user(username, email, password, role='patient'):
    """Registers a new user with hashed password."""
    conn = get_db_connection()
    cursor = conn.cursor()
    pwd_hash = generate_password_hash(password)
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        ''', (username, email, pwd_hash, role))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id, None
    except sqlite3.IntegrityError:
        conn.close()
        return None, "Username or email already exists."

def authenticate_user(identifier, password):
    """Authenticates user by username or email."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (identifier, identifier))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user['password_hash'], password):
        return dict(user)
    return None

def save_assessment(patient_name, patient_age, patient_gender, symptoms, ml_predictions, ai_summary, overall_urgency, user_id=None):
    """Saves assessment report to SQLite DB."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO assessments (user_id, patient_name, patient_age, patient_gender, symptoms, ml_predictions_json, ai_summary, overall_urgency)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, patient_name, patient_age, patient_gender, symptoms, json.dumps(ml_predictions), ai_summary, overall_urgency))
    conn.commit()
    assessment_id = cursor.lastrowid
    conn.close()
    return assessment_id

def get_user_assessments(user_id=None):
    """Fetches diagnostic assessment history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute('SELECT * FROM assessments WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    else:
        cursor.execute('SELECT * FROM assessments ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        item = dict(r)
        try:
            item['ml_predictions'] = json.loads(r['ml_predictions_json']) if r['ml_predictions_json'] else []
        except Exception:
            item['ml_predictions'] = []
        result.append(item)
    return result

def get_assessment_by_id(assessment_id):
    """Fetches single assessment record by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM assessments WHERE id = ?', (assessment_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    item = dict(row)
    try:
        item['ml_predictions'] = json.loads(row['ml_predictions_json']) if row['ml_predictions_json'] else []
    except Exception:
        item['ml_predictions'] = []
    return item

def delete_assessment(assessment_id, user_id=None):
    """Deletes an assessment record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute('DELETE FROM assessments WHERE id = ? AND user_id = ?', (assessment_id, user_id))
    else:
        cursor.execute('DELETE FROM assessments WHERE id = ?', (assessment_id,))
    conn.commit()
    conn.close()

def get_doctors(specialty='All', search_query=''):
    """Fetches specialist doctors directory filtered by specialty and query."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM doctors WHERE 1=1'
    params = []
    
    if specialty and specialty != 'All':
        query += ' AND specialty LIKE ?'
        params.append(f'%{specialty}%')
        
    if search_query:
        query += ' AND (name LIKE ? OR hospital LIKE ? OR location LIKE ?)'
        search_fmt = f'%{search_query}%'
        params.extend([search_fmt, search_fmt, search_fmt])
        
    query += ' ORDER BY name ASC'
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_appointment(doctor_id, doctor_name, patient_name, patient_email, appointment_date, reason='', user_id=None):
    """Creates a new appointment booking record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO appointments (user_id, doctor_id, doctor_name, patient_name, patient_email, appointment_date, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, doctor_id, doctor_name, patient_name, patient_email, appointment_date, reason))
    conn.commit()
    booking_id = cursor.lastrowid
    conn.close()
    return booking_id

def save_prescription_check(user_id, patient_name, prescribed_medicine, status, status_label, flags):
    """Logs prescription safety review to database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO prescription_checks (user_id, patient_name, prescribed_medicine, status, status_label, flags_json)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, patient_name, prescribed_medicine, status, status_label, json.dumps(flags)))
    conn.commit()
    check_id = cursor.lastrowid
    conn.close()
    return check_id

def get_knowledge_items(search_query='', category='All'):
    """Fetches articles from the Medical Knowledge Base table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM knowledge_base WHERE 1=1'
    params = []
    
    if category and category != 'All':
        query += ' AND category = ?'
        params.append(category)
        
    if search_query:
        query += ' AND (condition_name LIKE ? OR description LIKE ? OR symptoms LIKE ?)'
        s_fmt = f'%{search_query}%'
        params.extend([s_fmt, s_fmt, s_fmt])
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
