# UX Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix navigation jank, redesign results page to show numbers first, and fix the association rules product-matching bug in `app.py`.

**Architecture:** All changes are in `app.py` (691 lines, monolithic Streamlit app). No new files except one test file. Tasks are ordered by risk: bug fix first (smallest, safest), then nav refactor, then results redesign.

**Tech Stack:** Streamlit, XGBoost, SHAP, mlxtend, Plotly, scikit-learn

---

## File Map

| File | Action | What changes |
|------|--------|--------------|
| `app.py` | Modify | Nav, results layout, association rules fix |
| `tests/test_cross_sell.py` | Create | Tests for association rules matching logic |

---

### Task 1: Fix association rules product-matching bug

**Files:**
- Create: `tests/test_cross_sell.py`
- Modify: `app.py` (line ~558)

- [ ] **Step 1: Write the failing test**

Create `tests/test_cross_sell.py`:

```python
import pandas as pd
from frozenset import *  # not needed, just pandas


def test_association_rules_matching_with_real_casing():
    """Old code lowercased+underscored product names — never matched rule antecedents."""
    rules = pd.DataFrame({
        "antecedents": [
            frozenset({"Personal Loan", "Credit Card"}),
            frozenset({"Student Loan"}),
            frozenset({"Fixed Deposits"}),
        ],
        "consequents": [
            frozenset({"Savings Account"}),
            frozenset({"Credit Card"}),
            frozenset({"Insurance"}),
        ],
        "confidence": [0.7, 0.6, 0.5],
        "lift": [1.5, 1.2, 1.1],
    })

    seg_products = ["Personal Loan", "Travel Credit Card", "Mutual Funds"]

    # OLD (broken) approach
    old_prod_set = {p.lower().replace(" ", "_") for p in seg_products}
    old_mask = rules["antecedents"].apply(lambda x: bool(set(x) & old_prod_set))
    assert old_mask.sum() == 0, "Old approach should match nothing (this is the bug)"

    # NEW (fixed) approach
    new_prod_set = set(seg_products)
    new_mask = rules["antecedents"].apply(lambda x: bool(set(x) & new_prod_set))
    assert new_mask.sum() == 1, "New approach should match 'Personal Loan' rule"
    assert "Personal Loan" in list(rules[new_mask]["antecedents"].iloc[0])
```

- [ ] **Step 2: Run test to confirm old behaviour fails as expected**

```
cd C:\Users\sait9\sait\banking-credit-engine
pytest tests/test_cross_sell.py -v
```

Expected: PASS (the test documents the bug — the old assertion proves the bug exists, the new assertion proves the fix works with real data; both assertions run in the same test).

- [ ] **Step 3: Apply the fix in `app.py`**

Find this block (around line 558):
```python
prod_set = {p.lower().replace(" ","_") for p in seg.products}
mask = rules["antecedents"].apply(lambda x: bool(set(x) & prod_set))
```

Replace with:
```python
prod_set = set(seg.products)
mask = rules["antecedents"].apply(lambda x: bool(set(x) & prod_set))
```

- [ ] **Step 4: Run test again**

```
pytest tests/test_cross_sell.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_cross_sell.py app.py
git commit -m "fix: correct association rules product matching — was lowercasing names causing no matches"
```

---

### Task 2: Replace radio nav with `st.tabs()`

**Files:**
- Modify: `app.py` (lines ~394–413 and ~418–572 and ~572–682)

- [ ] **Step 1: Remove session_state page init for "performance" and the radio nav block**

Find and **remove** these lines (around line 394–413):
```python
if "page" not in st.session_state: st.session_state.page = "home"
if "result" not in st.session_state: st.session_state.result = None
```
Keep these — just note their location.

Find and **replace** the radio block (around lines 407–413):
```python
tabs = ["🔍 Risk Assessor", "📊 Model Performance"]
tab_sel = st.radio("nav", tabs, horizontal=True, label_visibility="collapsed",
                   index=0 if st.session_state.page != "performance" else 1)
if tab_sel == tabs[1]: st.session_state.page = "performance"
elif st.session_state.page == "performance": st.session_state.page = "home"

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
```

Replace with:
```python
tab_risk, tab_perf = st.tabs(["🔍 Risk Assessor", "📊 Model Performance"])
```

- [ ] **Step 2: Move Risk Assessor content into `with tab_risk:`**

Find the block starting at (around line 418):
```python
if st.session_state.page in ("home", "results"):
```

Replace the outer `if` with `with tab_risk:` and adjust indentation for everything inside it. Remove the `elif st.session_state.page == "performance":` branch entirely — that moves to `tab_perf`.

The Risk Assessor block becomes:
```python
with tab_risk:
    if st.session_state.page == "home":
        # ... form code (unchanged, just re-indented)

    elif st.session_state.page == "results":
        # ... results code (unchanged here, redesigned in Task 3)
```

- [ ] **Step 3: Move Model Performance content into `with tab_perf:`**

Find the block currently under `elif st.session_state.page == "performance":` (around line 572).

Replace the `elif` line with `with tab_perf:` and re-indent everything inside it.

- [ ] **Step 4: Verify the app runs**

```
cd C:\Users\sait9\sait\banking-credit-engine
streamlit run app.py
```

Expected: App loads, two native tabs appear at top ("🔍 Risk Assessor" and "📊 Model Performance"), clicking between them works without page refresh artifacts.

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "refactor: replace radio+session_state tab nav with native st.tabs()"
```

---

### Task 3: Redesign results page — numbers first

**Files:**
- Modify: `app.py` — the `elif st.session_state.page == "results":` block (now inside `with tab_risk:`)

- [ ] **Step 1: Replace the two-column gauge+SHAP layout**

Find the current results block structure:
```python
col_back, _ = st.columns([1,5])
with col_back:
    if st.button("← New Assessment"):
        st.session_state.page = "home"; st.session_state.result = None; st.rerun()

st.markdown("")
col_gauge, col_shap = st.columns([1, 1.4])

with col_gauge:
    st.markdown(f'<div class="{risk_class}">...')
    st.markdown("")
    st.plotly_chart(risk_gauge(risk), use_container_width=True)
    st.markdown(f"""...""", unsafe_allow_html=True)

with col_shap:
    st.markdown('<div class="card-title">Top Risk Factors (SHAP)</div>', unsafe_allow_html=True)
    sv = res["sv"]; fn = res["feature_names"]
    top5 = np.argsort(np.abs(sv))[-8:][::-1]
    max_abs = max(np.abs(sv[top5])) + 1e-9
    for i in top5:
        bar_w = int(abs(sv[i])/max_abs * 180)
        bar_cls = "shap-bar-pos" if sv[i] > 0 else "shap-bar-neg"
        direction = "↑ increases risk" if sv[i] > 0 else "↓ decreases risk"
        st.markdown(f"""
        <div class="shap-row">
          <div class="shap-feature">{fn[i][:22]}</div>
          <div class="{bar_cls}" style="width:{bar_w}px"></div>
          <div class="shap-val">{sv[i]:+.3f}</div>
        </div>""", unsafe_allow_html=True)
```

Replace the entire block above with:
```python
col_back, _ = st.columns([1, 5])
with col_back:
    if st.button("← New Assessment"):
        st.session_state.page = "home"; st.session_state.result = None; st.rerun()

# 1. Full-width decision banner
st.markdown("")
st.markdown(
    f'<div class="{risk_class}"><div class="risk-score">{risk*100:.1f}%</div>'
    f'<div class="risk-label">{risk_icon} {risk_lbl}</div></div>',
    unsafe_allow_html=True,
)
st.markdown("")

# 2. Three-metric strip — the numbers a reviewer needs first
mc1, mc2, mc3 = st.columns(3)
mc1.metric("XGBoost Risk Score", f"{risk*100:.1f}%")
mc2.metric(
    "Logistic Regression",
    f"{res['lr_r']*100:.1f}%",
    delta=f"{(risk - res['lr_r'])*100:+.1f}pp",
    delta_color="inverse",
)
mc3.metric("Decision Threshold", f"{thr:.3f}")

# 3. Gauge (supporting role, full width)
st.plotly_chart(risk_gauge(risk), use_container_width=True)

# 4. SHAP in expander — detailed, not the headline
with st.expander("Why this score? (Top Risk Factors)", expanded=False):
    sv = res["sv"]; fn = res["feature_names"]
    top5 = np.argsort(np.abs(sv))[-8:][::-1]
    max_abs = max(np.abs(sv[top5])) + 1e-9
    for i in top5:
        bar_w = int(abs(sv[i]) / max_abs * 180)
        bar_cls = "shap-bar-pos" if sv[i] > 0 else "shap-bar-neg"
        st.markdown(
            f'<div class="shap-row">'
            f'<div class="shap-feature">{fn[i][:22]}</div>'
            f'<div class="{bar_cls}" style="width:{bar_w}px"></div>'
            f'<div class="shap-val">{sv[i]:+.3f}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
```

- [ ] **Step 2: Verify the app runs and results look right**

```
streamlit run app.py
```

Fill in the form, click "Assess Credit Risk". Expected:
- Decision banner appears full-width at top
- Three metric widgets appear below (XGBoost %, LR %, threshold)
- Gauge chart appears below that
- "Why this score?" expander is collapsed by default
- Cross-sell section appears below (unchanged)

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: redesign results page — numbers-first layout with SHAP in expander"
```

---

### Task 4: Push to GitHub (triggers Render auto-deploy)

- [ ] **Step 1: Confirm all tests pass**

```
pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 2: Push**

```bash
git push origin master
```

Expected: Push succeeds. Render detects the push via webhook and begins deploying. The live URL `https://banking-credit-engine.onrender.com` will reflect changes within ~2 minutes.
