"""
page_overview.py
────────────────
Overview dashboard: KPI strip, analytics charts, quick prediction, recent records.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from core.data_processor import dataset_summary, TARGET_COLUMN, NUMERIC_FEATURES
from core.model_engine import predict_single, load_model


def _fmt_duration(minutes):
    """Format minutes into human-readable string."""
    if minutes is None:
        return "—"
    if minutes < 60:
        return f"{minutes:.1f} min"
    hours = minutes / 60
    return f"{hours:.1f} hr"


def _plotly_layout(title="", height=300):
    """Consistent Plotly layout for all charts."""
    return dict(
        title=dict(text=title, font=dict(size=12, color="#6B6B6B", family="Inter")),
        height=height,
        margin=dict(l=44, r=16, t=36, b=44),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FAFAF8",
        font=dict(family="Inter, sans-serif", size=11, color="#1A1A1A"),
        xaxis=dict(gridcolor="#EEECEA", linecolor="#E0DFDC", zerolinecolor="#E0DFDC"),
        yaxis=dict(gridcolor="#EEECEA", linecolor="#E0DFDC", zerolinecolor="#E0DFDC"),
        legend=dict(font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
    )


def render():
    # ── Data availability ─────────────────────────────────────────────
    df = st.session_state.get("dataset")
    has_data = df is not None and not df.empty
    summary = dataset_summary(df) if has_data else None
    model_artifact = load_model()
    has_model = model_artifact is not None

    # ━━ KPI STRIP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.markdown('<div class="section-divider">Key Metrics</div>', unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        val = f"{summary['row_count']:,}" if has_data else "—"
        st.metric("Total Deliveries", val)
    with k2:
        if has_data and summary.get("avg_duration") is not None:
            st.metric("Avg Duration", _fmt_duration(summary["avg_duration"]))
        else:
            st.metric("Avg Duration", "—", help="No duration data available")
    with k3:
        if has_model:
            mae = model_artifact.get("test_metrics", {}).get("mae")
            st.metric("Model MAE", f"{mae:.2f} min" if mae else "—")
        else:
            st.metric("Model MAE", "—", help="Train a model to see this metric")
    with k4:
        if has_model:
            r2 = model_artifact.get("test_metrics", {}).get("r2")
            st.metric("Model R²", f"{r2:.4f}" if r2 else "—")
        else:
            st.metric("Model R²", "—", help="Train a model to see this metric")

    st.markdown("")  # spacer

    # ━━ ANALYTICS CHARTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.markdown('<div class="section-divider">Delivery Analytics</div>', unsafe_allow_html=True)

    if not has_data:
        st.markdown(
            '<div class="empty-box">'
            '<div class="eb-icon">📊</div>'
            '<div class="eb-title">No dataset loaded</div>'
            '<div class="eb-desc">Upload a CSV in the Dataset page to see analytics here.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        chart1, chart2 = st.columns(2)

        with chart1:
            if summary and summary["has_target"]:
                durations = pd.to_numeric(df[TARGET_COLUMN], errors="coerce").dropna()
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=durations, nbinsx=40,
                    marker_color="#E65100", marker_line_color="#BF360C",
                    marker_line_width=0.5, opacity=0.85, name="Deliveries",
                ))
                fig.update_layout(**_plotly_layout("Duration Distribution"))
                fig.update_xaxes(title_text="Duration (min)")
                fig.update_yaxes(title_text="Count")
                st.plotly_chart(fig, use_container_width=True, key="ov_hist")
            else:
                st.info("Duration column not found — cannot show distribution.")

        with chart2:
            last_result = st.session_state.get("last_train_result")
            if has_model and last_result and "y_test" in last_result:
                y_test = last_result["y_test"]
                y_pred = last_result["y_test_pred"]
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=y_test, y=y_pred, mode="markers",
                    marker=dict(color="#E65100", size=4, opacity=0.45),
                    name="Predictions",
                ))
                mn, mx = min(min(y_test), min(y_pred)), max(max(y_test), max(y_pred))
                fig.add_trace(go.Scatter(
                    x=[mn, mx], y=[mn, mx], mode="lines",
                    line=dict(color="#9B9B9B", dash="dash", width=1),
                    name="Perfect",
                ))
                fig.update_layout(**_plotly_layout("Actual vs Predicted"))
                fig.update_xaxes(title_text="Actual (min)")
                fig.update_yaxes(title_text="Predicted (min)")
                st.plotly_chart(fig, use_container_width=True, key="ov_scatter")
            elif summary and summary["has_target"] and "distance_km" in df.columns:
                dist = pd.to_numeric(df["distance_km"], errors="coerce")
                dur = pd.to_numeric(df[TARGET_COLUMN], errors="coerce")
                plot_df = pd.DataFrame({"d": dist, "t": dur}).dropna()
                if len(plot_df) > 0:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=plot_df["d"], y=plot_df["t"], mode="markers",
                        marker=dict(color="#1565C0", size=3, opacity=0.35),
                        name="Deliveries",
                    ))
                    fig.update_layout(**_plotly_layout("Duration vs Distance"))
                    fig.update_xaxes(title_text="Distance (km)")
                    fig.update_yaxes(title_text="Duration (min)")
                    st.plotly_chart(fig, use_container_width=True, key="ov_dist")
                else:
                    st.info("Insufficient data for scatter chart.")
            elif summary and summary["has_target"] and "pickup_hour" in df.columns:
                hour = pd.to_numeric(df["pickup_hour"], errors="coerce")
                dur = pd.to_numeric(df[TARGET_COLUMN], errors="coerce")
                plot_df = pd.DataFrame({"h": hour, "d": dur}).dropna()
                hourly = plot_df.groupby("h")["d"].mean().reset_index()
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=hourly["h"], y=hourly["d"], marker_color="#1565C0",
                ))
                fig.update_layout(**_plotly_layout("Avg Duration by Hour"))
                fig.update_xaxes(title_text="Hour of Day")
                fig.update_yaxes(title_text="Avg Duration (min)")
                st.plotly_chart(fig, use_container_width=True, key="ov_hourly")
            else:
                st.info("Train a model or load distance data to see a second chart.")

    st.markdown("")

    # ━━ QUICK PREDICTION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.markdown('<div class="section-divider">Quick ETA Prediction</div>', unsafe_allow_html=True)

    if has_model:
        feature_names = model_artifact.get("feature_names", [])
        base_features = [f for f in NUMERIC_FEATURES
                         if any(fn == f or fn.startswith(f + "_") for fn in feature_names)]

        feature_defaults = {
            "distance_km":        (10.0, "Distance (km)"),
            "weight_kg":          (2.0, "Weight (kg)"),
            "pickup_hour":        (12, "Pickup Hour (0-23)"),
            "day_of_week":        (1, "Day of Week (0=Mon)"),
            "rating":             (4.5, "Rider Rating"),
            "rider_age":          (28, "Rider Age"),
            "multiple_deliveries": (1, "Multiple Deliveries"),
        }

        ncols = min(len(base_features), 4) if base_features else 1
        cols = st.columns(ncols)
        input_vals = {}
        for i, feat in enumerate(base_features):
            default_val, label = feature_defaults.get(feat, (0, feat))
            with cols[i % ncols]:
                if isinstance(default_val, float):
                    input_vals[feat] = st.number_input(
                        label, value=default_val, step=0.5, key=f"q_{feat}")
                else:
                    input_vals[feat] = st.number_input(
                        label, value=int(default_val), step=1, key=f"q_{feat}")

        if st.button("⚡ Predict ETA", key="quick_pred", type="primary"):
            result = predict_single(model_artifact, input_vals)
            pred = result["predicted_duration_min"]
            st.markdown(
                f'<div class="pred-card">'
                f'<div class="pred-label">Predicted Delivery Duration</div>'
                f'<div class="pred-value">{_fmt_duration(pred)}</div>'
                f'<div class="pred-sub">Model: {result["model_name"]} · '
                f'{len(result["features_used"])} features</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div class="empty-box">'
            '<div class="eb-icon">🔧</div>'
            '<div class="eb-title">No trained model available</div>'
            '<div class="eb-desc">Go to Model Performance to train a model first.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")

    # ━━ RECENT RECORDS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.markdown('<div class="section-divider">Recent Delivery Records</div>', unsafe_allow_html=True)

    if has_data:
        preferred_cols = [
            "order_id", "distance_km", "weight_kg", "service_type",
            "pickup_hour", TARGET_COLUMN, "vehicle_type", "traffic_density",
        ]
        display_cols = [c for c in preferred_cols if c in df.columns]
        if not display_cols:
            display_cols = list(df.columns[:8])

        recent = df[display_cols].tail(20).reset_index(drop=True)
        st.dataframe(recent, use_container_width=True, height=320)
        st.caption(f"Showing last {len(recent)} of {len(df):,} records")
    else:
        st.markdown(
            '<div class="empty-box">'
            '<div class="eb-icon">📋</div>'
            '<div class="eb-title">No records to display</div>'
            '<div class="eb-desc">Upload a CSV file in the Dataset page.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
