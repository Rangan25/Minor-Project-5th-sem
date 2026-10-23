"""
page_model.py
─────────────
Model training, evaluation, comparison, and performance visualisation.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from core.data_processor import TARGET_COLUMN, detect_features, dataset_summary
from core.model_engine import (
    MODEL_REGISTRY, train_model, evaluate_all_models,
    save_model, load_model,
)


def _layout(title="", height=320):
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
    df = st.session_state.get("dataset")
    has_data = df is not None and not df.empty

    if not has_data:
        st.warning("**No dataset loaded.** Upload a CSV in the **Dataset** page first.")
        st.markdown(
            '<div class="empty-box">'
            '<div class="eb-icon">📊</div>'
            '<div class="eb-title">No data for training</div>'
            '<div class="eb-desc">Load a dataset with a delivery duration column first.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    summary = dataset_summary(df)
    if not summary["has_target"]:
        st.error(
            f"Target column `{TARGET_COLUMN}` not found. The dataset needs a delivery "
            f"duration column (e.g. `actual_duration`, `delivery_time`, `time_taken`)."
        )
        return

    features = detect_features(df)
    st.caption(
        f"Dataset: {summary['row_count']:,} rows · "
        f"Features: {len(features['numeric'])} numeric, {len(features['categorical'])} categorical · "
        f"Target: `{TARGET_COLUMN}`"
    )

    # ── Training controls ─────────────────────────────────────────────
    st.markdown('<div class="section-divider">Train & Evaluate</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        names = list(MODEL_REGISTRY.keys())
        sel = st.selectbox("Select model", names,
                           index=names.index("Random Forest") if "Random Forest" in names else 0)
    with c2:
        test_size = st.slider("Test split", 0.1, 0.4, 0.2, 0.05, key="ts")
    with c3:
        st.markdown("")  # vertical spacer
        train_one = st.button(f"▶ Train {sel}", type="primary", key="train1")

    train_all = st.button("▶▶ Train All Models (Compare)", key="trainall")

    # ── Single train ──────────────────────────────────────────────────
    if train_one:
        with st.spinner(f"Training {sel}..."):
            result = train_model(df, model_name=sel, test_size=test_size)
        if not result["success"]:
            st.error(f"Training failed: {result['error']}")
        else:
            st.session_state["last_train_result"] = result
            st.session_state["all_results"] = [result]
            save_model(result)
            st.success(
                f"**{sel}** trained in {result['train_time_sec']}s — "
                f"MAE: {result['test_metrics']['mae']:.2f}, R²: {result['test_metrics']['r2']:.4f}"
            )
            st.rerun()

    # ── Train all ─────────────────────────────────────────────────────
    if train_all:
        with st.spinner("Training all models..."):
            results = evaluate_all_models(df, test_size=test_size)
        ok = [r for r in results if r["success"]]
        fail = [r for r in results if not r["success"]]
        if ok:
            best = min(ok, key=lambda r: r["test_metrics"]["mae"])
            save_model(best)
            st.session_state["last_train_result"] = best
            st.session_state["all_results"] = ok
            st.success(f"Trained {len(ok)} models. Best: **{best['model_name']}** (MAE: {best['test_metrics']['mae']:.2f})")
        for f in fail:
            st.error(f"Failed: {f.get('model_name', '?')} — {f.get('error', '?')}")
        if ok:
            st.rerun()

    # ── Display results ───────────────────────────────────────────────
    all_results = st.session_state.get("all_results", [])
    last = st.session_state.get("last_train_result")

    if not all_results and not last:
        saved = load_model()
        if saved:
            st.info(f"Saved model: **{saved.get('model_name', '?')}**. Train again to see full evaluation.")
            s1, s2, s3 = st.columns(3)
            with s1:
                st.metric("Model", saved.get("model_name", "—"))
            with s2:
                st.metric("Test MAE", f"{saved.get('test_metrics',{}).get('mae','—')}")
            with s3:
                st.metric("Test R²", f"{saved.get('test_metrics',{}).get('r2','—')}")
        else:
            st.markdown(
                '<div class="empty-box">'
                '<div class="eb-icon">🧪</div>'
                '<div class="eb-title">No results yet</div>'
                '<div class="eb-desc">Select a model and click Train to see metrics.</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        return

    # ── Comparison table ──────────────────────────────────────────────
    if len(all_results) > 1:
        st.markdown('<div class="section-divider">Model Comparison</div>', unsafe_allow_html=True)
        comp = []
        for r in all_results:
            comp.append({
                "Model": r["model_name"],
                "Train MAE": r["train_metrics"]["mae"],
                "Test MAE": r["test_metrics"]["mae"],
                "Train RMSE": r["train_metrics"]["rmse"],
                "Test RMSE": r["test_metrics"]["rmse"],
                "Train R²": r["train_metrics"]["r2"],
                "Test R²": r["test_metrics"]["r2"],
                "Time (s)": r["train_time_sec"],
            })
        comp_df = pd.DataFrame(comp).sort_values("Test MAE")
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

        # Bar chart
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Test MAE", x=comp_df["Model"].tolist(),
                             y=comp_df["Test MAE"].tolist(), marker_color="#E65100"))
        fig.add_trace(go.Bar(name="Train MAE", x=comp_df["Model"].tolist(),
                             y=comp_df["Train MAE"].tolist(), marker_color="#FFCC80"))
        fig.update_layout(**_layout("MAE Comparison", 280))
        fig.update_layout(barmode="group")
        st.plotly_chart(fig, use_container_width=True, key="comp_bar")

    # ── Detailed result ───────────────────────────────────────────────
    result = last or (all_results[0] if all_results else None)
    if not result:
        return

    st.markdown(f'<div class="section-divider">Detailed Results — {result["model_name"]}</div>', unsafe_allow_html=True)

    d1, d2, d3, d4, d5 = st.columns(5)
    with d1:
        st.metric("Model", result["model_name"])
    with d2:
        st.metric("Test MAE", f"{result['test_metrics']['mae']:.2f} min")
    with d3:
        st.metric("Test RMSE", f"{result['test_metrics']['rmse']:.2f} min")
    with d4:
        st.metric("Test R²", f"{result['test_metrics']['r2']:.4f}")
    with d5:
        st.metric("Train Time", f"{result['train_time_sec']}s")

    st.markdown("")

    # Charts
    ch1, ch2 = st.columns(2)

    with ch1:
        y_test = result["y_test"]
        y_pred = result["y_test_pred"]
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=y_test, y=y_pred, mode="markers",
                                  marker=dict(color="#E65100", size=4, opacity=0.45),
                                  name="Predictions"))
        mn, mx = min(min(y_test), min(y_pred)), max(max(y_test), max(y_pred))
        fig1.add_trace(go.Scatter(x=[mn, mx], y=[mn, mx], mode="lines",
                                  line=dict(color="#9B9B9B", dash="dash", width=1),
                                  name="Perfect"))
        fig1.update_layout(**_layout("Actual vs Predicted (Test)", 320))
        fig1.update_xaxes(title_text="Actual (min)")
        fig1.update_yaxes(title_text="Predicted (min)")
        st.plotly_chart(fig1, use_container_width=True, key="ap_scatter")

    with ch2:
        residuals = [p - a for a, p in zip(y_test, y_pred)]
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(x=residuals, nbinsx=40,
                                    marker_color="#1565C0", marker_line_color="#0D47A1",
                                    marker_line_width=0.5, opacity=0.8, name="Residuals"))
        fig2.add_vline(x=0, line_dash="dash", line_color="#9B9B9B", line_width=1)
        fig2.update_layout(**_layout("Residual Distribution (Test)", 320))
        fig2.update_xaxes(title_text="Error (min)")
        fig2.update_yaxes(title_text="Count")
        st.plotly_chart(fig2, use_container_width=True, key="res_hist")

    # Feature importance
    importance = result.get("importance")
    if importance:
        st.markdown('<div class="section-divider">Feature Importance</div>', unsafe_allow_html=True)
        imp_df = pd.DataFrame(
            sorted(importance.items(), key=lambda x: x[1], reverse=True)[:15],
            columns=["Feature", "Importance"],
        )
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            y=imp_df["Feature"].tolist()[::-1],
            x=imp_df["Importance"].tolist()[::-1],
            orientation="h", marker_color="#E65100",
        ))
        fig3.update_layout(**_layout("Top Features", max(280, len(imp_df) * 24)))
        st.plotly_chart(fig3, use_container_width=True, key="feat_imp")

    # Train vs Test detail
    with st.expander("Training vs Validation Metrics"):
        met_df = pd.DataFrame({
            "Metric": ["MAE", "RMSE", "R²"],
            "Training": [result["train_metrics"]["mae"], result["train_metrics"]["rmse"], result["train_metrics"]["r2"]],
            "Test":     [result["test_metrics"]["mae"],  result["test_metrics"]["rmse"],  result["test_metrics"]["r2"]],
        })
        met_df["Gap"] = met_df["Training"] - met_df["Test"]
        st.dataframe(met_df, use_container_width=True, hide_index=True)

        gap_r2 = result["train_metrics"]["r2"] - result["test_metrics"]["r2"]
        if gap_r2 > 0.15:
            st.warning(f"Potential overfitting: Train R² is {gap_r2:.3f} higher than Test R².")
        elif result["test_metrics"]["r2"] < 0.3:
            st.info("Low R² — the model explains limited variance. Consider more features or data.")
