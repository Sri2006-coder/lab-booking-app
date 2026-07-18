from database import init_db, get_db, return_db
from werkzeug.security import generate_password_hash
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def seed_db():
    init_db()
    conn = get_db()
    cursor = conn.cursor()
    
    # Seed Faculty (passwords are hashed before storage)
    admin_hash = generate_password_hash('admin123')
    faculty_hash = generate_password_hash('password123')
    
    cursor.execute("INSERT INTO faculty (name, email, password, role) VALUES (%s, %s, %s, %s) ON CONFLICT (email) DO NOTHING", 
                   ('Admin User', 'admin@lab.com', admin_hash, 'admin'))
    cursor.execute("INSERT INTO faculty (name, email, password, role) VALUES (%s, %s, %s, %s) ON CONFLICT (email) DO NOTHING", 
                   ('John Doe', 'john@lab.com', faculty_hash, 'faculty'))
    
    # Seed Labs
    labs = [('Lab 1',), ('Lab 2',), ('Lab 3',), ('Lab 4',), ('Lab 5',), ('Lab 6',), ('Conference Hall',), ('Seminar Hall',)]
    cursor.executemany("INSERT INTO labs (lab_name) VALUES (%s) ON CONFLICT (lab_name) DO NOTHING", labs)
    
    conn.commit()
    return_db(conn)
    logging.info("Database seeded successfully.")

if __name__ == '__main__':
    seed_db()

