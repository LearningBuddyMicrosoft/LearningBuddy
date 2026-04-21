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

with st.sidebar:
    if st.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("pages/testpages/login.py")

# NOTE: Assumes start_quiz returned:
#   { "id": int, "name": str, "questions": [
#       { "id": int, "text": str,
#         "type": "mcq" | "open_ended",
#         "options": ["A...", "B...", ...] }   # only for MCQ
#   ]}
# Adjust "text", "type", "options" below if your field names differ.

quiz_data = st.session_state.quiz_data
attempt_id = st.session_state.attempt_id
questions = quiz_data.get("questions", [])
quiz_name = quiz_data.get("name", "Quiz")

if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}   # { question_id: answer_string }

# ── Header ────────────────────────────────────────────────────────────────────
st.title(quiz_name)
answered = len([v for v in st.session_state.quiz_answers.values() if v])
st.caption(f"Attempt ID: {attempt_id}  ·  {answered}/{len(questions)} answered")
st.progress(answered / len(questions) if questions else 0)
st.divider()

if not questions:
    st.error("This quiz has no questions. Please contact your administrator.")
    st.stop()

# ── Render questions ──────────────────────────────────────────────────────────
for idx, q in enumerate(questions):
    qid = q["id"]
    q_text = q.get("text", q.get("question_text", f"Question {idx + 1}"))
    q_type = q.get("type", q.get("question_type", "mcq")).lower()

    st.markdown(f"**Q{idx + 1}.** {q_text}")

    if q_type == "mcq":
        options = q.get("options", [])
        display_options = ["— select an answer —"] + options
        current = st.session_state.quiz_answers.get(qid)
        default_idx = (options.index(current) + 1) if current in options else 0

        choice = st.radio(
            label="",
            options=display_options,
            index=default_idx,
            key=f"mcq_{qid}",
            label_visibility="collapsed",
        )
        st.session_state.quiz_answers[qid] = choice if choice != "— select an answer —" else None

    else:  # open_ended
        answer_text = st.text_area(
            label="Your answer",
            value=st.session_state.quiz_answers.get(qid) or "",
            key=f"oe_{qid}",
            placeholder="Type your answer here…",
            height=100,
            label_visibility="collapsed",
        )
        st.session_state.quiz_answers[qid] = answer_text.strip() or None

    st.divider()

# ── Submit ────────────────────────────────────────────────────────────────────
unanswered = [
    f"Q{i + 1}"
    for i, q in enumerate(questions)
    if not st.session_state.quiz_answers.get(q["id"])
]

if unanswered:
    st.warning(f"Unanswered: {', '.join(unanswered)}")

col_submit, col_cancel = st.columns([3, 1])
with col_submit:
    label = "Submit Quiz" if not unanswered else f"Submit anyway ({len(unanswered)} unanswered)"
    do_submit = st.button(label, type="primary", use_container_width=True)
with col_cancel:
    if st.button("Cancel", use_container_width=True):
        st.session_state.quiz_data = None
        st.session_state.attempt_id = None
        st.session_state.quiz_answers = {}
        st.switch_page("pages/testpages/dashboard.py")

if do_submit:
    # 1. Build the payload
    answers_payload = [
        {"attempt_id": attempt_id, "question_id": qid, "selected_option": answer}
        for qid, answer in st.session_state.quiz_answers.items()
        if answer
    ]

    # 2. Call the single, unified submission endpoint
    with st.spinner("Submitting and grading your answers…"):
        # Assuming your helper function is updated to match your backend payload
        batch_result = submit_batch_answers(attempt_id, answers_payload)

    if batch_result is None:
        st.error("Failed to submit answers. Please try again.")
        st.stop()

    # 3. THE CRUCIAL HAND-OFF: Save the graded result data for the Results page!
    st.session_state.last_quiz_result = batch_result 
    
    # Save the basic metadata
    st.session_state.last_attempt_id = attempt_id
    st.session_state.last_quiz_name = quiz_name
    st.session_state.last_answers_count = len(answers_payload)

    # 4. Clean up the active quiz memory
    st.session_state.quiz_data = None
    st.session_state.attempt_id = None
    st.session_state.quiz_answers = {}

    # 5. Jump to the results page!
    st.switch_page("pages/testpages/results.py")