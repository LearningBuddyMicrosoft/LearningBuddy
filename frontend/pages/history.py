# filepath: frontend/pages/history.py
import streamlit as st
from frontend.pages.helpers import reset_quiz

def show_history(colors):
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.image("logo2.png", width=350) 
    st.markdown(f"""
    <div class="hero-card">
        <h1> History</h1>
        <p class="subtle">Review your previous quiz attempts, scores, and reopen any quiz for review or retake.</p>
        <span class="stats-pill">{len(st.session_state.quiz_history)} Attempts</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    if not st.session_state.quiz_history:
        st.info("No quiz attempts yet. Complete a quiz and your history will appear here.")
    else:
        subjects = sorted({attempt.get("subject", "Uncategorized") for attempt in st.session_state.quiz_history})
        topics = sorted({attempt.get("topic", "General") for attempt in st.session_state.quiz_history})
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            selected_subject = st.selectbox(
                "Filter by subject",
                ["All"] + subjects,
                key="history_subject_filter",
            )
        with filter_col2:
            selected_topic = st.selectbox(
                "Filter by topic",
                ["All"] + topics,
                key="history_topic_filter",
            )
        with filter_col3:
            sort_mode = st.selectbox(
                "Sort attempts",
                ["Newest first", "Subject (A-Z)", "Topic (A-Z)", "Highest score"],
                key="history_sort_mode",
            )
        filtered_history = [
            attempt for attempt in st.session_state.quiz_history
            if (selected_subject == "All" or attempt.get("subject", "Uncategorized") == selected_subject)
            and (selected_topic == "All" or attempt.get("topic", "General") == selected_topic)
        ]
        if sort_mode == "Subject (A-Z)":
            filtered_history = sorted(
                filtered_history,
                key=lambda attempt: (
                    attempt.get("subject", "Uncategorized").lower(),
                    attempt.get("topic", "General").lower(),
                    attempt.get("timestamp", ""),
                ),
            )
        elif sort_mode == "Topic (A-Z)":
            filtered_history = sorted(
                filtered_history,
                key=lambda attempt: (
                    attempt.get("topic", "General").lower(),
                    attempt.get("subject", "Uncategorized").lower(),
                    attempt.get("timestamp", ""),
                ),
            )
        elif sort_mode == "Highest score":
            filtered_history = sorted(
                filtered_history,
                key=lambda attempt: (
                    attempt.get("percentage", 0),
                    attempt.get("score", 0),
                ),
                reverse=True,
            )
        if not filtered_history:
            st.info("No quiz attempts match the current subject/topic filter.")
        for idx, attempt in enumerate(filtered_history, start=1):
            st.markdown(f"""
            <div style="
                background:{colors["option_bg"]};
                border:1px solid {colors["border"]};
                border-radius:14px;
                padding:0.85rem;
                margin-bottom:0.75rem;">
                <strong>{attempt.get('quiz_title', f'Attempt {idx}')}</strong><br>
                <strong>Subject:</strong> {attempt.get('subject', 'Uncategorized')}<br>
                <strong>Topic:</strong> {attempt.get('topic', 'General')}<br>
                <strong>Score:</strong> {attempt['score']} / {attempt['total']}<br>
                <strong>Percentage:</strong> {attempt['percentage']}%<br>
                <strong>Completed:</strong> {attempt['timestamp']}<br>
                <strong>Flagged Questions:</strong> {attempt['flagged_count']}
            </div>
            """, unsafe_allow_html=True)
            c1, c2, _ = st.columns([1.1, 1.1, 3])
            with c1:
                if st.button("👀 Review Attempt", key=f"review_attempt_{idx}", use_container_width=True):
                    st.session_state.history_review = attempt
                    st.session_state.review_mode = "All"
                    st.session_state.page = "Review"
                    st.rerun()
            with c2:
                if st.button(" Retake This Quiz", key=f"retake_attempt_{idx}", use_container_width=True):
                    st.session_state.questions = attempt["questions"]
                    reset_quiz()
                    st.session_state.page = "Quiz"
                    st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)