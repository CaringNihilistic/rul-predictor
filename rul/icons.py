"""Inline SVG icons from Tabler Icons (MIT, https://tabler.io/icons), stored in public/icons.

Icons are read once, flattened onto one line (Markdown would otherwise break multi-line SVG)
and inherit `currentColor`, so CSS controls their colour and size.
"""
import re
from functools import lru_cache

from .config import ROOT

ICON_DIR = ROOT / "public" / "icons"


@lru_cache(maxsize=None)
def _svg(name: str) -> str:
    path = ICON_DIR / f"{name}.svg"
    if not path.exists():
        return ""
    s = path.read_text(encoding="utf-8")
    s = re.sub(r'\s(width|height|class)="[^"]*"', "", s)
    s = re.sub(r"\s+", " ", s).replace("> <", "><").strip()
    return s


def icon(name: str, cls: str = "ic") -> str:
    """Return an <i> wrapper holding the SVG. Unknown names render as an empty span, never an error."""
    return f"<i class='{cls}' aria-hidden='true'>{_svg(name)}</i>"


# Icon picked for each component, by keyword in its name.
_COMPONENT_ICONS = [
    ("hydraulic", "droplet"), ("cylinder", "droplet"), ("gear", "manual-gearbox"), ("engine", "engine"),
    ("pump", "ripple"), ("turbine", "windmill"), ("compressor", "wind"), ("fan", "propeller"),
    ("impeller", "propeller"), ("bearing", "nut"), ("motor", "circuit-motor"), ("valve", "adjustments-alt"),
    ("shaft", "ruler-2"), ("crane", "crane"), ("heat", "temperature"), ("conveyor", "forklift"), ("boiler", "barrel"),
]


def component_icon(name: str) -> str:
    n = str(name).lower()
    for key, ic in _COMPONENT_ICONS:
        if key in n:
            return ic
    return "settings"
