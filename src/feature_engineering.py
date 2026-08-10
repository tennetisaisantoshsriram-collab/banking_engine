import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

GRADE_MAP = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7}
NUMERIC_COLS = [
    'person_age', 'person_income', 'person_emp_length',
    'loan_amnt', 'loan_int_rate', 'loan_percent_income', 'debt_to_income'
]
MEDIAN_IMPUTE_COLS = ['loan_int_rate', 'person_emp_length']

class FeatureEngineer:
    def __init__(self):
        self.scaler = StandardScaler()
        self.medians: dict = {}
        self.encoded_columns: list = []

    def _base_transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        for col in MEDIAN_IMPUTE_COLS:
            X[col] = X[col].fillna(self.medians[col])
        X['debt_to_income'] = (X['loan_amnt'] / X['person_income'].replace(0, np.nan)).fillna(0)
        X['loan_grade'] = X['loan_grade'].map(GRADE_MAP)
        X['cb_person_default_on_file'] = (X['cb_person_default_on_file'] == 'Y').astype(int)
        X = pd.get_dummies(X, columns=['loan_intent', 'home_ownership'])
        return X

    def fit_transform(self, X: pd.DataFrame) -> pd.DataFrame:
        for col in MEDIAN_IMPUTE_COLS:
            self.medians[col] = X[col].median()
        X_out = self._base_transform(X)
        self.encoded_columns = X_out.columns.tolist()
        return X_out

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X_out = self._base_transform(X)
        for col in self.encoded_columns:
            if col not in X_out.columns:
                X_out[col] = 0
        return X_out[self.encoded_columns]

    def fit_transform_scaled(self, X: pd.DataFrame) -> pd.DataFrame:
        X_enc = self.fit_transform(X)
        X_scaled = X_enc.copy()
        present = [c for c in NUMERIC_COLS if c in X_scaled.columns]
        X_scaled[present] = self.scaler.fit_transform(X_enc[present])
        return X_scaled

    def transform_scaled(self, X: pd.DataFrame) -> pd.DataFrame:
        X_enc = self.transform(X)
        X_scaled = X_enc.copy()
        present = [c for c in NUMERIC_COLS if c in X_scaled.columns]
        X_scaled[present] = self.scaler.transform(X_enc[present])
        return X_scaled
