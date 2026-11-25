"""Design system helpers. Styles live in rul/style.css and are re-read on every page run,
so CSS edits apply immediately (no stale module cache). Palette: warm paper, graphite, maroon accent, safety amber.
Icons come from Tabler Icons (public/icons) via rul.icons."""
from pathlib import Path

import streamlit as st

from .config import BATCH, COLLEGE, PROGRAMME, TEAM
from .icons import icon

CSS_PATH = Path(__file__).with_name("style.css")

NAV_LINKS = [("Home", "/", "home", "building-factory-2"), ("About", "/about", "about", "school"),
             ("Methodology", "/methodology", "methodology", "route-2"),
             ("Predictor", "/predictor", "predictor", "gauge"), ("Data", "/data", "data", "database")]


def inject_css() -> None:
    st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def html(s: str) -> None:
    """Render an HTML snippet. Leading whitespace and blank lines are stripped so Markdown never treats it as code."""
    st.markdown("\n".join(l.strip() for l in s.splitlines() if l.strip()), unsafe_allow_html=True)


def pill(text: str, kind: str = "na") -> str:
    return f"<span class='pill {kind}'>{str(text).upper()}</span>"


def section(title: str, sub: str = "", eyebrow: str = "", num: int | None = None, ic: str = "") -> None:
    lead = f"<b>{num:02d}</b>" if num else (icon(ic) if ic else "")
    lab = f"{lead} {eyebrow}" if eyebrow else ""
    ey = f"<div class='eyebrow'>{lab}</div>" if lab else ""
    sb = f"<div class='lede'>{sub}</div>" if sub else ""
    html(f"<div class='sec'>{ey}<div class='h2'>{title}</div>{sb}</div>")


def subhead(title: str, ic: str = "settings", note: str = "") -> None:
    """Smaller in-page heading with an icon, used instead of Markdown ### headings."""
    sm = f"<small>{note}</small>" if note else ""
    html(f"<div class='sub'>{icon(ic)}<span>{title}</span>{sm}</div>")


_DEFAULT_ICONS = ["gauge", "alert-triangle", "tools", "currency-rupee", "search", "file-text"]


def cards(items, cols: int = 3) -> None:
    """Feature cards. Each item is (tag, title, desc) or (tag, title, desc, icon_name)."""
    cells = ""
    for i, it in enumerate(items):
        tag, title, desc = it[:3]
        ic = it[3] if len(it) > 3 else _DEFAULT_ICONS[i % len(_DEFAULT_ICONS)]
        cells += (f"<div class='cell'><div class='cell-top'><div class='ibox'>{icon(ic)}</div>"
                  f"<div class='tag'>{tag}</div></div>"
                  f"<div class='ct'>{title}</div><div class='cp'>{desc}</div></div>")
    html(f"<div class='cap g{cols}'>{cells}</div>")


def metric_card(label: str, value: str, sub: str = "", ic: str = "") -> str:
    i = icon(ic) if ic else ""
    return f"<div class='mc'><div class='ml'><span>{label}</span>{i}</div><div class='mv'>{value}</div><div class='ms'>{sub}</div></div>"


def page_header(title: str, sub: str, eyebrow: str, sheet: int, ic: str, meta: list[tuple[str, str]] | None = None) -> None:
    """Blueprint-style header for inner pages: hazard edge, sheet number, spinning gear badge."""
    items = meta or []
    meta_html = f"<span>{icon('ruler-measure')}Sheet {sheet:02d} / {len(NAV_LINKS):02d}</span>" + "".join(
        f"<span>{icon(i)}{t}</span>" for i, t in items)
    html(f"""
    <div class='phead'><div class='phead-grid'>
    <div><div class='eyebrow'>{icon(ic)} {eyebrow}</div>
    <div class='h2'>{title}</div><div class='lede'>{sub}</div>
    <div class='meta'>{meta_html}</div></div>
    <div class='pgear' aria-hidden='true'><div class='g1 spin'>{icon('settings')}</div>
    <div class='g2 spin-r'>{icon('settings')}</div><div class='core'>{icon(ic)}</div></div>
    </div></div>
    """)


def _brand() -> str:
    return f"<a class='brand' href='/' target='_self'><span class='mark'>{icon('settings', 'ic spin')}</span><span>RUL<em>Predictor</em></span></a>"


def render_nav(active: str = "") -> None:
    key = (active or "").strip("/") or "home"
    links = "".join(
        f"<a href='{h}' target='_self' class='{'on' if k == key else ''}'>{icon(ic)}{t}</a>" for t, h, k, ic in NAV_LINKS
    )
    html(f"""
    <div class='nav'><div class='nav-in'>
    {_brand()}
    <nav class='links'>{links}</nav>
    <a class='nav-cta' href='/predictor' target='_self'>{icon('bolt')}Open predictor</a>
    <details class='mm'><summary aria-label='Menu'><i></i><i></i></summary><div class='mpanel'>{links}</div></details>
    </div></div>
    """)


def footer() -> None:
    names = "".join(f"<span class='fi'>{icon('tool')}{m['name']}</span>" for m in TEAM)
    pages = "".join(f"<a href='{h}' target='_self'>{icon(ic)}{t}</a>" for t, h, _, ic in NAV_LINKS)
    college = f" · {COLLEGE}" if COLLEGE else ""
    html(f"""
    <div class='bleed foot'><div class='foot-in'>
    <div class='foot-grid'>
    <div>{_brand()}
    <p>Remaining useful life estimates for mechanical components, with failure modes, maintenance plans and cost impact.</p></div>
    <div><div class='fh'>Pages</div>{pages}</div>
    <div><div class='fh'>Built by</div>{names}</div>
    </div>
    <div class='foot-bar'>{PROGRAMME} · {BATCH}{college}<br>
    Academic project. Estimates are indicative; verify against OEM data and plant history before operational decisions.<br>
    Icons: Tabler Icons (MIT).</div>
    </div></div>
    """)
