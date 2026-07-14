import os
from dotenv import load_dotenv

# Load environment variables from .env file at application startup
load_dotenv()

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
# CSRF protection
from flask_wtf import CSRFProtect
from flask_socketio import SocketIO, emit
from database import get_db, return_db
import logging
import threading
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, messaging
from werkzeug.middleware.proxy_fix import ProxyFix

import json
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), '../frontend'))
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
# Use environment variable for secret key
app.secret_key = os.getenv("FLASK_SECRET_KEY")
# Validate required environment variables at startup
required_envs = ["FLASK_SECRET_KEY", "DATABASE_URL"]
missing = [var for var in required_envs if not os.getenv(var)]
if missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

# Auto-initialize and seed database on startup
try:
    from seed_db import seed_db
    seed_db()
    logging.info("[OK] Database initialized and seeded successfully.")
except Exception as e:
    logging.error(f"[ERROR] Database initialization/seeding failed: {e}")

# Optional Firebase key validation
if not os.getenv("FIREBASE_KEY") and not os.path.exists(os.path.join(os.path.dirname(__file__), "firebase_key.json")):
    raise RuntimeError("Firebase credentials not provided via FIREBASE_KEY env or firebase_key.json file")
app.permanent_session_lifetime = timedelta(minutes=10)
CORS(app, supports_credentials=True, origins=[
    "https://lab-booking-system-e77ad.web.app",
    "https://lab-booking-system-e77ad.firebaseapp.com",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:3000"
])

if not app.debug:
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE='None',
    )

# CSRF protection: This is a JSON-only API backend (no HTML forms).
# Session cookies use SameSite policy + CORS for cross-origin protection.
# CSRFProtect is initialized but globally exempted for JSON API compatibility.
# Re-enable per-route if HTML form endpoints are added in the future.
app.config['WTF_CSRF_ENABLED'] = False
csrf = CSRFProtect(app)

# Load UltraMsg configs for WhatsApp Group Integration
app.config['ULTRAMSG_INSTANCE_ID'] = os.environ.get("ULTRAMSG_INSTANCE_ID")
app.config['ULTRAMSG_TOKEN'] = os.environ.get("ULTRAMSG_TOKEN")
app.config['ULTRAMSG_GROUP_ID'] = os.environ.get("ULTRAMSG_GROUP_ID")

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

try:
    firebase_json = os.environ.get("FIREBASE_KEY")

    if firebase_json and not firebase_admin._apps:
        cred_dict = json.loads(firebase_json)
        # Fix escaped newlines that Render introduces when storing JSON as a string
        cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        logging.info("[OK] Firebase initialized from ENV")
    elif not firebase_admin._apps:
        key_path = os.path.join(os.path.dirname(__file__), "firebase_key.json")
        if os.path.exists(key_path):
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
            logging.info("[OK] Firebase initialized from firebase_key.json")
        else:
            logging.warning("[WARN] Firebase credentials not found")
except Exception as e:
    logging.error(f"[ERROR] Firebase init error: {e}")

# ── Background Push Notification Helper ──────────────────────────────────
# Sends FCM notifications in a background thread so HTTP responses are instant
def _send_push_background(tokens, title, body):
    """Fire-and-forget push notifications in a background thread."""
    def _worker():
        for token in tokens:
            if not token:
                continue
            try:
                msg = messaging.Message(
                    notification=messaging.Notification(title=title, body=body),
                    token=token
                )
                messaging.send(msg)
            except Exception:
                pass
    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()

def send_whatsapp_maintenance_notice(lab_name, status, reason=None, expected_end=None):
    instance_id = app.config.get("ULTRAMSG_INSTANCE_ID")
    token = app.config.get("ULTRAMSG_TOKEN")
    group_id = app.config.get("ULTRAMSG_GROUP_ID")
    
    if not (instance_id and token and group_id):
        logging.warning("WhatsApp credentials missing. Skipping WhatsApp notification.")
        return False
        
    url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
    
    if status == 'maintenance':
        message = (
            "🔧 *LAB MAINTENANCE NOTICE*\n\n"
            f"*Laboratory:* {lab_name}\n"
            f"*Status:* Under Maintenance\n"
            f"*Reason:* {reason or 'N/A'}\n"
            f"*Expected Completion:* {expected_end or 'TBD'}\n\n"
            "Please avoid booking this laboratory until further notice.\n\n"
            "Regards,\n"
            "Lab Booking System"
        )
    else:
        message = (
            "✅ *LAB AVAILABLE*\n\n"
            f"*Laboratory:* {lab_name}\n\n"
            "Maintenance work has been completed.\n"
            "This laboratory is now available for booking.\n\n"
            "Regards,\n"
            "Lab Booking System"
        )
        
    payload = {
        "token": token,
        "to": group_id,
        "body": message
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            logging.info(f"WhatsApp notification sent successfully for {lab_name}")
            return True
        else:
            logging.error(f"WhatsApp API error ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        logging.error(f"Failed to send WhatsApp message for {lab_name}: {e}")
        return False

@app.route("/send-notification", methods=["POST"])
def send_notification():
    data = request.json
    token = data.get("token")

    if not token:
        return jsonify({"error": "Token missing"}), 400

    message = messaging.Message(
        notification=messaging.Notification(
            title="Lab Booking",
            body="New booking created!"
        ),
        token=token
    )

    try:
        response = messaging.send(message)
        return jsonify({"success": True, "response": response})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

def make_row_dict(row, cursor):
    """
    Safely converts a database row (tuple, list, dict, or RealDictRow) 
    into a standard Python dict. Returns None if row is None.
    """
    if row is None:
        return None
    if isinstance(row, dict) or (hasattr(row, 'keys') and hasattr(row, '__getitem__')):
        return dict(row)
    colnames = [desc[0] for desc in cursor.description]
    return dict(zip(colnames, row))

def get_first_value(row):
    """
    Safely extracts the first column's value from a database row.
    Returns None if row is None.
    """
    if row is None:
        return None
    if isinstance(row, (tuple, list)):
        return row[0]
    return list(row.values())[0]

@app.route('/health')
def health():
    return {"status": "ok"}, 200

@app.route('/api/test-db')
def test_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        row = cursor.fetchone()
        
        # Also check if faculty table exists and how many users it has
        cursor.execute("SELECT COUNT(*) FROM faculty")
        fac_res = cursor.fetchone()
        fac_count = get_first_value(fac_res)
        
        return_db(conn)
        return jsonify({
            "status": "success",
            "connection_test": row,
            "faculty_count": fac_count
        })
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')
@app.route('/firebase-messaging-sw.js')
def serve_firebase_sw():
    return send_from_directory(app.static_folder, 'firebase-messaging-sw.js')

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
    # Fetch user by email only; verify password hash in Python
    cursor.execute("SELECT * FROM faculty WHERE email=%s", (email,))
    user = make_row_dict(cursor.fetchone(), cursor)
    return_db(conn)
    
    if user and check_password_hash(user['password'], password):
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

@app.route('/admin/stats')
def admin_stats():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_res = cursor.fetchone()
    total = get_first_value(total_res)

    cursor.execute("SELECT COUNT(DISTINCT lab_id) FROM bookings")
    labs_res = cursor.fetchone()
    labs = get_first_value(labs_res)

    cursor.execute("SELECT COUNT(*) FROM faculty WHERE role='faculty'")
    users_res = cursor.fetchone()
    users = get_first_value(users_res)

    return_db(conn)

    return jsonify({
        "total_bookings": total,
        "active_labs": labs,
        "faculty_users": users
    })

@app.route('/api/stats')
def get_stats():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM bookings")
    total_bookings = get_first_value(cursor.fetchone())
    
    cursor.execute("SELECT COUNT(*) as total FROM faculty")
    total_faculty = get_first_value(cursor.fetchone())
    
    cursor.execute("SELECT COUNT(DISTINCT lab_id) as total FROM fixed_schedule")
    active_labs = get_first_value(cursor.fetchone())
    
    return_db(conn)
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
    setting = make_row_dict(cursor.fetchone(), cursor)
    return_db(conn)
    
    limit = int(setting['value']) if setting and 'value' in setting else 2
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
    cursor.execute("""
        INSERT INTO settings (key, value) VALUES ('daily_limit', %s)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """, (str(new_limit),))
    conn.commit()
    return_db(conn)
    
    return jsonify({"success": True, "limit": new_limit})

@app.route('/download_sample', methods=['GET'])
def download_sample():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    from flask import Response
    csv_content = "day,period,lab\nMonday,1,Lab1\nMonday,2,Lab2\nTuesday,1,Lab1\n"
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
    return_db(conn)
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
        
        cursor.execute("INSERT INTO announcements (message, expires_at) VALUES (%s, %s)", (message, expires_at))
        conn.commit()
        
        try:
            socketio.emit('notice_update', {}, namespace='/')
            
            cursor.execute("SELECT token FROM fcm_tokens")
            tokens = [get_first_value(r) for r in cursor.fetchall()]

            # Send push notifications in background thread (non-blocking)
            if tokens:
                _send_push_background(tokens, "Admin Notice", message)
        except Exception as e:
            logging.error(f"Notice notification error: {e}")
            
        return_db(conn)
        return jsonify({"success": True})
    
    else:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("SELECT * FROM announcements WHERE expires_at > %s ORDER BY id DESC LIMIT 1", (now,))
        notice = make_row_dict(cursor.fetchone(), cursor)
        return_db(conn)
        
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
    notices = [make_row_dict(row, cursor) for row in cursor.fetchall()]
    return_db(conn)
    return jsonify(notices)

@app.route('/api/timetable')
def get_timetable():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    date = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
    day = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT lab_name FROM labs ORDER BY id")
    labs_rows = [make_row_dict(row, cursor) for row in cursor.fetchall()]
    labs = [row['lab_name'].strip() for row in labs_rows if row and row.get('lab_name')]
    
    cursor.execute("SELECT day, period, lab, subject FROM fixed_schedule WHERE day ILIKE %s", (day,))
    fixed_data = []
    for row in cursor.fetchall():
        d = make_row_dict(row, cursor)
        if d and d.get('lab'):
            d['lab'] = d['lab'].strip()
            fixed_data.append(d)
        
    cursor.execute("""
        SELECT b.day, b.period, l.lab_name as lab, f.name as faculty_name, b.id, b.faculty_id
        FROM bookings b 
        JOIN faculty f ON b.faculty_id = f.id 
        JOIN labs l ON b.lab_id = l.id
        WHERE b.booking_date=%s
    """, (date,))
    
    bookings_data = []
    user_id = session.get('user_id')
    role = session.get('role')
    for row in cursor.fetchall():
        b_dict = make_row_dict(row, cursor)
        if b_dict:
            b_dict['lab'] = b_dict['lab'].strip() if b_dict.get('lab') else ""
            b_dict['own'] = (b_dict.get('faculty_id') == user_id or role == 'admin')
            bookings_data.append(b_dict)
    
    return_db(conn)
    
    return jsonify({
        "day": day,
        "date": date,
        "periods": [1, 2, 3, 4, 5, 6, 7, 8],
        "labs": labs,
        "fixed": fixed_data,
        "bookings": bookings_data
    })

@app.route('/api/book', methods=['POST'])
def book_slot():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        data = request.get_json() or {}
        lab_name = data.get('lab') or data.get('labName')
        period = data.get('period')
        day = data.get('day')
        date = data.get('date')
        faculty_id = session['user_id']

        # Validation: Ensure all necessary fields exist
        if not lab_name or period is None or not day or not date:
            return jsonify({"success": False, "message": "Missing fields"}), 400

        conn = get_db()
        try:
            cursor = conn.cursor()
            
            # ✅ Enforce Daily Booking Limit
            cursor.execute("SELECT value FROM settings WHERE key='daily_limit'")
            setting = make_row_dict(cursor.fetchone(), cursor)
            daily_limit = int(setting['value']) if setting and setting.get('value') else 0
            
            if daily_limit > 0 and session.get('role') != 'admin':
                cursor.execute("SELECT COUNT(*) as count FROM bookings WHERE faculty_id = %s AND booking_date = %s", (faculty_id, date))
                current_bookings = get_first_value(cursor.fetchone()) or 0
                if current_bookings >= daily_limit:
                    return jsonify({"success": False, "message": f"Daily limit of {daily_limit} bookings reached."}), 403

            cursor.execute("SELECT id, status FROM labs WHERE lab_name = %s", (lab_name,))
            row = cursor.fetchone()

            if not row:
                return_db(conn)
                return jsonify({"success": False, "message": f"Invalid lab: {lab_name}"}), 400

            lab_id = row['id']
            
            # Check if lab is under maintenance
            if row.get('status') == 'maintenance':
                return_db(conn)
                return jsonify({
                    "success": False,
                    "message": "This laboratory is currently under maintenance. Please choose another laboratory."
                }), 403

            cursor.execute("SELECT id FROM bookings WHERE lab_id = %s AND booking_date = %s AND period = %s", (lab_id, date, period))
            if cursor.fetchone():
                return_db(conn)
                return jsonify({"success": False, "message": "Slot already booked"}), 409

            cursor.execute("INSERT INTO bookings (lab_id, faculty_id, day, period, booking_date) VALUES (%s, %s, %s, %s, %s)", (lab_id, faculty_id, day, period, date))
            conn.commit()

            # 🔔 SEND NOTIFICATION & LIVE UPDATE
            try:
                socketio.emit('booking_update', {"type": "new_booking"}, namespace='/')

                # Send push notifications in background thread (non-blocking)
                notif_conn = get_db()
                try:
                    notif_cursor = notif_conn.cursor()
                    notif_cursor.execute("""
                        SELECT f.token 
                        FROM fcm_tokens f 
                        JOIN faculty u ON f.faculty_id = u.id 
                        WHERE u.role = 'admin'
                    """)
                    tokens = [get_first_value(r) for r in notif_cursor.fetchall()]

                    if tokens:
                        faculty_name = session.get('name', 'Faculty')
                        msg_body = f"{faculty_name} booked {lab_name} (Period {period}) on {date}"
                        _send_push_background(tokens, "Lab Booking", msg_body)
                finally:
                    return_db(notif_conn)
            except Exception:
                pass

            return jsonify({"success": True})

        finally:
            return_db(conn)

    except Exception as e:
        logging.error(f"ERROR: {e}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/cancel_booking/<int:id>', methods=['DELETE'])
def cancel_booking(id):
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check ownership
    cursor.execute("SELECT faculty_id FROM bookings WHERE id=%s", (id,))
    booking = make_row_dict(cursor.fetchone(), cursor)
    if not booking or (booking.get('faculty_id') != session['user_id'] and session['role'] != 'admin'):
        return_db(conn)
        return jsonify({"success": False, "message": "Forbidden"}), 403
    
    cursor.execute("DELETE FROM bookings WHERE id=%s", (id,))
    conn.commit()
    return_db(conn)
    socketio.emit('booking_update', {"type": "cancel_booking"}, namespace='/')
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
        content = file.stream.read().decode("utf-8-sig", errors="replace")
        stream = io.StringIO(content)
        
        reader = csv.reader(stream)
        next(reader, None) # skip header
            
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM fixed_schedule")
        
        count = 0
        for row in reader:
            if len(row) < 4:
                continue
            
            day = row[0].strip()
            period = int(row[1].strip())
            lab = row[2].strip()
            subject = row[3].strip()
            
            logging.info(f"INSERTING: {day} {period} {lab} {subject}")
            
            cursor.execute("INSERT INTO fixed_schedule (day, period, lab, subject) VALUES (%s, %s, %s, %s) ON CONFLICT (day, period, lab) DO NOTHING", (day, period, lab, subject))
            count += 1
            
        conn.commit()
        return_db(conn)
        
        logging.info(f"Successfully uploaded {count} fixed schedule entries.")
        return jsonify({"success": True, "count": count})
    except Exception as e:
        logging.error(f"Upload error: {e}")
        return jsonify({"success": False, "message": str(e)})


@app.route('/labs', methods=['GET'])
def get_labs_dynamic():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM labs ORDER BY lab_name ASC")
    all_labs = [make_row_dict(row, cursor) for row in cursor.fetchall()]
    return_db(conn)
    return jsonify(all_labs)

@app.route('/add_lab', methods=['POST'])
def add_lab_dynamic():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    name = request.json.get('name')
    if not name:
         return jsonify({"success": False, "message": "Name is required"})
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM labs WHERE lab_name=%s", (name,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO labs (lab_name) VALUES (%s)", (name,))
            conn.commit()
        success = True
    except Exception as e:
        logging.error(f"Error adding lab: {e}", exc_info=True)
        success = False
    finally:
        return_db(conn)
    return jsonify({"success": success})

@app.route('/delete_lab', methods=['POST'])
def delete_lab_dynamic():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    lab_id = request.json.get('id')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bookings WHERE lab_id=%s", (lab_id,))
    cursor.execute("DELETE FROM labs WHERE id=%s", (lab_id,))
    conn.commit()
    return_db(conn)
    return jsonify({"success": True})

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
        cursor.execute("SELECT id FROM labs WHERE lab_name=%s", (lab_name,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO labs (lab_name) VALUES (%s)", (lab_name,))
            conn.commit()
        return_db(conn)
        return jsonify({"success": True})
    else:
        cursor.execute("SELECT * FROM labs ORDER BY lab_name ASC")
        labs = [make_row_dict(row, cursor) for row in cursor.fetchall()]
        return_db(conn)
        return jsonify(labs)

@app.route('/api/labs/<int:lab_id>/status', methods=['POST'])
def update_lab_status(lab_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
        
    data = request.get_json() or {}
    new_status = data.get('status')
    
    if new_status not in ['active', 'maintenance']:
        return jsonify({"success": False, "message": "Invalid status. Accepted values are: active, maintenance."}), 400
        
    reason = None
    expected_end = None
    
    if new_status == 'maintenance':
        reason = data.get('reason')
        expected_end = data.get('expected_end')
        
        if not reason:
            return jsonify({"success": False, "message": "Maintenance reason is mandatory."}), 400
        if not expected_end:
            return jsonify({"success": False, "message": "Expected completion date is mandatory."}), 400
            
        try:
            datetime.strptime(expected_end, "%Y-%m-%d")
        except ValueError:
            return jsonify({"success": False, "message": "Expected completion date must be in YYYY-MM-DD format."}), 400

    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Verify lab exists and fetch current status
        cursor.execute("SELECT id, lab_name, status FROM labs WHERE id = %s", (lab_id,))
        lab = cursor.fetchone()
        
        if not lab:
            return_db(conn)
            return jsonify({"success": False, "message": "Laboratory not found."}), 404
            
        lab_name = lab['lab_name']
        old_status = lab['status']
        
        # Duplicate Protection
        if old_status == new_status:
            return_db(conn)
            return jsonify({
                "success": True,
                "message": "No status change required."
            }), 200

        # Update lab status
        if new_status == 'maintenance':
            cursor.execute("""
                UPDATE labs 
                SET status = %s, maintenance_reason = %s, maintenance_start = %s, maintenance_end = %s
                WHERE id = %s
            """, (new_status, reason, datetime.now(), expected_end, lab_id))
            
            title = "Lab Status Update"
            message_text = f"🔧 {lab_name} is under maintenance."
            notif_type = "maintenance_start"
        else:
            cursor.execute("""
                UPDATE labs 
                SET status = 'active', maintenance_reason = NULL, maintenance_start = NULL, maintenance_end = NULL
                WHERE id = %s
            """, (lab_id,))
            
            title = "Lab Status Update"
            message_text = f"✅ {lab_name} is available for booking again."
            notif_type = "maintenance_end"
            
        # Write notification history
        cursor.execute("""
            INSERT INTO notifications (lab_id, title, message, notification_type, created_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (lab_id, title, message_text, notif_type, session.get('user_id')))
        
        conn.commit()
        logging.info(f"STATUS CHANGE: Admin={session.get('user_id')}, Lab={lab_id}, Prev={old_status}, New={new_status}, Timestamp={datetime.now()}")
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Database error during lab status toggle: {e}", exc_info=True)
        return_db(conn)
        return jsonify({"success": False, "message": "Internal database error occurred."}), 500
        
    finally:
        return_db(conn)

    # Dispatch notifications in a background thread
    def dispatch_notifications():
        try:
            notif_conn = get_db()
            notif_cursor = notif_conn.cursor()
            notif_cursor.execute("SELECT f.token FROM fcm_tokens f JOIN faculty u ON f.faculty_id = u.id WHERE u.role = 'faculty'")
            tokens = [r['token'] for r in notif_cursor.fetchall() if r and r.get('token')]
            return_db(notif_conn)
            
            if tokens:
                _send_push_background(tokens, "Lab Status Update", message_text)
        except Exception as fcm_err:
            logging.error(f"FCM Notification dispatch error: {fcm_err}")
            
        try:
            send_whatsapp_maintenance_notice(lab_name, new_status, reason, expected_end)
        except Exception as wa_err:
            logging.error(f"WhatsApp Notification dispatch error: {wa_err}")

    threading.Thread(target=dispatch_notifications, daemon=True).start()

    return jsonify({
        "success": True,
        "message": f"Lab status updated to {new_status}.",
        "lab": {
            "id": lab_id,
            "name": lab_name,
            "status": new_status,
            "reason": reason,
            "expected_end": expected_end
        }
    }), 200

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
        cursor.execute("SELECT b.*, l.lab_name FROM bookings b JOIN labs l ON b.lab_id = l.id WHERE b.faculty_id = %s ORDER BY b.booking_date DESC, b.period ASC", (faculty_id,))
    
    bookings = [make_row_dict(row, cursor) for row in cursor.fetchall()]
    return_db(conn)
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
        cursor.execute("SELECT id FROM bookings WHERE booking_date=%s", (date_str,))
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
    
    return_db(conn)
    return jsonify({
        "month": month,
        "year": year,
        "month_name": calendar.month_name[month],
        "days": days
    })


@app.route('/set_limit', methods=['POST'])
def set_limit():
    from flask import request
    limit = request.json.get("limit", 0)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO settings (key, value) VALUES ('daily_limit', %s)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """, (str(limit),))

    conn.commit()
    return_db(conn)

    return jsonify({"success": True})

@app.route('/current_user')
def current_user():
    return jsonify({
        "id": session.get("user_id"),
        "role": session.get("role")
    })

@app.route('/bookings', methods=['GET'])
def get_bookings():
    conn = get_db()

    cursor = conn.cursor()
    
    try:
        # Now fetch safely. We use LEFT JOIN to resolve lab names and faculty names if possible
        cursor.execute("""
            SELECT 
                b.*,
                l.lab_name as joined_lab,
                f.name as joined_faculty
            FROM bookings b
            LEFT JOIN labs l ON b.lab_id = l.id
            LEFT JOIN faculty f ON b.faculty_id = f.id
        """)
        rows = [make_row_dict(r, cursor) for r in cursor.fetchall()]
        
        result = []
        for row in rows:
            # Safely resolve columns allowing graceful fallback to schema defaults
            row_keys = row.keys()
            lab = row['joined_lab'] if 'joined_lab' in row_keys and row['joined_lab'] else (row['lab'] if 'lab' in row_keys else "Unknown Lab")
            date = row['booking_date'] if 'booking_date' in row_keys and row['booking_date'] else (row['date'] if 'date' in row_keys else "")
            f_id = row['faculty_id'] if 'faculty_id' in row_keys else None
            f_name = row['joined_faculty'] if 'joined_faculty' in row_keys and row['joined_faculty'] else (row['faculty_name'] if 'faculty_name' in row_keys and row['faculty_name'] else "Unknown")
            
            result.append({
                "lab": str(lab).strip(),
                "period": int(row['period']) if 'period' in row_keys and row['period'] else 0,
                "date": str(date).strip(),
                "faculty_id": f_id,
                "faculty_name": str(f_name).strip()
            })
            
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"[ERROR] ERROR in /bookings: {e}", exc_info=True)
        # Return graceful fallback JSON payload, absolutely no 500 error
        return jsonify([])
        
    finally:
        return_db(conn)

@app.route('/cancel', methods=['POST'])
def cancel_booking_custom():
    from flask import request
    data = request.json
    lab = data['lab']
    period = data['period']
    date = data['date']
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM labs WHERE lab_name=%s", (lab,))
    lab_row = make_row_dict(cursor.fetchone(), cursor)
    if lab_row:
        user_id = session.get('user_id')
        cursor.execute("DELETE FROM bookings WHERE lab_id=%s AND period=%s AND booking_date=%s AND faculty_id=%s", (lab_row['id'], period, date, user_id))
        conn.commit()
        socketio.emit('booking_update', {"type": "cancel_booking"}, namespace='/')
    return_db(conn)
    return jsonify({"success": True})

@app.route('/login', methods=['POST'])
def custom_login():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    # Fetch user by email only; verify password hash in Python
    cursor.execute("SELECT id, name, email, password, role FROM faculty WHERE email=%s",
                   (data['email'],))
    user = make_row_dict(cursor.fetchone(), cursor)
    return_db(conn)

    if user and check_password_hash(user['password'], data['password']):
        session['user_id'] = user['id']
        session['role'] = user['role']
        return jsonify({"success": True, "role": user['role']})
    return jsonify({"success": False, "message": "Invalid credentials"})


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email', '').strip().lower()
    
    # Faculty-only domain validation
    if not email.endswith('@jayshriram.edu.in'):
        return jsonify({"success": False, "message": "Only @jayshriram.edu.in emails are allowed"}), 403

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faculty WHERE email=%s", (email,))
    if cursor.fetchone():
        return_db(conn)
        return jsonify({"success": False, "message": "User already exists"})

    hashed_pw = generate_password_hash(data.get('password', ''))
    cursor.execute("""
    INSERT INTO faculty (name, email, password, role)
    VALUES (%s, %s, %s, 'faculty')
    """, (data.get('name', ''), email, hashed_pw))
    conn.commit()
    return_db(conn)
    return jsonify({"success": True})

@app.route('/api/faculty', methods=['GET'])
def get_faculty_list():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
        
    conn = get_db()

    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, role FROM faculty ORDER BY name ASC")
    rows = cursor.fetchall()
    return_db(conn)
    
    faculty_list = [make_row_dict(row, cursor) for row in rows]
    return jsonify({"success": True, "faculty": faculty_list})



@app.route('/upload_faculty', methods=['POST'])
def bulk_upload_faculty():
    if session.get('role') != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
        
    import csv
    import io
    file = request.files['file']
    content = file.stream.read().decode("UTF8", errors="replace")
    stream = io.StringIO(content)
    reader = csv.DictReader(stream, skipinitialspace=True)
    
    # Normalize headers
    if reader.fieldnames:
        reader.fieldnames = [str(f).strip().lower() for f in reader.fieldnames]

    conn = get_db()
    cursor = conn.cursor()

    count = 0
    for row in reader:
        # Fallbacks for empty rows
        if not row.get('name') or not row.get('email') or not row.get('password'):
            continue
            
        # Hash password before storing
        hashed_pw = generate_password_hash(row['password'].strip())
        cursor.execute("""
            INSERT INTO faculty (name, email, password, role) VALUES (%s, %s, %s, 'faculty')
            ON CONFLICT (email) DO NOTHING
        """, (row['name'].strip(), row['email'].strip(), hashed_pw))
        count += 1

    conn.commit()
    return_db(conn)
    return jsonify({"success": True, "count": count})

@app.route('/save-token', methods=['POST'])
def save_token():
    # Attempt to parse JSON input
    data = request.get_json(silent=True)
    logging.debug(f"/save-token hit. Data: {data}")
    logging.debug(f"Session: {dict(session)}")
    
    # 1. Error handling: If no JSON is received
    if data is None:
        logging.error("No JSON received at /save-token")
        return jsonify({"error": "No JSON received"}), 400
        
    # 2. Extract token safely
    token = data.get('token')
    
    # 3. Error handling: If token is missing
    if not token:
        logging.error("Token missing in JSON at /save-token")
        return jsonify({"error": "Token is missing"}), 400
        
    # 4. Print token to console/logs
    logging.info("FCM token received")
    
    # Add to DB
    try:
        conn = get_db()
        cursor = conn.cursor()
        user_id = session.get('user_id')
        
        # Save token. If user_id is None, it's a guest/unlogged token (useful for testing)
        cursor.execute("INSERT INTO fcm_tokens (faculty_id, token) VALUES (%s, %s) ON CONFLICT (token) DO NOTHING", (user_id, token))
        conn.commit()
        return_db(conn)
        logging.info(f"Token saved to DB. User ID: {user_id}")
    except Exception as e:
        logging.error(f"DB error in /save-token: {e}")
        pass

    # 5. Return success JSON response
    return jsonify({"message": "Token saved successfully", "user_id": session.get('user_id')}), 200

def send_notification(tokens, title, body):
    if not tokens:
        logging.warning("No tokens provided for push notification.")
        return False
        
    try:
        if isinstance(tokens, str):
            tokens = [tokens]
            
        msg = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            tokens=tokens,
        )
        response = messaging.send_multicast(msg)
        logging.info(f"Successfully sent {response.success_count} messages. Failed: {response.failure_count}")
        return response.success_count > 0
    except Exception as e:
        logging.error(f"Error sending FCM message: {e}")
        return False

@app.route('/send-test-notification', methods=['GET'])
def send_test_notification():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT token FROM fcm_tokens")
        rows = [make_row_dict(row, cursor) for row in cursor.fetchall()]
        return_db(conn)
        
        tokens = [row['token'] for row in rows if row and row.get('token')]
        
        if not tokens:
            return jsonify({"success": False, "message": "No tokens found in database."}), 404
            
        success = send_notification(tokens, "Test Notification", "This is a test push message")
        
        if success:
            return jsonify({"success": True, "message": f"Test notification sent to {len(tokens)} devices."})
        else:
            return jsonify({"success": False, "message": "Failed to send test notification. Check server logs."}), 500
            
    except Exception as e:
        logging.error(f"Test notification error: {e}")
        return jsonify({"success": False, "message": "Server error."}), 500

# ── Keep-Alive Ping (prevents Render free tier from sleeping) ────────────
def _keep_alive():
    """Ping own /health endpoint every 10 minutes to prevent cold starts."""
    import urllib.request
    import time
    url = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:5000") + "/health"
    while True:
        time.sleep(600)  # 10 minutes
        try:
            urllib.request.urlopen(url, timeout=10)
            logging.info("[KEEPALIVE] Ping sent")
        except Exception:
            pass

_keepalive_thread = threading.Thread(target=_keep_alive, daemon=True)
_keepalive_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=True, allow_unsafe_werkzeug=True)
