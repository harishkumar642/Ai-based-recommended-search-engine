import streamlit as st
import requests

st.title("AI Recommendation System")

user_input = st.text_input("Enter input:")

if st.button("Get Recommendation"):
    try:
        # Replace with your API URL later
        url = "http://localhost:8000/recommend"
        params = {"user_id": user_input}

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            st.success(data)
        else:
            st.error("Error in API")

    except:
        st.error("Backend not running")
