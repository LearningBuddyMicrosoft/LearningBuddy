import streamlit as st
from api_client import get_user_attempts, finish_attempt

# redirect if not logged in
if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

st.set_page_config(page_title="Results – Learning Buddy", page_icon="🎓", layout="centered")

with st.sidebar:
    if st.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("pages/testpages/login.py")

st.title("Quiz Results & History")
st.divider()

# show feedback for the most recent attempt
attempt_id = st.session_state.get("last_attempt_id")
quiz_name = st.session_state.get("last_quiz_name", "Quiz")
result_data = st.session_state.get("last_quiz_result")

if attempt_id and result_data:
    score = result_data.get("score", 0)
    total = result_data.get("total", 0)

    st.success("Your attempt has been submitted and recorded.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Quiz", quiz_name)
    col2.metric("Final Score", score)
    col3.metric("Total Questions", total)

    with st.spinner("Generating AI feedback…"):
        feedback = finish_attempt(attempt_id)

    if feedback:
        st.subheader("AI Summary")
        st.write(feedback["summary"])

        st.subheader("Detailed Feedback")
        for item in feedback["details"]:
            correct = item["your_answer"] == item["correct_answer"]
            icon = "✅" if correct else "❌"
            st.markdown(f"### {icon} {item['question']}")
            st.write(f"**Your answer:** {item['your_answer']}")
            st.write(f"**Correct answer:** {item['correct_answer']}")
            st.info(item["explanation"])
            if not correct and item.get("practice_tip"):
                st.warning(f"💡 **Practice tip:** {item['practice_tip']}")
            st.write(f"**Source:** {item['source']}")
            st.divider()

    if st.button("Dismiss Feedback"):
        st.session_state.pop("last_quiz_result", None)
        st.session_state.pop("last_attempt_id", None)
        st.rerun()

    st.divider()

# show attempt history
st.header("📚 All Quiz Attempts")

with st.spinner("Loading your grade book..."):
    attempts_data = get_user_attempts()

if not attempts_data:
    st.info("No completed attempts found.")
else:
    for quiz in attempts_data:
        st.subheader(quiz.get("quiz_name", "Unknown Quiz"))
        total_q = quiz.get("total_questions", 0)

        rows = []
        for i, attempt in enumerate(quiz.get("attempts", [])):
            score = attempt.get("score", 0)
            pct = (score / total_q * 100) if total_q > 0 else 0

            rows.append({
                "Attempt #": i + 1,
                "Date": attempt.get("date", "Unknown"),
                "Score": f"{score}/{total_q}",
                "Grade": f"{pct:.1f}%"
            })

        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        st.write("")

st.divider()

col_a, col_b = st.columns(2)
with col_a:
    if st.button("Back to Dashboard", use_container_width=True):
        st.switch_page("pages/testpages/dashboard.py")
with col_b:
    if st.button("Take Another Quiz", use_container_width=True):
        st.switch_page("pages/testpages/generate_quiz.py")
