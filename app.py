import streamlit as st
import requests
import uuid
import os

# Page config
st.set_page_config(page_title="Etlas AI Studio", page_icon="🤖")
st.title("🤖 Supabase Agent Chatbot")

# ✅ Clean env vars (remove quotes, extra spaces, accidental "KEY=" prefixes)
def clean_env(value: str) -> str:
    if not value:
        return ""
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]  # remove wrapping quotes
    if "=" in value and value.split("=")[0].isupper():
        # Handle accidental "API_TOKEN=xxx" pasted into Render
        value = value.split("=", 1)[1].strip()
    return value

api_token = clean_env(os.getenv("API_TOKEN", ""))
user_id = clean_env(os.getenv("USER_ID", ""))

if not api_token or not user_id:
    st.error("❌ Missing API_TOKEN or USER_ID in environment variables.")
    st.stop()

# Supabase edge function endpoint
url = "https://dhhwgviwnmzsfzbujchf.supabase.co/functions/v1/v2"
agent_id = "93dee35f-0ebe-42f6-beef-9a1abd1a6f12"

# Initialize conversation_id dynamically (hidden from UI)
if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = str(uuid.uuid4())

conversation_id = st.session_state["conversation_id"]

# Initialize chat history
if "conversation_history" not in st.session_state:
    st.session_state["conversation_history"] = []

# Display existing conversation
for sender, msg in st.session_state["conversation_history"]:
    with st.chat_message("user" if sender == "You" else "assistant"):
        st.markdown(msg)

# Chat input
message = st.chat_input("Type your message...")

if message:
    # Show user message
    st.session_state["conversation_history"].append(("You", message))
    with st.chat_message("user"):
        st.markdown(message)

    # Send to backend
    data = {
        "message": message,
        "agentId": agent_id,
        "conversationId": conversation_id,
        "userId": user_id,
        "useRAG": True,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        ai_message = result.get("message", "")
        st.session_state["conversation_history"].append(("AI", ai_message))

        with st.chat_message("assistant"):
            st.markdown(ai_message)

        if result.get("contextUsed"):
            st.info(f'📌 Context Used: {result["contextUsed"]}')
    except requests.exceptions.RequestException as e:
        error_msg = f"❌ Request failed: {e}"
        st.session_state["conversation_history"].append(("AI", error_msg))
        with st.chat_message("assistant"):
            st.error(error_msg)
