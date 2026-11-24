"""LLM layer (Groq free tier or Claude). Retrieval-augmented: the model only sees evidence we pass it."""
import json

from .config import CURRENCY, RUL_UNIT

SYSTEM_PROMPT = f"""You are a maintenance and reliability engineer assisting with Remaining Useful Life (RUL) assessment of industrial mechanical components.

Rules:
- The RUL number, range, risk level and condition statuses were already computed by validated models. NEVER output a different RUL number; explain and act on the given one.
- Ground every statement in the EVIDENCE provided (readings, knowledge-base excerpts, similar historical cases, asset trend). Cite knowledge-base excerpts by their id in square brackets, e.g. [centrifugal-pump:failure_modes].
- If something comes from your own general engineering knowledge instead of the evidence, end that sentence with "(general knowledge)".
- If the component is NOT in the knowledge base, say so plainly and keep recommendations conservative.
- If confidence is low or the ML model has little skill, say that clearly.
- Use the rule-based failure-mode hints as a starting point; re-order or add modes only when the evidence supports it.
- Do not invent part numbers, prices or standards you are unsure about.
- Ask at most 3 clarifying questions, only if the answers would change the assessment (duty cycle, last overhaul, lubricant, load, environment, units).
- RUL unit: {RUL_UNIT}. Currency: {CURRENCY}.

Respond with ONLY a JSON object with these keys:
  "summary": string (3-4 sentences for a maintenance manager),
  "failure_modes": list of {{"mode": string, "likelihood": "low|medium|high", "evidence": string}},
  "maintenance_actions": list of {{"action": string, "urgency": "immediate|within_1_week|next_planned_shutdown|routine", "reason": string}},
  "spares_to_stock": list of strings,
  "monitoring": list of strings (what to measure and how often),
  "clarifying_questions": list of strings (may be empty),
  "caveats": list of strings (may be empty)
"""


def build_prompt(R: dict) -> str:
    a, ctx = R["assessment"], R["context"]
    L = [
        f"COMPONENT: {R['label']} ({R['match_desc']})",
        f"OPERATING CONTEXT: load={ctx.get('load')}, environment={ctx.get('environment')}, "
        f"maintenance={ctx.get('maintenance')}, hours per day={ctx.get('hours_per_day')}",
        f"USER NOTES: {ctx.get('notes') or 'none'}",
        f"ESTIMATE [{a['method_label']}]: RUL {a['rul']:,.0f} h; P10-P90 {a['low']:,.0f}-{a['high']:,.0f} h; "
        f"health {a['health']:.0f}%; risk {a['risk']}; confidence {a['confidence']}",
        "CONDITION TABLE:",
    ]
    for p in a["params"]:
        L.append(f"  {p['Parameter']}: {p['Value']} | limits {p['Warn / Alarm']} | status {p['Status']} | fleet pct {p['Fleet percentile']}")
    if R.get("cross_check") is not None:
        L.append(f"CROSS-CHECK: engineering (Weibull) estimate gives RUL about {R['cross_check']:,.0f} h")
    L.append("RULE-BASED FAILURE-MODE HINTS:")
    for m in R["failure_modes"][:6]:
        L.append(f"  - {m['mode']}: {m['likelihood']} ({m['evidence']})")
    L.append("KNOWLEDGE-BASE EXCERPTS:")
    for c in R["chunks"]:
        tag = " (related component, not the same)" if c.get("related") else ""
        L.append(f"  [{c['id']}]{tag} {c['text'][:650]}")
    if R.get("analogues") is not None:
        L.append("SIMILAR HISTORICAL CASES FROM DATASET (nearest neighbours):")
        L.append(R["analogues"].round(2).to_string(index=False))
    if R.get("trend"):
        t = R["trend"]
        L.append(f"ASSET TREND: since {t['previous_hours']:,.0f} h, RUL fell by {t['rul_consumed']:,.0f} h over "
                 f"{t['delta_hours']:,.0f} operating hours (degradation index {t['degradation_index']:.2f}; "
                 f"{t['verdict']}).")
    L.append("HARNESS WARNINGS: " + ("; ".join(R["harness"].warnings) if R["harness"].warnings else "none"))
    return "\n".join(L)


def _call_groq(api_key: str, model: str, user: str) -> str:
    from groq import Groq

    resp = Groq(api_key=api_key).chat.completions.create(
        model=model, temperature=0.2, max_tokens=1600,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}],
    )
    return resp.choices[0].message.content


def _call_claude(api_key: str, model: str, user: str) -> str:
    import anthropic

    resp = anthropic.Anthropic(api_key=api_key).messages.create(
        model=model, max_tokens=1800, temperature=0.2, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


def fallback_analysis(R: dict) -> dict:
    a = R["assessment"]
    summary = (
        f"Estimated remaining life is about {a['rul']:,.0f} h (P10-P90: {a['low']:,.0f}-{a['high']:,.0f} h), "
        f"health score {a['health']:.0f}% and risk level {a['risk'].upper()}. "
        f"Schedule intervention before roughly {a['low']:,.0f} operating hours. "
        f"Confidence in this estimate is {a['confidence']}."
    )
    return {
        "summary": summary,
        "failure_modes": [{"mode": m["mode"], "likelihood": m["likelihood"], "evidence": m["evidence"]}
                          for m in R["failure_modes"]],
        "maintenance_actions": R["plan"],
        "spares_to_stock": R["spares"],
        "monitoring": [m["indicator"] for m in R["failure_modes"][:3]],
        "clarifying_questions": [],
        "caveats": ["Rule-based output from the knowledge base; the AI explanation was not used."],
    }


def _clean(data: dict, fb: dict) -> dict:
    out = {**fb, **{k: v for k, v in data.items() if k in fb and v}}
    fixed = []
    for m in out["failure_modes"]:
        fixed.append(m if isinstance(m, dict) else {"mode": str(m), "likelihood": "medium", "evidence": ""})
    out["failure_modes"] = fixed
    acts = []
    for a in out["maintenance_actions"]:
        acts.append(a if isinstance(a, dict) else {"action": str(a), "urgency": "routine", "reason": ""})
    out["maintenance_actions"] = acts
    for k in ("spares_to_stock", "monitoring", "clarifying_questions", "caveats"):
        out[k] = [str(x) for x in out[k]] if isinstance(out[k], list) else [str(out[k])]
    out["summary"] = str(out["summary"])
    return out


def analyze(provider: str, api_key: str, model: str, R: dict, fb: dict) -> dict:
    user = build_prompt(R)
    raw = _call_groq(api_key, model, user) if provider == "groq" else _call_claude(api_key, model, user)
    try:
        data = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
    except Exception:
        return {**fb, "summary": raw.strip()[:1500]}
    return _clean(data, fb)
