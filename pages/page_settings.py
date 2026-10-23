"""
page_settings.py
────────────────
Application settings: environment info, model artifacts, reset actions.
"""

import os
import glob
import streamlit as st

from core.model_engine import ARTIFACTS_DIR, list_saved_models, load_model, MODEL_REGISTRY


def render():
    # ── Environment ───────────────────────────────────────────────────
    st.markdown('<div class="section-divider">Environment</div>', unsafe_allow_html=True)

    e1, e2, e3 = st.columns(3)
    with e1:
        st.metric("Mode", "LOCAL")
    with e2:
        st.metric("Artifacts Path", os.path.basename(ARTIFACTS_DIR) or "artifacts")
    with e3:
        st.metric("Available Models", str(len(MODEL_REGISTRY)))

    # ── Registered model types ────────────────────────────────────────
    st.markdown('<div class="section-divider">Available Model Types</div>', unsafe_allow_html=True)
    for name in MODEL_REGISTRY:
        st.markdown(f"- `{name}`")

    # ── Saved artifacts ───────────────────────────────────────────────
    st.markdown('<div class="section-divider">Saved Model Artifacts</div>', unsafe_allow_html=True)
    tags = list_saved_models()
    if tags:
        for tag in tags:
            artifact = load_model(tag)
            if artifact:
                mname = artifact.get("model_name", "Unknown")
                mae = artifact.get("test_metrics", {}).get("mae")
                st.markdown(
                    f"- **{tag}** — {mname}"
                    + (f" (MAE: {mae:.2f})" if mae else "")
                )
            else:
                st.markdown(f"- **{tag}** — *(unreadable)*")
    else:
        st.caption("No saved model artifacts found.")

    # ── Current dataset ───────────────────────────────────────────────
    st.markdown('<div class="section-divider">Current Dataset</div>', unsafe_allow_html=True)
    df = st.session_state.get("dataset")
    fname = st.session_state.get("dataset_filename", "—")
    if df is not None and not df.empty:
        st.caption(f"File: `{fname}` · {len(df):,} rows x {len(df.columns)} columns")
    else:
        st.caption("No dataset loaded.")

    # ── Actions ───────────────────────────────────────────────────────
    st.markdown('<div class="section-divider">Actions</div>', unsafe_allow_html=True)

    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button("Clear Dataset", key="clr_ds"):
            for k in ["dataset", "dataset_filename", "last_train_result", "all_results"]:
                st.session_state.pop(k, None)
            st.success("Dataset cleared.")
            st.rerun()
    with a2:
        if st.button("Clear Training Results", key="clr_res"):
            for k in ["last_train_result", "all_results"]:
                st.session_state.pop(k, None)
            st.success("Results cleared.")
            st.rerun()
    with a3:
        if st.button("Delete Saved Models", key="del_mdl"):
            files = glob.glob(os.path.join(ARTIFACTS_DIR, "model_*.joblib"))
            for f in files:
                os.remove(f)
            st.success(f"Deleted {len(files)} artifact(s).")
            st.rerun()

    # ── About ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-divider">About</div>', unsafe_allow_html=True)
    st.markdown(
        "**AI/ML-Based Delivery Time Prediction in Logistics Management**  \n"
        "College Minor Project — 5th Semester  \n\n"
        "Uses machine learning to predict delivery times from historical logistics data.  \n"
        "Built with Streamlit · scikit-learn · Plotly · Pandas"
    )
