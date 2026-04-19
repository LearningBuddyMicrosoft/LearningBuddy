import streamlit as st
from api_client import get_dashboard
from pages.testpages.styles1 import apply_custom_css
apply_custom_css()

st.set_page_config(page_title="Dashboard – Learning Buddy", page_icon="🎓", layout="wide")
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
st.markdown("Dashboard") 
col1,col2,col3=st.columns([1,1,1])
with col2:
    st.image("logo.png",width=400)
data = get_dashboard()
if not data:
    st.stop()

st.markdown(f"### Welcome back , {data['username']} 👋")
st.markdown("<hr style='margin:0.2rem 0; border:1px solid #eee'>", unsafe_allow_html=True)
subjects = data.get("subjects", [])

if not subjects:
    st.info("You have no subjects yet. Head to **Manage** to create your first subject and upload materials.")
    if st.button("Go to Manage"):
        st.switch_page("pages/testpages/manage.py")
    st.stop()

total_topics = sum(len(s.get("topics", [])) for s in subjects)

col1, col2 = st.columns(2)
col1.metric("Subjects", len(subjects))
col2.metric("Topics", total_topics)

st.markdown("<hr style='margin:0.2rem 0; border:1px solid #eee'>", unsafe_allow_html=True)
st.subheader("Your Subjects & Topics")


cols = st.columns(3)

for i, subject in enumerate(subjects):
    topics = subject.get("topics", [])

    with cols[i % 3]:
        with st.expander(
            f"{subject['name']} ({len(topics)} topic{'s' if len(topics) != 1 else ''})",
            expanded=False
        ):
            if not topics:
                st.markdown(
                    "<div style='opacity:0.7'>No topics yet</div>",
                    unsafe_allow_html=True
                )
            else:
                for topic in topics:
                    st.markdown(f"- {topic['name']}")
st.markdown("<hr style='margin-top:0.2rem 0; border:1px solid #eee'>", unsafe_allow_html=True)
col_a, col_b = st.columns(2)
with col_a:
    if st.button("Add Subject / Topic", use_container_width=True):
        st.switch_page("pages/testpages/manage.py")
with col_b:
    if st.button("Generate a Quiz", use_container_width=True):
        st.switch_page("pages/testpages/generate_quiz.py")