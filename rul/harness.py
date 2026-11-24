"""Input harness: validates every request before it reaches the models or the LLM."""
import math
from dataclasses import dataclass, field


@dataclass
class HarnessReport:
    ok: bool
    component_type: str
    inputs: dict
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    out_of_range: list = field(default_factory=list)
    confidence: str = "medium"
    scope: str = ""


def run_harness(component_type, values, features, ref=None, scope="", has_skill=True) -> HarnessReport:
    errors, warnings, ood, clean = [], [], [], {}
    ctype = str(component_type).strip()
    if not ctype:
        errors.append("Component type is required.")

    for f in features:
        try:
            v = float(values.get(f))
        except (TypeError, ValueError):
            errors.append(f"{f} must be a number.")
            continue
        if not math.isfinite(v):
            errors.append(f"{f} must be a finite number.")
            continue
        if f != "Temperature" and v < 0:
            errors.append(f"{f} cannot be negative.")
            continue
        clean[f] = v

    severity = 0  # 0 typical, 1 near the edge of the data, 2 outside the observed data
    if ref:
        for f, v in clean.items():
            s = ref.get(f)
            if not s:
                continue
            if v < s["min"] or v > s["max"]:
                severity = 2
                ood.append(f)
                warnings.append(
                    f"{f} = {v:g} is outside the range seen in the dataset for {scope or 'this data'} "
                    f"({s['min']:g} to {s['max']:g}). The model is extrapolating."
                )
            elif v < s["p1"] or v > s["p99"]:
                severity = max(severity, 1)
                warnings.append(f"{f} = {v:g} is at the extreme edge of the observed data.")

    confidence = {0: "high", 1: "medium", 2: "low"}[severity]
    if ref is not None and not has_skill:
        confidence = "low"
        warnings.append(
            "Cross-validation shows this dataset gives the model very little predictive signal, "
            "so the ML estimate is only a weak guide."
        )
    return HarnessReport(not errors, ctype, clean, errors, warnings, ood, confidence, scope)
