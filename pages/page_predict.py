"""
page_predict.py
───────────────
Dedicated ETA prediction form with validation, results panel, and comparison.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from core.data_processor import NUMERIC_FEATURES, CATEGORICAL_FEATURES, TARGET_COLUMN
from core.model_engine import load_model, predict_single


def _fmt_duration(minutes):
    if minutes is None:
        return "—"
    if minutes < 60:
        return f"{minutes:.1f} min"
    h = int(minutes // 60)
    m = int(minutes % 60)
    return f"{h}h {m}m"


def render():
    model_artifact = load_model()
    has_model = model_artifact is not None
    df = st.session_state.get("dataset")
    has_data = df is not None and not df.empty

    if not has_model:
        st.warning(
            "**No trained model available.** "
            "Go to **Model Performance** to train a model, then return here."
        )
        st.markdown(
            '<div class="empty-box">'
            '<div class="eb-icon">🔧</div>'
            '<div class="eb-title">Train a model first</div>'
            '<div class="eb-desc">A trained model is required to make predictions.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Model info strip ──────────────────────────────────────────────
    feature_names = model_artifact.get("feature_names", [])
    model_name = model_artifact.get("model_name", "Unknown")
    test_metrics = model_artifact.get("test_metrics", {})

    ic1, ic2, ic3 = st.columns(3)
    with ic1:
        st.markdown(
            f'<span class="st-pill st-pill-green">MODEL READY</span> &nbsp; '
            f'<strong>{model_name}</strong>',
            unsafe_allow_html=True,
        )
    with ic2:
        mae = test_metrics.get("mae")
        st.caption(f"Test MAE: **{mae:.2f} min**" if mae else "Test MAE: —")
    with ic3:
        r2 = test_metrics.get("r2")
        st.caption(f"Test R²: **{r2:.4f}**" if r2 else "Test R²: —")

    st.markdown("---")

    # ── Determine input features ──────────────────────────────────────
    base_numeric = [f for f in NUMERIC_FEATURES
                    if any(fn == f or fn.startswith(f) for fn in feature_names)]
    base_categorical = []
    if has_data:
        for f in CATEGORICAL_FEATURES:
            matching = [fn for fn in feature_names if fn.startswith(f + "_")]
            if matching:
                base_categorical.append(f)

    # ── Prediction form ───────────────────────────────────────────────
    st.markdown('<div class="section-divider">Delivery Parameters</div>', unsafe_allow_html=True)

    with st.form("predict_form", clear_on_submit=False):
        input_vals = {}
        errors = []

        feature_config = {
            "distance_km":        {"label": "Distance (km)",       "default": 10.0, "step": 0.5, "min": 0.1,  "max": 500.0, "type": float},
            "weight_kg":          {"label": "Package Weight (kg)", "default": 2.0,  "step": 0.5, "min": 0.01, "max": 200.0, "type": float},
            "pickup_hour":        {"label": "Pickup Hour (0-23)",  "default": 12,   "step": 1,   "min": 0,    "max": 23,    "type": int},
            "day_of_week":        {"label": "Day of Week (0=Mon)", "default": 1,    "step": 1,   "min": 0,    "max": 6,     "type": int},
            "rating":             {"label": "Rider Rating (1-5)",  "default": 4.5,  "step": 0.1, "min": 1.0,  "max": 5.0,   "type": float},
            "rider_age":          {"label": "Rider Age",           "default": 28,   "step": 1,   "min": 18,   "max": 60,    "type": int},
            "multiple_deliveries":{"label": "Multiple Deliveries", "default": 1,    "step": 1,   "min": 0,    "max": 10,    "type": int},
        }

        # Numeric inputs
        ncols = min(len(base_numeric), 3) if base_numeric else 1
        num_cols = st.columns(ncols)
        for i, feat in enumerate(base_numeric):
            cfg = feature_config.get(feat, {"label": feat, "default": 0, "step": 1, "min": 0, "max": 1000, "type": float})
            with num_cols[i % ncols]:
                if cfg["type"] == float:
                    val = st.number_input(cfg["label"], value=cfg["default"],
                                          step=cfg["step"], min_value=cfg["min"],
                                          max_value=cfg["max"], key=f"p_{feat}")
                else:
                    val = st.number_input(cfg["label"], value=int(cfg["default"]),
                                          step=int(cfg["step"]), min_value=int(cfg["min"]),
                                          max_value=int(cfg["max"]), key=f"p_{feat}")
                input_vals[feat] = val

        # Categorical inputs
        if base_categorical and has_data:
            st.markdown('<div class="section-divider">Categorical Features</div>', unsafe_allow_html=True)
            cat_ncols = min(len(base_categorical), 3)
            cat_cols = st.columns(cat_ncols)
            for i, feat in enumerate(base_categorical):
                with cat_cols[i % cat_ncols]:
                    unique_vals = df[feat].dropna().unique().tolist() if feat in df.columns else []
                    unique_vals = sorted([str(v).strip() for v in unique_vals if str(v).strip()])
                    if unique_vals:
                        selected = st.selectbox(
                            feat.replace("_", " ").title(), unique_vals, key=f"p_cat_{feat}")
                        for fn in feature_names:
                            if fn.startswith(feat + "_"):
                                input_vals[fn] = 1.0 if fn == f"{feat}_{selected}" else 0.0

        # Timestamp
        st.markdown('<div class="section-divider">Pickup Timestamp (Optional)</div>', unsafe_allow_html=True)
        ts1, ts2 = st.columns(2)
        with ts1:
            pickup_date = st.date_input("Pickup Date", value=datetime.now().date(), key="p_date")
        with ts2:
            pickup_time = st.time_input("Pickup Time", value=datetime.now().time(), key="p_time")

        actual_duration = st.number_input(
            "Actual Duration (min) — leave 0 to skip comparison",
            value=0.0, step=1.0, min_value=0.0, key="p_actual",
        )

        sub1, sub2 = st.columns(2)
        with sub1:
            submitted = st.form_submit_button("⚡ Predict ETA", type="primary")
        with sub2:
            reset = st.form_submit_button("↺ Reset")

    if reset:
        st.rerun()

    # ── Results ───────────────────────────────────────────────────────
    if submitted:
        if "distance_km" in input_vals and input_vals["distance_km"] <= 0:
            errors.append("Distance must be > 0.")
        if "weight_kg" in input_vals and input_vals["weight_kg"] <= 0:
            errors.append("Weight must be > 0.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            with st.spinner("Running prediction..."):
                result = predict_single(model_artifact, input_vals)

            pred_min = result["predicted_duration_min"]
            pickup_dt = datetime.combine(pickup_date, pickup_time)
            eta = pickup_dt + timedelta(minutes=pred_min)

            st.markdown('<div class="section-divider">Prediction Results</div>', unsafe_allow_html=True)

            r1, r2c, r3 = st.columns(3)
            with r1:
                st.markdown(
                    f'<div class="pred-card">'
                    f'<div class="pred-label">Predicted Duration</div>'
                    f'<div class="pred-value">{_fmt_duration(pred_min)}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with r2c:
                st.metric("Estimated Arrival", eta.strftime("%H:%M"), delta=eta.strftime("%d %b %Y"))
            with r3:
                if actual_duration > 0:
                    error_min = pred_min - actual_duration
                    error_pct = (error_min / actual_duration) * 100
                    st.metric("Actual Duration", _fmt_duration(actual_duration))
                    badge = "st-pill-green" if abs(error_pct) < 15 else "st-pill-orange" if abs(error_pct) < 30 else "st-pill-red"
                    st.markdown(
                        f'Error: <span class="st-pill {badge}">'
                        f'{"+" if error_min > 0 else ""}{error_min:.1f} min ({error_pct:+.1f}%)</span>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.metric("Model", result["model_name"])
                    st.caption(f"{len(result['features_used'])} features used")
