import streamlit as st
from pages.testpages.styles1 import apply_custom_css
from api_client import get_user_attempts, start_quiz, start_attempt

apply_custom_css()

if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

with st.sidebar:
    if st.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("pages/testpages/login.py")

st.markdown("""
<div class="hero-card">
    <h1>📜 My Quizzes</h1>
    <p class="subtle">Review your past attempts or retry a quiz.</p>
</div>
""", unsafe_allow_html=True)

attempts_data = get_user_attempts()

if not attempts_data:
    st.info("No attempts found yet. Generate and take a quiz to see your history here.")
    if st.button("Generate a Quiz", use_container_width=True):
        st.switch_page("pages/testpages/generate_quiz.py")
    st.stop()

# Backend returns a list of groups:
# [{"quiz_id", "quiz_name", "total_questions", "attempts": [{"id", "date", "score"}, ...]}, ...]
grouped = attempts_data if isinstance(attempts_data, list) else attempts_data.get("quizzes", [])

if not grouped:
    st.info("No attempts found yet.")
    st.stop()

for group in grouped:
    quiz_name = group.get("quiz_name", "Unnamed Quiz")
    quiz_attempts = group.get("attempts", [])
    # quiz_id is on the GROUP, not on each individual attempt
    quiz_id = group.get("quiz_id")
    total_questions = group.get("total_questions", 0)

    with st.expander(f"📚 {quiz_name}  ({len(quiz_attempts)} attempt(s))", expanded=False):
        for i, attempt in enumerate(sorted(quiz_attempts, key=lambda x: x.get("date", ""), reverse=True)):
            attempt_id = attempt.get("id")
            date = attempt.get("date") or "Unknown date"
            score = attempt.get("score")
            btn_key = f"{quiz_id}_{i}"

            if isinstance(score, (int, float)) and total_questions > 0:
                score_display = f"{int(score)} / {total_questions}"
            elif isinstance(score, (int, float)):
                score_display = str(int(score))
            else:
                score_display = "Not scored"

            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.markdown(f"🗓️ {date}")
            with col2:
                st.markdown(f"🎯 Score: **{score_display}**")
            with col3:
                review_col, retry_col = st.columns(2)
                with review_col:
                    if st.button("Review", key=f"review_{btn_key}"):
                        st.session_state.selected_attempt = attempt_id
                        st.switch_page("pages/testpages/attempt_review.py")
                with retry_col:
                    if quiz_id and st.button("Retry", key=f"retry_{btn_key}"):
                        with st.spinner("Loading quiz…"):
                            quiz_detail = start_quiz(quiz_id)
                            new_attempt_id = start_attempt(quiz_id)
                        if quiz_detail and new_attempt_id:
                            st.session_state.quiz_data = quiz_detail
                            st.session_state.attempt_id = new_attempt_id
                            st.switch_page("pages/testpages/take_quiz.py")
                        else:
                            st.error("Could not restart quiz. Please try again.")

            st.markdown("<hr style='margin:0.4rem 0; border:1px solid #333'>", unsafe_allow_html=True)