"""Shared visual system — Anthropic-inspired minimalist dark theme."""

from __future__ import annotations

from html import escape

import streamlit as st

NAV_ITEMS = [
    ("Dashboard", "pages/1_Dashboard.py", "Market overview"),
    ("Stocks", "pages/2_Stocks.py", "Universe browser"),
    ("Signals", "pages/4_Signals.py", "Conviction engine"),
    ("Portfolio", "pages/5_Portfolio.py", "Holdings & allocation"),
    ("Settings", "pages/6_Settings.py", "Account"),
]

# Tone → left-border accent colour
_TONE_CLASS = {
    "emerald": "ns-stat--green",
    "green": "ns-stat--green",
    "amber": "ns-stat--amber",
    "rose": "ns-stat--red",
    "red": "ns-stat--red",
    "blue": "ns-stat--blue",
    "sky": "ns-stat--blue",
}


def apply_theme() -> None:
    """Inject the global CSS skin once per page load."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700&display=swap');

        :root {
            --bg:          #f8f9fa;
            --surface:     #f8f9fa;
            --surface-2:   #e9ecef;
            --surface-3:   #dee2e6;
            --border:      #dee2e6;
            --border-s:    #ced4da;
            --text:        #212529;
            --text-2:      #495057;
            --muted:       #6c757d;
            --accent:      #343a40;
            --accent-bg:   #e9ecef;
            --accent-dim:  #adb5bd;
            --blue:        #495057;
            --blue-bg:     #e9ecef;
            --green:       #343a40;
            --green-bg:    #e9ecef;
            --red:         #212529;
            --red-bg:      #dee2e6;
            --amber:       #6c757d;
            --amber-bg:    #e9ecef;
        }

        *, *::before, *::after { box-sizing: border-box; }

        html, body, [class*="css"] {
            font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif !important;
        }

        /* ── App background ─────────────────────────────────────── */
        .stApp {
            background: var(--bg) !important;
            color: var(--text) !important;
        }
        [data-testid="stAppViewContainer"] > .main { background: transparent !important; }
        .main .block-container {
            max-width: 1300px;
            padding-top: 1.5rem;
            padding-bottom: 4rem;
        }
        [data-testid="stHeader"] { background: transparent !important; }

        /* ── Sidebar ─────────────────────────────────────────────── */
        [data-testid="stSidebar"] {
            background: var(--surface) !important;
            border-right: 1px solid var(--border) !important;
        }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] { display: none; }
        [data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }

        /* ── Typography ──────────────────────────────────────────── */
        h1, h2, h3, h4, h5, h6 {
            font-family: "Inter", sans-serif !important;
            color: var(--text) !important;
            letter-spacing: 0;
            line-height: 1.25;
        }
        h1 { font-size: 1.625rem !important; font-weight: 700 !important; }
        h2 { font-size: 1.375rem !important; font-weight: 600 !important; }
        h3 { font-size: 1.125rem !important; font-weight: 600 !important; }
        h4 { font-size: 0.9375rem !important; font-weight: 600 !important; }

        p, .stMarkdown p { color: var(--text-2) !important; font-size: 0.875rem !important; }
        strong, b { color: var(--text) !important; }
        label { color: var(--text-2) !important; font-size: 0.875rem !important; }

        /* ── Buttons ─────────────────────────────────────────────── */
        .stButton > button,
        .stDownloadButton > button {
            background: var(--surface-2) !important;
            border: 1px solid var(--border-s) !important;
            border-radius: 8px !important;
            color: var(--text) !important;
            font-weight: 500 !important;
            font-size: 0.875rem !important;
            line-height: 1.1 !important;
            min-height: 2.4rem !important;
            padding: 0.4rem 0.875rem !important;
            box-shadow: none !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            transition: border-color 0.15s ease, background 0.15s ease !important;
        }
        .stButton > button p,
        .stDownloadButton > button p,
        div[data-testid="stFormSubmitButton"] > button p {
            margin: 0 !important;
            color: inherit !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            line-height: 1.1 !important;
        }
        .stButton > button:hover,
        .stDownloadButton > button:hover {
            background: var(--surface-3) !important;
            border-color: var(--accent-dim) !important;
            color: var(--text) !important;
        }

        div[data-testid="stFormSubmitButton"] > button {
            background: var(--accent) !important;
            border: 1px solid transparent !important;
            border-radius: 8px !important;
            color: #f8f9fa !important;
            font-weight: 600 !important;
            font-size: 0.875rem !important;
            line-height: 1.1 !important;
            min-height: 2.4rem !important;
            padding: 0.4rem 0.875rem !important;
            box-shadow: none !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            transition: opacity 0.15s ease !important;
        }
        div[data-testid="stFormSubmitButton"] > button:hover {
            opacity: 0.88 !important;
        }

        /* link buttons */
        [data-testid="stLinkButton"] a {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            background: var(--surface-2) !important;
            border: 1px solid var(--border-s) !important;
            border-radius: 8px !important;
            color: var(--text) !important;
            font-weight: 500 !important;
            font-size: 0.875rem !important;
            line-height: 1.1 !important;
            min-height: 2.4rem !important;
            padding: 0.4rem 0.875rem !important;
            text-decoration: none !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            transition: border-color 0.15s ease !important;
        }
        [data-testid="stLinkButton"] a:hover {
            border-color: var(--border-s) !important;
            background: var(--surface-3) !important;
        }

        /* ── Inputs ──────────────────────────────────────────────── */
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        textarea,
        .stNumberInput div[data-baseweb="input"] > div {
            background: var(--surface-2) !important;
            border: 1px solid var(--border-s) !important;
            border-radius: 8px !important;
            box-shadow: none !important;
        }
        div[data-baseweb="input"]:focus-within > div,
        div[data-baseweb="select"]:focus-within > div {
            border-color: var(--accent-dim) !important;
        }
        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea,
        .stSelectbox input {
            color: var(--text) !important;
            font-size: 0.875rem !important;
            background: transparent !important;
        }
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {
            color: var(--muted) !important;
        }

        /* ── Select popover ──────────────────────────────────────── */
        [data-baseweb="popover"] ul,
        [data-baseweb="menu"] {
            background: var(--surface-2) !important;
            border: 1px solid var(--border-s) !important;
            border-radius: 8px !important;
        }
        [data-baseweb="option"]:hover {
            background: var(--border) !important;
        }

        /* ── Form containers ─────────────────────────────────────── */
        .stForm,
        div[data-testid="stForm"] {
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
            padding: 1.25rem 1.25rem 0.75rem !important;
            box-shadow: none !important;
        }

        /* ── Metric widgets ──────────────────────────────────────── */
        [data-testid="stMetric"] {
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: 10px !important;
            padding: 0.875rem 1rem !important;
        }
        [data-testid="stMetricLabel"] {
            color: var(--text-2) !important;
            font-size: 0.7rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.06em !important;
        }
        [data-testid="stMetricValue"] {
            color: var(--text) !important;
            font-weight: 700 !important;
            font-size: 1.375rem !important;
        }

        /* ── Tabs ────────────────────────────────────────────────── */
        div[role="tablist"] {
            background: transparent !important;
            border-bottom: 1px solid var(--border) !important;
            gap: 0 !important;
            margin-bottom: 1.25rem !important;
        }
        button[data-baseweb="tab"] {
            background: transparent !important;
            border: none !important;
            border-bottom: 2px solid transparent !important;
            border-radius: 0 !important;
            color: var(--text-2) !important;
            font-weight: 500 !important;
            font-size: 0.875rem !important;
            padding: 0.625rem 1rem !important;
            margin-bottom: -1px !important;
            transition: color 0.15s ease !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: var(--text) !important;
            border-bottom-color: var(--accent) !important;
            background: transparent !important;
        }
        button[data-baseweb="tab"]:hover { color: var(--text) !important; }

        /* ── Alerts ──────────────────────────────────────────────── */
        .stAlert {
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
            font-size: 0.875rem !important;
        }
        .stAlert[data-baseweb="notification"][kind="positive"] {
            border-color: var(--border-s) !important;
        }
        .stAlert[data-baseweb="notification"][kind="negative"] {
            border-color: var(--text) !important;
        }

        /* ── Radio / Checkbox / Toggle ───────────────────────────── */
        .stRadio label, .stCheckbox label, .stToggle label {
            color: var(--text) !important;
            font-size: 0.875rem !important;
        }

        /* ── Expander ────────────────────────────────────────────── */
        div[data-testid="stExpander"] {
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: 10px !important;
        }

        /* ── Scrollbar ───────────────────────────────────────────── */
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb {
            background: var(--border-s);
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover { background: var(--muted); }

        /* ── Page-link nav items ─────────────────────────────────── */
        [data-testid="stPageLink-NavLink"] {
            border-radius: 7px !important;
            padding: 0.45rem 0.75rem !important;
            color: var(--text-2) !important;
            font-size: 0.875rem !important;
            font-weight: 500 !important;
            width: 100% !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            transition: all 0.15s ease !important;
            background: transparent !important;
        }
        [data-testid="stPageLink-NavLink"]:hover {
            background: var(--border) !important;
            color: var(--text) !important;
        }
        [data-testid="stPageLink-NavLink"][aria-current="page"] {
            background: var(--accent-bg) !important;
            color: var(--accent) !important;
        }

        /* ══════════════════════════════════════════════════════════
           Custom component classes
        ══════════════════════════════════════════════════════════ */

        /* Page header */
        .ns-page-header {
            padding-bottom: 1.25rem;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid var(--border);
        }
        .ns-page-header h1 {
            margin: 0 0 0.3rem !important;
            font-size: 1.5rem !important;
        }
        .ns-page-header p {
            margin: 0 !important;
            color: var(--text-2) !important;
            font-size: 0.875rem !important;
            line-height: 1.6 !important;
        }
        .ns-tag-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.375rem;
            margin-top: 0.75rem;
        }
        .ns-tag {
            display: inline-block;
            padding: 0.2rem 0.55rem;
            background: var(--surface-2);
            border: 1px solid var(--border-s);
            border-radius: 5px;
            font-size: 0.72rem;
            font-weight: 500;
            color: var(--text-2);
            letter-spacing: 0.01em;
        }

        /* Stat cards */
        .ns-stat {
            background: var(--surface);
            border: 1px solid var(--border);
            border-left: 3px solid transparent;
            border-radius: 10px;
            padding: 0.875rem 1rem;
            height: 100%;
        }
        .ns-stat--green  { border-left-color: var(--green); }
        .ns-stat--red    { border-left-color: var(--red); }
        .ns-stat--amber  { border-left-color: var(--amber); }
        .ns-stat--blue   { border-left-color: var(--blue); }
        .ns-stat--accent { border-left-color: var(--accent); }

        .ns-stat-label {
            font-size: 0.68rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: var(--text-2);
            margin-bottom: 0.4rem;
        }
        .ns-stat-value {
            font-size: 1.375rem;
            font-weight: 700;
            color: var(--text);
            line-height: 1.2;
            margin-bottom: 0.3rem;
        }
        .ns-stat-detail {
            font-size: 0.78rem;
            color: var(--text-2);
            line-height: 1.5;
        }

        /* Info card */
        .ns-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 0.875rem 1rem;
        }
        .ns-card h4 {
            font-size: 0.875rem !important;
            font-weight: 600 !important;
            color: var(--text) !important;
            margin: 0 0 0.375rem !important;
        }
        .ns-card-body {
            font-size: 0.8125rem;
            color: var(--text-2);
            line-height: 1.6;
        }
        .ns-card-rows { margin-top: 0.625rem; }
        .ns-card-row {
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
            padding: 0.375rem 0;
            border-top: 1px solid var(--border);
            font-size: 0.8rem;
        }
        .ns-card-key { color: var(--text-2); }
        .ns-card-val { color: var(--text); font-weight: 500; }

        /* Info band */
        .ns-band {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.625rem 0.875rem;
            margin: 0.5rem 0;
            display: flex;
            gap: 0.625rem;
            align-items: flex-start;
        }
        .ns-band-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--accent);
            flex-shrink: 0;
            margin-top: 0.375rem;
        }
        .ns-band-text { font-size: 0.8125rem; color: var(--text-2); line-height: 1.55; }
        .ns-band-title { font-weight: 600; color: var(--text); }

        /* Empty state */
        .ns-empty {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 2.5rem 1.5rem;
            text-align: center;
        }
        .ns-empty h4 {
            font-size: 0.9375rem !important;
            font-weight: 600 !important;
            color: var(--text) !important;
            margin: 0 0 0.4rem !important;
        }
        .ns-empty p {
            font-size: 0.8125rem !important;
            color: var(--text-2) !important;
            margin: 0 !important;
        }

        /* Section heading */
        .ns-section-title {
            font-size: 0.8125rem;
            font-weight: 600;
            color: var(--text);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 0.625rem;
        }

        /* Row divider */
        .ns-divider,
        .ns-row-divider {
            height: 1px;
            background: var(--border);
            margin: 0.375rem 0;
        }

        /* Signal pill */
        .ns-signal-pill {
            display: inline-flex;
            align-items: center;
            padding: 0.2rem 0.5rem;
            border-radius: 5px;
            font-size: 0.73rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            border: 1px solid transparent;
        }

        /* Sidebar brand */
        .ns-brand {
            display: flex;
            align-items: center;
            gap: 0.625rem;
            padding-bottom: 1.25rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid var(--border);
        }
        .ns-brand-mark {
            width: 30px;
            height: 30px;
            background: var(--accent);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 0.9rem;
            color: #f8f9fa;
            flex-shrink: 0;
            letter-spacing: -0.02em;
        }
        .ns-brand-name {
            font-size: 1rem;
            font-weight: 700;
            color: var(--text);
            letter-spacing: -0.02em;
        }
        .ns-brand-sub {
            font-size: 0.7rem;
            color: var(--muted);
            margin-top: 0.1rem;
        }
        .ns-nav-section {
            font-size: 0.68rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
            padding: 0 0.25rem;
            margin-bottom: 0.375rem;
        }
        .ns-sidebar-footer {
            margin-top: 1rem;
            padding: 0.75rem;
            background: var(--surface-2);
            border-radius: 8px;
            border: 1px solid var(--border);
        }
        .ns-footer-email {
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--text);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .ns-footer-risk {
            font-size: 0.72rem;
            color: var(--text-2);
            margin-top: 0.2rem;
        }

        [data-testid="stHorizontalBlock"] {
            gap: 0.75rem;
        }

        [data-testid="stHorizontalBlock"] [data-testid="stMarkdownContainer"] p {
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        .stButton > button:disabled,
        .stButton > button:disabled * {
            color: var(--muted) !important;
            opacity: 1 !important;
        }

        @media (max-width: 768px) {
            .main .block-container { padding-top: 1rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_shell(
    *,
    active_page: str | None,
    user_email: str,
    risk_profile: str | None,
    headline: str = "",
    show_nav: bool = True,
) -> None:
    """Render the shared sidebar."""
    risk = (risk_profile or "unassigned").capitalize()
    with st.sidebar:
        st.markdown(
            f"""
            <div class="ns-brand">
                <div class="ns-brand-mark">N</div>
                <div>
                    <div class="ns-brand-name">NiveshSutra</div>
                    <div class="ns-brand-sub">Indian equity intelligence</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if show_nav:
            st.markdown('<div class="ns-nav-section">Navigation</div>', unsafe_allow_html=True)
            for label, path, _ in NAV_ITEMS:
                st.page_link(path, label=label, disabled=label == active_page)
            st.markdown("")

        st.markdown(
            f"""
            <div class="ns-sidebar-footer">
                <div class="ns-footer-email">{escape(user_email)}</div>
                <div class="ns-footer-risk">Risk profile: {escape(risk)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_page_hero(
    *,
    kicker: str,
    title: str,
    body: str,
    pills: list[str] | None = None,
    aside_title: str | None = None,
    aside_rows: list[tuple[str, str]] | None = None,
) -> None:
    """Render a clean page header (replaces the editorial hero block)."""
    pill_markup = "".join(
        f'<span class="ns-tag">{escape(item)}</span>' for item in (pills or [])
    )
    pill_row = f'<div class="ns-tag-row">{pill_markup}</div>' if pill_markup else ""
    st.markdown(
        f"""
        <div class="ns-page-header">
            <h1>{escape(title)}</h1>
            <p>{escape(body)}</p>
            {pill_row}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_heading(title: str, body: str = "", kicker: str = "") -> None:
    """Render a compact section heading."""
    body_html = (
        f"<p style='margin:0.2rem 0 0;font-size:0.8125rem;color:var(--text-2)'>{escape(body)}</p>"
        if body
        else ""
    )
    st.markdown(
        f"""
        <div style="margin: 0.25rem 0 0.75rem">
            <div class="ns-section-title">{escape(title)}</div>
            {body_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_grid(items: list[dict[str, str]], columns: int | None = None) -> None:
    """Render a row of flat stat cards."""
    if not items:
        return
    column_count = columns or len(items)
    cols = st.columns(column_count, gap="small")
    for index, item in enumerate(items):
        col = cols[index % column_count]
        tone = item.get("tone", "blue")
        tone_class = _TONE_CLASS.get(tone, "ns-stat--blue")
        with col:
            st.markdown(
                f"""
                <div class="ns-stat {tone_class}">
                    <div class="ns-stat-label">{escape(item.get("label", ""))}</div>
                    <div class="ns-stat-value">{escape(item.get("value", ""))}</div>
                    <div class="ns-stat-detail">{escape(item.get("detail", ""))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_info_band(title: str, body: str) -> None:
    """Render a compact info callout."""
    st.markdown(
        f"""
        <div class="ns-band">
            <div class="ns-band-dot"></div>
            <div class="ns-band-text">
                <span class="ns-band-title">{escape(title)}: </span>{escape(body)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_note_card(title: str, body: str, rows: list[tuple[str, str]] | None = None) -> None:
    """Render a compact info card."""
    row_markup = "".join(
        f"""
        <div class="ns-card-row">
            <span class="ns-card-key">{escape(label)}</span>
            <span class="ns-card-val">{escape(value)}</span>
        </div>
        """
        for label, value in (rows or [])
    )
    rows_section = f'<div class="ns-card-rows">{row_markup}</div>' if row_markup else ""
    st.markdown(
        f"""
        <div class="ns-card">
            <h4>{escape(title)}</h4>
            <div class="ns-card-body">{escape(body)}</div>
            {rows_section}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, body: str) -> None:
    """Render a centered empty state."""
    st.markdown(
        f"""
        <div class="ns-empty">
            <h4>{escape(title)}</h4>
            <p>{escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_plotly_figure(fig, *, height: int = 320):
    """Apply the shared neutral theme to a Plotly figure."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f8f9fa",
        font=dict(color="#495057", family="Inter", size=12),
        xaxis=dict(
            gridcolor="#dee2e6",
            zerolinecolor="#ced4da",
            color="#495057",
        ),
        yaxis=dict(
            gridcolor="#dee2e6",
            zerolinecolor="#ced4da",
            color="#495057",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
            font=dict(color="#495057", size=11),
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        height=height,
    )
    return fig
