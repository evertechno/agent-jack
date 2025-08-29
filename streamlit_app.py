import streamlit as st
import requests
import uuid

st.title("Supabase Agent Handler Chat")

# Load API token from Streamlit secrets
api_token = st.secrets["API_TOKEN"]

url = "https://dhhwgviwnmzsfzbujchf.supabase.co/functions/v1/agent-chat"
agent_id = "1d1de20a-20b2-4973-b36b-98b579af3bae"

message = st.text_area("Message:", "Hello, how can you help me?", height=100)
system_prompt = st.text_area("System Prompt:", "You are a helpful assistant.", height=50)
use_rag = st.checkbox("Use RAG (Retrieval Augmented Generation)", value=True)

if st.button("Send"):
    conversation_id = str(uuid.uuid4())
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }
    data = {
        "message": message,
        "agentId": agent_id,
        "systemPrompt": system_prompt,
        "conversationId": conversation_id,
        "useRAG": use_rag
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        st.success(result.get("message", "No message returned."))
        st.write("Conversation ID:", result.get("conversationId", conversation_id))
    else:
        st.error(f"Error: {response.status_code}\n{response.text}")
