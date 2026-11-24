from pathlib import Path

import pandas as pd

from .config import ROOT


def resolve_path(p) -> Path:
    path = Path(p)
    return path if path.is_absolute() else ROOT / path


def load_dataset(entry: dict) -> pd.DataFrame:
    """Load a registered dataset and add a normalised `_type` column."""
    df = pd.read_csv(resolve_path(entry["path"]))
    features, target = entry["features"], entry["target"]
    need = [target, *features]
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise ValueError(f"Columns missing from {entry['path']}: {missing}")
    for c in need:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if entry.get("fixed_type"):
        df["_type"] = str(entry["fixed_type"]).strip()
    else:
        df["_type"] = df[entry["type_col"]].astype(str).str.strip()
    return df.dropna(subset=need).reset_index(drop=True)


def _feature_stats(d: pd.DataFrame, features) -> dict:
    return {
        f: {
            "min": float(d[f].min()),
            "p1": float(d[f].quantile(0.01)),
            "median": float(d[f].median()),
            "p99": float(d[f].quantile(0.99)),
            "max": float(d[f].max()),
        }
        for f in features
    }


def _rul_stats(s: pd.Series) -> dict:
    return {
        "min": float(s.min()),
        "q10": float(s.quantile(0.10)),
        "q25": float(s.quantile(0.25)),
        "median": float(s.median()),
        "q75": float(s.quantile(0.75)),
        "p95": float(s.quantile(0.95)),
        "max": float(s.max()),
    }


def build_profile(df: pd.DataFrame, features, target) -> dict:
    return {
        "n_rows": int(len(df)),
        "counts": {k: int(v) for k, v in df["_type"].value_counts().items()},
        "global": _feature_stats(df, features),
        "by_type": {t: _feature_stats(g, features) for t, g in df.groupby("_type")},
        "rul": _rul_stats(df[target]),
        "rul_by_type": {t: _rul_stats(g[target]) for t, g in df.groupby("_type")},
    }
