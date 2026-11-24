"""Cached shared resources for the Streamlit pages."""
import os

import streamlit as st

from .config import KB_PATH
from .data import load_dataset
from .knowledge import KnowledgeBase
from .model import train
from .registry import load_registry


@st.cache_resource(show_spinner=False)
def get_kb() -> KnowledgeBase:
    return KnowledgeBase(KB_PATH)


@st.cache_resource(show_spinner="Training models on your datasets...")
def get_models():
    models, errors = [], []
    for entry in load_registry():
        try:
            models.append(train(entry))
        except Exception as e:
            errors.append(f"{entry.get('name', entry.get('id'))}: {e}")
    return models, errors


@st.cache_data(show_spinner=False)
def get_overview() -> dict:
    rows, types, n, counts = 0, set(), 0, {}
    for entry in load_registry():
        try:
            df = load_dataset(entry)
        except Exception:
            continue
        n += 1
        rows += len(df)
        types |= set(df["_type"])
        for t, c in df["_type"].value_counts().items():
            counts[t] = counts.get(t, 0) + int(c)
    return {"datasets": n, "rows": rows, "types": len(types), "counts": counts}


def refresh() -> None:
    get_models.clear()
    get_overview.clear()


def secret(name: str) -> str:
    val = os.getenv(name, "")
    if val:
        return val
    try:
        return st.secrets.get(name, "")
    except Exception:
        return ""
