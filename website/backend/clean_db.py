from database import get_db

def clean_labs():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM labs")
    
    clean_list = ["Lab 1", "Lab 2", "Lab 5", "Lab 6", "Lab 7", "Seminar Hall", "Conference Hall"]
    for lab in clean_list:
        cursor.execute("INSERT INTO labs (lab_name) VALUES (?)", (lab,))
        
    conn.commit()
    conn.close()
    print("Database labs cleaned and resynced.")

if __name__ == "__main__":
    clean_labs()
