"""
data_processor.py
─────────────────
Handles CSV ingestion, validation, cleaning, and feature extraction
for the delivery‑time prediction pipeline.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, List, Optional


# ── Column‑name normalisation map ────────────────────────────────────────────
# Maps common alternative names to canonical internal names.
COLUMN_ALIASES = {
    # distance
    "distance": "distance_km",
    "distance_km": "distance_km",
    "delivery_distance": "distance_km",
    "dist": "distance_km",
    "distance (km)": "distance_km",
    # weight
    "weight": "weight_kg",
    "weight_kg": "weight_kg",
    "package_weight": "weight_kg",
    "parcel_weight": "weight_kg",
    "weight (kg)": "weight_kg",
    # service / type
    "service_type": "service_type",
    "service": "service_type",
    "delivery_type": "service_type",
    "type": "service_type",
    "shipping_type": "service_type",
    # pickup hour
    "pickup_hour": "pickup_hour",
    "hour": "pickup_hour",
    "pickup_time_hour": "pickup_hour",
    "order_hour": "pickup_hour",
    # day of week
    "day_of_week": "day_of_week",
    "weekday": "day_of_week",
    "dow": "day_of_week",
    "order_day": "day_of_week",
    # target — actual delivery duration (minutes)
    "actual_duration": "actual_duration_min",
    "actual_duration_min": "actual_duration_min",
    "delivery_duration": "actual_duration_min",
    "delivery_time": "actual_duration_min",
    "duration": "actual_duration_min",
    "time_taken": "actual_duration_min",
    "time_taken(min)": "actual_duration_min",
    "time_taken (min)": "actual_duration_min",
    "delivery_time_min": "actual_duration_min",
    "actual_time": "actual_duration_min",
    "total_time": "actual_duration_min",
    # order id
    "order_id": "order_id",
    "id": "order_id",
    "delivery_id": "order_id",
    "shipment_id": "order_id",
    # city / region
    "city": "city",
    "region": "region",
    "area": "region",
    "zone": "region",
    # vehicle
    "vehicle_type": "vehicle_type",
    "vehicle": "vehicle_type",
    "transport_mode": "vehicle_type",
    # traffic
    "traffic": "traffic_density",
    "traffic_density": "traffic_density",
    "traffic_level": "traffic_density",
    "road_traffic_density": "traffic_density",
    # weather
    "weather": "weather",
    "weather_conditions": "weather",
    "weather_condition": "weather",
    # rating
    "rating": "rating",
    "delivery_person_rating": "rating",
    "delivery_person_ratings": "rating",
    "rider_rating": "rating",
    # age
    "age": "rider_age",
    "delivery_person_age": "rider_age",
    "rider_age": "rider_age",
    # multiple deliveries
    "multiple_deliveries": "multiple_deliveries",
    "multiple_deliveries_avg": "multiple_deliveries",
    # festival
    "festival": "is_festival",
    "is_festival": "is_festival",
}

# Columns we consider numeric features for modelling
NUMERIC_FEATURES = [
    "distance_km", "weight_kg", "pickup_hour", "day_of_week",
    "rating", "rider_age", "multiple_deliveries",
]
CATEGORICAL_FEATURES = [
    "service_type", "vehicle_type", "traffic_density", "weather",
    "city", "region", "is_festival",
]
TARGET_COLUMN = "actual_duration_min"


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to canonical names using the alias map."""
    renamed = {}
    for col in df.columns:
        key = col.strip().lower().replace("-", "_")
        if key in COLUMN_ALIASES:
            renamed[col] = COLUMN_ALIASES[key]
    return df.rename(columns=renamed)


def load_csv(file_or_path) -> pd.DataFrame:
    """
    Load a CSV from a file path or a file‑like object (e.g. Streamlit UploadedFile).
    Returns raw DataFrame after column normalisation.
    """
    df = pd.read_csv(file_or_path)
    df = normalise_columns(df)
    return df


def dataset_summary(df: pd.DataFrame) -> Dict:
    """Return a summary dict suitable for the dashboard KPI strip."""
    summary = {
        "row_count": len(df),
        "col_count": len(df.columns),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing": df.isnull().sum().to_dict(),
        "total_missing": int(df.isnull().sum().sum()),
        "has_target": TARGET_COLUMN in df.columns,
    }
    if summary["has_target"]:
        target = pd.to_numeric(df[TARGET_COLUMN], errors="coerce")
        summary["avg_duration"] = round(float(target.mean()), 2) if not target.isna().all() else None
        summary["median_duration"] = round(float(target.median()), 2) if not target.isna().all() else None
        summary["min_duration"] = round(float(target.min()), 2) if not target.isna().all() else None
        summary["max_duration"] = round(float(target.max()), 2) if not target.isna().all() else None
    return summary


def detect_features(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Detect which numeric and categorical features are present."""
    present_num = [c for c in NUMERIC_FEATURES if c in df.columns]
    present_cat = [c for c in CATEGORICAL_FEATURES if c in df.columns]
    return {"numeric": present_num, "categorical": present_cat}


def clean_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    Basic cleaning: strip whitespace from strings, coerce numerics,
    drop rows where target is missing.  Returns (cleaned_df, report).
    """
    report = {"rows_before": len(df)}
    cleaned = df.copy()

    # Strip string columns
    str_cols = cleaned.select_dtypes(include="object").columns
    for col in str_cols:
        cleaned[col] = cleaned[col].astype(str).str.strip()
        # Replace common "NaN" strings
        cleaned[col] = cleaned[col].replace(
            ["NaN", "nan", "None", "none", "", "null", "NULL"], np.nan
        )

    # Coerce numeric features
    for col in NUMERIC_FEATURES:
        if col in cleaned.columns:
            cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

    # Coerce target
    if TARGET_COLUMN in cleaned.columns:
        cleaned[TARGET_COLUMN] = pd.to_numeric(cleaned[TARGET_COLUMN], errors="coerce")
        cleaned = cleaned.dropna(subset=[TARGET_COLUMN])

    report["rows_after"] = len(cleaned)
    report["rows_dropped"] = report["rows_before"] - report["rows_after"]
    return cleaned, report


def prepare_features(
    df: pd.DataFrame,
    feature_cols: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Build a feature matrix from the DataFrame.
    Returns (X, used_feature_names).
    Handles one‑hot encoding for categoricals found in the data.
    """
    features = detect_features(df)
    num_cols = features["numeric"]
    cat_cols = features["categorical"]

    if feature_cols is not None:
        num_cols = [c for c in num_cols if c in feature_cols]
        cat_cols = [c for c in cat_cols if c in feature_cols]

    parts = []
    used_names = []

    # Numeric
    for col in num_cols:
        if col in df.columns:
            series = pd.to_numeric(df[col], errors="coerce").fillna(0)
            parts.append(series.rename(col))
            used_names.append(col)

    # Categorical — one‑hot
    for col in cat_cols:
        if col in df.columns:
            dummies = pd.get_dummies(df[col], prefix=col, dummy_na=False)
            parts.append(dummies)
            used_names.extend(dummies.columns.tolist())

    if not parts:
        return pd.DataFrame(), []

    X = pd.concat(parts, axis=1).fillna(0)
    return X, list(X.columns)
