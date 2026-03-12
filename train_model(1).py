"""
Food Wastage Predictor — Model Training
Style: Model comparison + Cross Validation + GridSearchCV
"""

import pandas as pd
import numpy as np
import joblib
import json

from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error

# ── Load Data ──────────────────────────────────────────────────────────────────

df = pd.read_csv('Final_data_1.csv')

df.head()
df.shape
df.isnull().sum()

# ── Feature Engineering ────────────────────────────────────────────────────────

DAY_ORDER = {
    'Monday': 0, 'Tuesday': 1, 'Wednesday': 2,
    'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6
}

df['Day_enc']           = df['Day'].map(DAY_ORDER)
df['Meal_type_enc']     = (df['Meal_type'] == 'Dinner').astype(int)
df['Meal_category_enc'] = (df['Meal_category'] == 'Mixed').astype(int)
df['Special_event_enc'] = (df['Special_event'] == 'Yes').astype(int)

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

x = df[features]
y = df['Total_Waste_kg']

x = np.asarray(x)
y = np.asarray(y)

# ── Train/Test Split ───────────────────────────────────────────────────────────

x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.2, random_state=42
)

# ── Step 1: Model Selection ────────────────────────────────────────────────────
# Comparing models with default hyperparameters using cross validation

models = [
    Ridge(),
    KNeighborsRegressor(),
    RandomForestRegressor(random_state=0),
    GradientBoostingRegressor(random_state=0),
]

def compareusingcrossvalidation():
    for model in models:
        cv_score      = cross_val_score(model, x, y, cv=5, scoring='r2')
        mean_accuracy = sum(cv_score) / len(cv_score)
        mean_accuracy = mean_accuracy * 100
        mean_accuracy = round(mean_accuracy, 2)

        print('Cross validation R² scores for the', model, '=', cv_score)
        print('Mean R² score of the', model, '=', mean_accuracy, '%')
        print('------------------------------------------')

compareusingcrossvalidation()

# ── Step 2: Hyperparameter Tuning with GridSearchCV ────────────────────────────

models = [
    Ridge(),
    KNeighborsRegressor(),
    RandomForestRegressor(random_state=0),
    GradientBoostingRegressor(random_state=0),
]

model_hyperparameters = {
    'ridge_hyperparameters': {
        'alpha': [0.1, 1.0, 10.0, 100.0]
    },
    'KNN_hyperparameters': {
        'n_neighbors': [3, 5, 10]
    },
    'random_forest_hyperparameters': {
        'n_estimators': [10, 50, 100, 200]
    },
    'gradientboosting_hyperparameters': {
        'n_estimators':  [100, 200],
        'learning_rate': [0.05, 0.1],
        'max_depth':     [3, 4],
    }
}

print(model_hyperparameters.keys())

modelkeys = list(model_hyperparameters.keys())

def modelselection(list_of_models, hyperparameters_dictionary):
    result = []
    i = 0
    for model in list_of_models:
        key    = modelkeys[i]
        params = hyperparameters_dictionary[key]
        i += 1
        print(model)
        print(params)
        print('--------------------------------------------------')

        classifier = GridSearchCV(model, params, cv=5, scoring='r2')
        classifier.fit(x_train, y_train)
        result.append({
            'model used':           model,
            'highest score':        classifier.best_score_,
            'best hyperparameters': classifier.best_params_,
            'best estimator':       classifier.best_estimator_,
        })

    result_dataframe = pd.DataFrame(
        result, columns=['model used', 'highest score', 'best hyperparameters', 'best estimator']
    )
    return result_dataframe

result = modelselection(models, model_hyperparameters)
print(result)

# ── Step 3: Pick Best Model ────────────────────────────────────────────────────

best_idx   = result['highest score'].idxmax()
best_row   = result.iloc[best_idx]
best_model = best_row['best estimator']

print('\nBest model:', best_row['model used'])
print('Best R² score:', round(best_row['highest score'] * 100, 2), '%')
print('Best hyperparameters:', best_row['best hyperparameters'])

# ── Step 4: Final Evaluation ───────────────────────────────────────────────────

best_model.fit(x_train, y_train)
preds = best_model.predict(x_test)

mae  = mean_absolute_error(y_test, preds)
rmse = np.sqrt(mean_squared_error(y_test, preds))
r2   = r2_score(y_test, preds)

print('\nFinal Test Metrics:')
print(f'  MAE:  {mae:.4f} kg')
print(f'  RMSE: {rmse:.4f} kg')
print(f'  R²:   {r2:.4f}')

print('\nFeature Importances:')
if hasattr(best_model, 'feature_importances_'):
    for f, i in sorted(
        zip(features, best_model.feature_importances_), key=lambda x: -x[1]
    ):
        print(f'  {f}: {i:.4f}')

# ── Step 5: Save Model ─────────────────────────────────────────────────────────

joblib.dump(best_model, 'waste_model.pkl')
print('\nModel saved as waste_model.pkl')

metadata = {
    'features': features,
    'metrics': {
        'mae':  round(mae, 4),
        'rmse': round(rmse, 4),
        'r2':   round(r2, 4),
    },
    'feature_importances': dict(
        zip(features, best_model.feature_importances_.tolist())
    ) if hasattr(best_model, 'feature_importances_') else {}
}

with open('model_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print('Metadata saved as model_metadata.json')
