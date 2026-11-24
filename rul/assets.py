"""Loads images from public/images, shrinks them once and embeds them as data URIs.

Source PNGs can be several MB (engine.png is ~4 MB). Each is resized and re-encoded as JPEG in memory.
The picture's own background colour (sampled from its corner) is applied to the frame around it,
so illustrations on a cream or white background blend in instead of looking boxed.
"""
import base64
import io

import streamlit as st
from PIL import Image

from .config import ROOT

IMG_DIR = ROOT / "public" / "images"
FILES = {
    "hero": "mechanical_eng.png",
    "gear": "Gear.png",
    "hydraulic": "Hydraulic Cylinder.png",
    "engine": "engine.png",
}


@st.cache_data(show_spinner=False)
def _encode(path: str, mtime: float, max_side: int):
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert("RGB")
    im.thumbnail((max_side, max_side))
    r, g, b = im.getpixel((2, 2))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88, optimize=True)
    uri = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    return uri, f"#{r:02x}{g:02x}{b:02x}"


def _load(key: str, max_side: int):
    name = FILES.get(key)
    path = IMG_DIR / name if name else None
    if not path or not path.exists():
        return None, None
    try:
        return _encode(str(path), path.stat().st_mtime, max_side)
    except Exception:
        return None, None


def img_tag(key: str, alt: str, max_side: int = 900) -> str:
    uri, _ = _load(key, max_side)
    if not uri:
        return "<div class='noimg'>Image not found in public/images</div>"
    return f"<img src='{uri}' alt='{alt}'>"


def frame(key: str, alt: str, max_side: int = 1000) -> str:
    """Full-width framed picture (hero, About, Predictor)."""
    uri, bg = _load(key, max_side)
    if not uri:
        return "<div class='frame'><div class='noimg'>Image not found in public/images</div></div>"
    return f"<div class='frame' style='background:{bg}'><img src='{uri}' alt='{alt}'></div>"


def pic(key: str, alt: str, max_side: int = 800) -> str:
    """Fixed-height picture area for component cards."""
    uri, bg = _load(key, max_side)
    if not uri:
        return "<div class='pic'><div class='noimg'>Image not found</div></div>"
    return f"<div class='pic' style='background:{bg}'><img src='{uri}' alt='{alt}'></div>"


def key_for_component(name: str):
    """Map a component name (dataset type or knowledge-base name) to one of the supplied images."""
    n = str(name).lower()
    if "hydraulic" in n:
        return "hydraulic"
    if "gear" in n:
        return "gear"
    if "engine" in n:
        return "engine"
    return None
