import streamlit as st
from ai_backend import ai_query

st.title("Simple Query APP")
userInput = st.text_input("Ask something:")

if st.button("Submit"):
    if userInput.strip():
        with st.spinner("Thinking...."):
            result = ai_query(userInput)

            st.write(result)