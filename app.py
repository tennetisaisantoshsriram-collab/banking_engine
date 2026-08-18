"""
Banking Credit Default Risk & Cross-Sell Engine
Streamlit Prototype — No login required
"""

import os, pickle, warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    roc_auc_score, roc_curve, precision_recall_curve,
    f1_score, precision_score, recall_score, confusion_matrix
)
from xgboost import XGBClassifier
import shap
from mlxtend.frequent_patterns import fpgrowth, association_rules as mlxtend_rules
from dataclasses import dataclass, field
from typing import List

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Banking Credit Risk Engine",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }

/* ── Hero header ── */
.hero {
    background: linear-gradient(135deg, #0a2540 0%, #1a3a5c 50%, #0d3b6e 100%);
    border-radius: 18px;
    padding: 2.2rem 2.8rem;
    margin-bottom: 1.8rem;
    box-shadow: 0 8px 32px rgba(10,37,64,0.28);
}
.hero-title {
    font-size: 2rem; font-weight: 800; color: #ffffff;
    letter-spacing: -0.5px; margin: 0 0 0.3rem 0;
}
.hero-sub {
    font-size: 1rem; color: #a8c4e0; font-weight: 400; margin: 0;
}
.hero-badge {
    display: inline-block;
    background: rgba(99,91,255,0.25);
    color: #a89fff;
    border: 1px solid rgba(99,91,255,0.4);
    border-radius: 20px;
    padding: 3px 14px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-bottom: 0.7rem;
}

/* ── Cards ── */
.card {
    background: #ffffff;
    border-radius: 14px;
    padding: 1.6rem 1.8rem;
    box-shadow: 0 4px 20px rgba(10,37,64,0.08);
    margin-bottom: 1.2rem;
    border: 1px solid #e8edf5;
}
.card-title {
    font-size: 0.85rem; font-weight: 700; color: #0a2540;
    text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 1rem;
}

/* ── Risk badges ── */
.risk-low {
    background: linear-gradient(135deg, #00c896, #00a878);
    color: white; border-radius: 12px; padding: 1.4rem 1.8rem;
    box-shadow: 0 6px 20px rgba(0,200,150,0.3);
}
.risk-medium {
    background: linear-gradient(135deg, #ffa502, #e09000);
    color: white; border-radius: 12px; padding: 1.4rem 1.8rem;
    box-shadow: 0 6px 20px rgba(255,165,2,0.3);
}
.risk-high {
    background: linear-gradient(135deg, #ff4757, #cc2233);
    color: white; border-radius: 12px; padding: 1.4rem 1.8rem;
    box-shadow: 0 6px 20px rgba(255,71,87,0.3);
}
.risk-score { font-size: 3rem; font-weight: 800; line-height: 1; }
.risk-label { font-size: 0.9rem; font-weight: 600; opacity: 0.9; margin-top: 0.3rem; }

/* ── Metric pill ── */
.metric-pill {
    background: #f4f7fc; border-radius: 10px;
    padding: 0.9rem 1.2rem; text-align: center;
    border: 1px solid #e0e8f5;
}
.metric-val { font-size: 1.5rem; font-weight: 700; color: #0a2540; }
.metric-lbl { font-size: 0.72rem; color: #6b7a99; font-weight: 500; margin-top: 2px; }

/* ── Product chip ── */
.product-chip {
    display: inline-block;
    background: linear-gradient(135deg, #f0f4ff, #e8eeff);
    color: #3730a3;
    border: 1px solid #c7d2fe;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 0.82rem;
    font-weight: 600;
    margin: 4px 4px 4px 0;
}

/* ── Segment card ── */
.segment-card {
    background: linear-gradient(135deg, #f0fdf4, #dcfce7);
    border: 1px solid #86efac;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
}
.segment-name { font-size: 1.1rem; font-weight: 700; color: #166534; }
.segment-desc { font-size: 0.82rem; color: #4b7a5e; margin-top: 4px; }

/* ── SHAP bar ── */
.shap-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.shap-feature { font-size: 0.8rem; color: #374151; font-weight: 500; width: 180px; flex-shrink: 0; }
.shap-bar-pos { height: 8px; background: #ff4757; border-radius: 4px; }
.shap-bar-neg { height: 8px; background: #00c896; border-radius: 4px; }
.shap-val { font-size: 0.75rem; color: #6b7a99; font-weight: 600; }

/* ── Divider ── */
.divider { height: 1px; background: #e8edf5; margin: 1.2rem 0; }

/* ── Nav tabs ── */
.nav-bar {
    display: flex; gap: 8px; margin-bottom: 1.5rem;
    background: #f4f7fc; border-radius: 12px; padding: 6px;
    border: 1px solid #e0e8f5;
}
.nav-tab {
    flex: 1; text-align: center; padding: 8px 0;
    border-radius: 8px; font-size: 0.85rem; font-weight: 600;
    cursor: pointer; color: #6b7a99; border: none; background: transparent;
}
.nav-tab-active {
    background: #0a2540; color: white;
    box-shadow: 0 2px 8px rgba(10,37,64,0.2);
}

/* ── Back button ── */
.stButton > button {
    background: #0a2540; color: white; border: none;
    border-radius: 10px; font-weight: 600; font-size: 0.9rem;
    padding: 0.5rem 1.5rem;
    transition: background 0.2s;
}
.stButton > button:hover { background: #1a3a5c; }

/* ── Input styling ── */
.stSelectbox > div > div, .stNumberInput > div > div > input,
.stSlider > div { border-radius: 8px !important; }

/* ── Table ── */
.perf-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
.perf-table th {
    background: #0a2540; color: white; padding: 10px 14px;
    text-align: left; font-weight: 600;
}
.perf-table td { padding: 9px 14px; border-bottom: 1px solid #e8edf5; color: #374151; }
.perf-table tr:nth-child(even) td { background: #f8fafd; }
.perf-table .winner { color: #00c896; font-weight: 700; }

/* ── Status dot ── */
.status-dot {
    display: inline-block; width: 8px; height: 8px;
    background: #00c896; border-radius: 50%; margin-right: 6px;
    box-shadow: 0 0 6px rgba(0,200,150,0.6);
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%,100%{opacity:1} 50%{opacity:0.5}
}
</style>
""", unsafe_allow_html=True)

# ── Constants ────────────────────────────────────────────────────────────────
GRADE_MAP        = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7}
NUMERIC_COLS     = ["person_age","person_income","person_emp_length","loan_amnt",
                    "loan_int_rate","loan_percent_income","debt_to_income"]
MEDIAN_IMPUTE    = ["loan_int_rate","person_emp_length"]
REQUIRED_COLUMNS = ["person_age","person_income","person_emp_length","loan_amnt",
                    "loan_int_rate","loan_percent_income","loan_grade","loan_intent",
                    "home_ownership","cb_person_default_on_file","loan_status"]
DATA_PATH        = "data/credit_risk_dataset.csv"

INTENT_PRODUCT = {
    "EDUCATION":         ["Student Loan","Credit Card"],
    "MEDICAL":           ["Health Insurance","Personal Loan"],
    "VENTURE":           ["Business Loan","Investment Account"],
    "PERSONAL":          ["Personal Loan","Credit Card"],
    "HOMEIMPROVEMENT":   ["Home Loan","Savings Account"],
    "DEBTCONSOLIDATION": ["Balance Transfer Card","Personal Loan"],
}
GRADE_PRODUCT = {
    "A": ["Investment Account","Premium Credit Card"],
    "B": ["Investment Account"],
    "C": ["Savings Account"],
}

@dataclass
class Segment:
    name: str; description: str
    products: List[str] = field(default_factory=list)

SEGMENTS = {
    "young_starter":       Segment("Young Starter",       "Age < 30, Income < ₹40K/yr — early career",
                                   ["Student Loan","Secured Credit Card","Savings Account"]),
    "rising_professional": Segment("Rising Professional", "Age 30–45, Income ₹40K–₹80K — growth stage",
                                   ["Personal Loan","Travel Credit Card","Mutual Funds"]),
    "established_earner":  Segment("Established Earner",  "Age 30–55, Income > ₹80K — wealth building",
                                   ["Home Loan","Premium Credit Card","Investment Portfolio"]),
    "senior_stable":       Segment("Senior Stable",       "Age > 55 — preservation & retirement",
                                   ["Fixed Deposits","Insurance","Retirement Fund"]),
}

def assign_segment(age, income):
    if age > 55:                                    return SEGMENTS["senior_stable"]
    if age < 30 and income < 40_000:               return SEGMENTS["young_starter"]
    if 30 <= age <= 45 and 40_000 <= income <= 80_000: return SEGMENTS["rising_professional"]
    if 30 <= age <= 55 and income > 80_000:        return SEGMENTS["established_earner"]
    if income < 40_000:                            return SEGMENTS["young_starter"]
    if income <= 80_000:                           return SEGMENTS["rising_professional"]
    return SEGMENTS["established_earner"]

# ── Feature Engineering ───────────────────────────────────────────────────────
class FeatureEngineer:
    def __init__(self):
        self.scaler = StandardScaler(); self.medians = {}; self.encoded_columns = []

    def _base(self, X):
        X = X.copy()
        for c in MEDIAN_IMPUTE: X[c] = X[c].fillna(self.medians.get(c, 0))
        X["debt_to_income"] = (X["loan_amnt"] / X["person_income"].replace(0, np.nan)).fillna(0)
        X["loan_grade"] = X["loan_grade"].map(GRADE_MAP)
        X["cb_person_default_on_file"] = (X["cb_person_default_on_file"] == "Y").astype(int)
        return pd.get_dummies(X, columns=["loan_intent","home_ownership"])

    def fit_transform(self, X):
        for c in MEDIAN_IMPUTE: self.medians[c] = X[c].median()
        out = self._base(X); self.encoded_columns = out.columns.tolist(); return out

    def transform(self, X):
        out = self._base(X)
        for c in self.encoded_columns:
            if c not in out.columns: out[c] = 0
        return out[self.encoded_columns]

    def fit_transform_scaled(self, X):
        enc = self.fit_transform(X); sc = enc.copy()
        p = [c for c in NUMERIC_COLS if c in sc.columns]
        sc[p] = self.scaler.fit_transform(enc[p]); return sc

    def transform_scaled(self, X):
        enc = self.transform(X); sc = enc.copy()
        p = [c for c in NUMERIC_COLS if c in sc.columns]
        sc[p] = self.scaler.transform(enc[p]); return sc

# ── Synthetic demo data (if CSV not found) ───────────────────────────────────
def make_demo_data(n=5000, seed=42):
    rng = np.random.default_rng(seed)
    grades   = rng.choice(["A","B","C","D","E","F","G"], n, p=[.15,.20,.22,.18,.12,.08,.05])
    intents  = rng.choice(["EDUCATION","MEDICAL","VENTURE","PERSONAL","HOMEIMPROVEMENT","DEBTCONSOLIDATION"], n)
    owners   = rng.choice(["RENT","MORTGAGE","OWN","OTHER"], n, p=[.40,.35,.20,.05])
    cb       = rng.choice(["N","Y"], n, p=[.78,.22])
    age      = rng.integers(20, 70, n)
    income   = rng.integers(15000, 180000, n)
    emp_len  = rng.uniform(0, 30, n)
    loan_amt = rng.integers(1000, 35000, n)
    int_rate = rng.uniform(5, 24, n)
    pct_inc  = loan_amt / income
    grade_num = np.array([GRADE_MAP[g] for g in grades])
    log_odds = (-3 + 0.4*grade_num + 0.06*int_rate - 0.00002*income
                + 0.5*(cb=="Y").astype(int) + rng.normal(0, 0.5, n))
    prob     = 1 / (1 + np.exp(-log_odds))
    status   = (rng.random(n) < prob).astype(int)
    return pd.DataFrame({"person_age":age,"person_income":income,
        "person_emp_length":emp_len,"loan_amnt":loan_amt,"loan_int_rate":int_rate,
        "loan_percent_income":pct_inc,"loan_grade":grades,"loan_intent":intents,
        "home_ownership":owners,"cb_person_default_on_file":cb,"loan_status":status})

# ── Model training (cached) ───────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_model():
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)[REQUIRED_COLUMNS].copy()
        source = "Kaggle dataset"
    else:
        df = make_demo_data()
        source = "synthetic demo data"

    X = df.drop(columns=["loan_status"]); y = df["loan_status"]
    X_tr, X_tmp, y_tr, y_tmp = train_test_split(X, y, test_size=.30, stratify=y, random_state=42)
    X_val, X_te, y_val, y_te = train_test_split(X_tmp, y_tmp, test_size=.50, stratify=y_tmp, random_state=42)

    fe = FeatureEngineer()
    X_tr_sc  = fe.fit_transform_scaled(X_tr)
    X_val_sc = fe.transform_scaled(X_val); X_te_sc = fe.transform_scaled(X_te)
    X_tr_enc = fe.transform(X_tr)
    X_val_enc= fe.transform(X_val); X_te_enc = fe.transform(X_te)

    lr = LogisticRegression(solver="lbfgs", max_iter=1000, class_weight="balanced", random_state=42)
    lr.fit(X_tr_sc, y_tr)

    spw = float((y_tr==0).sum()/(y_tr==1).sum())
    xgb = XGBClassifier(scale_pos_weight=spw, max_depth=5, learning_rate=0.05,
                         n_estimators=200, subsample=0.8, colsample_bytree=0.8,
                         random_state=42, eval_metric="auc", verbosity=0)
    xgb.fit(X_tr_enc, y_tr)
    explainer = shap.TreeExplainer(xgb)

    # threshold
    p_, r_, t_ = precision_recall_curve(y_val, xgb.predict_proba(X_val_enc)[:,1])
    f1s = 2*p_*r_/(p_+r_+1e-9); threshold = float(t_[np.argmax(f1s[:-1])])

    def metrics(y_true, y_proba, thr):
        yp = (y_proba>=thr).astype(int)
        fpr,tpr,_ = roc_curve(y_true, y_proba)
        return {"roc_auc":roc_auc_score(y_true,y_proba),
                "precision":precision_score(y_true,yp,zero_division=0),
                "recall":recall_score(y_true,yp,zero_division=0),
                "f1":f1_score(y_true,yp,zero_division=0),
                "ks":float(np.max(tpr-fpr))}

    lr_m  = metrics(y_te, lr.predict_proba(X_te_sc)[:,1], threshold)
    xgb_m = metrics(y_te, xgb.predict_proba(X_te_enc)[:,1], threshold)

    # association rules
    all_prods = sorted({p for v in INTENT_PRODUCT.values() for p in v} |
                       {p for v in GRADE_PRODUCT.values() for p in v})
    def basket(row):
        b = set(INTENT_PRODUCT.get(str(row.get("loan_intent","")).upper(),[]))
        b.update(GRADE_PRODUCT.get(str(row.get("loan_grade","")),[]))
        return {p:(p in b) for p in all_prods}
    txns = pd.DataFrame([basket(r) for _,r in df.iterrows()], dtype=bool)
    freq = fpgrowth(txns, min_support=0.05, use_colnames=True)
    rules = mlxtend_rules(freq, metric="confidence", min_threshold=0.4).sort_values("lift",ascending=False) if not freq.empty else pd.DataFrame()

    return dict(fe=fe, lr=lr, xgb=xgb, explainer=explainer, threshold=threshold,
                lr_m=lr_m, xgb_m=xgb_m, df=df, rules=rules,
                X_te=X_te_enc, y_te=y_te, X_te_sc=X_te_sc,
                feature_names=X_te_enc.columns.tolist(), source=source)

# ── Gauge chart ───────────────────────────────────────────────────────────────
def risk_gauge(score):
    color = "#00c896" if score < 0.3 else ("#ffa502" if score < 0.5 else "#ff4757")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(score*100, 1),
        number={"suffix":"%","font":{"size":36,"color":"#0a2540"}},
        gauge={"axis":{"range":[0,100],"tickcolor":"#b0bec5"},
               "bar":{"color":color,"thickness":0.6},
               "bgcolor":"white",
               "borderwidth":0,
               "steps":[{"range":[0,30],"color":"#d1fae5"},
                        {"range":[30,50],"color":"#fef3c7"},
                        {"range":[50,100],"color":"#ffe4e6"}],
               "threshold":{"line":{"color":color,"width":3},"thickness":0.8,"value":score*100}},
    ))
    fig.update_layout(height=220, margin=dict(t=20,b=10,l=20,r=20), paper_bgcolor="white")
    return fig

# ── Session state init ────────────────────────────────────────────────────────
if "page" not in st.session_state: st.session_state.page = "home"
if "result" not in st.session_state: st.session_state.result = None

# ── HERO HEADER ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-badge">⬡ ML PROTOTYPE</div>
  <div class="hero-title">🏦 Banking Credit Risk Engine</div>
  <div class="hero-sub">Credit Default Prediction · Customer Segmentation · Cross-Sell Recommendations</div>
</div>
""", unsafe_allow_html=True)

# ── TAB NAV ───────────────────────────────────────────────────────────────────
tabs = ["🔍 Risk Assessor", "📊 Model Performance"]
tab_sel = st.radio("nav", tabs, horizontal=True, label_visibility="collapsed",
                   index=0 if st.session_state.page != "performance" else 1)
if tab_sel == tabs[1]: st.session_state.page = "performance"
elif st.session_state.page == "performance": st.session_state.page = "home"

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# PAGE: RISK ASSESSOR
# ════════════════════════════════════════════════════════════════════════════════
if st.session_state.page in ("home", "results"):

    if st.session_state.page == "home":
        st.markdown('<div class="card-title">Customer Information</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1.1, 1.1, 1])

        with col1:
            st.markdown('<div class="card-title" style="font-size:0.75rem">Personal Details</div>', unsafe_allow_html=True)
            age        = st.number_input("Age", 18, 80, 30)
            income     = st.number_input("Annual Income ($)", 5000, 500000, 55000, step=1000)
            emp_length = st.slider("Employment Length (years)", 0.0, 40.0, 4.0, 0.5)
            home_own   = st.selectbox("Home Ownership", ["RENT","MORTGAGE","OWN","OTHER"])
            cb_default = st.selectbox("Prior Default on File", ["N","Y"],
                                      format_func=lambda x: "No" if x=="N" else "Yes")

        with col2:
            st.markdown('<div class="card-title" style="font-size:0.75rem">Loan Details</div>', unsafe_allow_html=True)
            loan_amnt    = st.number_input("Loan Amount ($)", 500, 100000, 10000, step=500)
            loan_int     = st.slider("Interest Rate (%)", 5.0, 25.0, 12.0, 0.1)
            loan_grade   = st.selectbox("Loan Grade", ["A","B","C","D","E","F","G"])
            loan_intent  = st.selectbox("Loan Intent",
                           ["EDUCATION","MEDICAL","VENTURE","PERSONAL","HOMEIMPROVEMENT","DEBTCONSOLIDATION"])
            pct_inc      = round(loan_amnt / max(income,1), 4)
            st.metric("Loan-to-Income Ratio", f"{pct_inc:.1%}")

        with col3:
            st.markdown('<div class="card-title" style="font-size:0.75rem">Quick Summary</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="metric-pill" style="margin-bottom:8px">
              <div class="metric-val">${income:,}</div>
              <div class="metric-lbl">Annual Income</div>
            </div>
            <div class="metric-pill" style="margin-bottom:8px">
              <div class="metric-val">${loan_amnt:,}</div>
              <div class="metric-lbl">Loan Amount</div>
            </div>
            <div class="metric-pill" style="margin-bottom:8px">
              <div class="metric-val">{loan_int}%</div>
              <div class="metric-lbl">Interest Rate</div>
            </div>
            <div class="metric-pill">
              <div class="metric-val">Grade {loan_grade}</div>
              <div class="metric-lbl">Loan Grade</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")
        assess = st.button("⚡ Assess Credit Risk", use_container_width=True)

        if assess:
            with st.spinner("Running risk model..."):
                m = load_model()
                customer = pd.DataFrame([{
                    "person_age": age, "person_income": income,
                    "person_emp_length": emp_length, "loan_amnt": loan_amnt,
                    "loan_int_rate": loan_int, "loan_percent_income": pct_inc,
                    "loan_grade": loan_grade, "loan_intent": loan_intent,
                    "home_ownership": home_own, "cb_person_default_on_file": cb_default,
                }])
                X_enc = m["fe"].transform(customer)
                X_sc  = m["fe"].transform_scaled(customer)
                risk  = float(m["xgb"].predict_proba(X_enc)[0,1])
                lr_r  = float(m["lr"].predict_proba(X_sc)[0,1])
                sv    = m["explainer"].shap_values(X_enc)
                sv    = sv[1][0] if isinstance(sv, list) else sv[0]
                seg   = assign_segment(age, income)
                st.session_state.result = dict(
                    risk=risk, lr_r=lr_r, sv=sv,
                    feature_names=m["feature_names"], seg=seg,
                    rules=m["rules"], threshold=m["threshold"],
                    age=age, income=income, loan_grade=loan_grade,
                )
                st.session_state.page = "results"
                st.rerun()

    # ── RESULTS PAGE ─────────────────────────────────────────────────────────
    elif st.session_state.page == "results":
        res = st.session_state.result
        risk = res["risk"]; thr = res["threshold"]

        if risk < 0.3:
            risk_class = "risk-low"; risk_icon = "✅"; risk_lbl = "LOW RISK — Eligible for Cross-Sell"
        elif risk < 0.5:
            risk_class = "risk-medium"; risk_icon = "⚠️"; risk_lbl = "MEDIUM RISK — Proceed with Caution"
        else:
            risk_class = "risk-high"; risk_icon = "🚨"; risk_lbl = "HIGH RISK — Loan Not Recommended"

        col_back, _ = st.columns([1,5])
        with col_back:
            if st.button("← New Assessment"):
                st.session_state.page = "home"; st.session_state.result = None; st.rerun()

        st.markdown("")
        col_gauge, col_shap = st.columns([1, 1.4])

        with col_gauge:
            st.markdown(f'<div class="{risk_class}"><div class="risk-score">{risk*100:.1f}%</div><div class="risk-label">{risk_icon} {risk_lbl}</div></div>', unsafe_allow_html=True)
            st.markdown("")
            st.plotly_chart(risk_gauge(risk), use_container_width=True)
            st.markdown(f"""
            <div class="metric-pill" style="text-align:left;padding:1rem">
              <span class="status-dot"></span>
              <b style="color:#0a2540">Model Comparison</b><br>
              <small style="color:#6b7a99">XGBoost: <b>{risk*100:.1f}%</b> &nbsp;|&nbsp; Logistic Reg: <b>{res['lr_r']*100:.1f}%</b></small><br>
              <small style="color:#6b7a99">Decision threshold: <b>{thr:.3f}</b></small>
            </div>""", unsafe_allow_html=True)

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

        # ── Cross-sell ──
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        if risk < 0.3:
            seg = res["seg"]
            st.markdown(f"""
            <div class="segment-card">
              <div class="segment-name">🎯 Segment: {seg.name}</div>
              <div class="segment-desc">{seg.description}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("**Recommended Products:**")
            chips = "".join([f'<span class="product-chip">🏷 {p}</span>' for p in seg.products])
            st.markdown(chips, unsafe_allow_html=True)

            rules = res["rules"]
            if not rules.empty:
                st.markdown("<br>**Association Rule Boosts:**", unsafe_allow_html=True)
                prod_set = {p.lower().replace(" ","_") for p in seg.products}
                mask = rules["antecedents"].apply(lambda x: bool(set(x) & prod_set))
                filtered = rules[mask].head(3)
                if not filtered.empty:
                    for _, r in filtered.iterrows():
                        a = ", ".join(sorted(r["antecedents"]))
                        c = ", ".join(sorted(r["consequents"]))
                        st.markdown(f"- **{a}** → {c} &nbsp; *(conf={r['confidence']:.2f}, lift={r['lift']:.2f})*")
        else:
            st.info(f"Customer not eligible for cross-sell (risk score {risk:.1%} ≥ 30% threshold).")

# ════════════════════════════════════════════════════════════════════════════════
# PAGE: MODEL PERFORMANCE
# ════════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "performance":
    m = None
    with st.spinner("Loading models and computing metrics..."):
        m = load_model()

    # ── Metrics table ──
    st.markdown('<div class="card-title">Model Comparison — Test Set</div>', unsafe_allow_html=True)
    lm, xm = m["lr_m"], m["xgb_m"]
    keys = ["roc_auc","precision","recall","f1","ks"]
    labels = ["ROC-AUC","Precision","Recall","F1 Score","KS Statistic"]

    rows = ""
    for k, lbl in zip(keys, labels):
        lv, xv = lm[k], xm[k]
        lw = 'class="winner"' if lv > xv else ""
        xw = 'class="winner"' if xv > lv else ""
        rows += f"<tr><td>{lbl}</td><td {lw}>{lv:.4f}</td><td {xw}>{xv:.4f}</td></tr>"

    st.markdown(f"""
    <table class="perf-table">
      <thead><tr><th>Metric</th><th>Logistic Regression</th><th>XGBoost</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ──
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="card-title">ROC Curves</div>', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor("white"); ax.set_facecolor("#fafbfd")
        for name, proba, color in [
            ("Logistic Reg", m["lr"].predict_proba(m["X_te_sc"])[:,1], "#635bff"),
            ("XGBoost",      m["xgb"].predict_proba(m["X_te"])[:,1],   "#00c896"),
        ]:
            fpr, tpr, _ = roc_curve(m["y_te"], proba)
            auc = roc_auc_score(m["y_te"], proba)
            ax.plot(fpr, tpr, color=color, lw=2, label=f"{name} (AUC={auc:.3f})")
        ax.plot([0,1],[0,1],"--", color="#b0bec5", lw=1, label="Random")
        ax.set_xlabel("False Positive Rate", fontsize=9)
        ax.set_ylabel("True Positive Rate", fontsize=9)
        ax.legend(fontsize=8); ax.grid(alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.savefig("outputs/roc_curves.png", dpi=150, bbox_inches="tight")
        plt.close()

    with c2:
        st.markdown('<div class="card-title">Confusion Matrix (XGBoost)</div>', unsafe_allow_html=True)
        xgb_pred = (m["xgb"].predict_proba(m["X_te"])[:,1] >= m["threshold"]).astype(int)
        cm = confusion_matrix(m["y_te"], xgb_pred)
        fig, ax = plt.subplots(figsize=(5, 4))
        fig.patch.set_facecolor("white")
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                    xticklabels=["No Default","Default"],
                    yticklabels=["No Default","Default"],
                    annot_kws={"size":13,"weight":"bold"})
        ax.set_xlabel("Predicted", fontsize=9); ax.set_ylabel("Actual", fontsize=9)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.savefig("outputs/confusion_matrix.png", dpi=150, bbox_inches="tight")
        plt.close()

    c3, c4 = st.columns(2)

    with c3:
        st.markdown('<div class="card-title">SHAP Feature Importance</div>', unsafe_allow_html=True)
        sv_all = m["explainer"].shap_values(m["X_te"])
        sv_all = sv_all[1] if isinstance(sv_all, list) else sv_all
        mean_abs = np.abs(sv_all).mean(axis=0)
        top10 = np.argsort(mean_abs)[-10:]
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor("white"); ax.set_facecolor("#fafbfd")
        colors_bar = ["#635bff" if mean_abs[i] > np.median(mean_abs) else "#a89fff" for i in top10]
        ax.barh([m["feature_names"][i][:20] for i in top10], mean_abs[top10], color=colors_bar)
        ax.set_xlabel("Mean |SHAP Value|", fontsize=9); ax.grid(alpha=0.3, axis="x")
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.savefig("outputs/shap_importance.png", dpi=150, bbox_inches="tight")
        plt.close()

    with c4:
        st.markdown('<div class="card-title">Default Rate by Loan Grade</div>', unsafe_allow_html=True)
        df = m["df"]
        gr = df.groupby("loan_grade")["loan_status"].mean().reindex(["A","B","C","D","E","F","G"])
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor("white"); ax.set_facecolor("#fafbfd")
        bars = ax.bar(gr.index, gr.values,
                      color=["#00c896","#3dd9ac","#ffa502","#ff7043","#ff5252","#ff4757","#cc2233"])
        ax.set_ylabel("Default Rate", fontsize=9)
        ax.set_ylim(0, 1); ax.grid(alpha=0.3, axis="y")
        for b, v in zip(bars, gr.values):
            ax.text(b.get_x()+b.get_width()/2, v+0.02, f"{v:.0%}", ha="center", fontsize=8, fontweight="bold")
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.savefig("outputs/default_by_grade.png", dpi=150, bbox_inches="tight")
        plt.close()

    # ── Dataset stats ──
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Dataset Overview</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    dr = df["loan_status"].mean()
    m1.markdown(f'<div class="metric-pill"><div class="metric-val">{len(df):,}</div><div class="metric-lbl">Total Records</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-pill"><div class="metric-val">{dr:.1%}</div><div class="metric-lbl">Default Rate</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-pill"><div class="metric-val">{df.shape[1]-1}</div><div class="metric-lbl">Features</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-pill"><div class="metric-val">{m["source"].split()[0].title()}</div><div class="metric-lbl">Data Source</div></div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;color:#b0bec5;font-size:0.75rem;padding:0.5rem 0">
  Banking Credit Risk Engine &nbsp;·&nbsp; ML Internship Portfolio Prototype &nbsp;·&nbsp;
  XGBoost + SHAP + FP-Growth &nbsp;·&nbsp; Built with Streamlit
</div>
""", unsafe_allow_html=True)
