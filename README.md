# RUL Predictor

Remaining Useful Life Prediction of Mechanical Components Using Machine Learning.
Mechanical Engineering college project (Kaushalendra Singh, Abdul Rahman, Ayush Yadav).

## Run
```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env          # optional: GROQ_API_KEY and/or ANTHROPIC_API_KEY
python smoke_test.py          # checks the whole pipeline without the UI
python -m streamlit run app.py
```

## Pages
Home, About (introduction, data sourcing, team), Methodology, Predictor, Data & Knowledge.

## Architecture (retrieval-augmented, not a single prompt)
1. **Harness** (`rul/harness.py`): validates input, flags out-of-range values, sets confidence.
2. **Resolver** (`rul/knowledge.py`): maps any typed component to a dataset type and/or a knowledge-base entry (aliases + fuzzy match).
3. **Estimation**
   - In a registered dataset: random-forest model (`rul/model.py`), 5-fold CV, range from CV residuals.
   - Otherwise: Weibull reliability estimate with condition factors (`rul/engine.py`).
4. **Retrieval**: TF-IDF search over knowledge-base chunks, plus nearest historical records from the dataset.
5. **LLM** (`rul/llm.py`): Groq or Claude gets only validated numbers and retrieved evidence, cites excerpts, may ask clarifying questions, and cannot change the RUL. Works without a key (rule-based fallback).
6. **Outputs**: failure modes, maintenance plan, spares, cost and downtime, asset memory (`data/history.jsonl`), PDF report (`rul/report.py`).

## Adding data
- **More datasets:** Data & Knowledge page -> upload a CSV, choose target, features and component type.
- **More components:** edit `rul/kb/components.json` (values are indicative, verify against OEM manuals).

## Assumptions to confirm (`rul/config.py`)
RUL unit is hours; units of vibration (mm/s), temperature (C) and pressure (bar) are assumed; add your college name in `COLLEGE`.
