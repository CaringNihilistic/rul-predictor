import streamlit as st

from rul.state import get_models
from rul.icons import icon
from rul.ui import cards, html, page_header, section, subhead

page_header("How it works.", "The system is a retrieval-augmented pipeline, not a single prompt to an AI model.", "Methodology", 3, "route-2",
            [("math-function", "Weibull + random forest"), ("search", "TF-IDF retrieval"), ("cpu", "Groq / Claude")])
subhead("System diagram", "topology-star-3", "Data flow")

st.graphviz_chart("""
digraph G {
  rankdir=LR; bgcolor="transparent"; node [shape=box, style="rounded,filled", fillcolor="#fbfaf7", color="#8a1c1c", penwidth=1.4, fontname="Arial", fontsize=11, fontcolor="#1d1b19"];
  edge [color="#56606b", fontname="Arial", fontsize=10, fontcolor="#56606b"];
  input [label="User input\\n(component + readings)"];
  harness [label="Harness\\nvalidate and route"];
  resolve [label="Component resolver\\n(dataset / knowledge base)"];
  ml [label="ML model\\n(trained on CSV)"];
  wb [label="Weibull estimate\\n(reliability + condition)"];
  rag [label="Retrieval\\nKB excerpts + similar cases"];
  llm [label="LLM (Groq / Claude)\\ngrounded explanation"];
  out [label="Report\\nRUL, risk, plan, cost, PDF", fillcolor="#1c1a19", color="#e3a622", fontcolor="#e3a622"];
  input -> harness -> resolve;
  resolve -> ml [label=" in dataset"]; resolve -> wb [label=" other"];
  ml -> rag; wb -> rag; rag -> llm -> out;
}
""")

section("The five stages.", "", "Stages", num=1)
cards([
    ("STG-1", "Harness", "Rejects invalid values, matches the component name (typos and synonyms included) and warns when readings fall outside the data the model has seen. It also sets a confidence level.", "filter"),
    ("STG-2", "Estimation", "If the component exists in a registered dataset, a random-forest model gives the RUL. Otherwise an engineering estimate is used: a Weibull life model conditioned on hours already run, scaled by condition factors.", "math-function"),
    ("STG-3", "Retrieval", "The knowledge base (TF-IDF search over failure modes, maintenance and spares) and the most similar historical records are retrieved as evidence.", "search"),
    ("STG-4", "Grounded explanation", "Groq or Claude receives only validated numbers plus the retrieved evidence. It may not change the RUL, must cite excerpts and may ask clarifying questions.", "cpu"),
    ("STG-5", "Decision outputs", "Failure modes ranked by evidence, maintenance actions by urgency, planned versus breakdown cost, and a PDF report. Asset tags add memory so degradation speed can be tracked.", "report-analytics"),
], cols=3)

section("Key formulas.", "The maths behind the engineering estimate.", "Formulas", num=2)
subhead("Remaining life from a Weibull model", "math-function", "EQ-01")
st.markdown("For a component that has already survived *t* hours, with survival probability *q*:")
st.latex(r"RUL_q = \eta\left[\left(\tfrac{t}{\eta}\right)^{\beta} - \ln q\right]^{1/\beta} - t")
st.markdown("where η is the characteristic life and β the shape parameter. The median RUL uses q = 0.5, the pessimistic (P10) uses q = 0.9 and the optimistic (P90) uses q = 0.1. The result is multiplied by a condition factor built from vibration and temperature against warning and alarm limits, plus load, environment and maintenance quality.")
subhead("Health score", "heartbeat", "EQ-02")
st.markdown("Remaining life as a share of the typical life of a new part:")
st.latex(r"Health = 100 \cdot \frac{RUL}{L_{ref}}")
subhead("Expected extra cost of waiting", "currency-rupee", "EQ-03")
st.markdown("For a further H hours of operation:")
st.latex(r"E[\Delta C] = P(\text{fail within } H)\,(C_{breakdown} - C_{planned})")

section("Model quality on your datasets.", "5-fold cross-validation. R² near zero means the model is no better than predicting the average.", "Validation", num=3)
models, errors = get_models()
for e in errors:
    st.error(e)
rows = []
for dm in models:
    m = dm.typed_metrics
    rows.append({
        "Dataset": dm.entry["name"], "Rows": dm.profile["n_rows"], "Component types": ", ".join(dm.types),
        "R²": round(m["r2"], 3), "MAE (h)": round(m["mae"]), "Baseline MAE (h)": round(m["baseline_mae"]),
        "Usable signal": "Yes" if m["has_skill"] else "Weak",
    })
if rows:
    st.dataframe(rows, hide_index=True)
    if any(r["Usable signal"] == "Weak" for r in rows):
        st.warning("At least one dataset shows weak predictive signal. The app lowers its confidence for those predictions and shows the engineering estimate as a cross-check.")

section("Limitations.", "Read these before trusting a number.", "Caveats", num=4)
LIMITS = [
    "The knowledge-base life and limit values are <b>indicative</b>. They must be reviewed against OEM manuals and plant history.",
    "The context multipliers (load, environment, maintenance quality) are engineering judgement, not fitted from data.",
    "The 80% range reflects model or life scatter only, not every source of uncertainty.",
    "Estimates for components outside any dataset are rough guidance, not a substitute for inspection.",
]
html("".join(f"<div class='banner warn'>{icon('alert-triangle')}<div>{t}</div></div>" for t in LIMITS))
