# MedPredict AI — Disease Prediction Mini Project

An AI-powered web app that predicts possible diseases from user-selected symptoms
using **Random Forest** and **XGBoost** classifiers, and returns personalized
health suggestions and precautions.

## Features
- 🔍 Searchable symptom input (132 symptoms)
- 🤖 Disease prediction with Random Forest & XGBoost (compare both or pick one)
- 💡 Personalized health suggestions & precautions for 41 diseases
- 📊 Live model accuracy stats on the "How It Works" section
- 🎨 Polished, responsive UI with the MedPredict AI hero design

## Project Structure
```
medpredict-ai/
├── app.py                     # Flask backend + /predict API
├── train_model.py             # Trains & saves the RF / XGBoost models
├── requirements.txt
├── data/
│   ├── Training.csv
│   └── Testing.csv
├── models/                    # Generated after running train_model.py
│   ├── rf_model.pkl
│   ├── xgb_model.pkl
│   ├── label_encoder.pkl
│   ├── symptoms.pkl
│   └── metrics.json
├── utils/
│   └── health_suggestions.py  # Disease -> description/precautions mapping
├── templates/
│   └── index.html
└── static/
    ├── css/style.css
    ├── js/script.js
    └── images/hero-bg.png
```

## Setup & Run

1. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Train the models** (creates the `models/` folder contents)
   ```bash
   python train_model.py
   ```
   You should see output like:
   ```
   Random Forest test accuracy: 0.9762
   XGBoost test accuracy: 0.9762
   ```

4. **Run the app**
   ```bash
   python app.py
   ```
   Then open **http://localhost:5000** in your browser.

> Note: if `xgboost` isn't installed, `train_model.py` automatically falls back
> to scikit-learn's `GradientBoostingClassifier` so the project still runs —
> but run `pip install xgboost` for the real XGBoost model used in the UI labels.

## Dataset
`data/Training.csv` and `data/Testing.csv` contain 132 binary symptom columns
and a `prognosis` column with 41 possible diseases (the classic Kaggle
"Disease Prediction Using Machine Learning" dataset).

## How Prediction Works
1. The user selects symptoms in the UI (converted to a 132-length binary vector).
2. The vector is sent to `/predict`, which runs it through the trained
   Random Forest and/or XGBoost model.
3. The model with the higher confidence is shown as the headline prediction,
   both are shown side-by-side for comparison.
4. `utils/health_suggestions.py` maps the predicted disease to a description,
   severity level, and precaution list shown in the UI.

## Disclaimer
This project is for **educational purposes only**. It is not a medical device
and predictions should never replace professional medical diagnosis or advice.

## Customize
- Swap `static/images/hero-bg.png` for your own hero image.
- Edit `utils/health_suggestions.py` to refine precautions/descriptions.
- Tune model hyperparameters in `train_model.py`.
