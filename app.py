import streamlit as st
import requests
import uuid

st.set_page_config(page_title="Etlas AI Studio", page_icon="🤖")
st.title("🤖 Supabase Agent Chatbot")

api_token = os.environ["API_TOKEN"]
user_id = os.environ["USER_ID"]

url = "https://dhhwgviwnmzsfzbujchf.supabase.co/functions/v1/agent-handler"
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
        "useRAG": True,  # Always using RAG here; you can add toggle if needed
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        ai_message = result.get("message", "")
        st.session_state["conversation_history"].append(("AI", ai_message))

        # Show AI response
        with st.chat_message("assistant"):
            st.markdown(ai_message)

        if result.get("contextUsed"):
            st.info(f'Context Used: {result["contextUsed"]}')
    else:
        error_msg = f"Error: {response.status_code}\n{response.text}"
        st.session_state["conversation_history"].append(("AI", error_msg))
        with st.chat_message("assistant"):
            st.error(error_msg)
