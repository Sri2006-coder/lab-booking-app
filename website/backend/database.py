import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'lab_booking.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Faculty Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS faculty (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'faculty'
    )
    ''')
    
    # Labs Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS labs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lab_name TEXT NOT NULL
    )
    ''')
    
    # Fixed Schedule Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fixed_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT,
        period INTEGER,
        lab TEXT
    )
    ''')
    
    # Bookings Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lab_id INTEGER,
        faculty_id INTEGER,
        day TEXT,
        period INTEGER,
        booking_date TEXT,
        FOREIGN KEY (lab_id) REFERENCES labs(id),
        FOREIGN KEY (faculty_id) REFERENCES faculty(id)
    )
    ''')
    
    # Announcements Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('daily_limit', '2')")
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
