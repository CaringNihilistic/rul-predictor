"""Dataset registry: every CSV the app can learn from is described here (data/registry.json)."""
import json
import re

import pandas as pd

from .config import DATA_DIR, REGISTRY_PATH, ROOT, UPLOAD_DIR

DEFAULT_DATASETS = [
    {
        "id": "construction_machines",
        "name": "Construction machine components",
        "path": "construction_machine_data.csv",
        "type_col": "Component_Type",
        "fixed_type": None,
        "target": "Remaining_Useful_Life",
        "features": ["Vibration", "Temperature", "Pressure", "Operating_Hours"],
        "id_col": "Component_ID",
        "source": "Kaggle",
        "builtin": True,
    }
]


def save_registry(datasets: list) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps({"datasets": datasets}, indent=2), encoding="utf-8")


def load_registry() -> list:
    if not REGISTRY_PATH.exists():
        save_registry(DEFAULT_DATASETS)
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))["datasets"]


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "dataset"


def add_dataset(df: pd.DataFrame, entry: dict) -> dict:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    slug = _slug(entry["name"])
    path = UPLOAD_DIR / f"{slug}.csv"
    df.to_csv(path, index=False)
    entry = {**entry, "id": slug, "path": str(path.relative_to(ROOT)), "builtin": False}
    save_registry([d for d in load_registry() if d["id"] != slug] + [entry])
    return entry


def remove_dataset(dataset_id: str) -> None:
    save_registry([d for d in load_registry() if d["id"] != dataset_id or d.get("builtin")])
