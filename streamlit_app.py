import streamlit as st
import requests
import uuid
from supabase import create_client, Client

st.set_page_config(page_title="Supabase Agent Chat", page_icon="🤖")
st.title("🤖 Supabase Agent Chatbot")

# --- Load secrets ---
# The API_TOKEN is the unique key for your enterprise customer from the 'api_keys' table
api_token = st.secrets["API_TOKEN"]
connection_id = st.secrets.get("CONNECTION_ID", None)

supabase_url = st.secrets.get("SUPABASE_URL", None)
supabase_key = st.secrets.get("SUPABASE_KEY", None)  # Use anon key for writing to the Leads table

# Ensure Supabase creds exist for the lead capture form
if not supabase_url or not supabase_key:
    st.error("🚨 Missing Supabase credentials in secrets.toml")
    st.stop()

# Setup Supabase client for public tables like 'Leads'
supabase: Client = create_client(supabase_url, supabase_key)

# --- Lead capture workflow ---
if "lead_captured" not in st.session_state:
    st.session_state["lead_captured"] = False

if not st.session_state["lead_captured"]:
    st.subheader("👋 Before we start, please tell us a bit about you:")

    with st.form("lead_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email ID")
        phone = st.text_input("Phone Number")
        submitted = st.form_submit_button("Continue")

    if submitted:
        if not name or not email or not phone:
            st.warning("⚠️ Please fill in all details before continuing.")
        else:
            # Save to Supabase leads table
            try:
                lead_data = {
                    "name": name,
                    "email": email,
                    "phone": phone
                }
                response = supabase.table("Leads").insert(lead_data).execute()

                if response.data:
                    st.success("✅ Thanks! You can now chat with the bot.")
                    st.session_state["lead_captured"] = True
                    st.experimental_rerun() # Rerun to show the chatbot UI immediately
                else:
                    st.error("❌ Failed to save lead. Try again.")
                    st.stop()

            except Exception as e:
                st.error(f"❌ Error saving to Supabase: {e}")
                st.stop()

# --- If lead captured, show chatbot ---
if st.session_state["lead_captured"]:
    url = "https://dhhwgviwnmzsfzbujchf.supabase.co/functions/v1/agent-handler"
    agent_id = "93dee35f-0ebe-42f6-beef-9a1abd1a6f12"

    # Initialize conversation_id dynamically
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

        # --- Send to backend ---
        # NOTE: We no longer send 'userId'. The user is identified by the API Token.
        data = {
            "message": message,
            "agentId": agent_id,
            "conversationId": conversation_id,
            "connectionId": connection_id,
            "useRAG": True,
            "databaseQuery": True
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}" # Securely sends the customer's API key
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            result = response.json()
            ai_message = result.get("message", "Sorry, I encountered an issue.")
            st.session_state["conversation_history"].append(("AI", ai_message))

            with st.chat_message("assistant"):
                st.markdown(ai_message)

            if result.get("contextUsed"):
                st.info(f'Context Used: {result["contextUsed"]}')
        else:
            error_msg = f"Error: {response.status_code}\n{response.text}"
            st.session_state["conversation_history"].append(("AI", error_msg))
            with st.chat_message("assistant"):
                st.error(error_msg)
