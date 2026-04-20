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
st.set_page_config(page_title="Upload – Learning Buddy", page_icon="🎓", layout="wide")
if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

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
        st.session_state.quiz_data = None
        st.session_state.attempt_id = None
        st.switch_page("pages/testpages/login.py")
st.markdown("Upload") 
col1,col2,col3=st.columns([1,1,1])
with col2:
    st.image("logo.png",width=400)

def load_dashboard():
    return get_dashboard()

dashboard = load_dashboard()
subjects = dashboard.get("subjects", []) if dashboard else []
st.subheader("Upload Lecture Material (PDF)")

all_topics = [t for s in subjects for t in s.get("topics", [])]

if not all_topics:
    st.warning("Create at least one topic before uploading materials.")
else:
    topic_options = {f"{t['name']}": t["id"] for t in all_topics}

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
col1,col2,col3=st.columns([1,2,1])
with col2:
    if st.button("Generate Quiz", use_container_width=True,disabled=uploaded_file is None):
                st.switch_page("pages/testpages/generate_quiz.py")
