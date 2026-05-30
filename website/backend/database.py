import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
import os
import logging

DATABASE_URL = os.environ.get("DATABASE_URL")

# Connection pool: reuse connections instead of creating a new one per request
_pool = None

def _get_pool():
    global _pool
    if _pool is None or _pool.closed:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is not set!")
        _pool = ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=DATABASE_URL,
            cursor_factory=RealDictCursor
        )
        logging.info("[OK] Database connection pool created (2-10 connections)")
    return _pool

def get_db():
    """Get a connection from the pool."""
    return _get_pool().getconn()

def return_db(conn):
    """Return a connection to the pool (use instead of conn.close())."""
    try:
        if conn and not conn.closed:
            _get_pool().putconn(conn)
    except Exception:
        # If pool is somehow broken, just close the connection
        try:
            conn.close()
        except Exception:
            pass

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
        subject TEXT,
        UNIQUE (day, period, lab)
    )
    ''')
    # Ensure unique constraint exists for databases created before this migration
    cursor.execute('''
    CREATE UNIQUE INDEX IF NOT EXISTS uq_fixed_schedule_day_period_lab
    ON fixed_schedule (day, period, lab)
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
    return_db(conn)

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")

