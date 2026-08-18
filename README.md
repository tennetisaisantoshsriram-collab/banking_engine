# Banking Credit Default Risk & Cross-Sell Engine

An end-to-end machine learning system that predicts loan default risk and recommends cross-sell banking products to low-risk customers.

Built as an internship portfolio project demonstrating full ML engineering: data pipeline, model comparison, explainability, recommendation engine, and interactive UI.

---

## What It Does

| Module | Description |
|--------|-------------|
| **Credit Risk Predictor** | Predicts probability a loan applicant will default (0–100%) |
| **Model Comparison** | Logistic Regression baseline vs XGBoost production model |
| **Explainability** | SHAP values show which features drive each prediction |
| **Cross-Sell Engine** | Routes low-risk customers into personalised product recommendations |
| **Association Rules** | FP-Growth mines co-occurrence patterns for product boosting |

---

## Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/tennetisaisantoshsriram-collab/banking_engine.git
cd banking_engine
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Get the Dataset
Download `credit_risk_dataset.csv` from Kaggle:
> Search: **"Credit Risk Dataset laotse"**

Place it in the `data/` folder:
```
data/credit_risk_dataset.csv
```

### 3. Run the Notebook
Open `banking_credit_engine.ipynb` in Jupyter and run all cells top to bottom.

```bash
jupyter notebook banking_credit_engine.ipynb
```

---

## Project Structure

```
banking_engine/
├── banking_credit_engine.ipynb   # Main notebook — complete project
├── requirements.txt
├── data/
│   └── README.txt                # Dataset download instructions
├── src/
│   ├── data_loader.py            # CSV loading, schema validation, stratified split
│   ├── feature_engineering.py   # Imputation, encoding, scaling, derived features
│   ├── models/
│   │   └── baseline.py          # Logistic Regression model
│   └── recommender/
│       └── __init__.py
├── report/
└── tests/
    ├── test_data_loader.py
    ├── test_baseline.py
    └── test_feature_engineering.py
```

---

## Dataset

**Source:** Kaggle Credit Risk Dataset (~32,000 rows)

| Column | Type | Role |
|--------|------|------|
| `person_age` | numeric | Feature |
| `person_income` | numeric | Feature |
| `person_emp_length` | numeric | Feature |
| `loan_amnt` | numeric | Feature |
| `loan_int_rate` | numeric | Feature |
| `loan_percent_income` | numeric | Feature |
| `loan_grade` | categorical (A–G) | Feature |
| `loan_intent` | categorical | Feature |
| `home_ownership` | categorical | Feature |
| `cb_person_default_on_file` | binary (Y/N) | Feature |
| `loan_status` | binary (0/1) | **Target** (1 = default) |

Class distribution: ~22% default, ~78% no-default.

---

## Models

### Logistic Regression (Baseline)
- Solver: `lbfgs`, `class_weight='balanced'`
- Purpose: interpretable baseline, establishes minimum acceptable performance

### XGBoost (Production)
- Hyperparameter tuning: `RandomizedSearchCV` (20 iter, 5-fold CV)
- Class imbalance: `scale_pos_weight = count(0) / count(1)`
- Threshold: selected by maximising F1 on validation set (not default 0.5)
- Explainability: SHAP `TreeExplainer`

---

## Cross-Sell Engine

Applied only to customers with predicted default probability **< 30%**.

### Step 1 — Rule-Based Segmentation

| Segment | Criteria | Products |
|---------|----------|----------|
| Young Starter | Age < 30, Income < 40K | Student Loan, Secured Credit Card, Savings Account |
| Rising Professional | Age 30–45, Income 40K–80K | Personal Loan, Travel Credit Card, Mutual Funds |
| Established Earner | Age 30–55, Income > 80K | Home Loan, Premium Credit Card, Investment Portfolio |
| Senior Stable | Age > 55 | Fixed Deposits, Insurance, Retirement Fund |

### Step 2 — FP-Growth Association Rules
- Synthetic transaction table built from `loan_intent` + `loan_grade` → product baskets
- Parameters: `min_support=0.05`, `min_confidence=0.4`
- Rules ranked by lift and used to boost segment recommendations

---

## Results

| Metric | Logistic Regression | XGBoost |
|--------|--------------------|---------| 
| ROC-AUC | — | — |
| Precision | — | — |
| Recall | — | — |
| F1 Score | — | — |
| KS Statistic | — | — |

*Values populate when you run the notebook.*

---

## Run Tests

```bash
pytest tests/ -v
```

---

## Tech Stack

`pandas` · `numpy` · `scikit-learn` · `xgboost` · `shap` · `mlxtend` · `matplotlib` · `seaborn` · `reportlab`

---

## Business Impact

For a bank processing 10,000 applications/month at avg loan $15,000:
- **Default detection** catches the majority of likely defaulters before approval
- **Cross-sell routing** targets ~7,800 eligible low-risk customers/month — even 5% conversion represents meaningful incremental revenue

---

*Internship Portfolio Project — Banking Credit Default Risk & Cross-Sell Engine*
