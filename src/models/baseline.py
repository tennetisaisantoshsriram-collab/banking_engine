import numpy as np
from sklearn.linear_model import LogisticRegression

class BaselineModel:
    def __init__(self):
        self.model = LogisticRegression(
            solver='lbfgs', max_iter=1000, class_weight='balanced', random_state=42
        )

    def train(self, X, y) -> None:
        self.model.fit(X, y)

    def predict_proba(self, X) -> np.ndarray:
        return self.model.predict_proba(X)[:, 1]

    def predict(self, X, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X) >= threshold).astype(int)
