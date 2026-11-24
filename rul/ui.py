"""Design system helpers. Styles live in rul/style.css and are re-read on every page run,
so CSS edits apply immediately (no stale module cache). Palette: white, warm neutrals, one maroon accent."""
from pathlib import Path

import streamlit as st

from .config import BATCH, COLLEGE, PROGRAMME, TEAM

CSS_PATH = Path(__file__).with_name("style.css")

MARK = ("<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round'>"
        "<path d='M4 16a8 8 0 1 1 16 0'/><path d='M12 16l4-5'/><circle cx='12' cy='16' r='1.4' fill='currentColor'/></svg>")

NAV_LINKS = [("Home", "/", "home"), ("About", "/about", "about"), ("Methodology", "/methodology", "methodology"),
             ("Predictor", "/predictor", "predictor"), ("Data", "/data", "data")]


def inject_css() -> None:
    st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def html(s: str) -> None:
    """Render an HTML snippet. Leading whitespace and blank lines are stripped so Markdown never treats it as code."""
    st.markdown("\n".join(l.strip() for l in s.splitlines() if l.strip()), unsafe_allow_html=True)


def pill(text: str, kind: str = "na") -> str:
    return f"<span class='pill {kind}'>{str(text).upper()}</span>"


def section(title: str, sub: str = "", eyebrow: str = "", num: int | None = None) -> None:
    lab = f"<b>{num:02d}</b> &nbsp;{eyebrow}" if num else eyebrow
    ey = f"<div class='eyebrow'>{lab}</div>" if lab else ""
    sb = f"<div class='lede'>{sub}</div>" if sub else ""
    html(f"<div class='sec'>{ey}<div class='h2'>{title}</div>{sb}</div>")


def cards(items, cols: int = 3) -> None:
    cells = ""
    for tag, title, desc in items:
        cells += f"<div class='cell'><div class='tag'>{tag}</div><div class='ct'>{title}</div><div class='cp'>{desc}</div></div>"
    html(f"<div class='cap g{cols}'>{cells}</div>")


def metric_card(label: str, value: str, sub: str = "") -> str:
    return f"<div class='mc'><div class='ml'>{label}</div><div class='mv'>{value}</div><div class='ms'>{sub}</div></div>"


def render_nav(active: str = "") -> None:
    key = (active or "").strip("/") or "home"
    links = "".join(
        f"<a href='{h}' target='_self' class='{'on' if k == key else ''}'>{t}</a>" for t, h, k in NAV_LINKS
    )
    html(f"""
    <div class='nav'><div class='nav-in'>
    <a class='brand' href='/' target='_self'><span class='mark'>{MARK}</span><span>RUL<em>Predictor</em></span></a>
    <nav class='links'>{links}</nav>
    <a class='nav-cta' href='/predictor' target='_self'>Open predictor</a>
    <details class='mm'><summary aria-label='Menu'><i></i><i></i></summary><div class='mpanel'>{links}</div></details>
    </div></div>
    """)


def footer() -> None:
    names = "".join(f"<span class='fi'>{m['name']}</span>" for m in TEAM)
    pages = "".join(f"<a href='{h}' target='_self'>{t}</a>" for t, h, _ in NAV_LINKS)
    college = f" · {COLLEGE}" if COLLEGE else ""
    html(f"""
    <div class='bleed foot'><div class='foot-in'>
    <div class='foot-grid'>
    <div><a class='brand' href='/' target='_self'><span class='mark'>{MARK}</span><span>RUL<em>Predictor</em></span></a>
    <p>Remaining useful life estimates for mechanical components, with failure modes, maintenance plans and cost impact.</p></div>
    <div><div class='fh'>Pages</div>{pages}</div>
    <div><div class='fh'>Built by</div>{names}</div>
    </div>
    <div class='foot-bar'>{PROGRAMME} · {BATCH}{college}<br>
    Academic project. Estimates are indicative; verify against OEM data and plant history before operational decisions.</div>
    </div></div>
    """)
