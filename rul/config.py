from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
REGISTRY_PATH = DATA_DIR / "registry.json"
HISTORY_PATH = DATA_DIR / "history.jsonl"
KB_PATH = ROOT / "rul" / "kb" / "components.json"

# ---- Project identity (edit freely) ----
PROJECT_NAME = "RUL Predictor"
PROJECT_TITLE = "Remaining Useful Life Prediction of Mechanical Components Using Machine Learning"
PROGRAMME = "Mechanical Engineering"
BATCH = "Batch of 2027"
COLLEGE = ""  # TODO: add your college / department name
TEAM = [
    {"name": "Kaushalendra Singh", "initials": "KS"},
    {"name": "Abdul Rahman", "initials": "AR"},
    {"name": "Ayush Yadav", "initials": "AY"},
]

# ---- Modelling ----
STD_FEATURES = ["Vibration", "Temperature", "Pressure", "Operating_Hours"]
# ASSUMPTION: the Kaggle file does not state units. Confirm and edit.
FEATURE_UNITS = {"Vibration": "mm/s", "Temperature": "°C", "Pressure": "bar", "Operating_Hours": "h"}
RUL_UNIT = "hours"
CURRENCY = "INR"
MIN_SKILL_R2 = 0.10  # below this cross-validated R2 the ML model is treated as having no real signal

GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"
CLAUDE_DEFAULT_MODEL = "claude-sonnet-5-5"
