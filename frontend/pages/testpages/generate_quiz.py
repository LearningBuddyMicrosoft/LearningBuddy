import streamlit as st
from pathlib import Path
from api_client import get_dashboard, generate_quiz, start_quiz, start_attempt
from pages.testpages.styles1 import apply_custom_css
apply_custom_css()
if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

st.set_page_config(page_title="Generate Quiz – Learning Buddy", page_icon="🎓", layout="centered")
st.markdown("""
<style>
.block-container {
    padding-top: 2.5rem; 
}
</style>
""", unsafe_allow_html=True)#removes top padding above logo
with st.sidebar:
    if st.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("pages/testpages/login.py")

st.markdown("Generate a quiz") 
col1,col2,col3=st.columns([1,1,1])
with col2:
    logo_path = Path(__file__).resolve().parents[2] / "logo.png"
    if logo_path.exists():
        st.image(logo_path.read_bytes(), width=400)
    else:
        st.warning("Logo file not found.")
st.caption("Select topics, configure your quiz, and let AI build it for you.")
st.markdown("<hr style='margin:0.2rem 0; border:1px solid #eee'>", unsafe_allow_html=True)

@st.cache_data(show_spinner=False, ttl=30)
def load_dashboard():
    return get_dashboard()

dashboard = load_dashboard()
subjects = dashboard.get("subjects", []) if dashboard else []
all_topics = [t for s in subjects for t in s.get("topics", [])]

if not all_topics:
    st.warning("You need at least one topic before generating a quiz.")
    if st.button("Go to Manage"):
        st.switch_page("pages/testpages/manage.py")
    st.stop()

topic_options = {t["name"]: t["id"] for t in all_topics}

with st.form("generate_quiz_form"):
    quiz_name = st.text_input("Quiz name", placeholder="e.g. Week 3 Revision")

    selected_topic_names = st.multiselect(
        "Topics to include",
        options=list(topic_options.keys()),
        help="Select one or more topics. Questions will be grounded in their uploaded materials.",
    )

    col1, col2 = st.columns(2)
    with col1:
        difficulty = st.slider("Difficulty level", min_value=1, max_value=3, value=3,
                               help="1 = Easy   3 = Hard")
    with col2:
        length = st.number_input("Number of questions", min_value=1, max_value=50, value=10, step=1)

    

    submitted = st.form_submit_button("Generate Quiz", use_container_width=True)

if submitted:
    if not quiz_name.strip():
        st.warning("Please give your quiz a name.")
        st.stop()
    if not selected_topic_names:
        st.warning("Select at least one topic.")
        st.stop()

    topic_ids = [topic_options[name] for name in selected_topic_names]

    with st.spinner("Generating your quiz… this may take a moment."):
        quiz = generate_quiz(
            name=quiz_name.strip(),
            difficulty_level=int(difficulty),
            length=int(length),
            topic_ids=topic_ids,
            open_ended = False,
        )

    if not quiz:
        st.stop()

    quiz_id = quiz["id"]
    st.success(f"Quiz '{quiz.get('name', quiz_name)}' generated!")

    with st.spinner("Preparing your quiz…"):
        quiz_detail = start_quiz(quiz_id)       # fetches questions
        attempt_id = start_attempt(quiz_id)     # creates attempt record

    if not quiz_detail or not attempt_id:
        st.error("Quiz was generated but could not be started. Please try again.")
        st.stop()

    # NOTE: We assume start_quiz returns:
    #   { "id": int, "name": str, "questions": [
    #       { "id": int, "text": str,
    #         "type": "mcq" | "open_ended",
    #         "options": ["A...", "B...", ...] }   # present only for MCQ
    #   ]}
    # Update field names in take_quiz.py too if your schema differs.

    st.session_state.quiz_data = quiz_detail
    st.session_state.attempt_id = attempt_id

    st.switch_page("pages/testpages/take_quiz.py")