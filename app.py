import streamlit as st
import requests
import uuid
import os

# 🚀 Page config
st.set_page_config(page_title="Etlas AI Studio", page_icon="🤖", layout="wide")
st.title("🤖 Supabase Agent Chatbot")

# ✅ Clean env vars helper
def clean_env(value: str) -> str:
    if not value:
        return ""
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    if "=" in value and value.split("=")[0].isupper():
        value = value.split("=", 1)[1].strip()
    return value

# ✅ Load environment variables
api_token = clean_env(os.getenv("API_TOKEN", ""))
user_id = clean_env(os.getenv("USER_ID", ""))
HUSH_AUTH_TOKEN = clean_env(os.getenv("HUSH_AUTH_TOKEN", ""))

if not api_token or not user_id:
    st.error("❌ Missing API_TOKEN or USER_ID in environment variables.")
    st.stop()

if not HUSH_AUTH_TOKEN:
    st.error("❌ Missing HUSH_AUTH_TOKEN in environment variables.")
    st.stop()

# 🔗 API URLs
SUPABASE_AGENT_URL = "https://dhhwgviwnmzsfzbujchf.supabase.co/functions/v1/v2"
HUSH_URL = "https://kdikcecnfoqhzyoyizly.supabase.co/functions/v1/hush"
AGENT_ID = "93dee35f-0ebe-42f6-beef-9a1abd1a6f12"

# 🧠 Initialize session state
if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = str(uuid.uuid4())

if "conversation_history" not in st.session_state:
    st.session_state["conversation_history"] = []

conversation_id = st.session_state["conversation_id"]

# 🧩 Function to call Hush API
def call_hush_api(message: str, history: list):
    headers = {
        "Authorization": f"Bearer {HUSH_AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {"message": message, "conversationHistory": history}
    try:
        res = requests.post(HUSH_URL, headers=headers, json=data, timeout=60)
        res.raise_for_status()
        return res.text
    except requests.exceptions.RequestException as e:
        return f"❌ Hush API Error: {e}"

# 🧩 Function to call Supabase Agent API
def call_agent_api(message: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }
    data = {
        "message": message,
        "agentId": AGENT_ID,
        "conversationId": conversation_id,
        "userId": user_id,
        "useRAG": True,
    }
    try:
        response = requests.post(SUPABASE_AGENT_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result.get("message", ""), result.get("contextUsed", "")
    except requests.exceptions.RequestException as e:
        return f"❌ Request failed: {e}", None

# 💬 Display existing conversation
for sender, msg in st.session_state["conversation_history"]:
    with st.chat_message("user" if sender == "You" else "assistant"):
        st.markdown(msg)

# 💭 Chat input box
message = st.chat_input("Type your message...")

if message:
    # Save user message
    st.session_state["conversation_history"].append(("You", message))
    with st.chat_message("user"):
        st.markdown(message)

    # 🔍 Detect @hush command
    if "@hush" in message.lower():
        hush_text = message.split("@hush", 1)[1].strip()
        with st.spinner("🤫 Sending to Hush..."):
            ai_message = call_hush_api(hush_text, st.session_state["conversation_history"])
    else:
        with st.spinner("⚡ Thinking..."):
            ai_message, context_used = call_agent_api(message)
        if context_used:
            st.info(f'📌 Context Used: {context_used}')

    # Display AI response
    st.session_state["conversation_history"].append(("AI", ai_message))
    with st.chat_message("assistant"):
        st.markdown(ai_message)

# 💅 Enhanced UI styling
st.markdown(
    """
    <style>
    .stChatInput textarea {
        border-radius: 12px;
        border: 1px solid #dcdcdc;
        background-color: #fafafa;
    }
    .stChatMessage {
        border-radius: 14px;
        padding: 8px 14px;
    }
    .stAlert {
        margin-top: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True
)
