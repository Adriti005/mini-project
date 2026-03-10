"""
train_model.py
Run this script to retrain the model from scratch using the CSV data.
Usage: python train_model.py
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import joblib
import json

# ── Load data ─────────────────────────────────────────────────────────────────
df = pd.read_csv('Final_data_1.csv')

# ── Encode categorical columns ────────────────────────────────────────────────
DAY_ORDER = {
    'Monday': 0, 'Tuesday': 1, 'Wednesday': 2,
    'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6
}
df['Day_enc']           = df['Day'].map(DAY_ORDER)
df['Meal_type_enc']     = (df['Meal_type'] == 'Dinner').astype(int)
df['Meal_category_enc'] = (df['Meal_category'] == 'Mixed').astype(int)
df['Special_event_enc'] = (df['Special_event'] == 'Yes').astype(int)

# ── Features and target ───────────────────────────────────────────────────────
features = [
    'Students_enrolled',
    'Attendance_percent',
    'Special_event_enc',
    'Menu_count',
    'Previous_day_leftover_kg',
    'Nonveg_items',
    'Meal_type_enc',
    'Day_enc',
    'Main_nonveg_kg',
    'Main_veg_kg',
    'People_served',
]

X = df[features]
y = df['Total_Waste_kg']

# ── Train/test split ──────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ── Train model ───────────────────────────────────────────────────────────────
model = GradientBoostingRegressor(
    n_estimators=200,
    learning_rate=0.1,
    max_depth=4,
    random_state=42
)
model.fit(X_train, y_train)

# ── Evaluate ──────────────────────────────────────────────────────────────────
preds = model.predict(X_test)
mae   = mean_absolute_error(y_test, preds)
rmse  = np.sqrt(mean_squared_error(y_test, preds))
r2    = r2_score(y_test, preds)

print(f"MAE:  {mae:.4f} kg")
print(f"RMSE: {rmse:.4f} kg")
print(f"R²:   {r2:.4f}")

print("\nFeature Importances:")
for f, i in sorted(zip(features, model.feature_importances_), key=lambda x: -x[1]):
    print(f"  {f}: {i:.4f}")

# ── Save model and metadata ───────────────────────────────────────────────────
joblib.dump(model, 'waste_model.pkl')
print("\nModel saved as waste_model.pkl")

metadata = {
    "features": features,
    "metrics": {
        "mae":  round(mae, 4),
        "rmse": round(rmse, 4),
        "r2":   round(r2, 4)
    },
    "feature_importances": dict(zip(features, model.feature_importances_.tolist()))
}
with open('model_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
print("Metadata saved as model_metadata.json")
