import html
import re

import streamlit as st

from api_client import get_user_attempts, finish_attempt
from pages.testpages.styles1 import apply_custom_css, apply_results_page_css

# page setup
st.set_page_config(page_title="Results – Learning Buddy", page_icon="🎓", layout="wide")
apply_custom_css()

# redirect if not logged in
if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

with st.sidebar:
    if st.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("pages/testpages/login.py")

# pull attempt metadata
attempt_id = st.session_state.get("last_attempt_id")
quiz_name = st.session_state.get("last_quiz_name", "Quiz")
answers_count = st.session_state.get("last_answers_count", 0)

apply_results_page_css()

# no attempt found
if not attempt_id:
    st.info("No completed attempt found. Take a quiz first!")
    if st.button("Generate a Quiz"):
        st.switch_page("pages/testpages/generate_quiz.py")
    st.stop()

# cache key for graded data
cache_key = f"feedback_cache_{attempt_id}"

# fetch graded attempt if not cached
if cache_key not in st.session_state:
    with st.spinner("Generating AI feedback…"):
        graded = finish_attempt(attempt_id)
        if graded:
            st.session_state[cache_key] = graded

graded = st.session_state.get(cache_key, {})

def sanitize_text(value: str) -> str:
    text = str(value or "")
    text = re.sub(r"<\s*>", "", text)
    text = text.replace("</>", "").replace("<>", "")
    return html.escape(text).replace("\n", "  \n")


# extract graded data
score = graded.get("score", 0)
graded_questions = graded.get("graded_questions", [])
summary = graded.get("summary", "")

# header
st.markdown("<div class='results-shell'>", unsafe_allow_html=True)
st.markdown(
    f"""
    <section class="results-hero">
        <span class="results-eyebrow">Results workspace</span>
        <h1>{quiz_name}</h1>
        <p>Your latest attempt is recorded below, along with AI feedback and your full quiz history.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

# metrics
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

# layout for feedback + actions
top_col, side_col = st.columns([1.7, 1], gap="large")

with top_col:
    st.markdown("<div class='section-title'>AI Feedback</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-copy'>A concise summary of how this attempt went.</div>", unsafe_allow_html=True)

    if summary:
        st.markdown("<span class='status-pill'>Latest attempt graded</span>", unsafe_allow_html=True)
        st.success("Your attempt has been submitted and recorded.")
        st.markdown(summary, unsafe_allow_html=True)

        # detailed feedback
        if graded_questions:
            st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>Detailed Feedback</div>", unsafe_allow_html=True)

            for i, item in enumerate(graded_questions, start=1):
                question_text = sanitize_text(item.get("question_text", ""))
                your = sanitize_text(item.get("your_answer", ""))
                correct = sanitize_text(item.get("correct_answer", ""))
                explanation = sanitize_text(item.get("explanation", ""))
                practice_tip = sanitize_text(item.get("practice_tip", ""))
                source = sanitize_text(item.get("source", ""))

                is_correct = your == correct
                icon = "✅" if is_correct else "❌"

                # question header
                st.markdown(f"### {icon} Question {i}")
                st.markdown(f"**{question_text}**")

                # answers
                col_a, col_b = st.columns(2)
                with col_a:
                    if is_correct:
                        st.success(f"**Your answer:** {your}")
                    else:
                        st.error(f"**Your answer:** {your}")

                with col_b:
                    st.success(f"**Correct answer:** {correct}")

                # explanation + tip
                if explanation:
                    st.info(f"💬 {explanation}")

                if practice_tip:
                    st.warning(f"💡 {practice_tip}")

                if source:
                    st.caption(f"📘 Source: {source}")

                st.divider()

        # dismiss button
        if st.button("Dismiss Feedback", use_container_width=True):
            st.session_state.pop(cache_key, None)
            st.session_state.pop("last_attempt_id", None)
            st.session_state.pop("last_quiz_name", None)
            st.session_state.pop("last_answers_count", None)
            st.switch_page("pages/testpages/dashboard.py")

    else:
        st.warning("Could not load detailed feedback for this attempt.")

with side_col:
    st.markdown("<div class='section-title'>Next Move</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-copy'>Keep momentum going.</div>", unsafe_allow_html=True)

    if st.button("Take Another Quiz", use_container_width=True, type="primary"):
        st.switch_page("pages/testpages/generate_quiz.py")

    if st.button("Back to Dashboard", use_container_width=True):
        st.switch_page("pages/testpages/dashboard.py")

# history section
st.markdown("<div class='section-title'>All Quiz Attempts</div>", unsafe_allow_html=True)
st.markdown("<div class='section-copy'>Your grade book across all quizzes.</div>", unsafe_allow_html=True)

with st.spinner("Loading your grade book..."):
    attempts_data = get_user_attempts()

if not attempts_data:
    st.info("No completed attempts found.")
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
        st.markdown(f"<div class='history-title'>{quiz.get('quiz_name', 'Unknown Quiz')}</div>", unsafe_allow_html=True)

        if history_table:
            st.dataframe(history_table, use_container_width=True, hide_index=True)
        else:
            st.write("No attempts recorded for this quiz yet.")

        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
