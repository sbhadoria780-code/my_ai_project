import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key-in-production")
    DATABASE_PATH = os.path.join(BASE_DIR, "attendance.db")

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    ENCODINGS_FOLDER = os.path.join(BASE_DIR, "static", "encodings")

    # Face recognition tuning
    FACE_MATCH_TOLERANCE = 0.45      # lower = stricter match
    MIN_CONFIDENCE_PERCENT = 55      # below this we treat the face as "Unknown"

    # Face quality checks
    BLUR_THRESHOLD = 60.0            # Laplacian variance below this = "too blurry"
    LOW_LIGHT_THRESHOLD = 50.0       # mean pixel brightness (0-255) below this = "too dark"

    # Attendance rules
    LATE_ENTRY_TIME = "09:30:00"     # HH:MM:SS - marked "Late" after this time

    # Default admin account (created automatically on first run)
    DEFAULT_ADMIN_USERNAME = "admin"
    DEFAULT_ADMIN_PASSWORD = "admin123"   # change immediately after first login!
