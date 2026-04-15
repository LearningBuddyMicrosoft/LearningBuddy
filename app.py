import os
import tempfile
import streamlit as st
from frontend.pages.helpers import initialize_session_state, reset_quiz, submit_quiz
from frontend.pages.styles import get_theme_colors, apply_custom_css
from frontend.pages.auth import show_auth
from frontend.pages.home import show_home
from frontend.pages.quiz import show_quiz
from frontend.pages.review import show_review
from frontend.pages.flagged import show_flagged
from frontend.pages.history import show_history
from frontend.pages.profile import show_profile
from frontend.pages.progress import show_progress
from frontend.pages.topic import show_topic_select

st.set_page_config(
    page_title="Learning Buddy",
    page_icon="📘",
    layout="wide"
)

initialize_session_state()
colors = get_theme_colors(st.session_state.theme)
apply_custom_css(colors)

if not st.session_state.authenticated:
    show_auth()
else:
    st.markdown("<div class='main-navbar'>", unsafe_allow_html=True)
    nav_options = ["Topic","Home", "Quiz", "Flagged", "History", "Profile", "Progress"]
    selected = st.sidebar.radio("Navigation", nav_options)
    st.session_state.page = selected
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.page == "Home":
        show_home(colors)
    elif st.session_state.page == "Quiz":
        show_quiz()
    elif st.session_state.page == "Review":
        show_review(colors)
    elif st.session_state.page == "Flagged":
        show_flagged()
    elif st.session_state.page == "History":
        show_history(colors)
    elif st.session_state.page == "Profile":
        show_profile()
    elif st.session_state.page == "Progress":
        show_progress()
    elif st.session_state.page == "Topic":
        show_topic_select()

st.markdown("""
<div class="footer-fixed">
    Learning Buddy © 2026
</div>
""", unsafe_allow_html=True)
