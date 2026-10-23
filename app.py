"""
app.py
------
Main entry point for the DeliverIQ dashboard.
Run:  python -m streamlit run app.py
"""

import streamlit as st
from pages.styles import get_global_css
from pages import page_overview, page_predict, page_dataset, page_model, page_settings
from core.model_engine import load_model


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DeliverIQ - Delivery Time Prediction",
    page_icon="⏱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global styles ────────────────────────────────────────────────────────────
st.markdown(get_global_css(), unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown(
        '<div class="sidebar-logo">'
        '<div class="sidebar-logo-icon">⏱</div>'
        '<div>'
        '<div class="sidebar-logo-text">DeliverIQ</div>'
        '<div class="sidebar-logo-sub">ETA Prediction Engine</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Navigation — use radio for reliable state management
    page = st.radio(
        "Navigation",
        options=[
            "📊  Overview",
            "⚡  Predict ETA",
            "📂  Dataset",
            "🧪  Model Performance",
            "⚙️  Settings",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # System status
    df = st.session_state.get("dataset")
    model_artifact = load_model()

    st.caption("SYSTEM STATUS")
    if df is not None and not df.empty:
        fname = st.session_state.get("dataset_filename", "dataset")
        st.markdown(
            f'<span class="st-pill st-pill-green">DATA LOADED</span> &nbsp; '
            f'<span style="font-size:0.75rem;">{len(df):,} rows</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="st-pill st-pill-gray">NO DATA</span>',
            unsafe_allow_html=True,
        )

    if model_artifact:
        mname = model_artifact.get("model_name", "?")
        st.markdown(
            f'<span class="st-pill st-pill-green">MODEL</span> &nbsp; '
            f'<span style="font-size:0.75rem;">{mname}</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="st-pill st-pill-gray">NO MODEL</span>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center;">'
        '<span class="env-label">● LOCAL</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.caption("Minor Project · 5th Sem")


# ── Map radio selection to clean page name ───────────────────────────────────
PAGE_MAP = {
    "📊  Overview":          "Overview",
    "⚡  Predict ETA":       "Predict ETA",
    "📂  Dataset":           "Dataset",
    "🧪  Model Performance": "Model Performance",
    "⚙️  Settings":          "Settings",
}
current_page = PAGE_MAP.get(page, "Overview")


# ── Page header ──────────────────────────────────────────────────────────────
header_left, header_right = st.columns([5, 1])
with header_left:
    st.markdown(f"### {current_page}")
    st.caption(f"DeliverIQ / {current_page}")
with header_right:
    if st.button("↻ Refresh", key="refresh_btn"):
        st.rerun()

st.markdown("---")


# ── Page routing ─────────────────────────────────────────────────────────────
if current_page == "Overview":
    page_overview.render()
elif current_page == "Predict ETA":
    page_predict.render()
elif current_page == "Dataset":
    page_dataset.render()
elif current_page == "Model Performance":
    page_model.render()
elif current_page == "Settings":
    page_settings.render()
