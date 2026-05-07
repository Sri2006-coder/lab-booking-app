import sqlite3
import os

DB_PATH = os.path.join('website', 'data', 'lab_booking.db')

def check_tokens():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM fcm_tokens")
        rows = cursor.fetchall()
        if not rows:
            print("No tokens found in fcm_tokens table.")
        for row in rows:
            print(row)
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_tokens()
