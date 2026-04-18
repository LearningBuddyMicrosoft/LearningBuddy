import streamlit as st
from api_client import get_attempts

if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

st.title("📜 Past Attempts")

attempts_data = get_attempts()

if not attempts_data:
    st.info("No attempts found yet.")
    st.stop()

# 🔥 FLATTEN the grouped structure
flat_attempts = []
for quiz in attempts_data:
    for attempt in quiz["attempts"]:
        flat_attempts.append({
            "id": attempt["id"],
            "date": attempt["date"],
            "score": attempt["score"],
            "quiz_name": quiz["quiz_name"]
        })

# 🔥 SORT safely
for a in sorted(flat_attempts, key=lambda x: x["date"], reverse=True):
    if st.button(
        f"{a['date']} — {a['quiz_name']} — Score {a['score']}",
        key=f"att_{a['id']}"
    ):
        st.session_state.selected_attempt = a["id"]
        st.switch_page("pages/testpages/attempt_review.py")