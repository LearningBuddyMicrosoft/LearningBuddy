import streamlit as st

def get_theme_colors(theme):
    if theme == "Dark":
        return {
            "bg_gradient": "linear-gradient(135deg, #0f172a 0%, #111827 45%, #1e293b 100%)",
            "text_color": "#e5ecf6",
            "sub_text": "#94a3b8",
            "shell_bg": "#0f172a",
            "shell_button": "linear-gradient(180deg, #1e293b 0%, #111827 100%)",
            "card_bg": "rgba(15,23,42,0.88)",
            "card_bg_2": "rgba(15,23,42,0.92)",
            "border": "rgba(255,255,255,0.08)",
            "input_bg": "#111827",
            "option_bg": "#172033",
            "accent": "#ffd166",
            "accent_2": "#60a5fa",
            "success_bg": "#052e16",
            "success_border": "#22c55e",
            "error_bg": "#3f0d12",
            "error_border": "#ef4444",
            "warning_bg": "#3b2f0b",
            "warning_border": "#f59e0b",
            "badge_bg": "rgba(15,23,42,0.6)",  # Theme-based for badges/pills
            "pill_bg": "rgba(15,23,42,0.4)",   # Theme-based for stats pills
        }
    # Light theme: Use soft grays/blues instead of white
    return {
        "bg_gradient": "linear-gradient(135deg, #edf3ff 0%, #f8fbff 45%, #e6eefc 100%)",
        "text_color": "#172033",
        "sub_text": "#5b6783",
        "shell_bg": "#1f2a44",
        "shell_button": "linear-gradient(180deg, #2d3a5a 0%, #22304d 100%)",
        "card_bg": "rgba(240,248,255,0.88)",  # Soft blue-gray instead of white
        "card_bg_2": "rgba(240,248,255,0.94)",  # Soft blue-gray instead of white
        "border": "rgba(31,42,68,0.08)",
        "input_bg": "#f0f8ff",  # Light blue-gray instead of black/white
        "option_bg": "#e6f3ff",  # Light blue-gray instead of black/white
        "accent": "#ffd166",
        "accent_2": "#4c6fff",
        "success_bg": "#ecfdf3",
        "success_border": "#22c55e",
        "error_bg": "#fef2f2",
        "error_border": "#ef4444",
        "warning_bg": "#fff7ed",
        "warning_border": "#f59e0b",
        "badge_bg": "rgba(31,42,68,0.1)",  # Theme-based for badges/pills
        "pill_bg": "rgba(31,42,68,0.05)",   # Theme-based for stats pills
    }

def apply_custom_css(colors):
    st.markdown(f"""
    <style>
    .stApp {{
        background: {colors["bg_gradient"]};
        color: {colors["text_color"]};
    }}

    .block-container {{
        max-width: 1180px;
        padding-top: 0.6rem !important;
        padding-bottom: 5rem !important;
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    .main-navbar {{
        position: sticky;
        top: 0;
        z-index: 999;
        width: 100vw;
        margin-left: calc(-50vw + 50%);
        background: {colors["shell_bg"]};
        border-bottom: 1px solid {colors["border"]};
        box-shadow: 0 8px 20px rgba(0,0,0,0.16);
        padding: 12px 0;
        margin-bottom: 1rem;
    }}

    .hero-card {{
        background: {colors["card_bg"]};
        backdrop-filter: blur(10px);
        border: 1px solid {colors["border"]};
        border-radius: 16px;
        padding: 0.9rem 1.1rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.08);
        margin-bottom: 0.7rem;
    }}

    .hero-card h1 {{
        margin: 0 0 0.2rem 0 !important;
        font-size: 1.6rem !important;
        line-height: 1.1 !important;
    }}

    .hero-card h3 {{
        margin: 0 !important;
        font-size: 0.98rem !important;
        line-height: 1.2 !important;
    }}

    .hero-card p {{
        margin: 0.3rem 0 0 0 !important;
        font-size: 0.92rem !important;
        line-height: 1.3 !important;
    }}

    .content-card {{
        background: {colors["card_bg_2"]};
        border: 1px solid {colors["border"]};
        border-radius: 16px;
        padding: 1rem 1.1rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.08);
        margin-top: 0.5rem;
    }}

    .quiz-card {{
        background: {colors["card_bg_2"]};
        border: 1px solid {colors["border"]};
        border-radius: 16px;
        padding: 0.95rem 1rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.08);
        margin-top: 0.2rem;
    }}

    .quiz-topbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
        margin-bottom: 0.7rem;
        flex-wrap: wrap;
    }}

    .quiz-label {{
        font-size: 1rem;
        font-weight: 700;
        color: {colors["text_color"]};
    }}

    .quiz-meta {{
        font-size: 0.85rem;
        color: {colors["sub_text"]};
        font-weight: 600;
    }}

    .auth-shell {{
        max-width: 1000px;
        height:50px;
        margin: 12vh auto 0 auto;
        background: {colors["card_bg_2"]};
        border-radius: 22px;
        padding: 1.4rem;
        border: 1px solid {colors["border"]};
        box-shadow: 0 14px 32px rgba(0,0,0,0.12);
    }}
    .sign{{
        height:400px;
        background: {colors["shell_bg"]};  /* Use theme instead of hardcoded color */
    }}

    .auth-top {{
        text-align: center;
        margin-bottom: 0.8rem;
    }}

    .auth-badge {{
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        background: {colors["badge_bg"]};  /* Theme-based instead of white */
        color: {colors["accent"]};
        font-weight: 700;
        font-size: 0.9rem;
        margin-bottom: 0.7rem;
        border: 1px solid {colors["border"]};
    }}

    .subtle {{
        color: {colors["sub_text"]};
    }}

    .stats-pill {{
        display: inline-block;
        margin-right: 0.35rem;
        margin-top: 0.35rem;
        padding: 0.25rem 0.6rem;
        border-radius: 999px;
        background: {colors["pill_bg"]};  /* Theme-based instead of white */
        border: 1px solid {colors["border"]};
        font-weight: 600;
        font-size: 0.8rem;
        color: {colors["text_color"]};
    }}

    .review-correct {{
        background: {colors["success_bg"]};
        border: 1px solid {colors["success_border"]};
        border-radius: 14px;
        padding: 0.8rem;
        margin-bottom: 0.75rem;
    }}

    .review-wrong {{
        background: {colors["error_bg"]};
        border: 1px solid {colors["error_border"]};
        border-radius: 14px;
        padding: 0.8rem;
        margin-bottom: 0.75rem;
    }}

    .review-flagged {{
        background: {colors["warning_bg"]};
        border: 1px solid {colors["warning_border"]};
        border-radius: 14px;
        padding: 0.75rem;
        margin-bottom: 0.75rem;
    }}

    .footer-fixed {{
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background: {colors["shell_bg"]};
        color: {colors["text_color"]};
        text-align: center;
        padding: 11px 16px;
        font-size: 0.9rem;
        font-weight: 600;
        z-index: 999;
        border-top: 1px solid {colors["border"]};
        box-shadow: 0 -6px 16px rgba(0,0,0,0.14);
    }}

    div.stButton > button {{
        width:100%;
        max-width:320px;
        margin:0 auto;
        display: block;
        border-radius: 12px;
        border: 1px solid transparent;
        background: {colors["shell_button"]};  /* Use theme */
        color: white;
        font-weight: 600;
        padding: 0.65rem 0.8rem;
        font-size: 0.93rem;
        transition: all 0.25s ease;
        box-shadow: 0 4px 10px rgba(0,0,0,0.10);
        cursor: pointer;
    }}

    div.stButton > button:hover {{
        transform: translateY(-2px);
        border: 1px solid {colors["accent"]};
        background: linear-gradient(180deg, #33476d 0%, #293b60 100%);
        color: {colors["accent"]};
        box-shadow: 0 8px 18px rgba(0,0,0,0.18);
    }}

    div[data-baseweb="input"] > div {{
        border-radius: 12px !important;
        border: 1px solid {colors["border"]} !important;
        background: {colors["input_bg"]} !important;
    }}

    div[data-baseweb="input"] input {{
        color: {colors["text_color"]} !important;
        background: {colors["input_bg"]} !important;  /* Ensure no white */
    }}

    [data-testid="stFileUploader"] {{
        background: {colors["option_bg"]};
        border: 2px dashed {colors["border"]};
        border-radius: 14px;
        padding: 0.8rem;
    }}

    div[role="radiogroup"] > label {{
        background: {colors["option_bg"]};
        padding: 0.55rem 0.75rem;
        border-radius: 10px;
        border: 1px solid {colors["border"]};
        margin-bottom: 0.45rem;
        color: {colors["text_color"]};
    }}

    div[role="radiogroup"] > label[data-baseweb="radio"] {{
        background: {colors["option_bg"]} !important;  /* Override any white */
    }}

    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, {colors["accent_2"]}, {colors["accent"]});
    }}

    /* Additional overrides for selects, checkboxes, etc. */
    div[data-baseweb="select"] > div {{
        background: {colors["input_bg"]} !important;
        border: 1px solid {colors["border"]} !important;
        border-radius: 12px !important;
    }}

    div[data-baseweb="checkbox"] > div {{
        background: {colors["option_bg"]} !important;
    }}

    body, h1, h2, h3, h4, h5, h6, p, span, label, div {{
        color: {colors["text_color"]} !important;
    }}

    div.stButton > button {{
        color: white !important;
        -webkit-text-fill-color: white !important;
    }}

    @media (max-width: 768px) {{
        .hero-card, .content-card, .quiz-card, .auth-shell {{
            padding: 0.9rem;
            border-radius: 14px;
        }}

        .hero-card h1 {{
            font-size: 1.35rem !important;
        }}

        div.stButton > button {{
            font-size: 0.86rem;
            padding: 0.6rem 0.5rem;
        }}

        .quiz-topbar {{
            flex-direction: column;
            align-items: flex-start;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)