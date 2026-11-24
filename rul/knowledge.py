"""Engineering knowledge base: component resolution (aliases + fuzzy match) and chunk retrieval (TF-IDF RAG)."""
import json
import re
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

GENERIC_ID = "generic-mechanical-component"


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


class KnowledgeBase:
    def __init__(self, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.meta = {k: v for k, v in data.items() if k != "components"}
        self.items = data["components"]
        self.generic = next(i for i in self.items if i["id"] == GENERIC_ID)
        self.known = [i for i in self.items if i["id"] != GENERIC_ID]

        docs = [f"{i['name']} {' '.join(i['aliases'])}" for i in self.known]
        self._name_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5)).fit(docs)
        self._name_mat = self._name_vec.transform(docs)

        self.chunks = self._build_chunks()
        texts = [c["text"] for c in self.chunks]
        self._chunk_vec = TfidfVectorizer(stop_words="english").fit(texts)
        self._chunk_mat = self._chunk_vec.transform(texts)

    # ---------- chunks ----------
    def _build_chunks(self) -> list:
        chunks = []
        for it in self.items:
            lim = "; ".join(
                f"{k} warning {v['warn']} alarm {v['alarm']} {v['unit']}"
                for k, v in it.get("limits", {}).items()
            )
            base = {"component_id": it["id"], "component": it["name"]}
            chunks.append({**base, "id": f"{it['id']}:overview", "kind": "overview",
                           "text": f"{it['name']} ({it['category']}). {it['description']} "
                                   f"Typical characteristic life about {it['life']['eta']:,} h "
                                   f"(Weibull shape {it['life']['beta']}). "
                                   f"Condition limits: {lim or 'not defined'}."})
            chunks.append({**base, "id": f"{it['id']}:failure_modes", "kind": "failure modes",
                           "text": "Failure modes of " + it["name"] + ": " + "; ".join(
                               f"{m['mode']} - cause: {m['cause']} - watch: {m['indicator']}"
                               for m in it["failure_modes"])})
            chunks.append({**base, "id": f"{it['id']}:maintenance", "kind": "maintenance",
                           "text": "Maintenance of " + it["name"] + ": " + "; ".join(
                               f"{t['task']} about every {t['interval_h']:,} h" for t in it["maintenance"])})
            chunks.append({**base, "id": f"{it['id']}:spares", "kind": "spares",
                           "text": "Critical spares for " + it["name"] + ": " + ", ".join(it["spares"])})
        return chunks

    # ---------- resolution ----------
    def names(self) -> list:
        return [i["name"] for i in self.known]

    def resolve(self, text: str):
        """Return (item or None, score, how)."""
        t = norm(text)
        if not t:
            return None, 0.0, "empty"
        keys = {i["id"]: {norm(i["name"]), *[norm(a) for a in i["aliases"]]} for i in self.known}
        for it in self.known:
            if t in keys[it["id"]]:
                return it, 1.0, "exact"
        best, best_len = None, 0
        for it in self.known:
            for k in keys[it["id"]]:
                if len(k) >= 4 and f" {k} " in f" {t} " and len(k) > best_len:
                    best, best_len = it, len(k)
        if best:
            return best, 0.9, "alias in text"
        sims = cosine_similarity(self._name_vec.transform([t]), self._name_mat)[0]
        i = int(np.argmax(sims))
        if sims[i] >= 0.30:
            return self.known[i], float(sims[i]), "fuzzy"
        return None, float(sims[i]), "unknown"

    # ---------- retrieval ----------
    def retrieve(self, query: str, component_id=None, k: int = 4) -> list:
        sims = cosine_similarity(self._chunk_vec.transform([query]), self._chunk_mat)[0]
        if component_id:
            own = [i for i, c in enumerate(self.chunks) if c["component_id"] == component_id]
            first = [i for i in own if self.chunks[i]["kind"] == "overview"]
            rest = sorted([i for i in own if i not in first], key=lambda i: -sims[i])
            sel, related = (first + rest)[:k], False
        else:
            gen = [i for i, c in enumerate(self.chunks)
                   if c["component_id"] == GENERIC_ID and c["kind"] == "overview"]
            others = [int(i) for i in np.argsort(-sims) if self.chunks[int(i)]["component_id"] != GENERIC_ID]
            sel, related = (gen + others)[:k], True
        return [{**self.chunks[i], "score": float(sims[i]), "related": related} for i in sel]


def resolve_component(text: str, kb: KnowledgeBase, models: list) -> dict:
    """Decide which dataset (if any) and which KB entry a free-text component name maps to."""
    item, score, how = kb.resolve(text)
    names = {norm(text)}
    if item:
        names |= {norm(item["name"])} | {norm(a) for a in item["aliases"]}
    for dm in models:
        for typ in dm.types:
            if norm(typ) in names:
                return {"dm": dm, "dtype": typ, "kb": item, "how": how, "score": score}
    return {"dm": None, "dtype": None, "kb": item, "how": how, "score": score}
