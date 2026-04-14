from database import init_db, get_db

def seed_db():
    init_db()
    conn = get_db()
    cursor = conn.cursor()
    
    # Seed Faculty
    cursor.execute("INSERT OR IGNORE INTO faculty (name, email, password, role) VALUES (?, ?, ?, ?)", 
                   ('Admin User', 'admin@lab.com', 'admin123', 'admin'))
    cursor.execute("INSERT OR IGNORE INTO faculty (name, email, password, role) VALUES (?, ?, ?, ?)", 
                   ('John Doe', 'john@lab.com', 'password123', 'faculty'))
    
    # Seed Labs
    labs = [('Lab 1',), ('Lab 2',), ('Conference Hall',), ('Seminar Hall',), ('Lab 5',), ('Lab 6',), ('Lab 7',)]
    cursor.executemany("INSERT INTO labs (lab_name) VALUES (?)", labs)
    
    conn.commit()
    conn.close()
    print("Database seeded successfully.")

if __name__ == '__main__':
    seed_db()
