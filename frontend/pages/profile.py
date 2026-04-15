# filepath: frontend/pages/profile.py
import streamlit as st

def show_profile():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.image("logo2.png", width=350) 
    st.markdown("""
    <div class="hero-card">
        <h1>Profile</h1>
        <p class="subtle">Manage your account settings and theme preferences.</p>
    </div>
    """, unsafe_allow_html=True)
    st.write(f"**Username:** {st.session_state.username}")
    st.write(f"**Theme:** {st.session_state.theme}")
    st.write(f"**Quiz Attempts:** {len(st.session_state.quiz_history)}")
    st.write(f"**Currently Flagged Questions:** {len(st.session_state.flagged_questions)}")
    c1, c2, _ = st.columns([1.1, 1.1, 3])
    with c1:
        if st.button("🌙 Toggle Dark Mode", use_container_width=True):
            st.session_state.theme = "Dark" if st.session_state.theme == "Light" else "Light"
            st.rerun()
    with c2:
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.page = "AuthLanding"
            st.session_state.auth_page = "Landing"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)