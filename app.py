import sys
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Streamlit re-reads this script and the page scripts on every run, but keeps imported modules in memory.
# After a git pull on Streamlit Cloud that leaves a stale rul.* next to new page code (ImportError).
# Drop the rul package from the module cache whenever any of its files is newer than when it was loaded.
_pkg = sys.modules.get("rul")
if _pkg is not None:
    _newest = max(p.stat().st_mtime for p in (Path(__file__).parent / "rul").rglob("*.py"))
    if _newest > getattr(_pkg, "_loaded_at", 0):
        for _m in [m for m in sys.modules if m == "rul" or m.startswith("rul.")]:
            del sys.modules[_m]
import rul  # noqa: E402

if not hasattr(rul, "_loaded_at"):
    rul._loaded_at = time.time()

load_dotenv()

st.set_page_config(
    page_title="RUL Predictor | Mechanical Engineering",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from rul.ui import footer, inject_css, render_nav  # noqa: E402

inject_css()

pages = [
    st.Page("views/home.py", title="Home", default=True),
    st.Page("views/about.py", title="About", url_path="about"),
    st.Page("views/methodology.py", title="Methodology", url_path="methodology"),
    st.Page("views/predictor.py", title="Predictor", url_path="predictor"),
    st.Page("views/data_kb.py", title="Data and Knowledge", url_path="data"),
]
nav = st.navigation(pages, position="hidden")
render_nav(getattr(nav, "url_path", "") or "")
nav.run()
footer()
