import streamlit as st


def _apply_css(css: str):
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def apply_custom_css():
    _apply_css(
        """
        div.stButton > button,
        div[data-testid="stForm"] button {
            background-color: #205a56;
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.2s ease;
        }

        div.stButton > button:hover,
        div[data-testid="stForm"] button:hover {
            background-color: #2f7a73;
        }

        div.stButton > button:active,
        div[data-testid="stForm"] button:active {
            transform: scale(0.98);
        }
        """
    )


QUIZ_PAGE_CSS = """
    :root {
        --quiz-bg: #0b1117;
        --quiz-panel: #121b24;
        --quiz-panel-2: #17222d;
        --quiz-panel-3: #1d2a36;
        --quiz-border: rgba(141, 170, 191, 0.16);
        --quiz-text: #eef4f8;
        --quiz-muted: #95a6b8;
        --quiz-accent: #43c6ac;
        --quiz-accent-soft: rgba(67, 198, 172, 0.16);
        --quiz-highlight: #7cc7ff;
        --quiz-warning: #f2c66d;
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at top left, rgba(67, 198, 172, 0.12), transparent 30%),
            radial-gradient(circle at top right, rgba(124, 199, 255, 0.12), transparent 24%),
            linear-gradient(180deg, #0d141b 0%, #091017 100%);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1c202b 0%, #171b25 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    [data-testid="stSidebar"] * {
        color: var(--quiz-text);
    }

    .block-container {
        max-width: 1250px;
        padding-top: 2.2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3, h4, p, label, span, div {
        color: var(--quiz-text);
    }

    .quiz-shell {
        display: grid;
        gap: 1.9rem;
    }

    .quiz-hero {
        padding: 2.1rem 2.15rem;
        border-radius: 28px;
        border: 1px solid var(--quiz-border);
        background:
            linear-gradient(135deg, rgba(67, 198, 172, 0.16), rgba(124, 199, 255, 0.09)),
            linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.01));
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.28);
    }

    .quiz-eyebrow {
        display: inline-block;
        margin-bottom: 0.85rem;
        padding: 0.3rem 0.65rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.05);
        color: #c8f4ea;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .quiz-hero h1 {
        margin: 0;
        font-size: clamp(2rem, 4vw, 3.3rem);
        line-height: 1;
        letter-spacing: -0.04em;
    }

    .quiz-hero p {
        margin: 1rem 0 0;
        max-width: 700px;
        color: var(--quiz-muted);
        font-size: 1rem;
        line-height: 1.7;
    }

    .metric-card {
        padding: 1.25rem 1.2rem;
        border-radius: 22px;
        border: 1px solid var(--quiz-border);
        background: linear-gradient(180deg, rgba(23, 34, 45, 0.96), rgba(18, 27, 36, 0.96));
        min-height: 148px;
        margin-top: 1.35rem;
    }

    .metric-label {
        margin-bottom: 0.7rem;
        color: var(--quiz-muted);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1;
    }

    .metric-subtext {
        margin-top: 0.75rem;
        color: var(--quiz-muted);
        font-size: 0.95rem;
        line-height: 1.5;
    }

    .section-card {
        padding: 1.6rem;
        border-radius: 24px;
        border: 1px solid var(--quiz-border);
        background: linear-gradient(180deg, rgba(18, 27, 36, 0.98), rgba(14, 21, 28, 0.98));
        box-shadow: 0 18px 48px rgba(0, 0, 0, 0.22);
    }

    .section-title {
        margin-top: 1.2rem;
        margin-bottom: 1rem;
        color: var(--quiz-text);
        font-size: 1.05rem;
        font-weight: 700;
    }

    .navigator-caption {
        color: var(--quiz-muted);
        font-size: 0.92rem;
        margin-bottom: 1.15rem;
        line-height: 1.55;
    }

    .question-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        background: var(--quiz-accent-soft);
        color: #d4fff5;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .question-title {
        margin: 1.2rem 0 0.7rem;
        font-size: clamp(1.45rem, 2.2vw, 2rem);
        line-height: 1.2;
        font-weight: 750;
    }

    .question-meta {
        color: var(--quiz-muted);
        font-size: 0.95rem;
        margin-bottom: 1.35rem;
    }

    .answer-hint {
        margin-top: 0.8rem;
        color: var(--quiz-muted);
        font-size: 0.92rem;
        line-height: 1.55;
    }

    .footer-note {
        color: var(--quiz-muted);
        font-size: 0.9rem;
        margin-top: 1rem;
        line-height: 1.55;
    }

    [data-testid="column"] {
        gap: 1rem;
    }

    [data-testid="stHorizontalBlock"] {
        gap: 1.2rem;
    }

    div[data-testid="stSelectbox"] {
        margin-bottom: 1rem;
    }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--quiz-accent), var(--quiz-highlight));
    }

    .stProgress > div > div {
        background-color: rgba(255, 255, 255, 0.08);
    }

    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    div[data-testid="stTextArea"] textarea {
        background: var(--quiz-panel-2);
        color: var(--quiz-text);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
    }

    div[data-testid="stTextArea"] textarea {
        min-height: 170px;
    }

    div[role="radiogroup"] {
        gap: 1rem;
    }

    div[role="radiogroup"] label {
        padding: 1rem 1.05rem;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.07);
        background: rgba(255, 255, 255, 0.02);
    }

    div[role="radiogroup"] label:hover {
        border-color: rgba(67, 198, 172, 0.4);
        background: rgba(67, 198, 172, 0.08);
    }

    div.stButton > button,
    div[data-testid="stForm"] button {
        min-height: 3.15rem;
        border-radius: 16px;
    }

    div.stButton {
        margin-top: 0.35rem;
    }

    div[data-testid="stVerticalBlock"] div.stButton > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.06);
    }

    div[data-testid="stAlert"] {
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    @media (max-width: 900px) {
        .block-container {
            padding-top: 1.2rem;
        }

        .quiz-hero {
            padding: 1.5rem;
        }

        .metric-card,
        .section-card {
            border-radius: 20px;
        }
    }
"""


RESULTS_PAGE_CSS = """
    :root {
        --quiz-bg: #0b1117;
        --quiz-panel: #121b24;
        --quiz-panel-2: #17222d;
        --quiz-border: rgba(141, 170, 191, 0.16);
        --quiz-text: #eef4f8;
        --quiz-muted: #95a6b8;
        --quiz-accent: #43c6ac;
        --quiz-accent-soft: rgba(67, 198, 172, 0.16);
        --quiz-highlight: #7cc7ff;
        --quiz-danger: #ff8d8d;
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at top left, rgba(67, 198, 172, 0.12), transparent 30%),
            radial-gradient(circle at top right, rgba(124, 199, 255, 0.12), transparent 24%),
            linear-gradient(180deg, #0d141b 0%, #091017 100%);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1c202b 0%, #171b25 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    [data-testid="stSidebar"] * {
        color: var(--quiz-text);
    }

    .block-container {
        max-width: 1250px;
        padding-top: 2.2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3, h4, p, label, span, div {
        color: var(--quiz-text);
    }

    .results-shell {
        display: grid;
        gap: 1.9rem;
    }

    .results-hero {
        padding: 2.1rem 2.15rem;
        border-radius: 28px;
        border: 1px solid var(--quiz-border);
        background:
            linear-gradient(135deg, rgba(67, 198, 172, 0.16), rgba(124, 199, 255, 0.09)),
            linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.01));
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.28);
    }

    .results-eyebrow {
        display: inline-block;
        margin-bottom: 0.85rem;
        padding: 0.3rem 0.65rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.05);
        color: #c8f4ea;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .results-hero h1 {
        margin: 0;
        font-size: clamp(2rem, 4vw, 3.2rem);
        line-height: 1;
        letter-spacing: -0.04em;
    }

    .results-hero p {
        margin: 1rem 0 0;
        max-width: 740px;
        color: var(--quiz-muted);
        font-size: 1rem;
        line-height: 1.7;
    }

    .metric-card {
        margin-top: 1.2rem;
        padding: 1.25rem 1.2rem;
        border-radius: 22px;
        border: 1px solid var(--quiz-border);
        background: linear-gradient(180deg, rgba(23, 34, 45, 0.96), rgba(18, 27, 36, 0.96));
        min-height: 148px;
    }

    .metric-label {
        margin-bottom: 0.7rem;
        color: var(--quiz-muted);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1;
    }

    .metric-subtext {
        margin-top: 0.75rem;
        color: var(--quiz-muted);
        font-size: 0.95rem;
        line-height: 1.5;
    }

    .section-card {
        padding: 1.6rem;
        border-radius: 24px;
        border: 1px solid var(--quiz-border);
        background: linear-gradient(180deg, rgba(18, 27, 36, 0.98), rgba(14, 21, 28, 0.98));
        box-shadow: 0 18px 48px rgba(0, 0, 0, 0.22);
    }

    .section-title {
        margin-top: 1.2rem;
        margin-bottom: 0.35rem;
        color: var(--quiz-text);
        font-size: 1.12rem;
        font-weight: 700;
    }

    .section-copy {
        color: var(--quiz-muted);
        font-size: 0.95rem;
        margin-bottom: 1.2rem;
        line-height: 1.6;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        background: var(--quiz-accent-soft);
        color: #d4fff5;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .feedback-body {
        padding: 1.2rem 1.25rem;
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.07);
        background: rgba(255, 255, 255, 0.02);
        color: var(--quiz-text);
        line-height: 1.65;
        margin-top: 0.95rem;
    }

    .history-card {
        padding: 1.2rem 1.25rem;
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.07);
        background: rgba(255, 255, 255, 0.02);
        margin-bottom: 1.2rem;
    }

    .history-title {
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 0.95rem;
    }

    [data-testid="column"] {
        gap: 1rem;
    }

    [data-testid="stHorizontalBlock"] {
        gap: 1.2rem;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 18px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.07);
        margin-top: 0.25rem;
    }

    div[data-testid="stDataFrame"] [role="grid"] {
        background: rgba(255, 255, 255, 0.02);
    }

    div.stButton > button,
    div[data-testid="stForm"] button {
        min-height: 3.15rem;
        border-radius: 16px;
    }

    div.stButton {
        margin-top: 0.45rem;
    }

    div[data-testid="stVerticalBlock"] div.stButton > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.06);
    }

    div[data-testid="stAlert"] {
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    @media (max-width: 900px) {
        .block-container {
            padding-top: 1.2rem;
        }

        .results-hero {
            padding: 1.5rem;
        }

        .metric-card,
        .section-card {
            border-radius: 20px;
        }
    }
"""


PROGRESS_PAGE_CSS = """
    :root {
        --quiz-bg: #0b1117;
        --quiz-panel: #121b24;
        --quiz-panel-2: #17222d;
        --quiz-border: rgba(141, 170, 191, 0.16);
        --quiz-text: #eef4f8;
        --quiz-muted: #95a6b8;
        --quiz-accent: #43c6ac;
        --quiz-accent-soft: rgba(67, 198, 172, 0.16);
        --quiz-highlight: #7cc7ff;
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at top left, rgba(67, 198, 172, 0.12), transparent 30%),
            radial-gradient(circle at top right, rgba(124, 199, 255, 0.12), transparent 24%),
            linear-gradient(180deg, #0d141b 0%, #091017 100%);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1c202b 0%, #171b25 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    [data-testid="stSidebar"] * {
        color: var(--quiz-text);
    }

    .block-container {
        max-width: 1250px;
        padding-top: 2.2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3, h4, p, label, span, div {
        color: var(--quiz-text);
    }

    .progress-shell {
        display: grid;
        gap: 1.9rem;
    }

    .progress-hero {
        padding: 2.1rem 2.15rem;
        border-radius: 28px;
        border: 1px solid var(--quiz-border);
        background:
            linear-gradient(135deg, rgba(67, 198, 172, 0.16), rgba(124, 199, 255, 0.09)),
            linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.01));
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.28);
    }

    .progress-eyebrow {
        display: inline-block;
        margin-bottom: 0.85rem;
        padding: 0.3rem 0.65rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.05);
        color: #c8f4ea;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .progress-hero h1 {
        margin: 0;
        font-size: clamp(2rem, 4vw, 3.2rem);
        line-height: 1;
        letter-spacing: -0.04em;
    }

    .progress-hero p {
        margin: 1rem 0 0;
        max-width: 760px;
        color: var(--quiz-muted);
        font-size: 1rem;
        line-height: 1.7;
    }

    .metric-card {
        margin-top: 1.2rem;
        padding: 1.25rem 1.2rem;
        border-radius: 22px;
        border: 1px solid var(--quiz-border);
        background: linear-gradient(180deg, rgba(23, 34, 45, 0.96), rgba(18, 27, 36, 0.96));
        min-height: 148px;
    }

    .metric-label {
        margin-bottom: 0.7rem;
        color: var(--quiz-muted);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1;
    }

    .metric-subtext {
        margin-top: 0.75rem;
        color: var(--quiz-muted);
        font-size: 0.95rem;
        line-height: 1.5;
    }

    .section-title {
        margin-top: 0.35rem;
        margin-bottom: 0.45rem;
        color: var(--quiz-text);
        font-size: 1.12rem;
        font-weight: 700;
    }

    .section-copy {
        color: var(--quiz-muted);
        font-size: 0.95rem;
        margin-bottom: 1.2rem;
        line-height: 1.6;
    }

    .mastery-card {
        padding: 1.25rem;
        border-radius: 22px;
        border: 1px solid rgba(255, 255, 255, 0.07);
        background: linear-gradient(180deg, rgba(18, 27, 36, 0.94), rgba(14, 21, 28, 0.94));
        min-height: 180px;
    }

    .mastery-title {
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 0.7rem;
    }

    .mastery-value {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 0.85rem;
    }

    .mastery-copy {
        margin-top: 0.8rem;
        color: var(--quiz-muted);
        font-size: 0.92rem;
        line-height: 1.55;
    }

    .mastery-stats {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 0.65rem;
        padding: 0.7rem 0.85rem;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        background: rgba(255, 255, 255, 0.03);
    }

    .mastery-stats-label {
        color: var(--quiz-muted);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .mastery-stats-value {
        color: var(--quiz-text);
        font-size: 0.94rem;
        font-weight: 700;
    }

    .topic-card {
        padding: 1.35rem;
        border-radius: 24px;
        border: 1px solid var(--quiz-border);
        background: linear-gradient(180deg, rgba(18, 27, 36, 0.98), rgba(14, 21, 28, 0.98));
        box-shadow: 0 18px 48px rgba(0, 0, 0, 0.22);
        margin-bottom: 1.4rem;
    }

    .topic-title {
        font-size: 1.08rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }

    .topic-copy {
        color: var(--quiz-muted);
        font-size: 0.93rem;
        margin-bottom: 1rem;
    }

    .trend-pill {
        display: inline-flex;
        align-items: center;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        background: var(--quiz-accent-soft);
        color: #d4fff5;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .trend-pill.down {
        background: rgba(255, 138, 138, 0.14);
        color: #ffd2d2;
    }

    .trend-pill.flat {
        background: rgba(124, 199, 255, 0.14);
        color: #d9efff;
    }

    .insight-stack {
        padding: 0.5rem 0 0;
    }

    .insight-label {
        color: var(--quiz-muted);
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-top: 1rem;
        margin-bottom: 0.35rem;
    }

    .insight-value {
        font-size: 1.5rem;
        font-weight: 800;
        line-height: 1.1;
    }

    .insight-subtext {
        color: var(--quiz-muted);
        font-size: 0.92rem;
        margin-top: 0.3rem;
    }

    [data-testid="column"] {
        gap: 1rem;
    }

    [data-testid="stHorizontalBlock"] {
        gap: 1.2rem;
    }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--quiz-accent), var(--quiz-highlight));
    }

    .stProgress > div > div {
        background-color: rgba(255, 255, 255, 0.08);
    }

    div[data-testid="stPlotlyChart"] {
        border-radius: 20px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.07);
        background: rgba(255, 255, 255, 0.02);
        padding: 0.35rem;
    }

    div[data-testid="stAlert"] {
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    @media (max-width: 900px) {
        .block-container {
            padding-top: 1.2rem;
        }

        .progress-hero {
            padding: 1.5rem;
        }

        .metric-card,
        .topic-card,
        .mastery-card {
            border-radius: 20px;
        }
    }
"""


def apply_quiz_page_css():
    _apply_css(QUIZ_PAGE_CSS)


def apply_results_page_css():
    _apply_css(RESULTS_PAGE_CSS)


def apply_progress_page_css():
    _apply_css(PROGRESS_PAGE_CSS)
