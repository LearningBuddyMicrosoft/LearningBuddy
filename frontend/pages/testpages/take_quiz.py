import streamlit as st
from api_client import submit_batch_answers

if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

if not st.session_state.get("quiz_data") or not st.session_state.get("attempt_id"):
    st.warning("No active quiz found. Please generate a quiz first.")
    if st.button("Generate a Quiz"):
        st.switch_page("pages/testpages/generate_quiz.py")
    st.stop()

st.set_page_config(page_title="Take Quiz – Learning Buddy", page_icon="🎓", layout="centered")

st.markdown("""
<style>
.quiz-hero {
    padding: 1.2rem 1.3rem;
    border-radius: 20px;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: white;
    margin-bottom: 1rem;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 10px 24px rgba(0,0,0,0.16);
}
.quiz-hero h1 {
    margin: 0;
    font-size: 1.8rem;
    line-height: 1.1;
}
.quiz-hero p {
    margin: 0.45rem 0 0 0;
    color: #cbd5e1;
}
.quiz-meta {
    display: inline-block;
    margin-top: 0.7rem;
    margin-right: 0.45rem;
    padding: 0.3rem 0.7rem;
    border-radius: 999px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.08);
    font-size: 0.85rem;
    font-weight: 600;
}
.question-card {
    background: #0f172a;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 1rem 1rem 0.8rem 1rem;
    margin-bottom: 1rem;
    box-shadow: 0 6px 18px rgba(0,0,0,0.10);
}
.question-number {
    color: #94a3b8;
    font-size: 0.9rem;
    font-weight: 700;
    margin-bottom: 0.35rem;
}
.question-text {
    color: white;
    font-size: 1.05rem;
    font-weight: 600;
    line-height: 1.45;
    margin-bottom: 0.8rem;
}
.section-label {
    font-size: 0.92rem;
    font-weight: 700;
    color: #475569;
    margin-bottom: 0.3rem;
}
.submit-shell {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 1rem;
    margin-top: 0.8rem;
}
div.stButton > button {
    border-radius: 12px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🎓 Learning Buddy")
    st.caption("Focus on one question at a time and submit when ready.")
    st.divider()

    if st.button("Back to Dashboard", use_container_width=True):
        st.switch_page("pages/testpages/dashboard.py")

    if st.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("pages/testpages/login.py")

quiz_data = st.session_state.quiz_data
attempt_id = st.session_state.attempt_id
questions = quiz_data.get("questions", [])
quiz_name = quiz_data.get("name", "Quiz")

if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}

if not questions:
    st.error("This quiz has no questions. Please contact your administrator.")
    st.stop()

answered = len([v for v in st.session_state.quiz_answers.values() if v])
progress_value = answered / len(questions) if questions else 0

st.markdown(
    f"""
    <div class="quiz-hero">
        <h1>{quiz_name}</h1>
        <p>Answer each question carefully. You can still submit if some are left blank.</p>
        <span class="quiz-meta">Attempt ID: {attempt_id}</span>
        <span class="quiz-meta">{answered}/{len(questions)} answered</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.progress(progress_value)

for idx, q in enumerate(questions):
    qid = q["id"]
    q_text = q.get("text", q.get("question_text", f"Question {idx + 1}"))
    q_type = q.get("type", q.get("question_type", "mcq")).lower()

    st.markdown(
        f"""
        <div class="question-card">
            <div class="question-number">Question {idx + 1}</div>
            <div class="question-text">{q_text}</div>
        """,
        unsafe_allow_html=True,
    )

    if q_type == "mcq":
        options = q.get("options", [])
        display_options = ["— select an answer —"] + options
        current = st.session_state.quiz_answers.get(qid)
        default_idx = (options.index(current) + 1) if current in options else 0

        choice = st.radio(
            label=f"Answer for question {idx + 1}",
            options=display_options,
            index=default_idx,
            key=f"mcq_{qid}",
            label_visibility="collapsed",
        )
        st.session_state.quiz_answers[qid] = choice if choice != "— select an answer —" else None

    else:
        answer_text = st.text_area(
            label=f"Your answer for question {idx + 1}",
            value=st.session_state.quiz_answers.get(qid) or "",
            key=f"oe_{qid}",
            placeholder="Type your answer here…",
            height=120,
            label_visibility="collapsed",
        )
        st.session_state.quiz_answers[qid] = answer_text.strip() or None

    st.markdown("</div>", unsafe_allow_html=True)

unanswered = [
    f"Q{i + 1}"
    for i, q in enumerate(questions)
    if not st.session_state.quiz_answers.get(q["id"])
]

st.markdown('<div class="submit-shell">', unsafe_allow_html=True)

if unanswered:
    st.warning(f"You still have unanswered questions: {', '.join(unanswered)}")
else:
    st.success("All questions answered. Ready to submit.")

col_submit, col_cancel = st.columns([3, 1])

with col_submit:
    submit_label = "Submit Quiz" if not unanswered else f"Submit Anyway ({len(unanswered)} unanswered)"
    do_submit = st.button(submit_label, type="primary", use_container_width=True)

with col_cancel:
    if st.button("Cancel", use_container_width=True):
        st.session_state.quiz_data = None
        st.session_state.attempt_id = None
        st.session_state.quiz_answers = {}
        st.switch_page("pages/testpages/dashboard.py")

st.markdown("</div>", unsafe_allow_html=True)

if do_submit:
    answers_payload = [
        {"attempt_id": attempt_id, "question_id": qid, "selected_option": answer}
        for qid, answer in st.session_state.quiz_answers.items()
        if answer
    ]

    with st.spinner("Submitting and grading your answers…"):
        batch_result = submit_batch_answers(attempt_id, answers_payload)

    if batch_result is None:
        st.error("Failed to submit answers. Please try again.")
        st.stop()

    st.session_state.last_quiz_result = batch_result
    st.session_state.last_attempt_id = attempt_id
    st.session_state.last_quiz_name = quiz_name
    st.session_state.last_answers_count = len(answers_payload)

    st.session_state.quiz_data = None
    st.session_state.attempt_id = None
    st.session_state.quiz_answers = {}

    st.switch_page("pages/testpages/results.py")