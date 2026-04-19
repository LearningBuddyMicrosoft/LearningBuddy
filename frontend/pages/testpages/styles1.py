import streamlit as st
def apply_custom_css():
    st.markdown("""
    <style>
    /* Style for all buttons (default color) */
    div.stButton > button, 
    div[data-testid="stForm"] button {
        background-color: #205a56; 
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    /* Hover and active states for default buttons */
    div.stButton > button:hover,
    div[data-testid="stForm"] button:hover {
        background-color: #2f7a73;
    }

    div.stButton > button:active,
    div[data-testid="stForm"] button:active {
        transform: scale(0.98);
    }
    </style>
    """, unsafe_allow_html=True)