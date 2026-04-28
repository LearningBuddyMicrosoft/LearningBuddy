import streamlit as st

from api_client import get_user_attempts
from pages.testpages.styles1 import apply_custom_css, apply_results_page_css

st.set_page_config(page_title="Results – Learning Buddy", page_icon="🎓", layout="wide")
apply_custom_css()


if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

with st.sidebar:
    if st.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("pages/testpages/login.py")

attempt_id = st.session_state.get("last_attempt_id")
quiz_name = st.session_state.get("last_quiz_name", "Quiz")
answers_count = st.session_state.get("last_answers_count", 0)
result_data = st.session_state.get("last_quiz_result")

apply_results_page_css()

if not attempt_id:
    st.info("No completed attempt found. Take a quiz first!")
    if st.button("Generate a Quiz"):
        st.switch_page("pages/testpages/generate_quiz.py")
    st.stop()

score = result_data.get("score", 0) if result_data else 0
feedback = result_data.get("feedback") if result_data else None
if feedback:
    feedback = feedback.replace("**Performance Summary**", "", 1).strip()

st.markdown("<div class='results-shell'>", unsafe_allow_html=True)
st.markdown(
    f"""
    <section class="results-hero">
        <span class="results-eyebrow">Results workspace</span>
        <h1>{quiz_name}</h1>
        <p>
            Your latest attempt is recorded below, along with AI feedback and your full quiz history in the same dark workspace.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

metric_cols = st.columns(4)
metrics = [
    ("Attempt", f"#{attempt_id}", "Latest submission recorded"),
    ("Score", f"{score}", "Final score from this attempt"),
    ("Answered", f"{answers_count}", "Responses included in grading"),
    ("Status", "Saved", "Ready for review"),
]

for col, (label, value, subtext) in zip(metric_cols, metrics):
    with col:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-subtext">{subtext}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

top_col, side_col = st.columns([1.7, 1], gap="large")

with top_col:
    st.markdown("<div class='section-title'>AI Feedback</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-copy'>A concise summary of how this latest attempt went.</div>",
        unsafe_allow_html=True,
    )

    if result_data:
        st.markdown("<span class='status-pill'>Latest attempt graded</span>", unsafe_allow_html=True)
        st.success("Your attempt has been submitted and recorded.")
        st.markdown(
            f"<div class='feedback-body'>{feedback or 'No feedback provided.'}</div>",
            unsafe_allow_html=True,
        )
        if st.button("Dismiss Feedback", use_container_width=True):
            del st.session_state["last_quiz_result"]
            st.rerun()
    else:
        st.warning("Could not load detailed feedback for this attempt.")

with side_col:
    st.markdown("<div class='section-title'>Next Move</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-copy'>Keep momentum going from here.</div>",
        unsafe_allow_html=True,
    )
    if st.button("Take Another Quiz", use_container_width=True, type="primary"):
        st.switch_page("pages/testpages/select_quiz.py")
    if st.button("Back to Dashboard", use_container_width=True):
        st.switch_page("pages/testpages/dashboard.py")

st.markdown("<div class='section-title'>All Quiz Attempts</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='section-copy'>Your grade book across all quizzes, organized by quiz name.</div>",
    unsafe_allow_html=True,
)

with st.spinner("Loading your grade book..."):
    attempts_data = get_user_attempts()

if not attempts_data:
    st.info("No completed attempts found. Take a quiz first!")
else:
    for quiz in attempts_data:
        total_q = quiz.get("total_questions", 0)
        history_table = []

        for i, attempt in enumerate(quiz.get("attempts", [])):
            item_score = attempt.get("score", 0)
            percentage = (item_score / total_q * 100) if total_q > 0 else 0
            history_table.append(
                {
                    "Attempt #": i + 1,
                    "Date": attempt.get("date", "Unknown"),
                    "Score": f"{item_score} / {total_q}",
                    "Grade": f"{percentage:.1f}%",
                }
            )

        st.markdown("<div class='history-card'>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='history-title'>{quiz.get('quiz_name', 'Unknown Quiz')}</div>",
            unsafe_allow_html=True,
        )
        if history_table:
            st.dataframe(history_table, use_container_width=True, hide_index=True)
        else:
            st.write("No attempts recorded for this quiz yet.")
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
