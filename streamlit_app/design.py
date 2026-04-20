"""Shared visual system for the Streamlit experience."""

from __future__ import annotations

from html import escape

import streamlit as st


NAV_ITEMS = [
    ("Dashboard", "pages/1_Dashboard.py", "Market panorama"),
    ("Stocks", "pages/2_Stocks.py", "Universe explorer"),
    ("Signals", "pages/4_Signals.py", "Conviction engine"),
    ("Portfolio", "pages/5_Portfolio.py", "Allocation studio"),
    ("Settings", "pages/6_Settings.py", "Preferences"),
]


def apply_theme() -> None:
    """Inject the shared CSS skin once per page."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Space+Grotesk:wght@400;500;700&display=swap');

        :root {
            --ns-bg: #07111f;
            --ns-bg-soft: #0b1629;
            --ns-surface: rgba(10, 21, 39, 0.88);
            --ns-surface-strong: rgba(15, 30, 52, 0.96);
            --ns-line: rgba(164, 185, 213, 0.16);
            --ns-line-strong: rgba(243, 164, 92, 0.35);
            --ns-text: #f7f2e9;
            --ns-muted: #9aabc4;
            --ns-emerald: #5de4c7;
            --ns-sky: #7bc8ff;
            --ns-amber: #f3a45c;
            --ns-rose: #ff7f90;
            --ns-shadow: 0 30px 80px rgba(0, 0, 0, 0.28);
        }

        html, body, [class*="css"]  {
            font-family: "Space Grotesk", sans-serif;
        }

        .stApp {
            color: var(--ns-text);
            background:
                radial-gradient(circle at 15% 15%, rgba(123, 200, 255, 0.18), transparent 28%),
                radial-gradient(circle at 85% 10%, rgba(243, 164, 92, 0.16), transparent 24%),
                radial-gradient(circle at 75% 45%, rgba(93, 228, 199, 0.12), transparent 22%),
                linear-gradient(180deg, #07111f 0%, #091524 35%, #07111f 100%);
            background-attachment: fixed;
        }

        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            opacity: 0.14;
            background-image:
                linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px);
            background-size: 120px 120px;
            mask-image: linear-gradient(180deg, rgba(0,0,0,0.45), transparent 90%);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stAppViewContainer"] > .main {
            background: transparent;
        }

        .main .block-container {
            max-width: 1320px;
            padding-top: 1.4rem;
            padding-bottom: 4rem;
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(7, 17, 31, 0.96) 0%, rgba(11, 22, 41, 0.96) 100%);
            border-right: 1px solid var(--ns-line);
        }

        [data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            display: none;
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 1.4rem;
        }

        h1, h2, h3, h4 {
            font-family: "Cormorant Garamond", serif;
            letter-spacing: -0.03em;
            color: var(--ns-text);
        }

        h1 {
            font-size: clamp(3rem, 6vw, 5.4rem);
            line-height: 0.92;
            margin-bottom: 0.8rem;
        }

        h2 {
            font-size: clamp(2rem, 4vw, 3.2rem);
            line-height: 0.96;
        }

        h3 {
            font-size: clamp(1.4rem, 3vw, 2rem);
        }

        p, li, label, [data-testid="stCaptionContainer"], .stMarkdown, .stText {
            color: var(--ns-muted);
        }

        .stButton > button,
        .stDownloadButton > button,
        div[data-testid="stFormSubmitButton"] > button {
            min-height: 2.9rem;
            border-radius: 999px;
            border: 1px solid rgba(243, 164, 92, 0.32);
            color: var(--ns-text);
            background:
                linear-gradient(135deg, rgba(243, 164, 92, 0.22), rgba(123, 200, 255, 0.16));
            box-shadow: 0 12px 36px rgba(0, 0, 0, 0.2);
            transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
            font-weight: 600;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover {
            transform: translateY(-1px);
            border-color: rgba(243, 164, 92, 0.56);
            background:
                linear-gradient(135deg, rgba(243, 164, 92, 0.3), rgba(123, 200, 255, 0.22));
        }

        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        textarea,
        .stNumberInput div[data-baseweb="input"] > div {
            border-radius: 20px !important;
            border: 1px solid var(--ns-line) !important;
            background: rgba(15, 28, 48, 0.82) !important;
            box-shadow: none !important;
        }

        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea,
        .stSelectbox input,
        .stMultiSelect input {
            color: var(--ns-text) !important;
        }

        .stRadio label,
        .stCheckbox label,
        .stToggle label {
            color: var(--ns-muted) !important;
        }

        .stForm,
        div[data-testid="stExpander"],
        [data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(12, 23, 40, 0.92), rgba(15, 30, 52, 0.92));
            border: 1px solid var(--ns-line);
            border-radius: 26px;
            box-shadow: var(--ns-shadow);
        }

        .stForm {
            padding: 1rem 1rem 0.4rem;
        }

        [data-testid="stMetric"] {
            padding: 1rem 1.1rem;
        }

        [data-testid="stMetricLabel"] {
            color: var(--ns-muted);
            font-weight: 500;
        }

        [data-testid="stMetricValue"] {
            font-family: "Cormorant Garamond", serif;
            letter-spacing: -0.03em;
        }

        div[role="tablist"] {
            gap: 0.6rem;
            margin-bottom: 1rem;
        }

        button[data-baseweb="tab"] {
            border-radius: 999px !important;
            border: 1px solid var(--ns-line) !important;
            background: rgba(9, 18, 33, 0.72) !important;
            color: var(--ns-muted) !important;
            padding: 0.5rem 1rem !important;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: var(--ns-text) !important;
            border-color: rgba(243, 164, 92, 0.42) !important;
            background: linear-gradient(135deg, rgba(243, 164, 92, 0.22), rgba(123, 200, 255, 0.16)) !important;
        }

        .stAlert {
            border-radius: 22px;
            border: 1px solid var(--ns-line);
        }

        .ns-sidebar-brand {
            padding: 1rem 1rem 1.2rem;
            border: 1px solid rgba(243, 164, 92, 0.18);
            border-radius: 28px;
            background:
                radial-gradient(circle at top right, rgba(243, 164, 92, 0.18), transparent 34%),
                linear-gradient(180deg, rgba(16, 28, 48, 0.95), rgba(9, 18, 33, 0.95));
            box-shadow: var(--ns-shadow);
            margin-bottom: 1rem;
        }

        .ns-sidebar-brand h2 {
            font-size: 2rem;
            margin: 0;
        }

        .ns-sidebar-kicker {
            text-transform: uppercase;
            letter-spacing: 0.24em;
            font-size: 0.68rem;
            color: var(--ns-amber);
        }

        .ns-sidebar-copy {
            font-size: 0.82rem;
            line-height: 1.6;
            color: var(--ns-muted);
        }

        .ns-sidebar-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.9rem;
        }

        .ns-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.42rem 0.72rem;
            border-radius: 999px;
            border: 1px solid rgba(123, 200, 255, 0.18);
            background: rgba(123, 200, 255, 0.08);
            color: var(--ns-text);
            font-size: 0.78rem;
            letter-spacing: 0.02em;
        }

        .ns-chip--emerald {
            border-color: rgba(93, 228, 199, 0.2);
            background: rgba(93, 228, 199, 0.1);
        }

        .ns-chip--amber {
            border-color: rgba(243, 164, 92, 0.24);
            background: rgba(243, 164, 92, 0.12);
        }

        .ns-chip--rose {
            border-color: rgba(255, 127, 144, 0.24);
            background: rgba(255, 127, 144, 0.12);
        }

        .ns-hero {
            position: relative;
            overflow: hidden;
            display: grid;
            grid-template-columns: minmax(0, 1.35fr) minmax(260px, 0.8fr);
            gap: 1rem;
            padding: 1.35rem;
            border-radius: 34px;
            border: 1px solid rgba(243, 164, 92, 0.18);
            background:
                radial-gradient(circle at top right, rgba(243, 164, 92, 0.18), transparent 32%),
                radial-gradient(circle at bottom left, rgba(93, 228, 199, 0.12), transparent 28%),
                linear-gradient(135deg, rgba(13, 25, 44, 0.97), rgba(6, 15, 29, 0.98));
            box-shadow: var(--ns-shadow);
            margin-bottom: 1.1rem;
        }

        .ns-hero::after {
            content: "";
            position: absolute;
            inset: auto -10% -35% 40%;
            height: 280px;
            background: radial-gradient(circle, rgba(123, 200, 255, 0.18), transparent 68%);
            filter: blur(22px);
            pointer-events: none;
        }

        .ns-kicker {
            display: inline-block;
            margin-bottom: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.28em;
            font-size: 0.72rem;
            color: var(--ns-amber);
        }

        .ns-hero h1,
        .ns-hero h2 {
            margin: 0;
            max-width: 13ch;
        }

        .ns-hero p {
            max-width: 56ch;
            font-size: 0.98rem;
            line-height: 1.75;
        }

        .ns-pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
            margin-top: 1rem;
        }

        .ns-hero-aside,
        .ns-note-card,
        .ns-empty-state,
        .ns-info-band,
        .ns-metric-card {
            border: 1px solid var(--ns-line);
            border-radius: 28px;
            background: linear-gradient(180deg, rgba(15, 28, 48, 0.88), rgba(9, 18, 33, 0.94));
            box-shadow: var(--ns-shadow);
        }

        .ns-hero-aside {
            padding: 1rem;
            align-self: stretch;
        }

        .ns-hero-aside h4,
        .ns-note-card h4,
        .ns-empty-state h4 {
            margin: 0 0 0.45rem;
            font-family: "Space Grotesk", sans-serif;
            letter-spacing: 0.02em;
            color: var(--ns-text);
        }

        .ns-aside-row {
            display: flex;
            justify-content: space-between;
            gap: 0.8rem;
            padding: 0.7rem 0;
            border-bottom: 1px solid rgba(164, 185, 213, 0.1);
        }

        .ns-aside-row:last-child {
            border-bottom: 0;
        }

        .ns-aside-label {
            color: var(--ns-muted);
            font-size: 0.8rem;
        }

        .ns-aside-value {
            color: var(--ns-text);
            font-weight: 600;
        }

        .ns-section-heading {
            margin: 0.4rem 0 0.8rem;
        }

        .ns-section-heading h3 {
            margin: 0;
        }

        .ns-section-heading p {
            margin: 0.2rem 0 0;
        }

        .ns-metric-card {
            padding: 1rem 1.05rem;
            height: 100%;
        }

        .ns-metric-label {
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-size: 0.68rem;
            color: var(--ns-muted);
            margin-bottom: 0.5rem;
        }

        .ns-metric-value {
            font-family: "Cormorant Garamond", serif;
            font-size: clamp(2rem, 4vw, 3rem);
            line-height: 0.94;
            color: var(--ns-text);
            margin-bottom: 0.3rem;
        }

        .ns-metric-detail {
            color: var(--ns-muted);
            font-size: 0.82rem;
            line-height: 1.6;
        }

        .ns-metric-tone--emerald {
            border-color: rgba(93, 228, 199, 0.22);
        }

        .ns-metric-tone--amber {
            border-color: rgba(243, 164, 92, 0.22);
        }

        .ns-metric-tone--rose {
            border-color: rgba(255, 127, 144, 0.22);
        }

        .ns-info-band,
        .ns-empty-state,
        .ns-note-card {
            padding: 1rem 1.05rem;
        }

        .ns-info-band {
            margin: 0.8rem 0 1rem;
        }

        .ns-band-title {
            font-size: 0.9rem;
            color: var(--ns-text);
            margin-bottom: 0.25rem;
            font-weight: 600;
        }

        .ns-band-body {
            font-size: 0.84rem;
            line-height: 1.65;
        }

        .ns-list {
            display: grid;
            gap: 0.55rem;
            margin-top: 0.8rem;
        }

        .ns-list-item {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            padding-top: 0.55rem;
            border-top: 1px solid rgba(164, 185, 213, 0.1);
            font-size: 0.82rem;
        }

        .ns-list-item:first-child {
            border-top: 0;
            padding-top: 0;
        }

        .ns-list-label {
            color: var(--ns-muted);
        }

        .ns-list-value {
            color: var(--ns-text);
            font-weight: 600;
        }

        .ns-row-divider {
            margin: 0.35rem 0 0.6rem;
            border-bottom: 1px solid rgba(164, 185, 213, 0.12);
        }

        .ns-inline-label {
            color: var(--ns-muted);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
        }

        .ns-signal-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.45rem 0.78rem;
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.12);
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        @media (max-width: 980px) {
            .ns-hero {
                grid-template-columns: 1fr;
            }

            .main .block-container {
                padding-top: 1rem;
            }
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
    headline: str = "The orchestration layer for Indian equity intelligence.",
    show_nav: bool = True,
) -> None:
    """Render the shared sidebar shell."""
    risk = (risk_profile or "unassigned").capitalize()
    with st.sidebar:
        st.markdown(
            f"""
            <div class="ns-sidebar-brand">
                <div class="ns-sidebar-kicker">NiveshSutra</div>
                <h2>Market choreography</h2>
                <p class="ns-sidebar-copy">{escape(headline)}</p>
                <div class="ns-sidebar-chip-row">
                    <span class="ns-chip ns-chip--amber">{escape(user_email)}</span>
                    <span class="ns-chip ns-chip--emerald">Risk {escape(risk)}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if show_nav:
            st.markdown('<div class="ns-inline-label">Navigate</div>', unsafe_allow_html=True)
            for label, path, _ in NAV_ITEMS:
                st.page_link(path, label=label, disabled=label == active_page)
            st.markdown("")


def render_page_hero(
    *,
    kicker: str,
    title: str,
    body: str,
    pills: list[str] | None = None,
    aside_title: str | None = None,
    aside_rows: list[tuple[str, str]] | None = None,
) -> None:
    """Render a large editorial hero block."""
    pill_markup = "".join(
        f'<span class="ns-chip">{escape(item)}</span>' for item in (pills or [])
    )
    rows_markup = "".join(
        (
            '<div class="ns-aside-row">'
            f'<span class="ns-aside-label">{escape(label)}</span>'
            f'<span class="ns-aside-value">{escape(value)}</span>'
            "</div>"
        )
        for label, value in (aside_rows or [])
    )
    aside_markup = ""
    if aside_title or rows_markup:
        aside_markup = (
            '<div class="ns-hero-aside">'
            f"<h4>{escape(aside_title or 'Scene set')}</h4>"
            f"{rows_markup}"
            "</div>"
        )
    st.markdown(
        f"""
        <section class="ns-hero">
            <div>
                <div class="ns-kicker">{escape(kicker)}</div>
                <h1>{escape(title)}</h1>
                <p>{escape(body)}</p>
                <div class="ns-pill-row">{pill_markup}</div>
            </div>
            {aside_markup}
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section_heading(title: str, body: str = "", kicker: str = "") -> None:
    """Render a consistent section heading."""
    kicker_html = f'<div class="ns-kicker">{escape(kicker)}</div>' if kicker else ""
    body_html = f"<p>{escape(body)}</p>" if body else ""
    st.markdown(
        f"""
        <div class="ns-section-heading">
            {kicker_html}
            <h3>{escape(title)}</h3>
            {body_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_grid(items: list[dict[str, str]], columns: int | None = None) -> None:
    """Render a row of branded metric cards."""
    if not items:
        return
    column_count = columns or len(items)
    cols = st.columns(column_count)
    for index, item in enumerate(items):
        column = cols[index % column_count]
        tone = escape(item.get("tone", "emerald"))
        with column:
            st.markdown(
                f"""
                <div class="ns-metric-card ns-metric-tone--{tone}">
                    <div class="ns-metric-label">{escape(item.get("label", ""))}</div>
                    <div class="ns-metric-value">{escape(item.get("value", ""))}</div>
                    <div class="ns-metric-detail">{escape(item.get("detail", ""))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_info_band(title: str, body: str) -> None:
    """Render a short information band."""
    st.markdown(
        f"""
        <div class="ns-info-band">
            <div class="ns-band-title">{escape(title)}</div>
            <div class="ns-band-body">{escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_note_card(title: str, body: str, rows: list[tuple[str, str]] | None = None) -> None:
    """Render a compact explanatory card."""
    row_markup = "".join(
        (
            '<div class="ns-list-item">'
            f'<span class="ns-list-label">{escape(label)}</span>'
            f'<span class="ns-list-value">{escape(value)}</span>'
            "</div>"
        )
        for label, value in (rows or [])
    )
    st.markdown(
        f"""
        <div class="ns-note-card">
            <h4>{escape(title)}</h4>
            <div class="ns-band-body">{escape(body)}</div>
            <div class="ns-list">{row_markup}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, body: str) -> None:
    """Render a branded empty state."""
    st.markdown(
        f"""
        <div class="ns-empty-state">
            <h4>{escape(title)}</h4>
            <div class="ns-band-body">{escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_plotly_figure(fig, *, height: int = 320):
    """Apply the shared visual theme to Plotly figures."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(8,17,31,0.2)",
        font=dict(color="#f7f2e9", family="Space Grotesk"),
        xaxis=dict(
            gridcolor="rgba(164,185,213,0.12)",
            zerolinecolor="rgba(164,185,213,0.12)",
        ),
        yaxis=dict(
            gridcolor="rgba(164,185,213,0.12)",
            zerolinecolor="rgba(164,185,213,0.12)",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
            font=dict(color="#9aabc4"),
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        height=height,
    )
    return fig
