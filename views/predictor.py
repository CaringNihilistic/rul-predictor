from html import escape as esc

import pandas as pd
import streamlit as st

from rul.assets import frame, key_for_component
from rul.config import (
    CLAUDE_DEFAULT_MODEL, CURRENCY, FEATURE_UNITS, GROQ_DEFAULT_MODEL, STD_FEATURES,
)
from rul.cost import DEFAULT_COST
from rul.engine import CONTEXT_OPTIONS
from rul.knowledge import resolve_component
from rul.pipeline import run_assessment
from rul.state import get_kb, get_models, secret
from rul.ui import html, metric_card, pill, section

kb = get_kb()
models, train_errors = get_models()

DEFAULTS = {"Vibration": 2.0, "Temperature": 60.0, "Pressure": 10.0, "Operating_Hours": 5000.0}
STEPS = {"Vibration": 0.1, "Temperature": 1.0, "Pressure": 1.0, "Operating_Hours": 100.0}
STATUS_ICON = {"normal": "NORMAL", "warning": "WARNING", "alarm": "ALARM", "n/a": "-"}
URGENCY_ORDER = ["immediate", "within_1_week", "next_planned_shutdown", "routine"]
URGENCY_LABEL = {"immediate": "Immediate", "within_1_week": "Within 1 week",
                 "next_planned_shutdown": "Next planned shutdown", "routine": "Routine"}
URGENCY_KIND = {"immediate": "critical", "within_1_week": "high",
                "next_planned_shutdown": "medium", "routine": "low"}

section("Asset health assessment",
        "Choose a component type from the list, or pick Other and type any mechanical component. "
        "Components in the dataset use the trained model; everything else uses the engineering knowledge base.",
        "Predictor")
for e in train_errors:
    st.error(f"Dataset problem: {e}")

# ---------------- AI settings ----------------
with st.expander("AI assistant settings"):
    c1, c2 = st.columns([1, 1])
    use_ai = c1.toggle("Use AI for the explanation", value=True, key="ai_on")
    provider_label = c1.radio("Provider", ["Groq (free)", "Claude"], horizontal=True, key="ai_provider")
    provider = "groq" if provider_label.startswith("Groq") else "claude"
    key_name = "GROQ_API_KEY" if provider == "groq" else "ANTHROPIC_API_KEY"
    model_name = c2.text_input("Model", value=GROQ_DEFAULT_MODEL if provider == "groq" else CLAUDE_DEFAULT_MODEL,
                               key=f"ai_model_{provider}")
    api_key = c2.text_input(key_name, value=secret(key_name), type="password", key=f"ai_key_{provider}")
    st.caption("Without a key the app still works and shows a rule-based assessment from the knowledge base.")
ai_cfg = {"enabled": use_ai, "provider": provider, "api_key": api_key, "model": model_name}

# ---------------- Component ----------------
OTHER = "Other (type your own component)"


def build_options() -> dict:
    """Dataset types first (trained model), then knowledge-base components not already covered by a dataset type."""
    options, covered = {}, set()
    for dm in models:
        for t in dm.types:
            item = kb.resolve(t)[0]
            if item:
                covered.add(item["id"])
            options[f"{t}  ·  trained on data ({dm.entry['name']})"] = t
    for it in kb.known:
        if it["id"] not in covered:
            options[f"{it['name']}  ·  engineering estimate"] = it["name"]
    return options


opts = build_options()
sel_col, img_col = st.columns([1.5, 1], gap="large")
pick = sel_col.selectbox(
    "Component type", list(opts) + [OTHER], index=None, key="comp_pick",
    placeholder="Choose a component type",
    help="Choose Other to type any component, for example a bearing, valve or crane hook.",
)
if pick == OTHER:
    ctext = sel_col.text_input("Component name", key="comp_custom",
                               placeholder="e.g. screw conveyor, brake drum, forging press")
elif pick:
    ctext = opts[pick]
else:
    ctext = ""
tag = sel_col.text_input("Asset tag (optional)", key="asset_tag", placeholder="e.g. P-101A",
                         help="Remembers readings so the app can show how fast this asset is degrading.")

_img = key_for_component(ctext) if ctext.strip() else None
if _img:
    img_col.markdown(frame(_img, ctext, 700), unsafe_allow_html=True)

res = resolve_component(ctext, kb, models) if ctext.strip() else None
if res:
    if res["dm"]:
        extra = " Engineering knowledge is also available." if res["kb"] else ""
        st.success(f"Matched dataset **{res['dm'].entry['name']}** → **{res['dtype']}**. "
                   f"The data-trained model will be used.{extra}")
    elif res["kb"]:
        st.info(f"Matched knowledge base entry **{res['kb']['name']}**. An engineering (Weibull) estimate "
                "will be used. Add a dataset on the Data page to enable a data-trained model.")
    else:
        st.warning("Not found in any dataset or the knowledge base. A generic mechanical profile will be used; "
                   "the result is a rough guide and the AI will rely on general engineering knowledge.")

values, form_ok = {}, False
if res:
    route = "ml" if res["dm"] else "kb"
    features = res["dm"].features if route == "ml" else STD_FEATURES
    ref = None
    if route == "ml":
        ref = res["dm"].profile["by_type"].get(res["dtype"], res["dm"].profile["global"])
    with st.form("assess"):
        st.markdown("**Condition readings**")
        cols = st.columns(min(len(features), 4))
        for i, f in enumerate(features):
            unit = FEATURE_UNITS.get(f, "")
            label = f.replace("_", " ") + (f" ({unit})" if unit else "")
            if ref:
                s = ref[f]
                default, step = round(s["median"], 2), max((s["max"] - s["min"]) / 100, 0.01)
                hint = f"Observed in data: {s['min']:.2f} to {s['max']:.2f}"
            else:
                default, step = DEFAULTS.get(f, 0.0), STEPS.get(f, 1.0)
                hint = "Enter the current reading"
            values[f] = cols[i % len(cols)].number_input(
                label, value=float(default), step=float(step), help=hint, key=f"in_{route}_{f}_{ctext.strip().lower()}")

        with st.expander("Operating context (optional, sharpens the assessment)"):
            a, b, c = st.columns(3)
            load = a.selectbox("Load / duty", list(CONTEXT_OPTIONS["load"]), index=1)
            env = b.selectbox("Environment", list(CONTEXT_OPTIONS["environment"]), index=0)
            maint = c.selectbox("Maintenance quality", list(CONTEXT_OPTIONS["maintenance"]), index=1)
            d, e = st.columns(2)
            hpd = d.number_input("Operating hours per day", min_value=1.0, max_value=24.0, value=16.0)
            rated = e.number_input("Rated / normal pressure (0 = unknown)", min_value=0.0, value=0.0) \
                if route == "kb" else 0.0
            notes = st.text_area("Symptoms or notes for the AI (optional)", height=80,
                                 placeholder="e.g. new noise after last overhaul, leakage at gland, runs near maximum load...")

        with st.expander(f"Cost and downtime inputs ({CURRENCY}, illustrative defaults)"):
            x1, x2, x3 = st.columns(3)
            dt_cost = x1.number_input(f"Downtime cost per hour ({CURRENCY})", min_value=0.0, value=DEFAULT_COST["downtime_cost_hr"])
            rep_cost = x2.number_input(f"Planned repair cost ({CURRENCY})", min_value=0.0, value=DEFAULT_COST["repair_cost"])
            pl_dt = x3.number_input("Planned downtime (h)", min_value=0.0, value=DEFAULT_COST["planned_downtime_hr"])
            y1, y2 = st.columns(2)
            rep_mult = y1.number_input("Breakdown repair cost multiple", min_value=1.0, value=DEFAULT_COST["repair_mult"])
            dt_mult = y2.number_input("Breakdown downtime multiple", min_value=1.0, value=DEFAULT_COST["downtime_mult"])
        submitted = st.form_submit_button("Run assessment", type="primary")

    if submitted:
        context = {"load": load, "environment": env, "maintenance": maint, "hours_per_day": hpd,
                   "rated_pressure": rated, "notes": notes}
        cost_params = {"downtime_cost_hr": dt_cost, "repair_cost": rep_cost, "planned_downtime_hr": pl_dt,
                       "repair_mult": rep_mult, "downtime_mult": dt_mult}
        with st.spinner("Running assessment..."):
            st.session_state["result"] = run_assessment(
                kb, res, ctext, values, features, context, cost_params, tag=tag, ai=ai_cfg)
else:
    st.info("Start by choosing a component type above.")

# ---------------- Results ----------------
R = st.session_state.get("result")
if R:
    if not R["ok"]:
        for err in R["harness"].errors:
            st.error(err)
        st.stop()

    A, an = R["assessment"], R["analysis"]
    section(R["label"], R["match_desc"].capitalize() + ".", "Result")

    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(metric_card("Remaining useful life", f"{A['rul']:,.0f} h", "point estimate"), unsafe_allow_html=True)
    m2.markdown(metric_card("P10 – P90 range", f"{A['low']:,.0f}–{A['high']:,.0f}", "hours"), unsafe_allow_html=True)
    m3.markdown(
        f"<div class='mc'><div class='ml'>Health score</div><div class='mv'>{A['health']:.0f}%</div>"
        f"<div class='bar'><div style='width:{A['health']:.0f}%'></div></div></div>", unsafe_allow_html=True)
    m4.markdown(
        f"<div class='mc'><div class='ml'>Risk · Confidence</div><div style='margin-top:.55rem'>"
        f"{pill(A['risk'], A['risk'])} &nbsp; {pill(A['confidence'], {'high': 'low', 'medium': 'medium', 'low': 'high'}[A['confidence']])}"
        f"</div><div class='ms' style='margin-top:.4rem'>{esc(A['method_label'])}</div></div>", unsafe_allow_html=True)

    when = f"before about <b>{A['low']:,.0f} operating hours</b>"
    if A["latest_date"]:
        when += f" (around <b>{A['latest_date']:%d %b %Y}</b> at the stated utilisation)"
    kind = "banner warn" if A["risk"] in ("high", "critical") else "banner"
    html(f"<div class='{kind}'>Recommended: schedule intervention {when}. This is the pessimistic (P10) estimate.</div>")

    for w in R["harness"].warnings:
        st.warning(w)
    if R["generic"]:
        st.warning("This component is not in the knowledge base, so a generic profile was used.")

    t_sum, t_cond, t_fail, t_plan, t_cost, t_ev = st.tabs(
        ["Summary", "Condition", "Failure modes", "Maintenance plan", "Cost & downtime", "Evidence"])

    with t_sum:
        st.caption(R["analysis_source"])
        if R["ai_error"]:
            st.info(R["ai_error"])
        st.markdown(an["summary"])
        if an["clarifying_questions"]:
            st.markdown("**The assistant would like to know**")
            st.info("\n\n".join(f"• {q}" for q in an["clarifying_questions"]))
        if an["caveats"]:
            st.caption("Caveats: " + " · ".join(an["caveats"]))
        if R["pdf"]:
            st.download_button("Download PDF report", data=R["pdf"],
                               file_name=f"RUL_report_{(R['tag'] or R['label']).replace(' ', '_')}.pdf",
                               mime="application/pdf")
        else:
            st.warning(f"PDF could not be built: {R.get('pdf_error')}")

    with t_cond:
        df = pd.DataFrame(A["params"])
        df["Status"] = df["Status"].map(lambda s: STATUS_ICON.get(s, s))
        st.dataframe(df, hide_index=True)
        st.markdown("**Sensitivity:** change in RUL (hours) if one reading moves by ±20%")
        st.dataframe(R["sensitivity"], hide_index=True)
        if R["trend"]:
            t = R["trend"]
            st.info(f"Asset trend: since {t['previous_hours']:,.0f} h the RUL fell by {t['rul_consumed']:,.0f} h over "
                    f"{t['delta_hours']:,.0f} operating hours. Degradation index **{t['degradation_index']:.2f}** "
                    f"({t['verdict']}; 1.0 = on schedule).")
        if R["history"]:
            hist = pd.DataFrame(R["history"])[["ts", "hours", "rul", "low", "risk"]]
            st.markdown(f"**History for {R['tag']}**")
            st.dataframe(hist, hide_index=True)

    with t_fail:
        for m in an["failure_modes"]:
            lk = str(m.get("likelihood", "medium")).lower()
            html(f"<div class='fm'>{pill(lk, {'high': 'high', 'medium': 'medium', 'low': 'low'}.get(lk, 'na'))} "
                 f"<b>{esc(str(m.get('mode', '')))}</b><small>{esc(str(m.get('evidence', '')))}</small></div>")
        st.caption("Likelihood is ranked from how strongly the readings point to each mode, using the knowledge base.")

    with t_plan:
        acts = an["maintenance_actions"]
        for u in URGENCY_ORDER:
            group = [a for a in acts if a.get("urgency") == u]
            if group:
                st.markdown(pill(URGENCY_LABEL[u], URGENCY_KIND[u]), unsafe_allow_html=True)
                for a in group:
                    st.markdown(f"- {a.get('action', '')}" + (f" — *{a['reason']}*" if a.get("reason") else ""))
        if an["spares_to_stock"]:
            st.markdown("**Spares to stock**")
            st.markdown("\n".join(f"- {s}" for s in an["spares_to_stock"]))
        if an["monitoring"]:
            st.markdown("**What to monitor**")
            st.markdown("\n".join(f"- {s}" for s in an["monitoring"]))

    with t_cost:
        C = R["costs"]
        k1, k2, k3 = st.columns(3)
        k1.metric("Planned intervention", f"{CURRENCY} {C['planned']:,.0f}", f"{C['planned_downtime_hr']:.0f} h downtime", delta_color="off")
        k2.metric("Breakdown scenario", f"{CURRENCY} {C['breakdown']:,.0f}", f"{C['unplanned_downtime_hr']:.0f} h downtime", delta_color="off")
        k3.metric("Avoidable by acting early", f"{CURRENCY} {C['savings']:,.0f}")
        rows = pd.DataFrame([{
            "Defer maintenance by (h)": r["Defer by (h)"],
            "Failure probability": f"{r['Failure probability'] * 100:.0f}%",
            f"Expected extra cost ({CURRENCY})": f"{r['Expected extra cost']:,.0f}",
        } for r in C["rows"]])
        st.dataframe(rows, hide_index=True)
        st.markdown("**Probability of failure over time**")
        st.area_chart(A["curve"], x="Hours from now", y="Probability of failure (%)")

    with t_ev:
        st.markdown("**Method**")
        st.markdown("\n".join(f"- {n}" for n in A["notes"]))
        if R["cross_check"] is not None:
            st.info(f"Cross-check: the engineering (Weibull) estimate for this component class gives "
                    f"about **{R['cross_check']:,.0f} h**, versus **{A['rul']:,.0f} h** from the data-trained model. "
                    "A large gap means the dataset and typical industry life differ; ask which to trust.")
        if R["analogues"] is not None:
            st.markdown("**Most similar historical records in the dataset**")
            st.dataframe(R["analogues"], hide_index=True)
        st.markdown("**Knowledge-base excerpts retrieved for the AI**")
        for c in R["chunks"]:
            with st.expander(f"{c['id']}" + ("  (related component)" if c.get("related") else "")):
                st.write(c["text"])
        st.caption(kb.meta.get("disclaimer", ""))
