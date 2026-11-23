"""Compare regression models for the supplied student stress dataset."""
from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeRegressor

from config import CATEGORICAL_FEATURES, FEATURES, NUMERIC_FEATURES, TARGET

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "dataset" / "student_data.csv"
MODEL_PATH = ROOT / "model" / "model.pkl"
METRICS_PATH = ROOT / "model" / "metrics.json"


def load_dataset():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    df.columns = [str(column).strip().lower() for column in df.columns]
    missing = [column for column in FEATURES + [TARGET] if column not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(missing)}")
    df = df[FEATURES + [TARGET]].drop_duplicates().copy()
    for column in NUMERIC_FEATURES + [TARGET]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df[TARGET] = df[TARGET].replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=[TARGET])
    df[CATEGORICAL_FEATURES] = df[CATEGORICAL_FEATURES].fillna("Unknown").astype(str)
    if len(df) < 10:
        raise ValueError("At least 10 rows with a valid stress target are required for model evaluation.")
    if ((df[TARGET] < 1) | (df[TARGET] > 10)).any():
        raise ValueError("Stress target values must be between 1 and 10.")
    return df


def make_pipeline(regressor):
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    categorical = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    prep = ColumnTransformer([
        ("numeric", numeric, NUMERIC_FEATURES),
        ("categorical", categorical, CATEGORICAL_FEATURES),
    ])
    return Pipeline([("preprocessor", prep), ("regressor", regressor)])


def main():
    df = load_dataset()
    print(f"Dataset shape after cleaning: {df.shape}")
    print(f"Features: {FEATURES}")
    x_train, x_test, y_train, y_test = train_test_split(
        df[FEATURES], df[TARGET], test_size=0.2, random_state=42
    )
    estimators = {
        "Linear Regression": LinearRegression(),
        "Decision Tree Regressor": DecisionTreeRegressor(
            max_depth=7, min_samples_leaf=4, random_state=42
        ),
        "Random Forest Regressor": RandomForestRegressor(
            n_estimators=250, min_samples_leaf=2, random_state=42, n_jobs=-1
        ),
    }
    evaluated = []
    for name, estimator in estimators.items():
        pipeline = make_pipeline(estimator)
        pipeline.fit(x_train, y_train)
        predicted = pipeline.predict(x_test)
        evaluated.append({
            "name": name,
            "pipeline": pipeline,
            "mae": float(mean_absolute_error(y_test, predicted)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, predicted))),
            "r2": float(r2_score(y_test, predicted)),
        })
    best = max(evaluated, key=lambda item: (item["r2"], -item["rmse"], -item["mae"]))
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "model": best["pipeline"],
        "model_name": best["name"],
        "features": FEATURES,
        "target": TARGET,
    }, MODEL_PATH)
    metrics = {
        "model_name": best["name"],
        "mae": best["mae"],
        "rmse": best["rmse"],
        "r2": best["r2"],
        "record_count": int(len(df)),
        "feature_names": FEATURES,
        "target_name": TARGET,
        "evaluation": [
            {key: result[key] for key in ("name", "mae", "rmse", "r2")}
            for result in evaluated
        ],
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print("\nModel comparison (held-out 20% test set):")
    print(pd.DataFrame(metrics["evaluation"]).to_string(
        index=False, float_format=lambda value: f"{value:.4f}"
    ))
    print(f"\nSelected: {best['name']} | saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
