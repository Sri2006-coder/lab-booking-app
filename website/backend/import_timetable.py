from database import get_db
import csv
import os

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lab_booking_system', 'timetable.csv')

def import_timetable():
    if not os.path.exists(CSV_PATH):
        print(f"CSV file not found at {CSV_PATH}")
        return

    conn = get_db()
    cursor = conn.cursor()
    
    # Optional: Clear existing schedule if needed
    # cursor.execute("DELETE FROM fixed_schedule")
    
    with open(CSV_PATH, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 4:
                lab_id, day, period, subject = row[0], row[1], row[2], row[3]
                cursor.execute("INSERT INTO fixed_schedule (lab_id, day, period, subject) VALUES (?, ?, ?, ?)",
                               (lab_id, day, period, subject))
    
    conn.commit()
    conn.close()
    print("Timetable data imported successfully from CSV.")

if __name__ == '__main__':
    import_timetable()
