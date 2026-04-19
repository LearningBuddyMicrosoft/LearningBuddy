import streamlit as st
from api_client import get_dashboard

if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

st.set_page_config(page_title="Dashboard – Learning Buddy", page_icon="🎓", layout="wide")

with st.sidebar:
    if st.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.session_state.quiz_data = None
        st.session_state.attempt_id = None
        st.switch_page("pages/testpages/login.py")

st.markdown("## Dashboard")

data = get_dashboard()
if not data:
    st.stop()

st.subheader(f"Welcome back, {data['username']} 👋")
st.divider()

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

st.divider()
st.subheader("Your Subjects & Topics")

for subject in subjects:
    topics = subject.get("topics", [])
    with st.expander(f"{subject['name']}  ({len(topics)} topic{'s' if len(topics) != 1 else ''})", expanded=True):
        if not topics:
            st.caption("No topics yet. Add one in the Manage page.")
        else:
            cols = st.columns(3)
            for i, topic in enumerate(topics):
                with cols[i % 3]:
                    st.markdown(f"**{topic['name']}**")
                    if st.button("View Details", key=f"topic_detail_{topic['id']}"):
                        st.session_state["selected_topic_id"] = topic["id"]
                        st.switch_page("pages/testpages/manage.py")

st.divider()
col_a, col_b = st.columns(2)
with col_a:
    if st.button("Add Subject / Topic", use_container_width=True):
        st.switch_page("pages/testpages/manage.py")
with col_b:
    if st.button("Generate a Quiz", use_container_width=True):
        st.switch_page("pages/testpages/generate_quiz.py")