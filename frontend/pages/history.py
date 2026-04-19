import streamlit as st
from frontend.pages.styles import get_theme_colors

def show_history(colors):
    colors = get_theme_colors(st.session_state.theme)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.image("logo2.png", width=350)

    st.markdown(f"""
    <div class="hero-card">
        <h1>History</h1>
        <p class="subtle">Review your previous quiz attempts, scores, and timestamps.</p>
        <span class="stats-pill">{len(st.session_state.quiz_history)} Attempts</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='content-card'>", unsafe_allow_html=True)

    if not st.session_state.quiz_history:
        st.info("No quiz attempts yet. Complete a quiz and your history will appear here.")
    else:
        for idx, attempt in enumerate(st.session_state.quiz_history, start=1):
            st.markdown(f"""
            <div style="
                background:{colors["option_bg"]};
                border:1px solid {colors["border"]};
                border-radius:14px;
                padding:0.85rem;
                margin-bottom:0.75rem;">
                <strong>Attempt {idx}</strong><br>
                <strong>Score:</strong> {attempt['score']} / {attempt['total']}<br>
                <strong>Percentage:</strong> {attempt['percentage']}%<br>
                <strong>Completed:</strong> {attempt['timestamp']}<br>
                <strong>Flagged Questions:</strong> {attempt['flagged_count']}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)