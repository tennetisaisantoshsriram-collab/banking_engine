import pandas as pd
import pytest
from src.data_loader import load_data, split_data

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        'person_age': [25, 35, 45, 30, 55, 28, 40],
        'person_income': [30000, 60000, 90000, 50000, 70000, 25000, 85000],
        'person_emp_length': [2.0, 5.0, 10.0, 3.0, 20.0, 1.0, 8.0],
        'loan_amnt': [5000, 15000, 25000, 10000, 20000, 4000, 30000],
        'loan_int_rate': [12.5, 8.0, 7.5, 10.0, 9.5, 14.0, 7.0],
        'loan_percent_income': [0.17, 0.25, 0.28, 0.20, 0.29, 0.16, 0.35],
        'loan_grade': ['C', 'B', 'A', 'B', 'A', 'D', 'A'],
        'loan_intent': ['EDUCATION', 'PERSONAL', 'HOMEIMPROVEMENT', 'MEDICAL', 'VENTURE', 'EDUCATION', 'DEBTCONSOLIDATION'],
        'home_ownership': ['RENT', 'MORTGAGE', 'OWN', 'RENT', 'MORTGAGE', 'RENT', 'OWN'],
        'cb_person_default_on_file': ['N', 'N', 'N', 'Y', 'N', 'Y', 'N'],
        'loan_status': [1, 0, 0, 1, 0, 1, 0],
    })

def test_load_data_returns_correct_columns(tmp_path, sample_df):
    path = tmp_path / "test.csv"
    sample_df.to_csv(path, index=False)
    df = load_data(str(path))
    assert 'loan_status' in df.columns
    assert df.shape[1] == 11

def test_load_data_raises_on_missing_column(tmp_path, sample_df):
    bad_df = sample_df.drop(columns=['loan_status'])
    path = tmp_path / "bad.csv"
    bad_df.to_csv(path, index=False)
    with pytest.raises(ValueError, match="Missing columns"):
        load_data(str(path))

def test_split_data_proportions(sample_df):
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(sample_df)
    total = len(X_train) + len(X_val) + len(X_test)
    assert total == len(sample_df)
    assert len(X_train) > len(X_val)
