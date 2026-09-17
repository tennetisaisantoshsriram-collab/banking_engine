# UX Improvements — Banking Credit Risk Engine

**Date:** 2026-09-17
**Scope:** `app.py` only — no tech stack changes

---

## Problem

Three concrete pain points in the current UI:

1. **Navigation is janky** — `st.radio()` + 3-state `session_state.page` ("home"/"results"/"performance") with manual `st.rerun()` calls simulates tab switching. Fragile and unnecessary.

2. **Results page is cluttered** — Risk badge, gauge, model comparison pill, and SHAP bars are crammed into two columns. The numbers a bank officer needs most (risk %, model comparison, threshold) are buried.

3. **Association rules never fire** — Product names are lowercased and underscored before matching against rule antecedents, but antecedents use original casing. The "Association Rule Boosts" section always renders empty.

---

## Design

### 1. Navigation — replace radio with `st.tabs()`

**Before:** `st.radio()` nav bar + `session_state.page` with values "home", "results", "performance". Tab changes call `st.rerun()`.

**After:** `st.tabs(["🔍 Risk Assessor", "📊 Model Performance"])`. The form→results transition stays as session state but only inside Tab 1. Tab switching is handled natively by Streamlit — no `rerun()` needed for it.

Files changed: `app.py` — remove the radio nav block and the associated session_state.page branching for tab selection.

---

### 2. Results page — numbers-first layout

**Before:** Two columns — left has risk badge + gauge + model comparison pill; right has SHAP bars. Cross-sell below. No clear visual hierarchy.

**After:**

```
┌─────────────────────────────────────────────────────┐
│  🚨 HIGH RISK — Loan Not Recommended                │  ← full-width decision banner
├──────────────┬──────────────┬───────────────────────┤
│  Risk Score  │  XGB vs LR   │  Decision Threshold   │
│    73.2%     │ 73.2% / 61.4%│       0.412           │  ← 3 st.metric() columns
├──────────────┴──────────────┴───────────────────────┤
│  Gauge chart (full width, supporting role)          │
├─────────────────────────────────────────────────────┤
│  ▼ Why this score? (SHAP factors)  [st.expander]   │
├─────────────────────────────────────────────────────┤
│  Cross-sell section (only if risk < 30%)            │
└─────────────────────────────────────────────────────┘
```

Key changes:
- Decision banner spans full width at top
- Three `st.metric()` widgets in a row: risk %, model comparison delta, threshold
- Gauge moves below the strip — still present but not the first thing you see
- SHAP bars move into `st.expander("Why this score?")` — collapsed by default
- Cross-sell unchanged except for bug fix below

---

### 3. Bug fix — association rules product matching

**Before:**
```python
prod_set = {p.lower().replace(" ","_") for p in seg.products}
# "Personal Loan" → "personal_loan"  — never matches rule antecedents
```

**After:**
```python
prod_set = set(seg.products)
# "Personal Loan" → "Personal Loan"  — matches correctly
```

One-line fix in the results rendering block (~line 558 of current `app.py`).

---

## Scope

- All changes are in `app.py`
- No new files
- No dependency changes
- `src/` modules untouched (out of scope)
- Commit and push to `origin` (GitHub), which triggers Render auto-deploy

---

## Success Criteria

- Tab switching works without `st.rerun()`
- Risk %, model comparison, and threshold are the first numbers visible on results page
- SHAP section is visible but collapsed by default
- Association rule boosts appear when a low-risk customer's segment products match rule antecedents
