"""
page_dataset.py
───────────────
Dataset management: upload CSV, preview, statistics, column inspector, cleaning.
"""

import streamlit as st
import pandas as pd
import numpy as np

from core.data_processor import (
    load_csv, dataset_summary, detect_features, clean_dataset,
    TARGET_COLUMN, NUMERIC_FEATURES, CATEGORICAL_FEATURES,
)


def render():
    # ── Upload ────────────────────────────────────────────────────────
    st.markdown('<div class="section-divider">Upload Dataset</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload a delivery logistics CSV file",
        type=["csv"],
        help="Upload a CSV containing delivery records with columns like distance, weight, duration, etc.",
        key="csv_uploader",
    )

    if uploaded is not None:
        try:
            df = load_csv(uploaded)
            if df.empty:
                st.error("The uploaded file is empty or could not be parsed.")
                return
            st.session_state["dataset"] = df
            st.session_state["dataset_filename"] = uploaded.name
            st.success(f"Loaded **{uploaded.name}** — {len(df):,} rows x {len(df.columns)} columns")
        except Exception as e:
            st.error(f"Failed to parse CSV: {e}")
            return

    df = st.session_state.get("dataset")
    if df is None or df.empty:
        st.markdown(
            '<div class="empty-box">'
            '<div class="eb-icon">📂</div>'
            '<div class="eb-title">No dataset loaded</div>'
            '<div class="eb-desc">Upload a CSV file above to get started.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    summary = dataset_summary(df)
    features = detect_features(df)

    # ── KPI bar ───────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Rows", f"{summary['row_count']:,}")
    with m2:
        st.metric("Columns", f"{summary['col_count']}")
    with m3:
        st.metric("Missing Values", f"{summary['total_missing']:,}")
    with m4:
        st.metric("Target Column", "Detected" if summary["has_target"] else "Not Found")

    st.markdown("")

    # ── Tabs ──────────────────────────────────────────────────────────
    tab_preview, tab_stats, tab_columns, tab_clean = st.tabs([
        "Preview", "Statistics", "Columns", "Cleaning",
    ])

    # ── Preview ───────────────────────────────────────────────────────
    with tab_preview:
        sc1, sc2 = st.columns([3, 1])
        with sc1:
            search = st.text_input("Search records", placeholder="Type to filter...",
                                   key="ds_search", label_visibility="collapsed")
        with sc2:
            page_size = st.selectbox("Rows per page", [25, 50, 100], index=0, key="ds_psize")

        view_df = df.copy()
        if search:
            mask = view_df.astype(str).apply(
                lambda row: row.str.contains(search, case=False, na=False)
            ).any(axis=1)
            view_df = view_df[mask]
            st.caption(f"{len(view_df):,} matching rows")

        total_pages = max(1, (len(view_df) - 1) // page_size + 1)
        page = st.number_input("Page", 1, total_pages, 1, key="ds_page")
        start = (page - 1) * page_size

        st.dataframe(
            view_df.iloc[start:start + page_size].reset_index(drop=True),
            use_container_width=True, height=400,
        )
        st.caption(f"Page {page}/{total_pages} · Rows {start+1}-{min(start+page_size, len(view_df))} of {len(view_df):,}")

    # ── Statistics ────────────────────────────────────────────────────
    with tab_stats:
        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            desc = numeric_df.describe().T
            desc["missing"] = df[numeric_df.columns].isnull().sum()
            desc["missing_%"] = (desc["missing"] / len(df) * 100).round(1)
            st.markdown("**Descriptive Statistics (Numeric Columns)**")
            st.dataframe(desc, use_container_width=True)
        else:
            st.info("No numeric columns detected.")

        if summary["has_target"]:
            st.markdown("---")
            st.markdown(f"**Target Column:** `{TARGET_COLUMN}`")
            tc1, tc2, tc3, tc4 = st.columns(4)
            with tc1:
                st.metric("Mean", f"{summary.get('avg_duration', '—')}")
            with tc2:
                st.metric("Median", f"{summary.get('median_duration', '—')}")
            with tc3:
                st.metric("Min", f"{summary.get('min_duration', '—')}")
            with tc4:
                st.metric("Max", f"{summary.get('max_duration', '—')}")

    # ── Columns ───────────────────────────────────────────────────────
    with tab_columns:
        col_data = []
        for col in df.columns:
            missing = int(df[col].isnull().sum())
            missing_pct = round(missing / len(df) * 100, 1) if len(df) else 0
            role = "—"
            if col == TARGET_COLUMN:
                role = "Target"
            elif col in NUMERIC_FEATURES:
                role = "Numeric feature"
            elif col in CATEGORICAL_FEATURES:
                role = "Categorical feature"
            elif col == "order_id":
                role = "Identifier"

            sample = str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else "—"
            if len(sample) > 35:
                sample = sample[:35] + "..."

            col_data.append({
                "Column": col,
                "Type": str(df[col].dtype),
                "Role": role,
                "Unique": df[col].nunique(),
                "Missing": f"{missing} ({missing_pct}%)",
                "Sample": sample,
            })

        st.dataframe(pd.DataFrame(col_data), use_container_width=True, hide_index=True)
        st.caption(
            f"Detected: {len(features['numeric'])} numeric, "
            f"{len(features['categorical'])} categorical features"
        )

    # ── Cleaning ──────────────────────────────────────────────────────
    with tab_clean:
        st.markdown(
            "Strips whitespace, coerces numeric types, drops rows where "
            "the target column is missing."
        )
        if st.button("🧹 Clean Dataset", type="primary", key="clean_btn"):
            with st.spinner("Cleaning..."):
                cleaned, report = clean_dataset(df)
            st.session_state["dataset"] = cleaned
            st.success(
                f"Cleaned: {report['rows_before']:,} -> {report['rows_after']:,} rows "
                f"({report['rows_dropped']} dropped)"
            )
            st.rerun()

        missing = df.isnull().sum()
        missing = missing[missing > 0]
        if not missing.empty:
            st.markdown("**Columns with missing values:**")
            st.dataframe(
                pd.DataFrame({"Column": missing.index, "Missing": missing.values,
                               "Pct": (missing.values / len(df) * 100).round(1)}),
                use_container_width=True, hide_index=True,
            )
        else:
            st.success("No missing values detected.")
