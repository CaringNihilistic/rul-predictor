"""Asset memory: remembers past assessments per asset tag so degradation speed can be tracked."""
import json
from datetime import datetime

from .config import HISTORY_PATH


def log_assessment(rec: dict) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), **rec}
    with HISTORY_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")


def history(tag: str) -> list:
    if not HISTORY_PATH.exists() or not tag.strip():
        return []
    out = []
    for line in HISTORY_PATH.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(r.get("tag", "")).strip().lower() == tag.strip().lower():
            out.append(r)
    return out


def trend(records: list, hours: float, rul: float):
    """Degradation index = RUL consumed per operating hour since the previous reading (1.0 = on schedule)."""
    prev = [r for r in records if r.get("hours") is not None and r["hours"] < hours]
    if not prev:
        return None
    p = prev[-1]
    dh = hours - p["hours"]
    consumed = p["rul"] - rul
    idx = consumed / dh
    verdict = ("degrading faster than normal wear" if idx > 1.3
               else "degrading slower than expected" if idx < 0.7 else "wearing roughly as expected")
    return {"previous_rul": p["rul"], "previous_hours": p["hours"], "delta_hours": dh,
            "rul_consumed": consumed, "degradation_index": idx, "verdict": verdict}
