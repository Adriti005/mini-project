"""
Food Wastage Predictor — Flask API v2
Model: Gradient Boosting Regressor  |  R² = 0.9147  |  MAE ≈ 2.88 kg
Features now match app form fields directly.
"""

from flask import Flask, request, jsonify
import joblib
import numpy as np
import json
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(__file__)
model    = joblib.load(os.path.join(BASE_DIR, "waste_model.pkl"))

with open(os.path.join(BASE_DIR, "model_metadata.json")) as f:
    metadata = json.load(f)

METRICS   = metadata["metrics"]
DAY_ORDER = {"Monday":0,"Tuesday":1,"Wednesday":2,"Thursday":3,
             "Friday":4,"Saturday":5,"Sunday":6}

# ── CORS ──────────────────────────────────────────────────────────────────────
def _cors(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

@app.after_request
def after_request(response):
    return _cors(response)

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        from flask import Response
        return _cors(Response(status=204))

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "service": "Food Wastage Predictor API v2",
        "model":   "GradientBoostingRegressor",
        "metrics": METRICS,
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/model/info", methods=["GET"])
def model_info():
    return jsonify(metadata)


def _insight(waste_kg: float) -> dict:
    level = "low" if waste_kg < 10 else ("moderate" if waste_kg < 25 else "high")
    tip = {
        "low":      "Great! Waste is well-controlled today.",
        "moderate": "Consider reducing non-veg portion sizes slightly.",
        "high":     "High waste detected — review serving quantities."
    }[level]
    return {"waste_level": level, "tip": tip}


def _parse(data: dict):
    errors = []
    required = ["students_enrolled","attendance_percent","special_event",
                "menu_count","previous_day_leftover_kg","nonveg_items",
                "meal_type","day"]
    for f in required:
        if f not in data:
            errors.append(f"Missing: '{f}'")
    if errors:
        return None, errors

    try:
        students    = float(data["students_enrolled"])
        attendance  = float(data["attendance_percent"])
        special     = 1 if str(data["special_event"]).lower() in ("yes","true","1") else 0
        menu_count  = float(data["menu_count"])
        leftover    = float(data["previous_day_leftover_kg"])
        nonveg      = float(data["nonveg_items"])   # 0 or 1
        meal_type   = 1 if str(data["meal_type"]).lower() == "dinner" else 0
        day         = DAY_ORDER.get(str(data["day"]).capitalize(), 0)
    except (TypeError, ValueError) as e:
        return None, [str(e)]

    # Estimate food quantities from students + attendance
    people       = round(students * attendance / 100)
    main_veg_kg  = people * 0.10 * menu_count
    main_nonveg  = people * 0.08 if nonveg else 0.0

    vector = np.array([[
        students, attendance, special, menu_count, leftover,
        nonveg, meal_type, day, main_nonveg, main_veg_kg, people
    ]])

    return vector, []


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    vector, errors = _parse(data)
    if errors:
        return jsonify({"errors": errors}), 422

    predicted = max(0.0, round(float(model.predict(vector)[0]), 4))
    return jsonify({
        "predicted_waste_kg": predicted,
        "insight": _insight(predicted),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
