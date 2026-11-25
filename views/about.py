import streamlit as st

from rul.assets import frame
from rul.config import BATCH, COLLEGE, PROGRAMME, PROJECT_TITLE, TEAM
from rul.state import get_overview
from rul.icons import icon
from rul.ui import cards, html, page_header, section, subhead

ov = get_overview()

page_header("About the project.", PROJECT_TITLE, "About", 2, "school",
            [("users", f"{len(TEAM)} engineers"), ("calendar", BATCH), ("database", f"{ov['rows']:,} records")])

html(f"""
<div class='hero' style='padding:46px 0 10px'>
<div>
<div class='eyebrow'><b>00</b> Context</div>
<div class='h2'>Predictive maintenance, <span class='dim'>built by students.</span></div>
<div class='lede'>A machine-learning and reliability-engineering tool that turns sensor readings into a remaining-life estimate and a maintenance decision.</div>
<div class='fine'><span>{icon('manual-gearbox')}Gears</span><span>{icon('engine')}Engines</span><span>{icon('droplet')}Hydraulics</span><span>{icon('windmill')}Turbines</span><span>{icon('ripple')}Pumps</span></div>
</div>
<div class='fig'>
<div class='gear-a spin'>{icon('settings')}</div><div class='gear-b spin-r'>{icon('settings')}</div>
{frame('hero', 'Mechanical engineering components', 1000)}
<div class='fig-cap'><span><b>FIG. 02</b> · Components under study</span><span>Dept. of Mech. Engg.</span></div>
</div>
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
cards([
    ("STAGE-A", "Reactive", "Run until it breaks, then repair. Cheapest to plan, most expensive when it fails.", "hammer"),
    ("STAGE-B", "Preventive", "Service on a fixed calendar or hour count, whether the part needs it or not.", "calendar"),
    ("STAGE-C", "Predictive", "Act when the condition data says so. This project lives here.", "gauge"),
], cols=3)

section("Objectives.", "", "Goals", num=2)
cards([
    ("OBJ-01", "Predict RUL", "Estimate remaining life of mechanical components from sensor data using machine learning.", "gauge"),
    ("OBJ-02", "Cover any component", "Support pumps, turbines, compressors, impellers, bearings, gearboxes and more through a reusable knowledge base.", "manual-gearbox"),
    ("OBJ-03", "Support decisions", "Provide risk, failure modes, maintenance actions and cost impact, not just a number.", "list-check"),
], cols=3)

section("How we gathered the data.", "Three sources feed the system.", "Data", num=3)
cards([
    ("SRC-01", "Kaggle dataset", f"A public construction-machine component dataset downloaded from Kaggle: {ov['rows']:,} records, one row per component with sensor readings and its remaining useful life.", "database"),
    ("SRC-02", "Engineering knowledge base", "Failure modes, typical life, condition limits and service intervals compiled from standard reliability and maintenance practice. Values are indicative and meant to be reviewed against OEM manuals.", "books"),
    ("SRC-03", "Datasets you add", "Any run-to-failure CSV from public sources can be registered on the Data page and the model learns from it.", "upload"),
], cols=3)

subhead("Attributes in the Kaggle dataset", "table", "7 columns")
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
    f"<div class='person'><span class='pbg'>{icon('settings')}</span><div class='av'>{m['initials']}</div><div><div class='pn'>{m['name']}</div>"
    f"<div class='pr'>{icon('tool')}{PROGRAMME} student</div></div></div>"
    for m in TEAM
)
html(f"<div class='team'>{people}</div>")
html("<div class='lede' style='margin-top:18px'>Developed as a college project in the Department of Mechanical Engineering.</div>")
