import streamlit as st
import os
import re

def show_topic_select():
    base_path = os.path.join("user_topics", st.session_state.username)
    if st.session_state.get("topic_changed", False):
        st.success(f"Topic changed to: {st.session_state.selected_topic}. Click 'Home' in the sidebar to continue.")
        st.session_state.topic_changed = False  
    os.makedirs(base_path, exist_ok=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.image("logo2.png", width=350)

    st.markdown("""
    <div class="hero-card">
        <h2>Select a Topic</h2>
    </div>
    """, unsafe_allow_html=True)

    # ---- EXISTING BUTTONS (still fine) ----
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("Biology", use_container_width=True):
            st.session_state.selected_topic = "Biology"
            st.session_state.page = "Home"
            st.session_state.topic_folder = os.path.join("user_topics", "Biology")
            st.session_state.topic_changed = True
            st.rerun()

    with c2:
        if st.button("Computer Science", use_container_width=True):
            st.session_state.selected_topic = "Computer Science"
            st.session_state.page = "Home"
            st.session_state.topic_folder = os.path.join("user_topics", "Computer Science")
            st.session_state.topic_changed = True
            st.rerun()

    with c3:
        if st.button("Business", use_container_width=True):
            st.session_state.selected_topic = "Business"
            st.session_state.page = "Home"
            st.session_state.topic_changed = True
            st.rerun()
    
    st.markdown("""
        <div class="hero-card">
            <h2>Or Create a New Topic</h2>
        </div>
        """, unsafe_allow_html=True)
    topic_name = st.text_input("Topic name")

    if st.button("Create Topic", use_container_width=True):
        if not topic_name.strip():
            st.warning("Please enter a topic name.")
        else:
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', topic_name.strip())
            folder_path = os.path.join(base_path, safe_name)
            os.makedirs(folder_path, exist_ok=True)           

            st.session_state.selected_topic = safe_name
            st.session_state.topic_folder = folder_path
            st.session_state.topic_changed = True
            st.session_state.page = "Home"
            st.rerun()
    st.markdown("### Your Existing Topics")


    topics = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]

    if not topics:
        st.info("No topics created yet.")
    else:
        cols = st.columns(3)

        for i, topic in enumerate(topics):
            with cols[i % 3]:
                if st.button(f" {topic}", use_container_width=True):
                    st.session_state.selected_topic = topic
                    st.session_state.topic_folder = os.path.join(base_path, topic)
                    st.session_state.page = "Home"
                    st.rerun()