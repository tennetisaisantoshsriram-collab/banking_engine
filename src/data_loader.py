import pandas as pd
from sklearn.model_selection import train_test_split

REQUIRED_COLUMNS = [
    'person_age', 'person_income', 'person_emp_length',
    'loan_amnt', 'loan_int_rate', 'loan_percent_income',
    'loan_grade', 'loan_intent', 'home_ownership',
    'cb_person_default_on_file', 'loan_status'
]

def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    return df[REQUIRED_COLUMNS].copy()

def split_data(df: pd.DataFrame, val_size: float = 0.15, test_size: float = 0.15, random_state: int = 42):
    X = df.drop(columns=['loan_status'])
    y = df['loan_status']

    # First split: train vs (val+test)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=(val_size + test_size), stratify=y, random_state=random_state
    )

    # Second split: val vs test from temp set
    # Only stratify if we have enough samples in both classes
    val_ratio = val_size / (val_size + test_size)
    try:
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=(1 - val_ratio), stratify=y_temp, random_state=random_state
        )
    except ValueError:
        # Fall back to non-stratified split if stratification fails
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=(1 - val_ratio), stratify=None, random_state=random_state
        )

    return X_train, X_val, X_test, y_train, y_val, y_test
