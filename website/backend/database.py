import psycopg2
from psycopg2.extras import RealDictCursor
import os

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set!")
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Faculty Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS faculty (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'faculty'
    )
    ''')
    
    # Labs Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS labs (
        id SERIAL PRIMARY KEY,
        lab_name TEXT UNIQUE NOT NULL
    )
    ''')
    
    # Fixed Schedule Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fixed_schedule (
        id SERIAL PRIMARY KEY,
        day TEXT,
        period INTEGER,
        lab TEXT,
        subject TEXT
    )
    ''')
    
    # Bookings Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id SERIAL PRIMARY KEY,
        lab_id INTEGER,
        faculty_id INTEGER,
        day TEXT,
        period INTEGER,
        booking_date TEXT,
        FOREIGN KEY (lab_id) REFERENCES labs(id) ON DELETE CASCADE,
        FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE CASCADE
    )
    ''')
    
    # Announcements Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS announcements (
        id SERIAL PRIMARY KEY,
        message TEXT NOT NULL,
        expires_at TEXT NOT NULL
    )
    ''')
    
    # Settings Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    ''')
    cursor.execute("INSERT INTO settings (key, value) VALUES ('daily_limit', '2') ON CONFLICT (key) DO NOTHING")
    
    # FCM Tokens Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fcm_tokens (
        id SERIAL PRIMARY KEY,
        faculty_id INTEGER,
        token TEXT UNIQUE NOT NULL,
        FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE CASCADE
    )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")

