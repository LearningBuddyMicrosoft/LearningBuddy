import streamlit as st

if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

st.set_page_config(page_title="Results – Learning Buddy", page_icon="🎓", layout="centered")

with st.sidebar:
    if st.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("pages/testpages/login.py")

st.title("Results")
st.divider()

attempt_id = st.session_state.get("last_attempt_id")
quiz_name = st.session_state.get("last_quiz_name", "Quiz")
answers_count = st.session_state.get("last_answers_count", 0)

if not attempt_id:
    st.info("No completed attempt found. Take a quiz first!")
    if st.button("Generate a Quiz"):
        st.switch_page("pages/testpages/generate_quiz.py")
    st.stop()

st.success("Your attempt has been submitted and recorded!")

col1, col2 = st.columns(2)
col1.metric("Quiz", quiz_name)
col2.metric("Answers submitted", answers_count)

st.divider()

# ── TODO: Detailed results ────────────────────────────────────────────────────
# Once your /end-quiz endpoint is ready, call it here with `attempt_id` to fetch
# per-question feedback and render it.
#
# Suggested shape to handle:
#   result = get_quiz_results(attempt_id)   # add to api_client.py
#   {
#       "score": 7,
#       "total": 10,
#       "questions": [
#           {
#               "id": 1,
#               "text": "...",
#               "student_answer": "B",
#               "correct_answer": "A",
#               "is_correct": False,
#               "explanation": "...",
#               "topic_reference": "Section 3.2",
#           },
#           ...
#       ]
#   }

st.info(
    "Detailed per-question feedback will appear here once the `/end-quiz` endpoint "
    "is implemented. Your attempt has been saved and will count towards progress tracking."
)

st.divider()
col_a, col_b = st.columns(2)
with col_a:
    if st.button("Back to Dashboard", use_container_width=True):
        st.switch_page("pages/testpages/dashboard.py")
with col_b:
    if st.button("Take Another Quiz", use_container_width=True):
        st.switch_page("pages/testpages/generate_quiz.py")