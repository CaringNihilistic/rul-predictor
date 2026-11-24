"""One-click PDF asset health report (fpdf2, core fonts => latin-1 only)."""
from datetime import datetime

from fpdf import FPDF

from .config import BATCH, COLLEGE, CURRENCY, PROGRAMME, PROJECT_NAME, TEAM

URGENCY = {"immediate": "IMMEDIATE", "within_1_week": "WITHIN 1 WEEK",
           "next_planned_shutdown": "NEXT PLANNED SHUTDOWN", "routine": "ROUTINE"}


def _s(t) -> str:
    t = (str(t).replace("\u2013", "-").replace("\u2014", "-").replace("\u2022", "-")
         .replace("\u2264", "<=").replace("\u2265", ">=").replace("\u03b7", "eta")
         .replace("\u03b2", "beta").replace("\u00b2", "2").replace("\u2019", "'"))
    return t.encode("latin-1", "replace").decode("latin-1")


class _PDF(FPDF):
    def header(self):
        self.set_fill_color(125, 29, 29)
        self.rect(0, 0, 210, 16, "F")
        self.set_xy(10, 4)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, _s(f"{PROJECT_NAME} - Asset Health Report"), new_x="LMARGIN", new_y="NEXT")
        self.set_y(22)
        self.set_text_color(58, 54, 49)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(143, 136, 127)
        team = ", ".join(m["name"] for m in TEAM)
        line = f"{PROGRAMME} {BATCH}" + (f" - {COLLEGE}" if COLLEGE else "") + f" | {team} | Page {self.page_no()}"
        self.cell(0, 6, _s(line), align="C")


def _h2(pdf, text):
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(125, 29, 29)
    pdf.cell(0, 7, _s(text), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(58, 54, 49)
    pdf.set_font("Helvetica", "", 9.5)


def _p(pdf, text, bold=False):
    pdf.set_font("Helvetica", "B" if bold else "", 9.5)
    pdf.multi_cell(0, 5, _s(text), new_x="LMARGIN", new_y="NEXT")


def _bullets(pdf, items):
    pdf.set_font("Helvetica", "", 9.5)
    for it in items:
        pdf.multi_cell(0, 5, _s("- " + str(it)), new_x="LMARGIN", new_y="NEXT")


def build_pdf(R: dict) -> bytes:
    a, an, c = R["assessment"], R["analysis"], R["costs"]
    pdf = _PDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_font("Helvetica", "", 9.5)

    _p(pdf, f"Component: {R['label']}", bold=True)
    _p(pdf, f"Asset tag: {R['tag'] or '-'}    Date: {datetime.now():%d %b %Y %H:%M}")
    _p(pdf, f"Method: {a['method_label']}")

    _h2(pdf, "Key results")
    _p(pdf, f"Predicted remaining useful life: {a['rul']:,.0f} h   (P10-P90: {a['low']:,.0f} - {a['high']:,.0f} h)")
    _p(pdf, f"Health score: {a['health']:.0f}%    Risk: {a['risk'].upper()}    Confidence: {a['confidence'].upper()}")
    when = f"before about {a['low']:,.0f} operating hours" + (
        f" (around {a['latest_date']:%d %b %Y} at the stated utilisation)" if a["latest_date"] else "")
    _p(pdf, f"Recommended: schedule intervention {when}.")

    _h2(pdf, "Summary")
    _p(pdf, an["summary"])

    _h2(pdf, "Condition assessment")
    widths = [38, 32, 62, 22, 36]
    heads = ["Parameter", "Value", "Warn / Alarm", "Status", "Fleet percentile"]
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_fill_color(243, 240, 236)
    for w, h in zip(widths, heads):
        pdf.cell(w, 6, _s(h), border=1, fill=True)
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 8.5)
    for r in a["params"]:
        for w, k in zip(widths, heads):
            pdf.cell(w, 6, _s(str(r[k])[:42]), border=1)
        pdf.ln(6)

    _h2(pdf, "Likely failure modes")
    for m in an["failure_modes"][:6]:
        _p(pdf, f"{m.get('mode', '')} [{str(m.get('likelihood', '')).upper()}] - {m.get('evidence', '')}")

    _h2(pdf, "Maintenance plan")
    for m in an["maintenance_actions"]:
        _p(pdf, f"[{URGENCY.get(m.get('urgency'), str(m.get('urgency', '')).upper())}] {m.get('action', '')}"
                + (f" - {m.get('reason')}" if m.get("reason") else ""))
    if an["spares_to_stock"]:
        _p(pdf, "Spares to stock:", bold=True)
        _bullets(pdf, an["spares_to_stock"])
    if an["monitoring"]:
        _p(pdf, "Monitoring:", bold=True)
        _bullets(pdf, an["monitoring"])

    _h2(pdf, f"Cost and downtime ({CURRENCY}, illustrative inputs)")
    _p(pdf, f"Planned intervention: {c['planned']:,.0f} ({c['planned_downtime_hr']:.0f} h downtime)")
    _p(pdf, f"Breakdown scenario: {c['breakdown']:,.0f} ({c['unplanned_downtime_hr']:.0f} h downtime)")
    _p(pdf, f"Avoidable cost by acting before failure: {c['savings']:,.0f}", bold=True)
    for r in c["rows"]:
        _p(pdf, f"Defer {r['Defer by (h)']} h: failure probability {r['Failure probability'] * 100:.0f}%, "
                f"expected extra cost {r['Expected extra cost']:,.0f}")

    if an["clarifying_questions"]:
        _h2(pdf, "Open questions")
        _bullets(pdf, an["clarifying_questions"])
    _h2(pdf, "Caveats")
    _bullets(pdf, list(an["caveats"]) + a["notes"] + R["harness"].warnings +
             ["Academic project output. Verify against OEM data and plant history before operational use."])
    return bytes(pdf.output())
