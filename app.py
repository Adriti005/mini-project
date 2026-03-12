"""
Food Wastage Predictor — Flask API v2
Model: Gradient Boosting Regressor  |  R² = 0.9147  |  MAE ≈ 2.88 kg
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

# Average kg/count per person from training data
PER_PERSON = {
    "rice_kg":    0.102,
    "dal_kg":     0.1105,
    "roti_count": 2.8981,
    "veg_kg":     0.1311,
    "nonveg_kg":  0.0412,
}

# Reduction % based on waste level
REDUCTION = {
    "low":      0.05,   # 5%  reduction
    "moderate": 0.15,   # 15% reduction
    "high":     0.25,   # 25% reduction
}

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

# ── Helpers ────────────────────────────────────────────────────────────────────

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
    required = ["students_enrolled", "attendance_percent", "special_event",
                "menu_count", "previous_day_leftover_kg", "nonveg_items",
                "meal_type", "day"]
    for f in required:
        if f not in data:
            errors.append(f"Missing: '{f}'")
    if errors:
        return None, None, errors

    try:
        students   = float(data["students_enrolled"])
        attendance = float(data["attendance_percent"])
        special    = 1 if str(data["special_event"]).lower() in ("yes","true","1") else 0
        menu_count = float(data["menu_count"])
        leftover   = float(data["previous_day_leftover_kg"])
        nonveg     = float(data["nonveg_items"])
        meal_type  = 1 if str(data["meal_type"]).lower() == "dinner" else 0
        day        = DAY_ORDER.get(str(data["day"]).capitalize(), 0)
    except (TypeError, ValueError) as e:
        return None, None, [str(e)]

    people       = round(students * attendance / 100)
    main_veg_kg  = people * PER_PERSON["veg_kg"] * menu_count
    main_nonveg  = people * PER_PERSON["nonveg_kg"] if nonveg else 0.0

    vector = np.array([[
        students, attendance, special, menu_count, leftover,
        nonveg, meal_type, day, main_nonveg, main_veg_kg, people
    ]])

    context = {
        "people": people,
        "nonveg": nonveg,
        "menu_count": menu_count,
        "students": students,
        "attendance": attendance,
        "special": special,
        "leftover": leftover,
        "meal_type": meal_type,
        "day": day,
    }

    return vector, context, []


def _compute_recommendations(waste_kg: float, context: dict) -> dict:
    """
    Two-step approach:
    1. Fixed % reduction based on waste level
    2. Re-run ML model with reduced quantities to get optimized waste
    """
    people     = context["people"]
    level      = _insight(waste_kg)["waste_level"]
    reduction  = REDUCTION[level]

    # Step 1 — Recommended cooking quantities (reduced by %)
    rice      = round(people * PER_PERSON["rice_kg"]    * (1 - reduction), 1)
    dal       = round(people * PER_PERSON["dal_kg"]     * (1 - reduction), 1)
    roti      = round(people * PER_PERSON["roti_count"] * (1 - reduction))
    veg       = round(people * PER_PERSON["veg_kg"]     * context["menu_count"] * (1 - reduction), 1)
    nonveg_kg = round(people * PER_PERSON["nonveg_kg"]  * (1 - reduction), 1) if context["nonveg"] else 0

    # Step 2 — Re-run ML model with optimized quantities
    opt_main_veg    = veg
    opt_main_nonveg = nonveg_kg

    opt_vector = np.array([[
        context["students"],
        context["attendance"],
        context["special"],
        context["menu_count"],
        context["leftover"],
        context["nonveg"],
        context["meal_type"],
        context["day"],
        opt_main_nonveg,
        opt_main_veg,
        people,
    ]])

    optimized_waste = max(0.0, round(float(model.predict(opt_vector)[0]), 1))
    waste_reduction = round(waste_kg - optimized_waste, 1)

    return {
        "current_waste_kg":   waste_kg,
        "optimized_waste_kg": optimized_waste,
        "waste_reduction_kg": waste_reduction,
        "reduction_percent":  round(reduction * 100),
        "quantities": {
            "rice_kg":    rice,
            "dal_kg":     dal,
            "roti_count": roti,
            "veg_kg":     veg,
            "nonveg_kg":  nonveg_kg,
        }
    }


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


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    vector, context, errors = _parse(data)
    if errors:
        return jsonify({"errors": errors}), 422

    predicted = max(0.0, round(float(model.predict(vector)[0]), 4))
    return jsonify({
        "predicted_waste_kg": predicted,
        "insight":            _insight(predicted),
    })


@app.route("/predict/recommend", methods=["POST"])
def predict_and_recommend():
    """Predict waste AND return optimized cooking quantities."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    vector, context, errors = _parse(data)
    if errors:
        return jsonify({"errors": errors}), 422

    predicted = max(0.0, round(float(model.predict(vector)[0]), 1))
    recommendations = _compute_recommendations(predicted, context)

    return jsonify({
        "predicted_waste_kg": predicted,
        "insight":            _insight(predicted),
        "recommendations":    recommendations,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
