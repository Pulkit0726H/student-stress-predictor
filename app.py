"""Flask interface for student lifestyle and stress-level estimates."""
from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
from flask import Flask, render_template, request

from config import CATEGORICAL_FEATURES, FEATURES, FIELD_CONFIG, TARGET

ROOT = Path(__file__).resolve().parent
app = Flask(__name__)
MODEL_PATH = ROOT / "model" / "model.pkl"
METRICS_PATH = ROOT / "model" / "metrics.json"
DATA_PATH = ROOT / "dataset" / "student_data.csv"


def stress_category(score):
    if score < 4:
        return "Lower stress"
    if score < 7:
        return "Moderate stress"
    if score < 9:
        return "Higher stress"
    return "Very high stress"


def load_bundle():
    if not MODEL_PATH.exists():
        raise FileNotFoundError("The trained model is not available. Run python train_model.py, then restart the app.")
    return joblib.load(MODEL_PATH)


def read_form(source):
    values = {}
    for field in FIELD_CONFIG:
        key = field["key"]
        raw = source.get(key, "").strip()
        if not raw:
            raise ValueError(f"Please enter {field['label'].lower()}.")
        if key in CATEGORICAL_FEATURES:
            allowed = field["options"]
            if raw not in allowed:
                raise ValueError(f"Choose a valid option for {field['label'].lower()}.")
            values[key] = raw
            continue
        try:
            value = float(raw)
        except ValueError:
            raise ValueError(f"{field['label']} must be a number.")
        if not np.isfinite(value) or value < field["min"] or value > field["max"]:
            raise ValueError(f"{field['label']} must be between {field['min']} and {field['max']}.")
        if field["step"] == "1" and not value.is_integer():
            raise ValueError(f"{field['label']} must be a whole number.")
        values[key] = value
    return values


def predict(values):
    bundle = load_bundle()
    row = pd.DataFrame([[values[name] for name in FEATURES]], columns=FEATURES)
    return float(np.clip(bundle["model"].predict(row)[0], 1, 10))


def synthetic_dataset():
    notice = ROOT / "dataset" / "DATASET_NOTICE.txt"
    return notice.exists()


def build_routine(exam_count, stress_score):
    """Build a flexible, rule-based seven-day study outline from the estimate and exam count."""
    if stress_score < 4:
        load = "Steady"
        blocks = [
            "09:00–09:50 · Focus on the priority topic",
            "11:00–11:50 · Practice questions or active recall",
            "14:30–15:20 · Review mistakes and summarize",
        ]
        break_note = "Take a 10-minute reset between blocks and a longer lunch break."
        reset_note = "Finish focused study by late afternoon and keep your usual sleep routine."
    elif stress_score < 7:
        load = "Balanced"
        blocks = [
            "09:30–10:15 · Focus on the priority topic",
            "13:30–14:15 · Practice questions or active recall",
        ]
        break_note = "Take a 15-minute reset between blocks and leave time for lunch."
        reset_note = "Keep the evening flexible for a light review or rest."
    elif stress_score < 9:
        load = "Light and flexible"
        blocks = [
            "10:00–10:30 · One priority topic, broken into small tasks",
            "14:00–14:30 · Optional practice or recap block",
        ]
        break_note = "Leave at least 20 minutes between blocks; skip the optional block if it feels like too much."
        reset_note = "Keep a generous buffer, take regular breaks, and protect your usual sleep and meal times."
    else:
        load = "Minimum viable plan"
        blocks = [
            "Choose one manageable 25-minute priority study block",
            "Optional: a second 25-minute recap later, only if useful",
        ]
        break_note = "Stop after the first block if needed; a small completed task is enough for today."
        reset_note = "Keep the rest of the day open for meals, rest, and support from someone you trust if helpful."

    exam_groups = [[] for _ in range(7)]
    for exam_number in range(1, exam_count + 1):
        day_index = min(6, ((exam_number - 1) * 7) // max(exam_count, 1))
        exam_groups[day_index].append(exam_number)

    days = []
    for index, group in enumerate(exam_groups):
        if exam_count == 0:
            focus = "Review current coursework and note upcoming deadlines."
        elif group:
            labels = ", ".join(f"Exam {number}" for number in group)
            focus = f"Prioritize {labels}: choose one key topic and use practice questions."
        else:
            focus = "Spaced review of the next exam and catch up on any unfinished topic."
        days.append({
            "day": f"Day {index + 1}",
            "focus": focus,
            "blocks": blocks,
            "break_note": break_note,
            "reset_note": reset_note,
        })
    return days, load


@app.get("/")
def home():
    return render_template("index.html", fields=FIELD_CONFIG, error=None,
                           submitted={}, synthetic=synthetic_dataset())


@app.post("/predict")
def prediction():
    try:
        values = read_form(request.form)
        score = predict(values)
        return render_template("result.html", values=values, score=score,
                               category=stress_category(score), fields=FIELD_CONFIG,
                               old_score=None, error=None, synthetic=synthetic_dataset())
    except (ValueError, FileNotFoundError, OSError) as exc:
        return render_template("index.html", fields=FIELD_CONFIG, error=str(exc),
                               submitted=request.form, synthetic=synthetic_dataset()), 400


@app.post("/what-if")
def what_if():
    try:
        values = read_form(request.form)
        old_score = float(request.form.get("old_score", ""))
        if not np.isfinite(old_score) or not 1 <= old_score <= 10:
            raise ValueError("The previous estimate is missing or invalid. Please run a new prediction.")
        score = predict(values)
        return render_template("result.html", values=values, score=score,
                               category=stress_category(score), old_score=old_score,
                               fields=FIELD_CONFIG, error=None, synthetic=synthetic_dataset())
    except (ValueError, FileNotFoundError, OSError) as exc:
        return render_template("index.html", fields=FIELD_CONFIG, error=str(exc),
                               submitted=request.form, synthetic=synthetic_dataset()), 400


@app.post("/routine")
def routine():
    try:
        score = float(request.form.get("stress_score", ""))
        if not np.isfinite(score) or not 1 <= score <= 10:
            raise ValueError("The stress estimate is missing or invalid. Please make a new estimate.")
        raw_count = request.form.get("exam_count", "").strip()
        if not raw_count:
            raise ValueError("Enter the number of upcoming exams or deadlines.")
        count_value = float(raw_count)
        if not np.isfinite(count_value) or not count_value.is_integer() or not 0 <= count_value <= 30:
            raise ValueError("Enter a whole number of exams or deadlines from 0 to 30.")
        exam_count = int(count_value)
        days, load = build_routine(exam_count, score)
        return render_template("routine.html", score=score,
                               category=stress_category(score), exam_count=exam_count,
                               days=days, load=load, error=None,
                               synthetic=synthetic_dataset())
    except (ValueError, OSError) as exc:
        return render_template("routine.html", score=None, category=None,
                               exam_count=None, days=None, load=None,
                               error=str(exc), synthetic=synthetic_dataset()), 400


def dashboard_data():
    df = pd.read_csv(DATA_PATH)
    df.columns = [str(column).strip().lower() for column in df.columns]
    series = {}
    for feature in ("study_hours_per_day", "sleep_hours_per_night", "screen_time_hours_per_day"):
        points = df[[feature, TARGET]].apply(pd.to_numeric, errors="coerce").dropna().head(300)
        series[feature] = [{"x": float(row[0]), "y": float(row[1])} for row in points.to_numpy()]
    return series


def feature_importance(bundle):
    pipeline = bundle["model"]
    regressor = pipeline.named_steps.get("regressor")
    if not hasattr(regressor, "feature_importances_"):
        return None
    transformed_names = pipeline.named_steps["preprocessor"].get_feature_names_out()
    readable_names = [name.split("__", 1)[-1].replace("part_time_job_", "Part-time job: ")
                      for name in transformed_names]
    return sorted(zip(readable_names, regressor.feature_importances_.tolist()),
                  key=lambda pair: pair[1], reverse=True)


@app.get("/dashboard")
def dashboard():
    try:
        if not METRICS_PATH.exists():
            raise FileNotFoundError("Training metrics are missing. Run python train_model.py.")
        metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        bundle = load_bundle()
        return render_template("dashboard.html", metrics=metrics,
                               chart_data=json.dumps(dashboard_data()),
                               importance=feature_importance(bundle),
                               synthetic=synthetic_dataset(), error=None)
    except (FileNotFoundError, OSError, ValueError, KeyError) as exc:
        return render_template("dashboard.html", metrics=None, chart_data="{}",
                               importance=None, synthetic=synthetic_dataset(), error=str(exc))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
