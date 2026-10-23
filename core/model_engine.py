"""
model_engine.py
───────────────
Model training, evaluation, inference, and persistence for the
delivery‑time prediction pipeline.
"""

import os
import time
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any

from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

from core.data_processor import (
    TARGET_COLUMN,
    clean_dataset,
    prepare_features,
)


# ── Available model registry ─────────────────────────────────────────────────

def _get_model_registry() -> Dict[str, Any]:
    registry = {
        "Linear Regression": LinearRegression,
        "Decision Tree": DecisionTreeRegressor,
        "Random Forest": RandomForestRegressor,
        "Gradient Boosting": GradientBoostingRegressor,
    }
    if HAS_XGBOOST:
        registry["XGBoost"] = XGBRegressor
    return registry


MODEL_REGISTRY = _get_model_registry()

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")


def _ensure_artifacts_dir():
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)


# ── Training ──────────────────────────────────────────────────────────────────

def train_model(
    df: pd.DataFrame,
    model_name: str = "Random Forest",
    test_size: float = 0.2,
    random_state: int = 42,
) -> Dict:
    """
    Train a regression model on the provided DataFrame.
    Returns a result dict with metrics, model object, and metadata.
    """
    if model_name not in MODEL_REGISTRY:
        return {"success": False, "error": f"Unknown model: {model_name}"}

    if TARGET_COLUMN not in df.columns:
        return {"success": False, "error": f"Target column '{TARGET_COLUMN}' not found in dataset."}

    # Clean
    cleaned, clean_report = clean_dataset(df)
    if len(cleaned) < 10:
        return {"success": False, "error": f"Too few valid rows after cleaning ({len(cleaned)})."}

    # Features
    X, feature_names = prepare_features(cleaned)
    if X.empty:
        return {"success": False, "error": "No usable features detected in the dataset."}

    y = cleaned[TARGET_COLUMN].values

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # Train
    ModelClass = MODEL_REGISTRY[model_name]
    t0 = time.time()
    model = ModelClass()
    model.fit(X_train, y_train)
    train_time = round(time.time() - t0, 3)

    # Evaluate — train set
    y_train_pred = model.predict(X_train)
    train_metrics = {
        "mae": round(float(mean_absolute_error(y_train, y_train_pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_train, y_train_pred))), 4),
        "r2": round(float(r2_score(y_train, y_train_pred)), 4),
    }

    # Evaluate — test set
    y_test_pred = model.predict(X_test)
    test_metrics = {
        "mae": round(float(mean_absolute_error(y_test, y_test_pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_test_pred))), 4),
        "r2": round(float(r2_score(y_test, y_test_pred)), 4),
    }

    # Feature importance
    importance = _extract_importance(model, feature_names)

    result = {
        "success": True,
        "model_name": model_name,
        "model": model,
        "feature_names": feature_names,
        "train_metrics": train_metrics,
        "test_metrics": test_metrics,
        "train_time_sec": train_time,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "y_test": y_test.tolist(),
        "y_test_pred": y_test_pred.tolist(),
        "y_train": y_train.tolist(),
        "y_train_pred": y_train_pred.tolist(),
        "clean_report": clean_report,
        "importance": importance,
    }
    return result


def _extract_importance(model, feature_names: List[str]) -> Optional[Dict[str, float]]:
    """Try to extract feature importances from the model."""
    if hasattr(model, "feature_importances_"):
        imp = model.feature_importances_
        return {name: round(float(v), 4) for name, v in zip(feature_names, imp)}
    if hasattr(model, "coef_"):
        coef = np.abs(model.coef_)
        return {name: round(float(v), 4) for name, v in zip(feature_names, coef)}
    return None


# ── Persistence ───────────────────────────────────────────────────────────────

def save_model(result: Dict, tag: str = "latest") -> str:
    """Save model + metadata to artifacts/."""
    _ensure_artifacts_dir()
    path = os.path.join(ARTIFACTS_DIR, f"model_{tag}.joblib")
    payload = {
        "model": result["model"],
        "model_name": result["model_name"],
        "feature_names": result["feature_names"],
        "test_metrics": result["test_metrics"],
        "train_metrics": result["train_metrics"],
    }
    joblib.dump(payload, path)
    return path


def load_model(tag: str = "latest") -> Optional[Dict]:
    """Load a persisted model artifact."""
    _ensure_artifacts_dir()
    path = os.path.join(ARTIFACTS_DIR, f"model_{tag}.joblib")
    if not os.path.exists(path):
        return None
    return joblib.load(path)


def list_saved_models() -> List[str]:
    """Return tags of saved models."""
    _ensure_artifacts_dir()
    files = os.listdir(ARTIFACTS_DIR)
    tags = []
    for f in files:
        if f.startswith("model_") and f.endswith(".joblib"):
            tag = f[len("model_"):-len(".joblib")]
            tags.append(tag)
    return tags


# ── Inference ─────────────────────────────────────────────────────────────────

def predict_single(
    model_artifact: Dict,
    input_dict: Dict[str, Any],
) -> Dict:
    """
    Run a single prediction given a model artifact and an input dict
    of feature values.  Returns predicted duration in minutes.
    """
    model = model_artifact["model"]
    feature_names = model_artifact["feature_names"]

    # Build a single‑row DataFrame aligned to the trained feature set
    row = {}
    for fname in feature_names:
        if fname in input_dict:
            row[fname] = input_dict[fname]
        else:
            row[fname] = 0  # default for missing one-hot / optional features

    X = pd.DataFrame([row])[feature_names]
    pred = model.predict(X)[0]

    return {
        "predicted_duration_min": round(float(pred), 2),
        "model_name": model_artifact.get("model_name", "Unknown"),
        "features_used": feature_names,
    }


# ── Batch evaluation helpers ─────────────────────────────────────────────────

def evaluate_all_models(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> List[Dict]:
    """Train and evaluate every registered model. Returns list of result dicts."""
    results = []
    for name in MODEL_REGISTRY:
        res = train_model(df, model_name=name, test_size=test_size, random_state=random_state)
        results.append(res)
    return results
