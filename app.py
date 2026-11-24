import streamlit as st
from dotenv import load_dotenv

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
