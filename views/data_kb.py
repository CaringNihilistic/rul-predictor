from html import escape as esc

import pandas as pd
import streamlit as st

from rul.model import train
from rul.registry import add_dataset, load_registry, remove_dataset
from rul.state import get_kb, get_models, refresh
from rul.icons import component_icon, icon
from rul.ui import html, page_header, subhead

kb = get_kb()
models, errors = get_models()

page_header("Data and knowledge.", "Everything the predictor learns from. Add any run-to-failure CSV and it is used immediately.", "Data", 5, "database",
            [("table", f"{len(models)} dataset(s)"), ("books", f"{len(kb.known)} profiles"), ("upload", "CSV upload")])
for e in errors:
    st.error(e)

# ---------------- Registered datasets ----------------
subhead("Registered datasets", "database", f"{len(models)} loaded")
for dm in models:
    e, m = dm.entry, dm.typed_metrics
    with st.expander(f"{e['name']}  ·  {dm.profile['n_rows']:,} rows  ·  {len(dm.types)} component type(s)"):
        st.write(f"**Source:** {e.get('source') or '-'}  |  **Target:** `{dm.target}`  |  "
                 f"**Features:** {', '.join(dm.features)}")
        st.write(f"**Component types:** {', '.join(dm.types)}")
        st.write(f"**Cross-validation:** R² {m['r2']:.2f}, MAE {m['mae']:.0f} "
                 f"(baseline MAE {m['baseline_mae']:.0f}) — {'usable signal' if m['has_skill'] else 'weak signal'}")
        st.dataframe(dm.df.head(20), hide_index=True)
        if not e.get("builtin"):
            if st.button("Remove this dataset", key=f"rm_{e['id']}"):
                remove_dataset(e["id"])
                refresh()
                st.rerun()

# ---------------- Add dataset ----------------
subhead("Add a dataset", "upload", "CSV")
st.caption("Best format: one row per component snapshot with sensor columns and its remaining useful life. "
           "Public sources include Kaggle and the NASA prognostics repository.")
up = st.file_uploader("Upload a CSV file", type=["csv"])
if up:
    try:
        df = pd.read_csv(up)
    except Exception as ex:
        st.error(f"Could not read the file: {ex}")
        df = None
    if df is not None:
        st.dataframe(df.head(8), hide_index=True)
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        c1, c2 = st.columns(2)
        name = c1.text_input("Dataset name", value=up.name.rsplit(".", 1)[0])
        source = c2.text_input("Source (e.g. Kaggle link)")
        target = c1.selectbox("Target column (remaining useful life)", num_cols) if num_cols else None
        feats = c2.multiselect("Feature columns (sensors, hours, loads...)",
                               [c for c in num_cols if c != target], default=[c for c in num_cols if c != target][:6])
        mode = st.radio("Component type", ["Column in the file", "One type for the whole file"], horizontal=True)
        type_col, fixed = None, None
        if mode == "Column in the file":
            type_col = st.selectbox("Component type column", list(df.columns))
        else:
            fixed = st.text_input("Component type name", placeholder="e.g. Turbofan Engine, Bearing")
        id_opt = st.selectbox("ID column (optional)", ["(none)"] + list(df.columns))

        if st.button("Register and train", type="primary"):
            if not (name.strip() and target and feats):
                st.error("Give the dataset a name, a target column and at least one feature.")
            elif mode != "Column in the file" and not (fixed or "").strip():
                st.error("Enter the component type name.")
            else:
                entry = {"name": name.strip(), "target": target, "features": feats, "type_col": type_col,
                         "fixed_type": fixed.strip() if fixed else None,
                         "id_col": None if id_opt == "(none)" else id_opt, "source": source}
                saved = add_dataset(df, entry)
                try:
                    train(saved)
                except Exception as ex:
                    remove_dataset(saved["id"])
                    st.error(f"Dataset was rejected: {ex}")
                else:
                    refresh()
                    st.success("Dataset registered. The predictor now recognises its component types.")
                    st.rerun()

# ---------------- Knowledge base ----------------
subhead("Engineering knowledge base", "books", f"{len(kb.known)} profiles")
st.caption(kb.meta.get("disclaimer", ""))
pick = st.selectbox("Component profile", kb.names())
item = next(i for i in kb.known if i["name"] == pick)
html(f"<div class='kbhead'><div class='ibox'>{icon(component_icon(item['name']))}</div><div>"
     f"<div class='kn'>{esc(item['name'])}</div><div class='kc'>{esc(item['category'])}</div><p>{esc(item['description'])}</p></div></div>")
k1, k2 = st.columns(2)
k1.metric("Characteristic life (η)", f"{item['life']['eta']:,} h")
k2.metric("Weibull shape (β)", f"{item['life']['beta']}")
if item.get("limits"):
    st.dataframe(pd.DataFrame([{"Parameter": k, "Warning": v["warn"], "Alarm": v["alarm"], "Unit": v["unit"]}
                               for k, v in item["limits"].items()]), hide_index=True)
subhead("Failure modes", "alert-triangle")
st.dataframe(pd.DataFrame(item["failure_modes"])[["mode", "cause", "indicator"]], hide_index=True)
subhead("Maintenance tasks", "tools")
st.dataframe(pd.DataFrame(item["maintenance"]), hide_index=True)
subhead("Critical spares", "package")
st.markdown(", ".join(item["spares"]))
st.caption("To add or correct a component, edit `rul/kb/components.json` and restart the app.")
