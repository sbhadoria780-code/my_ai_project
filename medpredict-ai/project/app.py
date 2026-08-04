"""
app.py
-------
MedPredict AI — Flask backend.
Serves the front-end and exposes a /predict API that runs the selected
symptoms through a trained Random Forest or XGBoost model.
"""

import json
import os

import joblib
import numpy as np
from flask import Flask, jsonify, render_template, request

from utils.health_suggestions import get_health_suggestion

app = Flask(__name__)

MODELS_DIR = "models"

# ---------------- Load trained artifacts at startup ----------------
rf_model = None
xgb_model = None
label_encoder = None
symptom_columns = []
metrics = {}

try:
    rf_model = joblib.load(f"{MODELS_DIR}/rf_model.pkl")
    xgb_model = joblib.load(f"{MODELS_DIR}/xgb_model.pkl")
    label_encoder = joblib.load(f"{MODELS_DIR}/label_encoder.pkl")
    symptom_columns = joblib.load(f"{MODELS_DIR}/symptoms.pkl")
    with open(f"{MODELS_DIR}/metrics.json") as f:
        metrics = json.load(f)
    print(f"Models loaded. {len(symptom_columns)} symptoms, "
          f"{len(label_encoder.classes_)} diseases.")
except FileNotFoundError:
    print("[error] Trained models not found. Run `python train_model.py` first.")


def format_symptom_label(symptom: str) -> str:
    """Turn 'skin_rash' into 'Skin Rash' for display."""
    return symptom.replace("_", " ").strip().title()


@app.route("/")
def index():
    display_symptoms = sorted(
        [{"value": s, "label": format_symptom_label(s)} for s in symptom_columns],
        key=lambda x: x["label"],
    )
    return render_template("index.html", symptoms=display_symptoms, metrics=metrics)


@app.route("/predict", methods=["POST"])
def predict():
    if rf_model is None or xgb_model is None:
        return jsonify({"error": "Models are not trained yet. Run train_model.py first."}), 500

    data = request.get_json(force=True)
    selected_symptoms = data.get("symptoms", [])
    model_choice = data.get("model", "both")  # 'rf', 'xgb', or 'both'

    if not selected_symptoms:
        return jsonify({"error": "Please select at least one symptom."}), 400

    # Build the input feature vector
    input_vector = np.zeros(len(symptom_columns))
    matched = []
    for symptom in selected_symptoms:
        if symptom in symptom_columns:
            idx = symptom_columns.index(symptom)
            input_vector[idx] = 1
            matched.append(symptom)

    if not matched:
        return jsonify({"error": "None of the selected symptoms were recognized."}), 400

    input_df = input_vector.reshape(1, -1)

    results = {}

    if model_choice in ("rf", "both"):
        rf_pred_idx = rf_model.predict(input_df)[0]
        rf_proba = rf_model.predict_proba(input_df)[0]
        rf_disease = label_encoder.inverse_transform([rf_pred_idx])[0]
        results["random_forest"] = {
            "disease": rf_disease,
            "confidence": round(float(np.max(rf_proba)) * 100, 2),
        }

    if model_choice in ("xgb", "both"):
        xgb_pred_idx = xgb_model.predict(input_df)[0]
        xgb_proba = xgb_model.predict_proba(input_df)[0]
        xgb_disease = label_encoder.inverse_transform([xgb_pred_idx])[0]
        results["xgboost"] = {
            "disease": xgb_disease,
            "confidence": round(float(np.max(xgb_proba)) * 100, 2),
        }

    # Use the higher-confidence prediction as the "final" headline result
    if len(results) == 2:
        final_key = max(results, key=lambda k: results[k]["confidence"])
    else:
        final_key = list(results.keys())[0]

    final_disease = results[final_key]["disease"]
    suggestion = get_health_suggestion(final_disease)

    return jsonify({
        "matched_symptoms": [format_symptom_label(s) for s in matched],
        "predictions": results,
        "final_prediction": final_disease,
        "suggestion": suggestion,
    })


@app.route("/symptoms")
def get_symptoms():
    return jsonify(sorted(symptom_columns))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
