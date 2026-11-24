"""Quick check of the whole pipeline without Streamlit:  python smoke_test.py"""
from rul.config import KB_PATH
from rul.cost import DEFAULT_COST
from rul.knowledge import KnowledgeBase, resolve_component
from rul.model import train
from rul.pipeline import run_assessment
from rul.registry import load_registry

kb = KnowledgeBase(KB_PATH)
print("KB components:", len(kb.known))
for t in ["centrifugal pump", "gas turbine", "impeler", "Gear", "boiler feed pump", "quantum flux widget"]:
    item, score, how = kb.resolve(t)
    print(f"  {t!r:28} -> {item['name'] if item else None} ({how}, {score:.2f})")

models = [train(e) for e in load_registry()]
for dm in models:
    m = dm.typed_metrics
    print(f"Dataset {dm.entry['name']}: {dm.profile['n_rows']} rows, types={dm.types}, "
          f"R2={m['r2']:.3f}, MAE={m['mae']:.0f}, baseline MAE={m['baseline_mae']:.0f}")

STD = {"Vibration": 3.2, "Temperature": 85.0, "Pressure": 12.0, "Operating_Hours": 30000.0}
ctx = {"load": "Heavy", "environment": "Dusty or humid", "maintenance": "Average",
       "hours_per_day": 16.0, "rated_pressure": 10.0, "notes": "noise after last overhaul"}

for text, vals in [
    ("centrifugal pump", STD),
    ("Gear", {"Vibration": 3.0, "Temperature": 80.0, "Pressure": 200.0, "Operating_Hours": 1500.0}),
    ("quantum flux widget", STD),
]:
    res = resolve_component(text, kb, models)
    feats = res["dm"].features if res["dm"] else list(STD)
    R = run_assessment(kb, res, text, vals, feats, ctx, DEFAULT_COST, tag="", ai=None)
    if not R["ok"]:
        print(text, "-> harness errors:", R["harness"].errors)
        continue
    A = R["assessment"]
    print(f"\n{R['label']} [{R['route']}] RUL={A['rul']:.0f} h  P10-P90={A['low']:.0f}-{A['high']:.0f}  "
          f"health={A['health']:.0f}%  risk={A['risk']}  confidence={A['confidence']}")
    print("  top failure mode:", R["failure_modes"][0]["mode"], "-", R["failure_modes"][0]["likelihood"])
    print("  plan items:", len(R["plan"]), "| cost saving:", f"{R['costs']['savings']:,.0f}")
    print("  PDF:", f"{len(R['pdf']):,} bytes" if R["pdf"] else f"FAILED: {R['pdf_error']}")
    if R["pdf"]:
        open(f"smoke_report_{R['route']}.pdf", "wb").write(R["pdf"])
print("\nOK")
