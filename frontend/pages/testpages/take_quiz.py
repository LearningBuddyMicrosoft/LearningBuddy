import streamlit as st
from api_client import submit_batch_answers

# Redirect if not logged in
if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

# Ensure quiz + attempt exist
if not st.session_state.get("quiz_data") or not st.session_state.get("attempt_id"):
    st.warning("No active quiz found. Please generate a quiz first.")
    if st.button("Generate a Quiz"):
        st.switch_page("pages/testpages/generate_quiz.py")
    st.stop()

st.set_page_config(page_title="Take Quiz – Learning Buddy", page_icon="🎓", layout="centered")

with st.sidebar:
    if st.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("pages/testpages/login.py")

quiz_data = st.session_state.quiz_data
attempt_id = st.session_state.attempt_id
questions = quiz_data.get("questions", [])
quiz_name = quiz_data.get("name", "Quiz")

# Store answers
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}

# Header
st.title(quiz_name)
answered = len([v for v in st.session_state.quiz_answers.values() if v is not None])
st.caption(f"Attempt ID: {attempt_id}  ·  {answered}/{len(questions)} answered")
st.progress(answered / len(questions) if questions else 0)
st.divider()

if not questions:
    st.error("This quiz has no questions.")
    st.stop()

# Render questions
for idx, q in enumerate(questions):
    qid = int(q["id"])
    q_text = q.get("question_text", f"Question {idx + 1}")
    options = q.get("options", [])

    # Get stored answer and derive index for radio
    stored_answer = st.session_state.quiz_answers.get(qid)
    stored_index = options.index(stored_answer) if stored_answer in options else None

    st.markdown(f"**Q{idx + 1}. {q_text}**")

    choice = st.radio(
        label=f"Q{idx + 1}",
        options=options,
        key=f"mcq_{qid}",
        label_visibility="collapsed",
        index=stored_index,
    )

    # Always update from the widget's current value
    if choice is not None and st.session_state.quiz_answers.get(qid) != choice:
        st.session_state.quiz_answers[qid] = choice
        st.rerun()

    st.divider()

# Submit / Cancel
col_submit, col_cancel = st.columns([3, 1])

with col_submit:
    do_submit = st.button("Submit Quiz", type="primary", use_container_width=True)

with col_cancel:
    if st.button("Cancel", use_container_width=True):
        st.session_state.quiz_data = None
        st.session_state.attempt_id = None
        st.session_state.quiz_answers = {}
        st.switch_page("pages/testpages/dashboard.py")

# Handle submission
if do_submit:
    unanswered = [i+1 for i, q in enumerate(questions)
                  if st.session_state.quiz_answers.get(int(q["id"])) is None]
    if unanswered:
        st.warning(f"Please answer all questions before submitting. Unanswered: Q{', Q'.join(map(str, unanswered))}")
        st.stop()

    # Build answers from session state at submit time
    answers = [
        {
            "attempt_id": attempt_id,
            "question_id": int(q["id"]),
            "selected_option": st.session_state.quiz_answers[int(q["id"])]
        }
        for q in questions
    ]

    with st.spinner("Submitting and grading your answers…"):
        batch_result = submit_batch_answers(
            attempt_id=attempt_id,
            answers=answers
        )

    if batch_result is None:
        st.error("Failed to submit answers.")
        st.stop()

    st.session_state.last_quiz_result = batch_result
    st.session_state.last_attempt_id = attempt_id
    st.session_state.last_quiz_name = quiz_name

    st.session_state.quiz_data = None
    st.session_state.attempt_id = None
    st.session_state.quiz_answers = {}

    st.switch_page("pages/testpages/results.py")