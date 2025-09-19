import streamlit as st
import requests
import uuid

st.title("Supabase Agent Handler Chat")

# Load API token and user UUID from Streamlit secrets
api_token = st.secrets["API_TOKEN"]
user_id = st.secrets["USER_ID"]  # Add this to your .streamlit/secrets.toml

url = "https://dhhwgviwnmzsfzbujchf.supabase.co/functions/v1/agent-handler"
agent_id = "1d1de20a-20b2-4973-b36b-98b579af3bae"

# Initialize conversation_id dynamically (hidden from user)
if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = str(uuid.uuid4())

conversation_id = st.session_state["conversation_id"]

# Initialize session state for history
if "conversation_history" not in st.session_state:
    st.session_state["conversation_history"] = []

message = st.text_area("Message:", "", height=100)
use_rag = st.checkbox("Use RAG (Retrieval Augmented Generation)", value=True)

if st.button("Send"):
    if not message.strip():
        st.warning("Please enter a message before sending.")
    else:
        data = {
            "message": message,
            "agentId": agent_id,
            "conversationId": conversation_id,
            "userId": user_id,
            "useRAG": use_rag
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}"
        }
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            result = response.json()
            st.session_state["conversation_history"].append(("You", message))
            st.session_state["conversation_history"].append(("AI", result.get("message", "")))

            if result.get("contextUsed"):
                st.info(f'Context Used: {result["contextUsed"]}')
        else:
            st.error(f"Error: {response.status_code}\n{response.text}")

st.subheader("Conversation History")
for sender, msg in st.session_state["conversation_history"]:
    st.write(f"**{sender}:** {msg}")

# (conversation_id is kept internal, not displayed)
