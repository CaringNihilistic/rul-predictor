from rul.assets import frame, pic
from rul.config import BATCH, COLLEGE, PROGRAMME, TEAM
from rul.state import get_kb, get_overview
from rul.ui import cards, html, section

ov = get_overview()
kb = get_kb()
counts = ov.get("counts", {})

# ---------------- Hero ----------------
html(f"""
<div class='hero'>
<div>
<div class='tags'>
<span class='tagp'><i class='dot'></i>Academic project</span>
<span class='tagp'>{PROGRAMME} · {BATCH}</span>
</div>
<div class='hero-title' role='heading' aria-level='1'><span>Know the life left</span><span class='acc'>before the part fails.</span></div>
<div class='hero-sub'>Estimate the <strong>remaining useful life</strong> of pumps, turbines, compressors, impellers, gearboxes and more from vibration, temperature, pressure and running hours. Every result comes with <strong>failure modes, a maintenance plan and the cost of waiting</strong>.</div>
<div class='actions'>
<a class='btn solid' href='/predictor' target='_self'>Open the predictor</a>
<a class='btn line' href='/methodology' target='_self'>How it works</a>
</div>
<div class='fine'>Works without an API key<span>|</span>Add your own CSV data<span>|</span>PDF report for every asset</div>
</div>
{frame('hero', 'Mechanical engineering components', 1100)}
</div>
""")

# ---------------- Stats ----------------
html(f"""
<div class='stats'>
<div class='stat'><div class='n'>{ov['rows']:,}</div><div class='l'>Training records</div></div>
<div class='stat'><div class='n'>{ov['types']}</div><div class='l'>Component types in the dataset</div></div>
<div class='stat'><div class='n'>{len(kb.known)}</div><div class='l'>Engineering knowledge profiles</div></div>
<div class='stat'><div class='n'>2</div><div class='l'>AI providers: Groq and Claude</div></div>
</div>
""")

# ---------------- Components in the dataset ----------------
section("Components in the dataset.",
        "These three component types come from the Kaggle data and use the trained model directly. Everything else is handled by the knowledge base.",
        "Dataset", num=1)

COMP = [
    ("gear", "Gear", "Power transmission", "Transmits torque and speed between shafts. Wear, pitting and lubrication breakdown set its life."),
    ("engine", "Engine", "Prime mover", "Converts fuel energy to shaft power. Rings, liners, injectors and cooling decide when it needs overhaul."),
    ("hydraulic", "Hydraulic Cylinder", "Fluid power", "Linear actuator driven by oil pressure. Seals, rod surface and oil cleanliness dominate its life."),
]
cards_html = ""
for key, name, cat, desc in COMP:
    n = counts.get(name)
    note = f"<b>{n:,}</b> records in the dataset" if n else "Not found in the loaded dataset"
    cards_html += (
        f"<div class='ccard'>{pic(key, name, 800)}"
        f"<div class='cb'><div class='ctag'>{cat}</div><div class='ct'>{name}</div>"
        f"<div class='cp'>{desc}</div><div class='cn'>{note}</div></div></div>"
    )
html(f"<div class='cgrid'>{cards_html}</div>")

# ---------------- Capabilities ----------------
section("One number is not a decision. <span class='dim'>So every report carries the rest.</span>",
        "Plant teams act on risk, causes, work orders and money. Each assessment returns all four.",
        "What you get", num=2)
cards([
    ("Estimate", "RUL with an honest range", "Point estimate plus a P10 to P90 range, a health score, a risk level and a confidence level that drops when the data is weak."),
    ("Diagnose", "Failure modes and causes", "Likely failure modes ranked by how strongly your readings point to each one, with the symptoms to watch."),
    ("Plan", "Maintenance plan", "Actions grouped by urgency, inspection intervals, spares to stock and what to monitor next."),
    ("Cost", "Cost and downtime", "Planned versus breakdown cost and the expected extra cost of deferring maintenance, using your own rates."),
    ("Trace", "Evidence, not guesses", "The AI cites knowledge-base excerpts and similar historical records. It cannot change the model's number."),
    ("Report", "PDF and asset memory", "One-click asset health report. Tag an asset and the app tracks how fast it is degrading between readings."),
], cols=3)

# ---------------- Pipeline (soft band) ----------------
html("""
<div class='bleed band'><div class='band-in'>
<div class='eyebrow'><b>03</b> &nbsp;Pipeline</div>
<div class='h2'>From readings to a maintenance decision <span class='dim'>in four steps.</span></div>
<div class='band-grid'>
<div>
<div class='step'><div class='sn'>1</div><div><div class='st2'>Validate the input</div><div class='sd'>The harness rejects bad values, matches the component name and flags readings outside the range it has seen.</div></div></div>
<div class='step'><div class='sn'>2</div><div><div class='st2'>Estimate remaining life</div><div class='sd'>A random-forest model where your dataset covers the component. A Weibull reliability model with condition factors everywhere else.</div></div></div>
<div class='step'><div class='sn'>3</div><div><div class='st2'>Retrieve the evidence</div><div class='sd'>Knowledge-base excerpts and the most similar historical records are pulled in as context.</div></div></div>
<div class='step'><div class='sn'>4</div><div><div class='st2'>Explain and report</div><div class='sd'>Groq or Claude turns the evidence into a plan. Failure modes, cost and a PDF come out the other end.</div></div></div>
</div>
<div class='sample'>
<div class='s-head'><span><b>Sample assessment</b> · Centrifugal pump</span><span>Illustrative values</span></div>
<div class='s-top'>
<div><div class='s-k'>Remaining life</div><div class='s-v'>8,900 <small>h</small></div></div>
<div><div class='s-k'>Plan before</div><div class='s-v'>5,300 <small>h (P10)</small></div></div>
</div>
<div class='s-row'><b>Vibration</b><span>3.2 mm/s</span><span class='badge warn'>Warning</span></div>
<div class='s-row'><b>Temperature</b><span>71 °C</span><span class='badge ok'>Normal</span></div>
<div class='s-row'><b>Operating hours</b><span>30,000 h</span><span class='badge warn'>Warning</span></div>
<div class='s-row'><b>Risk level</b><span>Health 41%</span><span class='badge warn'>Medium</span></div>
<div class='s-foot'>Top failure mode: bearing wear or lubrication failure</div>
</div>
</div>
</div></div>
""")

# ---------------- Compare ----------------
section("Alarms tell you it is bad. <span class='dim'>This tells you how long you have.</span>",
        "How the approach differs from the usual ways plants decide when to maintain.", "Comparison", num=4)
html("""
<div class='cmpwrap'><table class='cmp'>
<thead><tr><th>Approach</th><th>Uses condition data</th><th>Estimates remaining life</th><th>Any component type</th><th>Cost of waiting</th></tr></thead>
<tbody>
<tr><td>Fixed-interval maintenance</td><td>No</td><td>No</td><td>Yes</td><td>No</td></tr>
<tr><td>Threshold alarms</td><td>Yes</td><td>No</td><td>Yes</td><td>No</td></tr>
<tr class='me'><td>RUL Predictor</td><td><b>Yes</b></td><td><b>Yes, with a range</b></td><td><b>Yes, via knowledge base</b></td><td><b>Yes</b></td></tr>
</tbody></table></div>
""")

# ---------------- Coverage ----------------
section("Not limited to one dataset.",
        "Pick any of these in the predictor, or choose Other and type your own. Unknown components use a generic mechanical profile and are clearly labelled.",
        "Coverage", num=5)
chips = "".join(f"<span class='pchip'>{n}</span>" for n in kb.names())
html(f"<div class='chips'>{chips}<span class='pchip alt'>or anything else you type</span></div>")

# ---------------- Team ----------------
section("Built by three mechanical engineering students.",
        f"{PROGRAMME} · {BATCH}" + (f" · {COLLEGE}" if COLLEGE else "") + ". A college project.", "Team", num=6)
people = "".join(
    f"<div class='person'><div class='av'>{m['initials']}</div><div><div class='pn'>{m['name']}</div>"
    f"<div class='pr'>{PROGRAMME} student</div></div></div>"
    for m in TEAM
)
html(f"<div class='team'>{people}</div>")

# ---------------- FAQ ----------------
section("Common questions.", "", "FAQ", num=7)
html("""
<div class='faq'>
<details><summary>Does it work for components that are not in the dataset?</summary>
<div class='ans'>Yes. Known components such as pumps, turbines, compressors, impellers, bearings and gearboxes use an engineering estimate from the knowledge base. Anything else uses a generic mechanical profile, and the result is labelled low confidence. Adding a run-to-failure CSV for a component upgrades it to a data-trained model.</div></details>
<details><summary>Where does the data come from?</summary>
<div class='ans'>Two places: a public construction-machine dataset downloaded from Kaggle, and a starter knowledge base compiled from standard reliability and maintenance practice. Any extra CSV can be registered on the Data page.</div></details>
<details><summary>How accurate is it?</summary>
<div class='ans'>The Methodology page shows cross-validated scores for every dataset. If the model barely beats predicting the average, the app says so and lowers its confidence instead of hiding it. Knowledge-base values are indicative and need review against OEM manuals.</div></details>
<details><summary>Does my data leave my machine?</summary>
<div class='ans'>Readings and datasets stay in the app. If you turn on the AI explanation, the validated numbers and retrieved excerpts are sent to the provider you pick, Groq or Claude. Turn it off and everything stays local.</div></details>
<details><summary>Can a plant use this for real decisions?</summary>
<div class='ans'>Treat it as decision support from an academic project. Verify results against OEM data, inspection findings and plant history before acting on them.</div></details>
</div>
""")

# ---------------- Final CTA ----------------
html("""
<div class='final'>
<div class='eyebrow'>Get started</div>
<div class='h2'>Stop guessing. <span class='dim'>Start planning.</span></div>
<p>Select a component, enter its readings and get the full assessment in seconds.</p>
<div class='actions'>
<a class='btn solid' href='/predictor' target='_self'>Open the predictor</a>
<a class='btn line' href='/about' target='_self'>About the project</a>
</div>
</div>
""")
