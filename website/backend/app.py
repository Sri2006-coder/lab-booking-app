from flask import Flask, request, jsonify, session, send_from_directory
from database import get_db
import os
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='../frontend')
app.secret_key = 'super_secret_key_for_lab_booking'
app.permanent_session_lifetime = timedelta(minutes=10)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faculty WHERE email=? AND password=?", (email, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session.permanent = True
        session['user_id'] = user['id']
        session['role'] = user['role']
        session['name'] = user['name']
        return jsonify({"success": True, "role": user['role'], "name": user['name']})
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route('/api/logout')
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route('/api/stats')
def get_stats():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM bookings")
    total_bookings = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM faculty")
    total_faculty = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(DISTINCT lab_id) as total FROM fixed_schedule")
    active_labs = cursor.fetchone()['total']
    
    conn.close()
    return jsonify({
        "totalBookings": total_bookings,
        "totalFaculty": total_faculty,
        "activeLabs": active_labs
    })

@app.route('/get_limit', methods=['GET'])
def get_limit():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key='daily_limit'")
    setting = cursor.fetchone()
    conn.close()
    
    limit = int(setting['value']) if setting else 2
    return jsonify({"limit": limit})

@app.route('/update_limit', methods=['POST'])
def update_limit():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    data = request.get_json()
    new_limit = data.get('limit')
    if new_limit is None:
        return jsonify({"success": False, "message": "Missing limit"}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('daily_limit', ?)", (str(new_limit),))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "limit": new_limit})

@app.route('/download_sample', methods=['GET'])
def download_sample():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    from flask import Response
    csv_content = "day,period,lab,subject\nMonday,1,Lab1,Math\nMonday,2,Lab2,Physics\nTuesday,1,Lab1,Chemistry\n"
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=sample_timetable.csv"}
    )

@app.route('/clear_timetable', methods=['POST'])
def clear_timetable():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fixed_schedule")
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/notice', methods=['GET', 'POST'])
def handle_notice():
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        if 'user_id' not in session or session['role'] != 'admin':
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        
        data = request.get_json()
        message = data.get('message')
        # Expires in 1 hour if not specified
        expires_at = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("INSERT INTO announcements (message, expires_at) VALUES (?, ?)", (message, expires_at))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    
    else:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("SELECT * FROM announcements WHERE expires_at > ? ORDER BY id DESC LIMIT 1", (now,))
        notice = cursor.fetchone()
        conn.close()
        
        if notice:
            remaining = datetime.strptime(notice['expires_at'], "%Y-%m-%d %H:%M:%S") - datetime.now()
            minutes = max(0, int(remaining.total_seconds() // 60))
            return jsonify({"message": notice['message'], "minutes": minutes})
        else:
            return jsonify(None)

@app.route('/api/notices', methods=['GET'])
def get_all_notices():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM announcements ORDER BY id DESC")
    notices = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(notices)

@app.route('/api/timetable')
def get_timetable():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    date = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
    labs_param = request.args.get('labs', '1,2')
    lab_ids = [int(x) for x in labs_param.split(',')]
    day = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get basic lab info
    if not lab_ids:
        return jsonify({"date": date, "day": day, "labs": [], "fixed": [], "bookings": []})
        
    placeholders = ','.join('?' for _ in lab_ids)
    cursor.execute(f"SELECT id, lab_name FROM labs WHERE id IN ({placeholders})", lab_ids)
    labs_info = [dict(row) for row in cursor.fetchall()]
    
    lab_names = [row['lab_name'] for row in labs_info]
    
    # Get fixed schedule data directly using lab TEXT matching
    if lab_names:
        placeholders_names = ','.join('?' for _ in lab_names)
        cursor.execute(f"SELECT * FROM fixed_schedule WHERE day=? AND lab IN ({placeholders_names})", [day] + lab_names)
        fixed_data = [dict(row) for row in cursor.fetchall()]
    else:
        fixed_data = []
        
    # Get booking data
    cursor.execute(f"""
        SELECT b.*, f.name as faculty_name 
        FROM bookings b 
        JOIN faculty f ON b.faculty_id = f.id 
        WHERE b.booking_date=? AND b.lab_id IN ({placeholders})
    """, [date] + lab_ids)
    
    bookings_data = []
    user_id = session.get('user_id')
    role = session.get('role')
    for row in cursor.fetchall():
        b_dict = dict(row)
        b_dict['own'] = (b_dict['faculty_id'] == user_id or role == 'admin')
        bookings_data.append(b_dict)
    
    conn.close()
    
    return jsonify({
        "day": day,
        "date": date,
        "labs": labs_info,
        "fixed": fixed_data,
        "bookings": bookings_data
    })

@app.route('/api/book', methods=['POST'])
def book_slot():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    data = request.get_json()
    lab_id = data.get('lab')
    period = data.get('period')
    day = data.get('day')
    date = data.get('date')
    faculty_id = session['user_id']
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check dynamic limit
    cursor.execute("SELECT COUNT(*) as total FROM bookings WHERE faculty_id=? AND booking_date=?", (faculty_id, date))
    total_bookings = cursor.fetchone()['total']
    
    cursor.execute("SELECT value FROM settings WHERE key='daily_limit'")
    setting_row = cursor.fetchone()
    daily_limit = int(setting_row['value']) if setting_row else 2
    
    if daily_limit > 0 and total_bookings >= daily_limit:
        conn.close()
        return jsonify({"success": False, "message": "limit"})
    
    # Check if slot is already in fixed schedule
    cursor.execute("SELECT lab_name FROM labs WHERE id=?", (lab_id,))
    lab_row = cursor.fetchone()
    if not lab_row:
        conn.close()
        return jsonify({"success": False, "message": "invalid_lab"})
    
    lab_name = lab_row['lab_name']
    cursor.execute("SELECT id FROM fixed_schedule WHERE lab=? AND day=? AND period=?", (lab_name, day, period))
    if cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "fixed"})

    # Check if already booked
    cursor.execute("SELECT id FROM bookings WHERE lab_id=? AND day=? AND period=? AND booking_date=?", (lab_id, day, period, date))
    if cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "booked"})
    
    # Insert booking
    cursor.execute("INSERT INTO bookings (lab_id, faculty_id, day, period, booking_date) VALUES (?, ?, ?, ?, ?)",
                   (lab_id, faculty_id, day, period, date))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/cancel_booking/<int:id>', methods=['DELETE'])
def cancel_booking(id):
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check ownership
    cursor.execute("SELECT faculty_id FROM bookings WHERE id=?", (id,))
    booking = cursor.fetchone()
    if not booking or (booking['faculty_id'] != session['user_id'] and session['role'] != 'admin'):
        conn.close()
        return jsonify({"success": False, "message": "Forbidden"}), 403
    
    cursor.execute("DELETE FROM bookings WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/upload', methods=['POST'])
def upload_timetable():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file part"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file"})

    import csv
    import io
    
    try:
        content = file.stream.read().decode("UTF-8", errors="replace")
        stream = io.StringIO(content)
        
        # Check header
        header_line = stream.readline()
        if not header_line:
            return jsonify({"success": False, "message": "Empty file"})
            
        header = [h.strip().lower() for h in header_line.split(',')]
        expected_header = ['day', 'period', 'lab', 'subject']
        if not all(h in header for h in expected_header):
            return jsonify({"success": False, "message": "Invalid file format. Required columns: day, period, lab, subject"})

        stream.seek(0)
        csv_input = csv.DictReader(stream, skipinitialspace=True)
        csv_input.fieldnames = [f.strip().lower() for f in csv_input.fieldnames]
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Note: We do NOT clear the timetable here anymore as per requirements, 
        # let the admin use the "Clear Timetable" button if needed.
        
        count = 0
        for row in csv_input:
            day = row.get('day', '').strip()
            period_str = row.get('period', '').strip()
            lab_name = row.get('lab', '').strip()
            subject = row.get('subject', '').strip()

            if not day or not period_str or not lab_name or not subject:
                continue
                
            try:
                period = int(period_str)
            except ValueError:
                print(f"Skipping row due to invalid integer conversion: {row}")
                continue
            
            cursor.execute("INSERT INTO fixed_schedule (lab, day, period, subject) VALUES (?, ?, ?, ?)",
                           (lab_name, day, period, subject))
            count += 1
        
        conn.commit()
        conn.close()
        print(f"Successfully uploaded {count} fixed schedule entries.")
        return jsonify({"success": True, "count": count})
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/labs', methods=['GET', 'POST'])
def handle_labs():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        if session['role'] != 'admin':
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        data = request.get_json()
        lab_name = data.get('name')
        cursor.execute("INSERT INTO labs (lab_name) VALUES (?)", (lab_name,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    else:
        cursor.execute("SELECT * FROM labs")
        labs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(labs)

@app.route('/api/mybookings')
def get_my_bookings():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    faculty_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    
    if session['role'] == 'admin':
        cursor.execute("""
            SELECT b.*, l.lab_name, f.name as faculty_name
            FROM bookings b 
            JOIN labs l ON b.lab_id = l.id 
            JOIN faculty f ON b.faculty_id = f.id
            ORDER BY b.booking_date DESC, b.period ASC
        """)
    else:
        cursor.execute("""
            SELECT b.*, l.lab_name 
            FROM bookings b 
            JOIN labs l ON b.lab_id = l.id 
            WHERE b.faculty_id = ? 
            ORDER BY b.booking_date DESC, b.period ASC
        """, (faculty_id,))
    
    bookings = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(bookings)

@app.route('/api/calendar')
def get_calendar():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    # Get month and year from args or default to current
    now = datetime.now()
    month = int(request.args.get('month', now.month))
    year = int(request.args.get('year', now.year))
    
    import calendar
    _, num_days = calendar.monthrange(year, month)
    
    conn = get_db()
    cursor = conn.cursor()
    
    days = []
    current_date_str = now.strftime("%Y-%m-%d")
    
    for d in range(1, num_days + 1):
        date_str = f"{year}-{month:02d}-{d:02d}"
        cursor.execute("SELECT id FROM bookings WHERE booking_date=?", (date_str,))
        is_booked = cursor.fetchone() is not None
        
        status = "free"
        if date_str == current_date_str:
            status = "today"
        elif is_booked:
            status = "booked"
            
        days.append({
            "day": d,
            "date": date_str,
            "status": status,
            "booked": is_booked
        })
    
    conn.close()
    return jsonify({
        "month": month,
        "year": year,
        "month_name": calendar.month_name[month],
        "days": days
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
