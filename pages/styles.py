"""
styles.py
---------
Global CSS for the DeliverIQ dashboard.
Designed to WORK WITH Streamlit's native rendering, not fight against it.
"""


def get_global_css() -> str:
    return """
<style>
/* ── Fonts ──────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Base ───────────────────────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* tighten main content area */
.main .block-container {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
    max-width: 1200px !important;
}

/* ── Hide chrome ────────────────────────────────────────────────────── */
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { display: none !important; }

/* ── Sidebar ────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #1B1B1F !important;
    min-width: 220px !important;
}
section[data-testid="stSidebar"] * {
    color: #D1D1D6 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.08) !important;
    margin: 6px 0 !important;
}
/* sidebar radio pills */
section[data-testid="stSidebar"] [role="radiogroup"] {
    gap: 2px !important;
}
section[data-testid="stSidebar"] [role="radiogroup"] label {
    background: transparent !important;
    border-radius: 6px !important;
    padding: 7px 12px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    transition: background 0.12s ease !important;
    cursor: pointer !important;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(255,255,255,0.07) !important;
}
section[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"],
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: #E65100 !important;
    color: #fff !important;
}
/* hide the actual radio circle */
section[data-testid="stSidebar"] [role="radiogroup"] input[type="radio"] {
    display: none !important;
}
section[data-testid="stSidebar"] [role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
    margin: 0 !important;
}

/* ── Metrics ────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #fff;
    border: 1px solid #E5E4E1;
    border-radius: 6px;
    padding: 14px 16px !important;
}
[data-testid="stMetric"]:hover {
    border-color: #D0CFCC;
}
[data-testid="stMetric"] label {
    font-size: 0.68rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    font-weight: 600 !important;
    color: #8A8A8E !important;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.3rem !important;
    font-weight: 600 !important;
    color: #1A1A1A !important;
}
[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
}

/* ── Buttons ────────────────────────────────────────────────────────── */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    border-radius: 5px !important;
    padding: 0.4rem 1.1rem !important;
    transition: all 0.12s ease !important;
}
/* primary */
.stButton > button[kind="primary"] {
    background: #E65100 !important;
    color: #fff !important;
    border: none !important;
}
.stButton > button[kind="primary"]:hover {
    background: #BF360C !important;
}
.stFormSubmitButton > button {
    background: #E65100 !important;
    color: #fff !important;
    border: none !important;
}

/* ── Tabs ───────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0 !important;
    border-bottom: 2px solid #E5E4E1 !important;
}
.stTabs [data-baseweb="tab"] {
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    color: #8A8A8E !important;
    padding: 8px 18px !important;
}
.stTabs [aria-selected="true"] {
    color: #E65100 !important;
    font-weight: 600 !important;
    border-bottom-color: #E65100 !important;
}

/* ── Dataframes ─────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #E5E4E1 !important;
    border-radius: 6px !important;
}

/* ── Inputs ─────────────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    border-radius: 5px !important;
}

/* ── Section divider lines ──────────────────────────────────────────── */
.section-divider {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #8A8A8E;
    border-bottom: 2px solid #E5E4E1;
    padding-bottom: 5px;
    margin-top: 6px;
    margin-bottom: 4px;
}

/* ── Status pills ───────────────────────────────────────────────────── */
.st-pill {
    display: inline-block;
    font-size: 0.66rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    padding: 2px 8px;
    border-radius: 4px;
    text-transform: uppercase;
    vertical-align: middle;
}
.st-pill-green  { background: #E8F5E9; color: #2E7D32; }
.st-pill-orange { background: #FFF3E0; color: #E65100; }
.st-pill-red    { background: #FFEBEE; color: #C62828; }
.st-pill-gray   { background: #F0EFEC; color: #8A8A8E; }
.st-pill-blue   { background: #E3F2FD; color: #1565C0; }

/* ── Prediction result card ─────────────────────────────────────────── */
.pred-card {
    background: #FFF3E0;
    border: 1px solid #FFB74D;
    border-radius: 6px;
    padding: 18px 20px;
    margin: 8px 0;
}
.pred-card .pred-label {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #8A8A8E;
    margin-bottom: 2px;
}
.pred-card .pred-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    color: #E65100;
    line-height: 1.3;
}
.pred-card .pred-sub {
    font-size: 0.72rem;
    color: #6B6B6B;
    margin-top: 4px;
}

/* ── Empty state ────────────────────────────────────────────────────── */
.empty-box {
    text-align: center;
    padding: 36px 20px;
    background: #FAFAF8;
    border: 1px dashed #D8D7D4;
    border-radius: 8px;
    margin: 8px 0;
}
.empty-box .eb-icon { font-size: 1.6rem; opacity: 0.45; margin-bottom: 6px; }
.empty-box .eb-title { font-size: 0.88rem; font-weight: 600; color: #6B6B6B; margin-bottom: 2px; }
.empty-box .eb-desc { font-size: 0.76rem; color: #9B9B9B; }

/* ── Logo in sidebar ────────────────────────────────────────────────── */
.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 4px 0 2px 0;
}
.sidebar-logo-icon {
    width: 34px; height: 34px;
    background: #E65100;
    border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; color: #fff;
}
.sidebar-logo-text {
    font-weight: 700; font-size: 0.92rem; color: #ECECF0 !important; line-height: 1.2;
}
.sidebar-logo-sub {
    font-size: 0.62rem; color: #8A8A8E !important; font-weight: 400;
}

/* ── Env badge in sidebar ───────────────────────────────────────────── */
.env-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem; font-weight: 700;
    letter-spacing: 0.08em;
    color: #4ADE80 !important;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 2px 8px; border-radius: 4px;
}

/* ── Misc ───────────────────────────────────────────────────────────── */
.mono { font-family: 'JetBrains Mono', monospace !important; }
</style>
"""
