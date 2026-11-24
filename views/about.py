import streamlit as st

from rul.assets import frame
from rul.config import BATCH, COLLEGE, PROGRAMME, PROJECT_TITLE, TEAM
from rul.state import get_overview
from rul.ui import cards, html, section

ov = get_overview()

html(f"""
<div class='hero' style='padding-bottom:30px'>
<div>
<div class='eyebrow'>About</div>
<div class='h2' style='font-size:clamp(32px,4vw,50px)'>About the project.</div>
<div class='lede'>{PROJECT_TITLE}</div>
</div>
{frame('hero', 'Mechanical engineering components', 1000)}
</div>
""")

section("Why remaining life matters.", "", "Introduction", num=1)
html("""
<div class='lede' style='max-width:780px;margin-top:0'>
Unplanned breakdowns of rotating and hydraulic equipment cost industry heavily in lost production, emergency repairs and
safety risk. Maintenance has moved from <b>reactive</b> (fix after failure) through <b>preventive</b> (fixed schedules)
to <b>predictive</b> (act when condition says so). The key quantity in predictive maintenance is the
<b>Remaining Useful Life (RUL)</b>: how many more operating hours a component can run before it needs intervention.
<br><br>
This project estimates RUL from condition-monitoring signals (vibration, temperature, pressure) and running hours.
It then converts the estimate into what a plant needs: a risk level, likely failure modes, a maintenance plan and the
cost of acting now versus waiting.
</div>
""")

section("Objectives.", "", "Goals", num=2)
cards([
    ("Objective 1", "Predict RUL", "Estimate remaining life of mechanical components from sensor data using machine learning."),
    ("Objective 2", "Cover any component", "Support pumps, turbines, compressors, impellers, bearings, gearboxes and more through a reusable knowledge base."),
    ("Objective 3", "Support decisions", "Provide risk, failure modes, maintenance actions and cost impact, not just a number."),
], cols=3)

section("How we gathered the data.", "Three sources feed the system.", "Data", num=3)
cards([
    ("Source 1", "Kaggle dataset", f"A public construction-machine component dataset downloaded from Kaggle: {ov['rows']:,} records, one row per component with sensor readings and its remaining useful life."),
    ("Source 2", "Engineering knowledge base", "Failure modes, typical life, condition limits and service intervals compiled from standard reliability and maintenance practice. Values are indicative and meant to be reviewed against OEM manuals."),
    ("Source 3", "Datasets you add", "Any run-to-failure CSV from public sources can be registered on the Data page and the model learns from it."),
], cols=3)

html("<div style='height:28px'></div>")
st.markdown("**Attributes in the Kaggle dataset**")
st.dataframe(
    {
        "Column": ["Component_ID", "Component_Type", "Vibration", "Temperature", "Pressure", "Operating_Hours", "Remaining_Useful_Life"],
        "Meaning": [
            "Unique identifier of the component record",
            "Category of the component (for example Gear, Engine, Hydraulic Cylinder)",
            "Measured vibration level",
            "Measured operating temperature",
            "Measured operating pressure",
            "Hours the component has already run",
            "Target: operating life left before intervention",
        ],
        "Role": ["ID", "Input", "Input", "Input", "Input", "Input", "Target"],
    },
    hide_index=True,
)

section("The team.", f"{PROGRAMME} students · {BATCH}" + (f" · {COLLEGE}" if COLLEGE else ""), "Builders", num=4)
people = "".join(
    f"<div class='person'><div class='av'>{m['initials']}</div><div><div class='pn'>{m['name']}</div>"
    f"<div class='pr'>{PROGRAMME} student</div></div></div>"
    for m in TEAM
)
html(f"<div class='team'>{people}</div>")
html("<div class='lede' style='margin-top:18px'>Developed as a college project in the Department of Mechanical Engineering.</div>")
