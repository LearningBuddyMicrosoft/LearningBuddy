import streamlit as st
from api_client import get_attempts

if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

st.title("📜 Past Attempts")

attempts = get_attempts()

if not attempts:
    st.info("No attempts found yet.")
    st.stop()

for a in sorted(attempts, key=lambda x: x["date"], reverse=True):
    if st.button(f"{a['date']} — Score {a['score']}", key=f"att_{a['id']}"):
        st.session_state.selected_attempt = a["id"]
        st.switch_page("pages/testpages/attempt_review.py")