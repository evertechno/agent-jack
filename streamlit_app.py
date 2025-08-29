import streamlit as st
import requests

st.title("Supabase Agent Chat")

# Load API token from Streamlit secrets
api_token = st.secrets["API_TOKEN"]

url = "https://dhhwgviwnmzsfzbujchf.supabase.co/functions/v1/agent-1756492837863"

# User input for the message
user_message = st.text_area("Enter your message:", "Hello, how can you help me?", height=100)

if st.button("Send"):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }
    data = {
        "message": user_message,
        "stream": False
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        st.success(result.get("message", "No message returned."))
    else:
        st.error(f"Error: {response.status_code}\n{response.text}")
