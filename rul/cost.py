"""Planned-vs-breakdown cost and downtime analysis."""
import numpy as np

HORIZONS = [100, 250, 500, 1000]

DEFAULT_COST = {
    "downtime_cost_hr": 20000.0,   # production loss per hour of downtime
    "repair_cost": 50000.0,        # planned repair cost (parts + labour)
    "planned_downtime_hr": 8.0,    # planned outage duration
    "repair_mult": 2.5,            # breakdown repair costs this many times more
    "downtime_mult": 3.0,          # breakdown outage lasts this many times longer
}


def cost_analysis(dist, p: dict) -> dict:
    values, probs = dist
    planned = p["repair_cost"] + p["planned_downtime_hr"] * p["downtime_cost_hr"]
    unplanned_dt = p["planned_downtime_hr"] * p["downtime_mult"]
    breakdown = p["repair_cost"] * p["repair_mult"] + unplanned_dt * p["downtime_cost_hr"]
    gap = breakdown - planned
    rows = []
    for h in HORIZONS:
        prob = float(np.interp(h, values, probs, left=0.0, right=1.0))
        rows.append({"Defer by (h)": h, "Failure probability": prob, "Expected extra cost": prob * gap})
    return {
        "planned": planned, "breakdown": breakdown, "savings": gap,
        "planned_downtime_hr": p["planned_downtime_hr"], "unplanned_downtime_hr": unplanned_dt,
        "rows": rows, "inputs": p,
    }
