import streamlit as st
from api_client import login, register

st.set_page_config(page_title="Login – Learning Buddy", page_icon="🎓", layout="centered")

# ── Already logged in ─────────────────────────────────────────────────────────
st.markdown("""
<style>
.block-container {
    padding-top: 2.5rem; 
}
</style>
""", unsafe_allow_html=True)#removes top padding above logo
if st.session_state.get("token"):
    st.switch_page("pages/testpages/dashboard.py")
col1,col2,col3=st.columns([1,2,1])
with col2:
    st.image("logo.png", width=500)
#st.caption("Your adaptive AI study assistant")
# st.divider()

tab_login, tab_register = st.tabs(["Log In", "Register"])

with tab_login:
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In", use_container_width=True)

    if submitted:
        if not username or not password:
            st.warning("Please enter both username and password.")
        else:
            ok, err = login(username, password)
            if ok:
                st.success("Logged in!")
                st.switch_page("pages/testpages/dashboard.py")
            else:
                st.error(err)

with tab_register:
    with st.form("register_form"):
        new_username = st.text_input("Choose a username")
        new_password = st.text_input("Choose a password", type="password")
        confirm_password = st.text_input("Confirm password", type="password")
        submitted_reg = st.form_submit_button("Create Account", use_container_width=True)

    if submitted_reg:
        if not new_username or not new_password:
            st.warning("Please fill in all fields.")
        elif new_password != confirm_password:
            st.error("Passwords do not match.")
        else:
            ok, err = register(new_username, new_password)
            if ok:
                st.success("Account created! You can now log in.")
            else:
                st.error(err)