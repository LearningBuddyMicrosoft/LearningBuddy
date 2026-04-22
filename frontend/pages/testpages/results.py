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

# 1. Grab the graded data we saved in the previous step
result_data = st.session_state.get("last_quiz_result")

if result_data:
    feedback = result_data.get("feedback") or "No feedback provided."
    score = result_data.get("score", 0)

    # 2. Display the top-level metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Quiz", quiz_name)
    col2.metric("Final Score", score)
    col3.metric("Answered", answers_count)

    st.divider()
    
    # 3. Display the detailed AI feedback
    st.subheader("AI Feedback")
    with st.container(border=True):
        st.markdown(feedback)
    
else:
    st.warning("Could not load detailed results. Please try taking the quiz again.")

st.divider()

st.divider()
col_a, col_b = st.columns(2)
with col_a:
    if st.button("Back to Dashboard", use_container_width=True):
        st.switch_page("pages/testpages/dashboard.py")
with col_b:
    if st.button("Take Another Quiz", use_container_width=True):
        st.switch_page("pages/testpages/generate_quiz.py")
