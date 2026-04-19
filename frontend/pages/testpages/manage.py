import os
import tempfile
import streamlit as st
from pages.testpages.styles1 import apply_custom_css
apply_custom_css()
DATABASE_URL = os.getenv("DATABASE_URL")
API_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

from api_client import (
    get_dashboard,
    create_subject,
    create_topic,
    upload_material,
    get_topic_details,
    get_questions_by_topic,
)

if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

st.set_page_config(page_title="Manage – Learning Buddy", page_icon="🎓", layout="wide")

with st.sidebar:
    if st.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("pages/testpages/login.py")
st.markdown("""
<style>
.block-container {
    padding-top: 2.5rem; 
}
</style>
""", unsafe_allow_html=True)#removes top padding above logo
st.markdown("Manage") 
col1,col2,col3=st.columns([1,1,1])
with col2:
    st.image("logo.png",width=400)
st.markdown("<hr style='margin:0.2rem 0; border:1px solid #eee'>", unsafe_allow_html=True)

@st.cache_data(show_spinner=False, ttl=30)
def load_dashboard():
    return get_dashboard()

def refresh():
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

dashboard = load_dashboard()
subjects = dashboard.get("subjects", []) if dashboard else []

tab_subjects, tab_topics, tab_upload, tab_details = st.tabs([
    "Subjects", "Topics", "Upload Material", "Topic Details"
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Subjects
# ════════════════════════════════════════════════════════════════════════════
with tab_subjects:
    st.subheader("Create a New Subject")

    with st.form("create_subject_form"):
        subject_name = st.text_input("Subject name", placeholder="e.g. Machine Learning")
        submitted = st.form_submit_button("Create Subject", use_container_width=True)

    if submitted:
        if not subject_name.strip():
            st.warning("Please enter a subject name.")
        else:
            ok, err = create_subject(subject_name.strip())
            if ok:
                st.success(f"Subject '{subject_name}' created!")
                refresh()
            else:
                st.error(err)

    st.markdown("<hr style='margin:0.2rem 0; border:1px solid #eee'>", unsafe_allow_html=True)
    st.markdown("### Existing Subjects")
    if not subjects:
        st.info("No subjects yet.")
    else:

        cols = st.columns(3)

        for i, subject in enumerate(subjects):
            topics = subject.get("topics", [])

            with cols[i % 3]:
                st.markdown(f"- **{subject['name']}**")

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Topics
# ════════════════════════════════════════════════════════════════════════════
with tab_topics:
    st.markdown("### Create a New Topic")

    if not subjects:
        st.warning("Create a subject first before adding topics.")
    else:
        subject_options = {s["name"]: s["id"] for s in subjects}

        with st.form("create_topic_form"):
            topic_name = st.text_input("Topic name", placeholder="e.g. Neural Networks")
            selected_subject = st.selectbox("Under subject", list(subject_options.keys()))
            submitted = st.form_submit_button("Create Topic", use_container_width=True)

        if submitted:
            if not topic_name.strip():
                st.warning("Please enter a topic name.")
            else:
                ok, err = create_topic(topic_name.strip(), subject_options[selected_subject])
                if ok:
                    st.success(f"Topic '{topic_name}' created under '{selected_subject}'!")
                    refresh()
                else:
                    st.error(err)

        st.markdown("<hr style='margin:0.2rem 0; border:1px solid #eee'>", unsafe_allow_html=True)
        st.subheader("Existing Topics by Subject")
        for s in subjects:
            with st.expander(f"{s['name']}"):
                if not s.get("topics"):
                    st.caption("No topics yet.")
                else:
                    for t in s["topics"]:
                        st.markdown(f"- **{t['name']}** ")

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — Upload Material
# ════════════════════════════════════════════════════════════════════════════
with tab_upload:
    st.subheader("Upload Lecture Material (PDF)")

    all_topics = [t for s in subjects for t in s.get("topics", [])]

    if not all_topics:
        st.warning("Create at least one topic before uploading materials.")
    else:
        topic_options = {f"{t['name']} (ID {t['id']})": t["id"] for t in all_topics}

        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
        selected_topic_label = st.selectbox("Link to topic", list(topic_options.keys()))

        if st.button("Upload", use_container_width=True, disabled=uploaded_file is None):
            topic_id = topic_options[selected_topic_label]

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
                
            with st.spinner("Uploading…"):
                result = upload_material(tmp_path, uploaded_file.name, topic_id)

            os.unlink(tmp_path)

            if result:
                st.success(f"'{uploaded_file.name}' uploaded successfully!")
            else:
                st.error("Upload failed. Check the backend logs.")

# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — Topic Details
# ════════════════════════════════════════════════════════════════════════════
with tab_details:
    st.subheader("View Topic Details")

    all_topics = [t for s in subjects for t in s.get("topics", [])]

    if not all_topics:
        st.info("No topics available.")
    else:
        topic_options = {f"{t['name']} (ID {t['id']})": t["id"] for t in all_topics}

        # Pre-select if navigated here from Dashboard
        default_label = None
        if st.session_state.get("selected_topic_id"):
            for label, tid in topic_options.items():
                if tid == st.session_state["selected_topic_id"]:
                    default_label = label
                    break

        selected_label = st.selectbox(
            "Select a topic",
            list(topic_options.keys()),
            index=list(topic_options.keys()).index(default_label) if default_label else 0,
        )
        topic_id = topic_options[selected_label]

        if st.button("Load Details", use_container_width=True):
            st.session_state["selected_topic_id"] = None
            with st.spinner("Fetching…"):
                details = get_topic_details(topic_id)
            if details:
                st.json(details)
            else:
                st.error("Could not load topic details.")

        if st.button("Load Questions", use_container_width=True):
            with st.spinner("Fetching questions..."):
                questions = get_questions_by_topic(topic_id)
                st.write(questions)
            if questions is None:
                st.error("Failed to fetch questions from backend")
            elif len(questions) == 0:
                st.warning("No questions found for this topic")
            else:
                st.success(f"Loaded {len(questions)} questions")

                for q in questions:
                    with st.container(border=True):
                        st.markdown(f"### {q.get('question_text', 'No question text')}")
                        st.markdown(f"**Difficulty:** {q.get('difficulty', 'N/A')}")
                        st.markdown(f"**Type:** {q.get('question_type', 'N/A')}")

                        options = q.get("options") or []
                        if options:
                            st.markdown("**Options:**")
                            for opt in options:
                                st.markdown(f"- {opt}")

                        st.markdown(f"**Answer:** `{q.get('correct_answer', '')}`")             
