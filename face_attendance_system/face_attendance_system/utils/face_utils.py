"""
Core AI helpers: face encoding, recognition, and image quality / anti-spoof checks.

Kept as plain functions (no classes) so the mini-project stays easy to read
and easy to extend.
"""
import base64
import io
import os
import pickle

import cv2
import numpy as np
from PIL import Image

from config import Config


# --------------------------------------------------------------------------
# Image decoding
# --------------------------------------------------------------------------
def decode_base64_image(data_url):
    """Convert a 'data:image/jpeg;base64,....' string from the browser
    webcam into an OpenCV BGR numpy array."""
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    img_bytes = base64.b64decode(data_url)
    pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    rgb = np.array(pil_img)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return bgr


# --------------------------------------------------------------------------
# Image quality / basic anti-spoof checks
# --------------------------------------------------------------------------
def check_image_quality(bgr_image):
    """Return a dict describing blur / lighting quality of a captured frame.

    This is a lightweight heuristic suitable for a mini-project:
      - Blur   -> variance of the Laplacian (low variance = blurry)
      - Light  -> mean pixel brightness (low = too dark)
    """
    gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    brightness = float(np.mean(gray))

    issues = []
    if blur_score < Config.BLUR_THRESHOLD:
        issues.append("Image is too blurry - hold the camera steady.")
    if brightness < Config.LOW_LIGHT_THRESHOLD:
        issues.append("Lighting is too low - move to a brighter spot.")

    return {
        "blur_score": round(blur_score, 2),
        "brightness": round(brightness, 2),
        "ok": len(issues) == 0,
        "issues": issues,
    }


def basic_spoof_check(bgr_image, face_location):
    """Very lightweight photo/screen spoof heuristic for a mini-project.

    Real anti-spoofing needs a trained liveness model (blink detection,
    depth, texture CNN, etc). Here we flag frames that look like a flat
    printed photo or a screen re-capture by combining low texture variance
    in the face region with unusually uniform color -- NOT production grade,
    but demonstrates the concept and is easy to swap out later.
    """
    top, right, bottom, left = face_location
    face_crop = bgr_image[max(top, 0):bottom, max(left, 0):right]
    if face_crop.size == 0:
        return {"suspicious": False, "reason": None}

    gray_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
    texture_var = cv2.Laplacian(gray_face, cv2.CV_64F).var()
    color_std = float(np.std(face_crop))

    suspicious = texture_var < 15 and color_std < 20
    return {
        "suspicious": bool(suspicious),
        "reason": "Low texture detail detected - possible photo/screen spoof."
        if suspicious else None,
    }


# --------------------------------------------------------------------------
# Face encoding (registration)
# --------------------------------------------------------------------------
def encode_face_from_image(bgr_image):
    """Detect faces in an image and return (encodings, locations, error_message)."""
    import face_recognition  # imported lazily so the rest of the app can run
    rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

    locations = face_recognition.face_locations(rgb, model="hog")
    if len(locations) == 0:
        return None, None, "No face detected. Please face the camera directly."
    if len(locations) > 1:
        return None, None, "Multiple faces detected. Only one person should be in frame."

    encodings = face_recognition.face_encodings(rgb, known_face_locations=locations)
    return encodings[0], locations[0], None


def save_encoding(student_id, encoding):
    os.makedirs(Config.ENCODINGS_FOLDER, exist_ok=True)
    path = os.path.join(Config.ENCODINGS_FOLDER, f"student_{student_id}.pkl")
    with open(path, "wb") as f:
        pickle.dump(encoding, f)
    return path


def load_all_encodings(students):
    """students: list of sqlite Row objects with id, name, encoding_path.
    Returns (list_of_encodings, list_of_student_rows) aligned by index."""
    encodings, matched_students = [], []
    for s in students:
        if not s["encoding_path"] or not os.path.exists(s["encoding_path"]):
            continue
        with open(s["encoding_path"], "rb") as f:
            enc = pickle.load(f)
        encodings.append(enc)
        matched_students.append(s)
    return encodings, matched_students


# --------------------------------------------------------------------------
# Face recognition (attendance marking)
# --------------------------------------------------------------------------
def recognize_faces(bgr_image, known_encodings, known_students):
    """Detect all faces in the frame and match each against known_encodings.

    Returns a list of dicts:
      { student (Row|None), confidence (float), location, is_unknown (bool) }
    """
    import face_recognition
    rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

    locations = face_recognition.face_locations(rgb, model="hog")
    if not locations:
        return []

    face_encodings = face_recognition.face_encodings(rgb, known_face_locations=locations)

    results = []
    for encoding, location in zip(face_encodings, locations):
        result = {"student": None, "confidence": 0.0, "location": location, "is_unknown": True}

        if known_encodings:
            distances = face_recognition.face_distance(known_encodings, encoding)
            best_idx = int(np.argmin(distances))
            best_distance = distances[best_idx]
            confidence = round(max(0.0, (1 - best_distance)) * 100, 1)

            if best_distance <= Config.FACE_MATCH_TOLERANCE and confidence >= Config.MIN_CONFIDENCE_PERCENT:
                result["student"] = known_students[best_idx]
                result["confidence"] = confidence
                result["is_unknown"] = False
            else:
                result["confidence"] = confidence

        spoof = basic_spoof_check(bgr_image, location)
        result["spoof_suspicious"] = spoof["suspicious"]
        result["spoof_reason"] = spoof["reason"]

        results.append(result)

    return results
