from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from .config import MIN_SKILL_R2
from .data import build_profile, load_dataset

TYPE_COL = "_type"


def _make_pipeline(with_type: bool) -> Pipeline:
    rf = RandomForestRegressor(n_estimators=200, min_samples_leaf=5, random_state=42, n_jobs=-1)
    if with_type:
        pre = ColumnTransformer(
            [("type", OneHotEncoder(handle_unknown="ignore", sparse_output=False), [TYPE_COL])],
            remainder="passthrough",
        )
    else:
        pre = "passthrough"
    return Pipeline([("pre", pre), ("rf", rf)])


def _evaluate(pipe, X, y) -> dict:
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    pred = cross_val_predict(pipe, X, y, cv=cv)
    resid = y.to_numpy() - pred
    r2 = float(r2_score(y, pred))
    return {
        "mae": float(mean_absolute_error(y, pred)),
        "baseline_mae": float(mean_absolute_error(y, np.full(len(y), float(y.mean())))),
        "r2": r2,
        "resid": resid.tolist(),
        "has_skill": r2 >= MIN_SKILL_R2,
    }


@dataclass
class DatasetModel:
    entry: dict
    df: pd.DataFrame
    features: list
    target: str
    profile: dict
    typed: Pipeline
    general: Pipeline
    typed_metrics: dict
    general_metrics: dict

    @property
    def types(self) -> list:
        return sorted(self.profile["counts"])


def train(entry: dict) -> DatasetModel:
    df = load_dataset(entry)
    if len(df) < 30:
        raise ValueError("Dataset needs at least 30 usable rows.")
    features, target = entry["features"], entry["target"]
    y = df[target]
    Xt, Xg = df[[TYPE_COL, *features]], df[features]
    typed, general = _make_pipeline(True), _make_pipeline(False)
    tm, gm = _evaluate(typed, Xt, y), _evaluate(general, Xg, y)
    typed.fit(Xt, y)
    general.fit(Xg, y)
    return DatasetModel(entry, df, features, target, build_profile(df, features, target),
                        typed, general, tm, gm)


def predict(dm: DatasetModel, route: str, ctype: str, inputs: dict) -> dict:
    if route == "type_specific":
        model, metrics = dm.typed, dm.typed_metrics
        X = pd.DataFrame([{TYPE_COL: ctype, **inputs}])[[TYPE_COL, *dm.features]]
    else:
        model, metrics = dm.general, dm.general_metrics
        X = pd.DataFrame([inputs])[dm.features]
    point = max(0.0, float(model.predict(X)[0]))
    values = np.sort(np.clip(point + np.asarray(metrics["resid"]), 0, None))
    probs = np.arange(1, len(values) + 1) / len(values)
    return {"rul": point, "values": values, "probs": probs, "metrics": metrics, "route": route}


def _subset(dm: DatasetModel, ctype: str) -> pd.DataFrame:
    d = dm.df[dm.df[TYPE_COL].str.lower() == str(ctype).lower()]
    return d if len(d) >= 10 else dm.df


def percentiles(dm: DatasetModel, ctype: str, inputs: dict) -> dict:
    d = _subset(dm, ctype)
    return {f: float((d[f] < inputs[f]).mean() * 100) for f in dm.features}


def analogues(dm: DatasetModel, ctype: str, inputs: dict, k: int = 5) -> pd.DataFrame:
    """Retrieve the k most similar historical records (nearest neighbours in standardised space)."""
    d = _subset(dm, ctype)
    X = d[dm.features]
    std = X.std().replace(0, 1.0)
    z = (X - pd.Series(inputs)[dm.features]) / std
    dist = np.sqrt((z ** 2).sum(axis=1))
    idx = dist.nsmallest(k).index
    cols = []
    id_col = dm.entry.get("id_col")
    if id_col and id_col in d.columns:
        cols.append(id_col)
    cols += [*dm.features, dm.target]
    out = d.loc[idx, cols].copy()
    out["distance"] = dist.loc[idx].round(2)
    return out.reset_index(drop=True)
