import numpy as np
from sklearn.datasets import make_classification
from src.models.baseline import BaselineModel

def test_predict_proba_range():
    X, y = make_classification(n_samples=200, n_features=10, random_state=42)
    m = BaselineModel()
    m.train(X, y)
    proba = m.predict_proba(X)
    assert proba.shape == (200,)
    assert proba.min() >= 0.0 and proba.max() <= 1.0

def test_predict_binary():
    X, y = make_classification(n_samples=200, n_features=10, random_state=42)
    m = BaselineModel()
    m.train(X, y)
    assert set(m.predict(X)).issubset({0, 1})

def test_threshold_effect():
    X, y = make_classification(n_samples=200, n_features=10, random_state=42)
    m = BaselineModel()
    m.train(X, y)
    assert m.predict(X, threshold=0.9).sum() <= m.predict(X, threshold=0.1).sum()
