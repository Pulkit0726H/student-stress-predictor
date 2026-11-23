"""Shared dataset schema for stress-level model training and inference."""
FEATURES = [
    "sleep_hours_per_night",
    "screen_time_hours_per_day",
    "study_hours_per_day",
    "exercise_minutes_per_day",
    "social_media_hours_per_day",
    "tea_coffee_cups_per_day",
    "attendance_percentage",
    "part_time_job",
    "extracurricular_hours_per_week",
    "deadlines_exams_this_week",
]
TARGET = "stress_level_1_to_10"
CATEGORICAL_FEATURES = ["part_time_job"]
NUMERIC_FEATURES = [feature for feature in FEATURES if feature not in CATEGORICAL_FEATURES]

FEATURE_LABELS = {
    "sleep_hours_per_night": "Sleep per night",
    "screen_time_hours_per_day": "Screen time per day",
    "study_hours_per_day": "Study hours per day",
    "exercise_minutes_per_day": "Exercise per day",
    "social_media_hours_per_day": "Social media per day",
    "tea_coffee_cups_per_day": "Tea or coffee cups per day",
    "attendance_percentage": "Attendance",
    "part_time_job": "Part-time job",
    "extracurricular_hours_per_week": "Extracurricular hours per week",
    "deadlines_exams_this_week": "Deadlines or exams this week",
}

# Bounds reflect the observed scale of this synthetic source dataset, while allowing
# sensible experimentation at common boundaries.
FIELD_CONFIG = [
    {"key": "sleep_hours_per_night", "label": "Sleep per night", "unit": "hours", "min": 0, "max": 24, "step": "0.1", "hint": "Average hours of sleep each night."},
    {"key": "screen_time_hours_per_day", "label": "Screen time per day", "unit": "hours", "min": 0, "max": 24, "step": "0.1", "hint": "Total daily screen time."},
    {"key": "study_hours_per_day", "label": "Study hours per day", "unit": "hours", "min": 0, "max": 24, "step": "0.1", "hint": "Average time spent studying each day."},
    {"key": "exercise_minutes_per_day", "label": "Exercise per day", "unit": "minutes", "min": 0, "max": 1440, "step": "1", "hint": "Daily exercise in minutes."},
    {"key": "social_media_hours_per_day", "label": "Social media per day", "unit": "hours", "min": 0, "max": 24, "step": "0.1", "hint": "Average daily social media use."},
    {"key": "tea_coffee_cups_per_day", "label": "Tea or coffee cups per day", "unit": "cups", "min": 0, "max": 100, "step": "1", "hint": "Total cups consumed each day."},
    {"key": "attendance_percentage", "label": "Attendance", "unit": "%", "min": 0, "max": 100, "step": "0.1", "hint": "Overall class attendance percentage."},
    {"key": "part_time_job", "label": "Part-time job", "unit": "", "type": "select", "options": ["No", "Yes"], "hint": "Whether you currently have a part-time job."},
    {"key": "extracurricular_hours_per_week", "label": "Extracurricular hours per week", "unit": "hours", "min": 0, "max": 168, "step": "0.1", "hint": "Weekly time spent on extracurricular activities."},
    {"key": "deadlines_exams_this_week", "label": "Deadlines or exams this week", "unit": "", "min": 0, "max": 30, "step": "1", "hint": "Number of upcoming deadlines and exams."},
]
