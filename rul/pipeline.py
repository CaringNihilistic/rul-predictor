"""End-to-end assessment pipeline: resolve -> harness -> estimate -> retrieve -> explain -> report."""
from . import cost as costmod
from . import engine, llm, memory
from . import model as mdl
from . import report as reportmod
from .config import STD_FEATURES
from .harness import run_harness


def _explain(R: dict, ai):
    fb = llm.fallback_analysis(R)
    if not ai or not ai.get("enabled"):
        return fb, "Rule-based (AI turned off)", None
    if not ai.get("api_key"):
        return fb, "Rule-based (no API key)", "Add an API key in AI settings to get the AI assessment."
    try:
        out = llm.analyze(ai["provider"], ai["api_key"], ai["model"], R, fb)
        return out, f"AI: {ai['provider']} / {ai['model']}", None
    except Exception as e:  # auth, network, rate limit, wrong model name
        return fb, "Rule-based (AI call failed)", f"AI call failed: {e}"


def run_assessment(kb, res: dict, ctext: str, values: dict, features: list, context: dict,
                   cost_params: dict, tag: str = "", ai=None) -> dict:
    dm, dtype, matched = res["dm"], res["dtype"], res["kb"]
    route = "ml" if dm else "kb"
    kb_item = matched or kb.generic

    ref = dm.profile["by_type"].get(dtype, dm.profile["global"]) if dm else None
    h = run_harness(ctext, values, features, ref=ref, scope=dtype or "",
                    has_skill=dm.typed_metrics["has_skill"] if dm else True)
    if not h.ok:
        return {"ok": False, "harness": h}
    vals = h.inputs

    cross, an = None, None
    if route == "ml":
        A = engine.assess_ml(dm, dtype, vals, context, matched, h.confidence)
        estimator = lambda v: mdl.predict(dm, "type_specific", dtype, v)["rul"]  # noqa: E731
        an = mdl.analogues(dm, dtype, vals)
        if matched and all(f in vals for f in STD_FEATURES):
            cross = engine.kb_median(matched, {f: vals[f] for f in STD_FEATURES}, context)
        label = dtype
        match_desc = f"found in dataset '{dm.entry['name']}'" + (" and in the knowledge base" if matched else "")
    else:
        A = engine.assess_kb(kb_item, vals, context, generic=matched is None)
        estimator = lambda v: engine.kb_median(kb_item, v, context)  # noqa: E731
        if matched:
            label, match_desc = kb_item["name"], "found in the knowledge base, not in any dataset"
        else:
            label = f"{ctext.strip().title()} (generic profile)"
            match_desc = "NOT found in any dataset or the knowledge base; generic mechanical profile used"

    sens = engine.sensitivity(estimator, vals, features)
    failure_modes = engine.rank_failure_modes(kb_item, A["params"])
    plan = engine.plan_from_kb(kb_item, A["risk"])
    costs = costmod.cost_analysis((A["dist_values"], A["dist_probs"]), cost_params)

    trend, hist = None, []
    hours = vals.get("Operating_Hours")
    if tag.strip():
        hist = memory.history(tag)
        if hours is not None:
            trend = memory.trend(hist, hours, A["rul"])
        memory.log_assessment({"tag": tag.strip(), "component": label, "hours": hours, "rul": A["rul"],
                               "low": A["low"], "health": A["health"], "risk": A["risk"]})

    chunks = kb.retrieve(f"{ctext} {context.get('notes', '')} failure modes maintenance",
                         matched["id"] if matched else None, 4)

    R = {
        "ok": True, "route": route, "label": label, "match_desc": match_desc, "tag": tag.strip(),
        "harness": h, "assessment": A, "failure_modes": failure_modes, "plan": plan,
        "spares": kb_item["spares"], "costs": costs, "sensitivity": sens, "analogues": an,
        "cross_check": cross, "chunks": chunks, "trend": trend, "history": hist,
        "context": context, "kb_item": kb_item, "generic": matched is None,
    }
    R["analysis"], R["analysis_source"], R["ai_error"] = _explain(R, ai)
    try:
        R["pdf"], R["pdf_error"] = reportmod.build_pdf(R), None
    except Exception as e:
        R["pdf"], R["pdf_error"] = None, str(e)
    return R
