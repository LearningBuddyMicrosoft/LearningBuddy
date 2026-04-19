import streamlit as st
def apply_custom_css():
    st.markdown("""
    <style>
    div.stButton > button, /*change colour of all buttons*/
    div[data-testid="stForm"] button { /* change colour of login button*/

        background-color: #205a56 !important; 
        color: white !important;
        border: none !important;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    div.stButton > button:hover,
    div[data-testid="stForm"] button:hover {
        background-color: #2f7a73 !important;
    }

    div.stButton > button:active,
    div[data-testid="stForm"] button:active {
        transform: scale(0.98);
    }
    .card {/*card subjects for topics*/
    padding: 14px;
    border-radius: 12px;
    background-color: #11161c;
    border: 1px solid #2a2f36;
    margin-bottom: 12px;
    }
    .card-title {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 4px;
    }

    .card-subtitle {
        font-size: 13px;
        opacity: 0.7;
        margin-bottom: 10px;
    }
        </style>
    """, unsafe_allow_html=True)