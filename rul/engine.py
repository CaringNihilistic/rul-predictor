"""Core assessment logic: reliability (Weibull) estimate, ML estimate wrapper, risk, failure modes, plan."""
import math
from datetime import date, timedelta

import numpy as np
import pandas as pd

from . import model as mdl
from .config import FEATURE_UNITS

LIMIT_KEY = {"Vibration": "vibration", "Temperature": "temperature"}
RISK_ORDER = ["low", "medium", "high", "critical"]
RANK = {"n/a": 0, "normal": 0, "warning": 1, "alarm": 2}
HORIZONS = [100, 250, 500, 1000]

# Engineering-judgement multipliers on remaining life (documented on the Methodology page).
CONTEXT_OPTIONS = {
    "load": {"Light": 1.10, "Normal": 1.00, "Heavy": 0.80, "Severe / shock loads": 0.65},
    "environment": {"Clean / controlled": 1.00, "Dusty or humid": 0.90, "Corrosive or very hot": 0.80},
    "maintenance": {"Well maintained": 1.05, "Average": 1.00, "Poor / overdue": 0.85},
}


def context_factor(ctx: dict) -> float:
    f = 1.0
    for key, opts in CONTEXT_OPTIONS.items():
        f *= opts.get(ctx.get(key), 1.0)
    return f


# ---------- Weibull helpers ----------
def weibull_rem(hours: float, eta: float, beta: float, q) -> np.ndarray:
    """Remaining life at conditional survival probability q, given `hours` already survived."""
    q = np.asarray(q, dtype=float)
    return np.maximum(0.0, eta * ((hours / eta) ** beta - np.log(q)) ** (1.0 / beta) - hours)


def reference_life(eta: float, beta: float) -> float:
    """Median life of a new part."""
    return eta * math.log(2) ** (1.0 / beta)


def param_factor(v: float, warn: float, alarm: float) -> float:
    if v <= warn:
        return 1.0
    if v <= alarm:
        return 1.0 - 0.5 * (v - warn) / max(alarm - warn, 1e-9)
    return max(0.15, 0.5 - 0.35 * min(1.0, (v - alarm) / max(alarm, 1e-9)))


def status_of(v: float, lim: dict) -> str:
    if v >= lim["alarm"]:
        return "alarm"
    if v >= lim["warn"]:
        return "warning"
    return "normal"


def hours_status(hours: float, eta: float) -> str:
    r = hours / eta
    return "alarm" if r >= 1.0 else "warning" if r >= 0.6 else "normal"


# ---------- distribution helpers ----------
def q_at(values, probs, p: float) -> float:
    return float(np.interp(p, probs, values))


def prob_within(values, probs, h: float) -> float:
    return float(np.interp(h, values, probs, left=0.0, right=1.0))


def kb_distribution(item: dict, values: dict, context: dict) -> dict:
    eta, beta = item["life"]["eta"], item["life"]["beta"]
    hours = max(float(values.get("Operating_Hours", 0.0)), 0.0)
    lim = item.get("limits", {})
    factors = {}
    for f, key in LIMIT_KEY.items():
        if key in lim and f in values:
            factors[key] = param_factor(values[f], lim[key]["warn"], lim[key]["alarm"])
    rated = float(context.get("rated_pressure") or 0)
    if rated > 0 and "Pressure" in values:
        dev = abs(values["Pressure"] - rated) / rated
        factors["pressure"] = 1.0 if dev <= 0.10 else max(0.6, 1.0 - 0.4 * (dev - 0.10) / 0.30)
    factors["operating context"] = context_factor(context)
    factor = float(np.prod(list(factors.values())))
    qs = np.linspace(0.999, 0.001, 500)
    return {"values": weibull_rem(hours, eta, beta, qs) * factor, "probs": 1 - qs,
            "factor": factor, "factors": factors}


def kb_median(item: dict, values: dict, context: dict) -> float:
    d = kb_distribution(item, values, context)
    return q_at(d["values"], d["probs"], 0.5)


# ---------- risk ----------
def risk_from_fraction(rul: float, ref: float) -> str:
    fr = rul / ref if ref > 0 else 0.0
    return "critical" if fr <= 0.10 else "high" if fr <= 0.25 else "medium" if fr <= 0.50 else "low"


def risk_from_dataset(rul: float, r: dict) -> str:
    if rul <= r["q10"]:
        return "critical"
    if rul <= r["q25"]:
        return "high"
    if rul <= r["median"]:
        return "medium"
    return "low"


def escalate(risk: str, statuses: list) -> str:
    if "alarm" in statuses and RISK_ORDER.index(risk) < 2:
        return "high"
    return risk


# ---------- tables ----------
def param_rows(values: dict, kb_item, pcts, eta) -> list:
    rows = []
    lim = (kb_item or {}).get("limits", {})
    for f, v in values.items():
        unit = FEATURE_UNITS.get(f, "")
        key = LIMIT_KEY.get(f)
        status, limtxt = "n/a", "-"
        if key and key in lim:
            L = lim[key]
            status, limtxt = status_of(v, L), f"{L['warn']:g} / {L['alarm']:g} {L['unit']}"
        elif f == "Operating_Hours" and eta:
            status = hours_status(v, eta)
            limtxt = f"{eta * 0.6:,.0f} / {eta:,.0f} h (60% / 100% of typical life)"
        pct = pcts.get(f) if pcts else None
        rows.append({
            "Parameter": f.replace("_", " "),
            "Value": f"{v:g} {unit}".strip(),
            "Warn / Alarm": limtxt,
            "Status": status,
            "Fleet percentile": f"{pct:.0f}th" if pct is not None else "-",
        })
    return rows


def make_assessment(*, route, dist_values, dist_probs, rul, ref_life, risk, params, method_label,
                    confidence, notes, hours_per_day, factors=None) -> dict:
    low, high = q_at(dist_values, dist_probs, 0.10), q_at(dist_values, dist_probs, 0.90)
    health = float(np.clip(100 * rul / ref_life, 0, 100)) if ref_life > 0 else 0.0
    grid = np.linspace(0, max(high * 1.2, 100.0), 60)
    curve = pd.DataFrame({
        "Hours from now": grid,
        "Probability of failure (%)": 100 * np.interp(grid, dist_values, dist_probs, left=0.0, right=1.0),
    })
    latest = None
    if hours_per_day and hours_per_day > 0:
        try:
            latest = date.today() + timedelta(days=float(low) / float(hours_per_day))
        except OverflowError:
            latest = None
    return {
        "route": route, "method_label": method_label, "rul": float(rul), "low": low, "high": high,
        "health": health, "risk": risk, "confidence": confidence, "params": params, "notes": notes,
        "dist_values": np.asarray(dist_values), "dist_probs": np.asarray(dist_probs),
        "prob_table": {h: prob_within(dist_values, dist_probs, h) for h in HORIZONS},
        "curve": curve, "latest_date": latest, "ref_life": ref_life, "factors": factors or {},
    }


def assess_kb(item: dict, values: dict, context: dict, generic: bool = False) -> dict:
    d = kb_distribution(item, values, context)
    rul = q_at(d["values"], d["probs"], 0.5)
    eta, beta = item["life"]["eta"], item["life"]["beta"]
    ref = reference_life(eta, beta)
    params = param_rows(values, item, None, eta)
    risk = escalate(risk_from_fraction(rul, ref), [r["Status"] for r in params])
    hours = values.get("Operating_Hours", 0.0)
    notes = [
        f"Weibull life model (characteristic life {eta:,} h, shape {beta}) conditioned on {hours:,.0f} h already run.",
        f"Condition and context factor applied to remaining life: {d['factor']:.2f}.",
    ]
    if hours > 2 * eta:
        notes.append("Operating hours are far beyond the typical life for this component class.")
    return make_assessment(
        route="kb", dist_values=d["values"], dist_probs=d["probs"], rul=rul, ref_life=ref, risk=risk,
        params=params, method_label="Engineering estimate (Weibull reliability + condition factors)",
        confidence="low" if generic else "medium", notes=notes,
        hours_per_day=context.get("hours_per_day"), factors=d["factors"],
    )


def assess_ml(dm, ctype: str, values: dict, context: dict, kb_item, confidence: str) -> dict:
    pr = mdl.predict(dm, "type_specific", ctype, values)
    pcts = mdl.percentiles(dm, ctype, values)
    r = dm.profile["rul_by_type"].get(ctype, dm.profile["rul"])
    eta = kb_item["life"]["eta"] if kb_item else None
    params = param_rows(values, kb_item, pcts, eta)
    risk = escalate(risk_from_dataset(pr["rul"], r), [p["Status"] for p in params])
    m = pr["metrics"]
    notes = [
        f"Random-forest model trained on dataset '{dm.entry['name']}' ({dm.profile['n_rows']:,} rows).",
        f"5-fold cross-validation: R2 = {m['r2']:.2f}, MAE = {m['mae']:.0f} h "
        f"(predicting the average gives MAE {m['baseline_mae']:.0f} h).",
        "Range is the 10th to 90th percentile of cross-validated model errors added to the prediction.",
    ]
    return make_assessment(
        route="ml", dist_values=pr["values"], dist_probs=pr["probs"], rul=pr["rul"],
        ref_life=r["p95"], risk=risk, params=params, method_label="Data-trained ML model (random forest)",
        confidence=confidence, notes=notes, hours_per_day=context.get("hours_per_day"),
    )


def sensitivity(estimator, values: dict, features: list, pct: float = 0.2) -> pd.DataFrame:
    base = estimator(values)
    rows = []
    for f in features:
        lo = estimator({**values, f: values[f] * (1 - pct)})
        hi = estimator({**values, f: values[f] * (1 + pct)})
        rows.append({"Parameter": f.replace("_", " "), "RUL at -20%": round(lo - base, 1),
                     "RUL at +20%": round(hi - base, 1)})
    return pd.DataFrame(rows)


def rank_failure_modes(item: dict, params: list) -> list:
    st = {}
    for r in params:
        k = r["Parameter"].lower()
        st["hours" if k.startswith("operating") else k] = r["Status"]
    levels = ["low", "medium", "high"]
    out = []
    for m in item.get("failure_modes", []):
        sig = [(s, st.get(s, "n/a")) for s in m.get("signals", [])]
        worst = max((RANK.get(x, 0) for _, x in sig), default=0)
        hot = [f"{s} {x}" for s, x in sig if RANK.get(x, 0) > 0]
        out.append({
            "mode": m["mode"], "cause": m["cause"], "indicator": m["indicator"],
            "likelihood": levels[worst],
            "evidence": ", ".join(hot) if hot else "no abnormal reading on related parameters",
        })
    out.sort(key=lambda d: -levels.index(d["likelihood"]))
    return out


def plan_from_kb(item: dict, risk: str) -> list:
    base = {"critical": "immediate", "high": "within_1_week",
            "medium": "next_planned_shutdown", "low": "routine"}[risk]
    out = []
    for t in item.get("maintenance", []):
        if t.get("type", "inspect") == "inspect":
            u = base
        else:
            u = "next_planned_shutdown" if risk in ("critical", "high") else "routine"
        out.append({"action": t["task"], "urgency": u,
                    "reason": f"Standard interval about {t['interval_h']:,} h"})
    return out
