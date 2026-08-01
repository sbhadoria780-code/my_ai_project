# FaceAttend — Face Recognition Attendance System (Mini Project)

A Flask + OpenCV + `face_recognition` web app that marks student attendance
from a browser webcam, with an admin dashboard, CSV/Excel export, and a
landing page styled after the reference design you shared.

---

## 1. Tech Stack

| Layer            | Tool                                   |
|-------------------|-----------------------------------------|
| Backend           | Flask, Flask-Login                     |
| Face AI           | OpenCV (`opencv-python-headless`), `face_recognition` (dlib) |
| Database          | SQLite (swap the connection string for MySQL if you want) |
| Reports           | pandas + openpyxl (CSV / Excel export) |
| Frontend          | Jinja2 templates, vanilla JS, Chart.js |

---

## 2. Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
```

`face_recognition` depends on **dlib**, which needs CMake and a C++ compiler
to build. If `pip install -r requirements.txt` fails on dlib:

- **Windows** — install `cmake` first (`pip install cmake`), or grab a
  prebuilt dlib wheel matching your Python version from
  `https://github.com/z-mahmud22/Dlib_Windows_Python3.x`, then re-run.
- **macOS** — `brew install cmake` first.
- **Linux** — `sudo apt-get install cmake build-essential` first.

```bash
# 3. Run the app (creates attendance.db and a default admin on first run)
python app.py
```

Visit **http://localhost:5000**. Default admin login: `admin` / `admin123`
(change it from the dashboard after logging in).

> The app uses your **browser's** webcam (via `getUserMedia`), not a server-side
> camera — so it works the same whether you run it locally or deploy it, and
> there's no OpenCV `VideoCapture` window to manage.

---

## 3. How it works

1. **Register a student** (`Students → Add Student`): capture a clear,
   front-facing photo through the browser webcam. The server checks the shot
   isn't too blurry/dark, detects exactly one face, computes a 128-d face
   encoding with `face_recognition`, and stores it (`static/encodings/*.pkl`).
2. **Mark attendance** (`Attendance`): capture a frame, the server compares
   it against every stored encoding, and returns the closest match above a
   confidence threshold. Duplicate attendance for the same day/subject is
   blocked automatically, and entries after `LATE_ENTRY_TIME` (see
   `config.py`) are marked **Late**.
3. **Dashboard**: today's totals, a 7-day attendance trend (Chart.js), recent
   scans, and a low-attendance alert list.
4. **Reports**: filter by date / name, export to CSV or Excel, or print.

---

## 4. Feature coverage vs. your spec

Everything under **AI Features (Core)**, **Attendance**, **Reports/Export**,
**Dashboard**, **Student Management**, **Admin Login**, and **CSV/Excel
export** is implemented and working end to end. A few items from your longer
wish-list are intentionally simplified or left as extension points, since a
full production build of all of them (SMS gateway, email delivery, a trained
liveness/anti-spoof model, MySQL, heatmap analytics, role hierarchies) is
well beyond a mini-project scope:

| Feature you listed              | Status in this build |
|----------------------------------|------------------------|
| Anti-spoofing (photo detection)  | Basic texture-variance heuristic in `utils/face_utils.py::basic_spoof_check` — flags obviously flat/low-detail captures. Swap in a trained liveness model for production. |
| Face quality check (blur/light)  | ✅ implemented (`check_image_quality`) |
| Multiple face detection          | ✅ implemented — rejects frames with >1 face during attendance |
| Late entry detection             | ✅ implemented (`LATE_ENTRY_TIME` in `config.py`) |
| Duplicate attendance prevention  | ✅ implemented (unique constraint + check) |
| CSV / Excel export               | ✅ implemented |
| PDF export                       | Not included — CSV/Excel cover the "download records" need; add via the `pdf` skill / `reportlab` if you need it |
| Dashboard stats + weekly chart   | ✅ implemented |
| Low attendance alert             | ✅ implemented on the dashboard |
| Student CRUD + search            | ✅ implemented |
| Admin login, hashed passwords, sessions | ✅ implemented (Flask-Login + Werkzeug hashing) |
| Audit log                        | ✅ table + logging helper (`database.py::log_action`); no dedicated viewer page yet — query the `audit_log` table directly, or add a simple list view |
| SQL injection protection         | ✅ all queries use parameterized SQLite calls |
| Face mask detection, SMS, email reports, attendance prediction, heatmaps, department-wise stats, role-based access levels, MySQL | Not built — these are genuine extensions, each roughly its own mini-feature. The code is structured (`utils/`, `database.py`) so you can add them incrementally. |

---

## 5. Project structure

```
face_attendance_system/
├── app.py                 # Flask routes
├── config.py               # thresholds & settings
├── database.py             # SQLite schema + helpers
├── utils/
│   └── face_utils.py       # encoding, recognition, quality/spoof checks
├── templates/               # Jinja2 pages
├── static/
│   ├── css/style.css
│   ├── img/hero-bg.png      # your uploaded background image
│   ├── uploads/              # student photos (created at runtime)
│   └── encodings/            # per-student .pkl face encodings
├── requirements.txt
└── attendance.db            # created automatically on first run
```

## 6. Notes for your report / viva

- Recognition uses `face_recognition`'s ResNet-based 128-d face embeddings
  (dlib under the hood) with Euclidean distance matching — mention this if
  asked "what algorithm" in a viva.
- Attendance capture happens client-side (browser webcam → base64 JPEG →
  POST to `/api/mark_attendance`), which is why no server GPU/webcam is
  required and it deploys cleanly to any host.
- Passwords are hashed with Werkzeug's `generate_password_hash`
  (PBKDF2-SHA256) — never stored in plaintext.
