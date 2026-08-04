"""
train_model.py
----------------
Trains a Random Forest and an XGBoost classifier on the disease-symptom
dataset (Training.csv / Testing.csv) and saves the trained models,
label encoder, and symptom list to the models/ directory.

Run this once before starting the Flask app:
    python train_model.py
"""

import json
import warnings

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    # Falls back to a scikit-learn Gradient Boosting model if the xgboost
    # package isn't installed, so the project still runs end-to-end.
    from sklearn.ensemble import GradientBoostingClassifier
    XGBOOST_AVAILABLE = False
    print("[warn] xgboost not installed — falling back to sklearn's "
          "GradientBoostingClassifier. Run `pip install xgboost` for the "
          "real XGBoost model.")

DATA_DIR = "data"
MODELS_DIR = "models"


def load_data():
    train_df = pd.read_csv(f"{DATA_DIR}/Training.csv")
    test_df = pd.read_csv(f"{DATA_DIR}/Testing.csv")

    # Drop any stray unnamed/empty columns present in the raw CSV export
    train_df = train_df.loc[:, ~train_df.columns.str.contains("^Unnamed")]
    test_df = test_df.loc[:, ~test_df.columns.str.contains("^Unnamed")]

    train_df.columns = train_df.columns.str.strip()
    test_df.columns = test_df.columns.str.strip()

    return train_df, test_df


def main():
    print("Loading data...")
    train_df, test_df = load_data()

    symptom_columns = [c for c in train_df.columns if c != "prognosis"]

    X_train = train_df[symptom_columns]
    y_train_raw = train_df["prognosis"].astype(str).str.strip()

    X_test = test_df[symptom_columns]
    y_test_raw = test_df["prognosis"].astype(str).str.strip()

    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(y_train_raw)
    y_test = label_encoder.transform(y_test_raw)

    print(f"Symptoms: {len(symptom_columns)} | Diseases: {len(label_encoder.classes_)}")
    print(f"Training samples: {len(X_train)} | Testing samples: {len(X_test)}")

    # ---------------- Random Forest ----------------
    print("\nTraining Random Forest...")
    rf_model = RandomForestClassifier(
        n_estimators=200, max_depth=None, random_state=42, n_jobs=-1
    )
    rf_model.fit(X_train, y_train)
    rf_preds = rf_model.predict(X_test)
    rf_acc = accuracy_score(y_test, rf_preds)
    print(f"Random Forest test accuracy: {rf_acc:.4f}")

    # ---------------- XGBoost ----------------
    print("\nTraining XGBoost..." if XGBOOST_AVAILABLE else "\nTraining Gradient Boosting (fallback)...")
    if XGBOOST_AVAILABLE:
        xgb_model = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            eval_metric="mlogloss",
            random_state=42,
            n_jobs=-1,
        )
    else:
        xgb_model = GradientBoostingClassifier(n_estimators=150, max_depth=4, random_state=42)

    xgb_model.fit(X_train, y_train)
    xgb_preds = xgb_model.predict(X_test)
    xgb_acc = accuracy_score(y_test, xgb_preds)
    print(f"XGBoost test accuracy: {xgb_acc:.4f}")

    # ---------------- Save artifacts ----------------
    print("\nSaving models...")
    joblib.dump(rf_model, f"{MODELS_DIR}/rf_model.pkl")
    joblib.dump(xgb_model, f"{MODELS_DIR}/xgb_model.pkl")
    joblib.dump(label_encoder, f"{MODELS_DIR}/label_encoder.pkl")
    joblib.dump(symptom_columns, f"{MODELS_DIR}/symptoms.pkl")

    metrics = {
        "random_forest_accuracy": round(rf_acc * 100, 2),
        "xgboost_accuracy": round(xgb_acc * 100, 2),
        "xgboost_is_real": XGBOOST_AVAILABLE,
        "num_symptoms": len(symptom_columns),
        "num_diseases": len(label_encoder.classes_),
    }
    with open(f"{MODELS_DIR}/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("\nDone! Models saved to the models/ directory.")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
