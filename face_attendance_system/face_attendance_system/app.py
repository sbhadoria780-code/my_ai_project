import io
import os
from datetime import datetime, timedelta

import pandas as pd
from flask import (Flask, render_template, request, redirect, url_for,
                    flash, jsonify, session, send_file, abort)
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                          login_required, current_user)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from config import Config
from database import get_db, init_db, log_action
from utils import face_utils

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.ENCODINGS_FOLDER, exist_ok=True)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access the admin panel."


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------
class AdminUser(UserMixin):
    def __init__(self, row):
        self.id = row["id"]
        self.username = row["username"]
        self.role = row["role"]


@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM admin WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return AdminUser(row) if row else None


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        row = conn.execute("SELECT * FROM admin WHERE username = ?", (username,)).fetchone()
        conn.close()

        if row and check_password_hash(row["password_hash"], password):
            login_user(AdminUser(row))
            log_action(username, "LOGIN", "Successful login")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard"))

        log_action(username, "LOGIN_FAILED", "Invalid credentials")
        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    log_action(current_user.username, "LOGOUT", "")
    logout_user()
    return redirect(url_for("index"))


@app.route("/account/change-password", methods=["POST"])
@login_required
def change_password():
    current_pw = request.form.get("current_password", "")
    new_pw = request.form.get("new_password", "")

    conn = get_db()
    row = conn.execute("SELECT * FROM admin WHERE id = ?", (current_user.id,)).fetchone()

    if not row or not check_password_hash(row["password_hash"], current_pw):
        flash("Current password is incorrect.", "error")
    elif len(new_pw) < 6:
        flash("New password must be at least 6 characters.", "error")
    else:
        conn.execute("UPDATE admin SET password_hash = ? WHERE id = ?",
                      (generate_password_hash(new_pw), current_user.id))
        conn.commit()
        log_action(current_user.username, "CHANGE_PASSWORD", "")
        flash("Password updated successfully.", "success")
    conn.close()
    return redirect(url_for("dashboard"))


# --------------------------------------------------------------------------
# Public landing page
# --------------------------------------------------------------------------
@app.route("/")
def index():
    conn = get_db()
    total_students = conn.execute("SELECT COUNT(*) c FROM students").fetchone()["c"]
    today = datetime.now().strftime("%Y-%m-%d")
    present_today = conn.execute(
        "SELECT COUNT(DISTINCT student_id) c FROM attendance WHERE date = ?", (today,)
    ).fetchone()["c"]
    absent_today = max(total_students - present_today, 0)
    pct = round((present_today / total_students) * 100, 2) if total_students else 0

    recent = conn.execute("""
        SELECT s.name, s.photo_path, a.time, a.status
        FROM attendance a JOIN students s ON a.student_id = s.id
        WHERE a.date = ?
        ORDER BY a.time DESC LIMIT 5
    """, (today,)).fetchall()
    conn.close()

    stats = {
        "total_students": total_students,
        "present_today": present_today,
        "absent_today": absent_today,
        "attendance_pct": pct,
    }
    return render_template("index.html", stats=stats, recent=recent)


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    total_students = conn.execute("SELECT COUNT(*) c FROM students").fetchone()["c"]
    today = datetime.now().strftime("%Y-%m-%d")
    present_today = conn.execute(
        "SELECT COUNT(DISTINCT student_id) c FROM attendance WHERE date = ?", (today,)
    ).fetchone()["c"]
    absent_today = max(total_students - present_today, 0)
    pct = round((present_today / total_students) * 100, 2) if total_students else 0

    recent = conn.execute("""
        SELECT s.name, s.roll_no, s.photo_path, a.time, a.status
        FROM attendance a JOIN students s ON a.student_id = s.id
        WHERE a.date = ?
        ORDER BY a.time DESC LIMIT 8
    """, (today,)).fetchall()

    # low attendance alert: students present < 60% of days since their first record
    low_attendance = conn.execute("""
        SELECT s.id, s.name, s.roll_no,
               COUNT(a.id) as days_present,
               (SELECT COUNT(DISTINCT date) FROM attendance) as total_days
        FROM students s
        LEFT JOIN attendance a ON a.student_id = s.id
        GROUP BY s.id
        HAVING total_days > 0 AND (CAST(days_present AS FLOAT) / total_days) < 0.6
        ORDER BY days_present ASC LIMIT 5
    """).fetchall()

    conn.close()

    stats = {
        "total_students": total_students,
        "present_today": present_today,
        "absent_today": absent_today,
        "attendance_pct": pct,
    }
    return render_template("dashboard.html", stats=stats, recent=recent,
                            low_attendance=low_attendance)


@app.route("/api/chart_data")
@login_required
def api_chart_data():
    """Attendance count for the last 7 days, for the dashboard line chart."""
    conn = get_db()
    labels, values = [], []
    for i in range(6, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        label = (datetime.now() - timedelta(days=i)).strftime("%a")
        count = conn.execute(
            "SELECT COUNT(DISTINCT student_id) c FROM attendance WHERE date = ?", (d,)
        ).fetchone()["c"]
        labels.append(label)
        values.append(count)
    conn.close()
    return jsonify({"labels": labels, "values": values})


# --------------------------------------------------------------------------
# Student management
# --------------------------------------------------------------------------
@app.route("/students")
@login_required
def students_list():
    q = request.args.get("q", "").strip()
    conn = get_db()
    if q:
        rows = conn.execute("""
            SELECT * FROM students
            WHERE name LIKE ? OR roll_no LIKE ? OR department LIKE ?
            ORDER BY name
        """, (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    else:
        rows = conn.execute("SELECT * FROM students ORDER BY name").fetchall()
    conn.close()
    return render_template("students.html", students=rows, query=q)


@app.route("/students/add", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll_no = request.form.get("roll_no", "").strip()
        department = request.form.get("department", "").strip()
        semester = request.form.get("semester", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        photo_data = request.form.get("photo_data", "")

        if not name or not roll_no:
            flash("Name and Roll Number are required.", "error")
            return render_template("add_student.html")

        conn = get_db()
        existing = conn.execute("SELECT id FROM students WHERE roll_no = ?", (roll_no,)).fetchone()
        if existing:
            conn.close()
            flash("A student with this Roll Number already exists.", "error")
            return render_template("add_student.html")

        encoding, photo_path = None, None
        if photo_data:
            try:
                bgr = face_utils.decode_base64_image(photo_data)
                quality = face_utils.check_image_quality(bgr)
                if not quality["ok"]:
                    conn.close()
                    flash(" ".join(quality["issues"]), "error")
                    return render_template("add_student.html")

                encoding, location, err = face_utils.encode_face_from_image(bgr)
                if err:
                    conn.close()
                    flash(err, "error")
                    return render_template("add_student.html")

                fname = secure_filename(f"{roll_no}_{name}.jpg").replace(" ", "_")
                photo_path = os.path.join(Config.UPLOAD_FOLDER, fname)
                import cv2
                cv2.imwrite(photo_path, bgr)
            except Exception as e:
                conn.close()
                flash(f"Could not process the captured photo: {e}", "error")
                return render_template("add_student.html")

        cur = conn.execute("""
            INSERT INTO students (name, roll_no, department, semester, email, phone, photo_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, roll_no, department, semester, email, phone, photo_path))
        student_id = cur.lastrowid

        if encoding is not None:
            enc_path = face_utils.save_encoding(student_id, encoding)
            conn.execute("UPDATE students SET encoding_path = ? WHERE id = ?", (enc_path, student_id))

        conn.commit()
        conn.close()
        log_action(current_user.username, "ADD_STUDENT", f"{name} ({roll_no})")
        flash(f"Student '{name}' registered successfully.", "success")
        return redirect(url_for("students_list"))

    return render_template("add_student.html")


@app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if not student:
        conn.close()
        abort(404)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        department = request.form.get("department", "").strip()
        semester = request.form.get("semester", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        conn.execute("""
            UPDATE students SET name=?, department=?, semester=?, email=?, phone=?
            WHERE id=?
        """, (name, department, semester, email, phone, student_id))
        conn.commit()
        conn.close()
        log_action(current_user.username, "EDIT_STUDENT", f"id={student_id}")
        flash("Student updated.", "success")
        return redirect(url_for("students_list"))

    conn.close()
    return render_template("edit_student.html", student=student)


@app.route("/students/<int:student_id>/delete", methods=["POST"])
@login_required
def delete_student(student_id):
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if student:
        if student["photo_path"] and os.path.exists(student["photo_path"]):
            os.remove(student["photo_path"])
        if student["encoding_path"] and os.path.exists(student["encoding_path"]):
            os.remove(student["encoding_path"])
        conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
        log_action(current_user.username, "DELETE_STUDENT", f"{student['name']}")
        flash("Student removed.", "success")
    conn.close()
    return redirect(url_for("students_list"))


# --------------------------------------------------------------------------
# Live webcam attendance
# --------------------------------------------------------------------------
@app.route("/attendance")
@login_required
def attendance_page():
    return render_template("attendance.html", late_time=Config.LATE_ENTRY_TIME)


@app.route("/api/mark_attendance", methods=["POST"])
@login_required
def api_mark_attendance():
    data = request.get_json(silent=True) or {}
    image_data = data.get("image")
    subject = data.get("subject", "General").strip() or "General"

    if not image_data:
        return jsonify({"success": False, "message": "No image received."}), 400

    try:
        bgr = face_utils.decode_base64_image(image_data)
    except Exception:
        return jsonify({"success": False, "message": "Invalid image data."}), 400

    quality = face_utils.check_image_quality(bgr)
    if not quality["ok"]:
        return jsonify({"success": False, "message": " ".join(quality["issues"]), "quality": quality})

    conn = get_db()
    students = conn.execute("SELECT * FROM students WHERE encoding_path IS NOT NULL").fetchall()
    known_encodings, known_students = face_utils.load_all_encodings(students)

    results = face_utils.recognize_faces(bgr, known_encodings, known_students)

    if not results:
        conn.close()
        return jsonify({"success": False, "message": "No face detected. Please face the camera."})

    if len(results) > 1:
        conn.close()
        return jsonify({"success": False,
                         "message": f"{len(results)} faces detected. Please attend one at a time."})

    result = results[0]

    if result["spoof_suspicious"]:
        conn.close()
        return jsonify({"success": False, "message": result["spoof_reason"]})

    if result["is_unknown"] or result["student"] is None:
        conn.close()
        return jsonify({"success": False,
                         "message": "Face not recognized. Please register first.",
                         "confidence": result["confidence"]})

    student = result["student"]
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    status = "Late" if time_str > Config.LATE_ENTRY_TIME else "Present"

    already = conn.execute(
        "SELECT id FROM attendance WHERE student_id=? AND date=? AND subject=?",
        (student["id"], today, subject),
    ).fetchone()

    if already:
        conn.close()
        return jsonify({
            "success": False,
            "duplicate": True,
            "message": f"Attendance already marked for {student['name']} today.",
            "name": student["name"],
        })

    conn.execute("""
        INSERT INTO attendance (student_id, date, time, status, confidence, subject)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (student["id"], today, time_str, status, result["confidence"], subject))
    conn.commit()
    conn.close()

    log_action(current_user.username, "MARK_ATTENDANCE",
               f"{student['name']} ({student['roll_no']}) - {status}")

    return jsonify({
        "success": True,
        "name": student["name"],
        "roll_no": student["roll_no"],
        "department": student["department"],
        "photo": "/" + student["photo_path"].split("static/", 1)[-1] if student["photo_path"] else None,
        "time": now.strftime("%I:%M:%S %p"),
        "date": now.strftime("%d %b %Y"),
        "status": status,
        "confidence": result["confidence"],
    })


# --------------------------------------------------------------------------
# Reports
# --------------------------------------------------------------------------
@app.route("/reports")
@login_required
def reports():
    date_filter = request.args.get("date", "")
    q = request.args.get("q", "").strip()

    query = """
        SELECT a.id, s.name, s.roll_no, s.department, a.date, a.time, a.status, a.confidence, a.subject
        FROM attendance a JOIN students s ON a.student_id = s.id
        WHERE 1=1
    """
    params = []
    if date_filter:
        query += " AND a.date = ?"
        params.append(date_filter)
    if q:
        query += " AND (s.name LIKE ? OR s.roll_no LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%"])
    query += " ORDER BY a.date DESC, a.time DESC LIMIT 500"

    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return render_template("reports.html", records=rows, date_filter=date_filter, query=q)


def _report_dataframe(date_filter, q):
    query = """
        SELECT s.name AS Name, s.roll_no AS "Roll No", s.department AS Department,
               a.date AS Date, a.time AS Time, a.status AS Status,
               a.confidence AS "Confidence %", a.subject AS Subject
        FROM attendance a JOIN students s ON a.student_id = s.id
        WHERE 1=1
    """
    params = []
    if date_filter:
        query += " AND a.date = ?"
        params.append(date_filter)
    if q:
        query += " AND (s.name LIKE ? OR s.roll_no LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%"])
    query += " ORDER BY a.date DESC, a.time DESC"

    conn = get_db()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


@app.route("/reports/export/<fmt>")
@login_required
def export_report(fmt):
    date_filter = request.args.get("date", "")
    q = request.args.get("q", "")
    df = _report_dataframe(date_filter, q)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if fmt == "csv":
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        mem = io.BytesIO(buf.getvalue().encode("utf-8"))
        log_action(current_user.username, "EXPORT_CSV", f"{len(df)} rows")
        return send_file(mem, mimetype="text/csv", as_attachment=True,
                          download_name=f"attendance_{stamp}.csv")

    if fmt == "excel":
        mem = io.BytesIO()
        with pd.ExcelWriter(mem, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Attendance")
        mem.seek(0)
        log_action(current_user.username, "EXPORT_EXCEL", f"{len(df)} rows")
        return send_file(mem,
                          mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                          as_attachment=True, download_name=f"attendance_{stamp}.xlsx")

    abort(404)


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5001)
