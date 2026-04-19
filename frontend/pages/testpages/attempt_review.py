import streamlit as st
from api_client import get_attempt

if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

if "selected_attempt" not in st.session_state:
    st.warning("No attempt selected.")
    st.switch_page("pages/testpages/attempts.py")
    st.stop()

attempt_id = st.session_state.selected_attempt
attempt = get_attempt(attempt_id)

if not attempt:
    st.error("Could not load attempt")
    st.stop()

snapshot = attempt["quiz_snapshot"]
responses = attempt["responses"]

st.title(snapshot["quiz_name"])
st.write(f"Score: {attempt['score']}")

for q in snapshot["questions"]:
    st.markdown(f"### {q['text']}")

    r = next((r for r in responses if r["question_id"] == q["id"]), None)

    if r:
        if r["is_correct"]:
            st.success(f"Your answer: {r['selected_option']}")
        else:
            st.error(f"Your answer: {r['selected_option']}")
            st.info(f"Correct: {q['correct_answer']}")
            st.caption(r["feedback"])