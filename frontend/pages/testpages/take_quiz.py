import streamlit as st

from api_client import submit_batch_answers
from pages.testpages.styles1 import apply_custom_css, apply_quiz_page_css

# page setup
st.set_page_config(page_title="Take Quiz – Learning Buddy", page_icon="🎓", layout="wide")
apply_custom_css()


def goto_question(index: int):
    # clamp navigation index to valid range
    if questions:
        st.session_state.current_question_index = max(0, min(index, len(questions) - 1))


# require login
if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

# require active quiz + attempt
if not st.session_state.get("quiz_data") or not st.session_state.get("attempt_id"):
    st.warning("No active quiz found. Please generate a quiz first.")
    if st.button("Generate a Quiz"):
        st.switch_page("pages/testpages/generate_quiz.py")
    st.stop()

with st.sidebar:
    if st.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("pages/testpages/login.py")

quiz_data = st.session_state.quiz_data
attempt_id = st.session_state.attempt_id
questions = quiz_data.get("questions", [])
quiz_name = quiz_data.get("name", "Quiz")

# store answers and current index in session
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}

if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0

if not questions:
    st.error("This quiz has no questions. Please contact your administrator.")
    st.stop()

goto_question(st.session_state.current_question_index)
apply_quiz_page_css()

# progress metrics
answered_count = sum(1 for q in questions if st.session_state.quiz_answers.get(q["id"]))
remaining_count = len(questions) - answered_count
completion_ratio = answered_count / len(questions) if questions else 0

current_index = st.session_state.current_question_index
current_question = questions[current_index]
current_qid = current_question["id"]
current_q_text = current_question.get(
    "text",
    current_question.get("question_text", f"Question {current_index + 1}"),
)

st.markdown("<div class='quiz-shell'>", unsafe_allow_html=True)
st.markdown(
    f"""
    <section class="quiz-hero">
        <span class="quiz-eyebrow">Quiz workspace</span>
        <h1>{quiz_name}</h1>
        <p>
            Stay in flow, move through questions one at a time, and keep an eye on your progress before you submit.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

metric_cols = st.columns(4)
metrics = [
    ("Progress", f"{answered_count}/{len(questions)}", "Questions answered"),
    ("Remaining", f"{remaining_count}", "Still left to review"),
    ("Attempt", f"#{attempt_id}", "Saved to your active session"),
    ("Completion", f"{completion_ratio:.0%}", "Ready to submit"),
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

st.markdown("<div style='margin-top: 0.35rem; margin-bottom: 0.7rem;'>", unsafe_allow_html=True)
st.progress(completion_ratio)
st.markdown("</div>", unsafe_allow_html=True)

nav_col, question_col = st.columns([0.95, 1.8], gap="large")

with nav_col:
    st.markdown("<div class='section-title'>Question Navigator</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='navigator-caption'>Jump to any question and track what is answered at a glance.</div>",
        unsafe_allow_html=True,
    )

    selected_label = st.selectbox(
        "Jump to question",
        options=[f"Q{i + 1}" for i in range(len(questions))],
        index=current_index,
        label_visibility="collapsed",
    )
    goto_question(int(selected_label[1:]) - 1)

    for idx, q in enumerate(questions):
        qid = q["id"]
        answered = bool(st.session_state.quiz_answers.get(qid))
        is_current = idx == st.session_state.current_question_index
        button_label = f"Q{idx + 1} · Answered" if answered else f"Q{idx + 1}"
        button_type = "primary" if is_current else "secondary"
        if st.button(button_label, key=f"jump_{qid}", use_container_width=True, type=button_type):
            goto_question(idx)
            st.rerun()

    st.markdown(
        f"<div class='footer-note'>Answered {answered_count} of {len(questions)}. "
        f"{remaining_count} still need attention.</div>",
        unsafe_allow_html=True,
    )

with question_col:
    st.markdown(
        f"""
        <span class="question-pill">Question {st.session_state.current_question_index + 1}</span>
        <div class="question-title">{current_q_text}</div>
        <div class="question-meta">
            Multiple choice question
        </div>
        """,
        unsafe_allow_html=True,
    )

    # MCQ only (open-ended disabled in generator)
    options = current_question.get("options", [])
    display_options = options
    current_answer = st.session_state.quiz_answers.get(current_qid)
    default_idx = options.index(current_answer) if current_answer in options else None

    choice = st.radio(
        label="Answer choices",
        options=display_options,
        index=default_idx,
        key=f"mcq_{current_qid}",
        label_visibility="collapsed",
    )
    st.session_state.quiz_answers[current_qid] = choice

    st.markdown(
        "<div class='answer-hint'>Pick the option that best matches your understanding.</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)
    prev_col, next_col = st.columns(2, gap="medium")
    with prev_col:
        if st.button(
            "Previous",
            use_container_width=True,
            disabled=st.session_state.current_question_index == 0,
        ):
            goto_question(st.session_state.current_question_index - 1)
            st.rerun()
    with next_col:
        if st.button(
            "Next",
            use_container_width=True,
            disabled=st.session_state.current_question_index == len(questions) - 1,
        ):
            goto_question(st.session_state.current_question_index + 1)
            st.rerun()

unanswered = [
    f"Q{i + 1}"
    for i, q in enumerate(questions)
    if not st.session_state.quiz_answers.get(q["id"])
]

if unanswered:
    st.warning(f"Still unanswered: {', '.join(unanswered)}")

st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
submit_col, cancel_col = st.columns([2.4, 1], gap="large")
with submit_col:
    submit_label = "Submit Quiz" if not unanswered else f"Submit anyway ({len(unanswered)} unanswered)"
    do_submit = st.button(submit_label, type="primary", use_container_width=True)
with cancel_col:
    if st.button("Cancel attempt", use_container_width=True):
        st.session_state.quiz_data = None
        st.session_state.attempt_id = None
        st.session_state.quiz_answers = {}
        st.session_state.current_question_index = 0
        st.switch_page("pages/testpages/dashboard.py")

st.markdown("</div>", unsafe_allow_html=True)

if do_submit:
    answers_payload = [
        {"attempt_id": attempt_id, "question_id": int(qid), "selected_option": answer}
        for qid, answer in st.session_state.quiz_answers.items()
        if answer is not None
    ]

    with st.spinner("Submitting and grading your answers..."):
        batch_result = submit_batch_answers(attempt_id, answers_payload)

    if batch_result is None:
        st.error("Failed to submit answers. Please try again.")
        st.stop()

    st.session_state.last_attempt_id = attempt_id
    st.session_state.last_quiz_name = quiz_name
    st.session_state.last_answers_count = len(answers_payload)

    st.session_state.quiz_data = None
    st.session_state.attempt_id = None
    st.session_state.quiz_answers = {}
    st.session_state.current_question_index = 0

    st.switch_page("pages/testpages/results.py")
