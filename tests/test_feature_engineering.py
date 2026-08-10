import pandas as pd
import pytest
from src.feature_engineering import FeatureEngineer

@pytest.fixture
def raw_X():
    return pd.DataFrame({
        'person_age': [25, 35, 45],
        'person_income': [30000, 60000, 90000],
        'person_emp_length': [2.0, None, 10.0],
        'loan_amnt': [5000, 15000, 25000],
        'loan_int_rate': [12.5, None, 7.5],
        'loan_percent_income': [0.17, 0.25, 0.28],
        'loan_grade': ['C', 'B', 'A'],
        'loan_intent': ['EDUCATION', 'PERSONAL', 'HOMEIMPROVEMENT'],
        'home_ownership': ['RENT', 'MORTGAGE', 'OWN'],
        'cb_person_default_on_file': ['N', 'Y', 'N'],
    })

def test_fit_transform_creates_debt_to_income(raw_X):
    fe = FeatureEngineer()
    out = fe.fit_transform(raw_X)
    assert 'debt_to_income' in out.columns

def test_fit_transform_no_nulls(raw_X):
    fe = FeatureEngineer()
    out = fe.fit_transform(raw_X)
    assert out.isnull().sum().sum() == 0

def test_loan_grade_ordinal(raw_X):
    fe = FeatureEngineer()
    out = fe.fit_transform(raw_X)
    assert out['loan_grade'].max() <= 7
    assert out['loan_grade'].min() >= 1

def test_cb_default_binary(raw_X):
    fe = FeatureEngineer()
    out = fe.fit_transform(raw_X)
    assert set(out['cb_person_default_on_file'].unique()).issubset({0, 1})

def test_transform_aligns_columns(raw_X):
    fe = FeatureEngineer()
    fe.fit_transform(raw_X)
    out = fe.transform(raw_X)
    assert list(out.columns) == fe.encoded_columns
