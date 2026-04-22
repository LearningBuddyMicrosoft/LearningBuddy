import streamlit as st
import pandas as pd
from api_client import get_user_attempts  # Make sure this is imported!

if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

st.set_page_config(page_title="Results – Learning Buddy", page_icon="🎓", layout="centered")

with st.sidebar:
    if st.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("pages/testpages/login.py")

st.title("Quiz Results & History")
st.divider()

# ─── SECTION 1: LATEST ATTEMPT FEEDBACK ─────────────────────────────────────────
# If the user JUST finished a quiz, show their immediate feedback at the top.
result_data = st.session_state.get("last_quiz_result")
quiz_name = st.session_state.get("last_quiz_name", "Quiz")

if result_data:
    st.success("Your attempt has been submitted and recorded!")
    
    score = result_data.get("score", 0) 
    feedback = (
        result_data.get("ai_feedback")
        or result_data.get("feedback")
        or "No feedback provided."
    )
    answers_count = result_data.get(
        "answers_count",
        st.session_state.get("last_answers_count", 0)
    )
    wrong_questions = result_data.get("wrong_questions", [])

    col1, col2, col3 = st.columns(3)
    col1.metric("Quiz", quiz_name)
    col2.metric("Final Score", score)
    col3.metric("Answered", answers_count)

    st.subheader("AI Feedback")
    with st.container(border=True):
        st.markdown(feedback)

    if wrong_questions:
        st.subheader("Questions to Review")
        for index, item in enumerate(wrong_questions, start=1):
            st.markdown(
                f"{index}. **Question:** {item.get('question', 'Unknown question')}  \n"
                f"Your answer: `{item.get('selected_answer', 'No answer')}`  \n"
                f"Correct answer: `{item.get('correct_answer', 'Unknown')}`"
            )
    
    if st.button("Dismiss Feedback"):
        del st.session_state["last_quiz_result"]
        st.rerun()
        
    st.divider()

# ─── SECTION 2: ALL ATTEMPTS HISTORY ────────────────────────────────────────────
st.header("📚 All Quiz Attempts")

with st.spinner("Loading your grade book..."):
    attempts_data = get_user_attempts()

if not attempts_data:
    st.info("No completed attempts found. Take a quiz first!")
else:
    # Loop through the grouped data from your FastAPI endpoint
    for quiz in attempts_data:
        st.subheader(quiz.get("quiz_name", "Unknown Quiz"))
        total_q = quiz.get("total_questions", 0)
        
        # We will format the raw JSON into a clean list of dictionaries for Streamlit's dataframe
        history_table = []
        
        for i, attempt in enumerate(quiz.get("attempts", [])):
            score = attempt.get("score", 0)
            
            # Safely calculate the percentage to avoid dividing by zero
            percentage = (score / total_q * 100) if total_q > 0 else 0
            
            history_table.append({
                "Attempt #": i + 1,
                "Date": attempt.get("date", "Unknown"),
                "Score": f"{score} / {total_q}",
                "Grade": f"{percentage:.1f}%"
            })
            
        if history_table:
            # Display the data in a beautiful, un-editable table
            st.dataframe(history_table, use_container_width=True, hide_index=True)
        else:
            st.write("No attempts recorded for this quiz yet.")
            
        st.write("") # Spacer between quizzes

st.divider()

# ─── FOOTER NAVIGATION ──────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)
with col_a:
    if st.button("Back to Dashboard", use_container_width=True):
        st.switch_page("pages/testpages/dashboard.py")
with col_b:
    if st.button("Take Another Quiz", use_container_width=True):
        st.switch_page("pages/testpages/generate_quiz.py")
