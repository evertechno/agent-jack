import streamlit as st
import requests
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AI Agent API Interface",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
        margin-bottom: 1rem;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #dc3545;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'current_conversation_id' not in st.session_state:
    st.session_state.current_conversation_id = None

# Load credentials from secrets
try:
    api_key = st.secrets["api"]["key"]
    base_url = st.secrets["api"]["base_url"]
    default_agent_id = st.secrets.get("defaults", {}).get("agent_id", "")
    default_user_id = st.secrets.get("defaults", {}).get("user_id", "")
    default_connection_id = st.secrets.get("defaults", {}).get("connection_id", "")
    secrets_loaded = True
except (KeyError, FileNotFoundError):
    secrets_loaded = False
    api_key = ""
    base_url = "https://dhhwgviwnmzsfzbujchf.supabase.co/functions/v1"
    default_agent_id = ""
    default_user_id = ""
    default_connection_id = ""

# Sidebar for API configuration
st.sidebar.markdown("## ⚙️ API Configuration")

if secrets_loaded:
    st.sidebar.success("✅ Credentials loaded from secrets")
    st.sidebar.markdown(f"**Base URL:** `{base_url}`")
    
    # Option to override API key
    override_key = st.sidebar.checkbox("Override API Key")
    if override_key:
        api_key = st.sidebar.text_input(
            "Custom API Key",
            type="password",
            help="Override the API key from secrets"
        )
else:
    st.sidebar.warning("⚠️ No secrets found. Using manual input.")
    api_key = st.sidebar.text_input(
        "API Key",
        type="password",
        help="Enter your Supabase API key"
    )
    base_url = st.sidebar.text_input(
        "Base URL",
        value="https://dhhwgviwnmzsfzbujchf.supabase.co/functions/v1",
        help="API base URL"
    )

# Main header
st.markdown('<div class="main-header">🤖 AI Agent API Interface</div>', unsafe_allow_html=True)

# Tab selection
tab1, tab2 = st.tabs(["💬 Agent Handler", "🗄️ Edge AI Agent (SQL)"])

# ===========================
# TAB 1: Agent Handler
# ===========================
with tab1:
    st.markdown('<div class="sub-header">Agent Handler Endpoint</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <strong>📝 Description:</strong> Interact with the AI agent for general conversations and RAG-enabled queries.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        agent_id = st.text_input(
            "Agent ID *",
            value=default_agent_id,
            placeholder="e.g., uuid-format-agent-id",
            help="Required: ID of the agent to interact with"
        )
        
        user_id = st.text_input(
            "User ID",
            value=default_user_id,
            placeholder="e.g., user-123",
            help="Recommended: User identifier for session management"
        )
    
    with col2:
        use_rag = st.checkbox(
            "Enable RAG",
            value=True,
            help="Enable knowledge base integration (default: true)"
        )
        
        continue_conversation = st.checkbox(
            "Continue Conversation",
            value=False,
            help="Continue the current conversation thread"
        )
    
    # Message input
    message = st.text_area(
        "Your Message *",
        placeholder="Type your message here...",
        height=100,
        help="Required: The message to send to the agent"
    )
    
    # Send button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        send_button = st.button("📤 Send Message", use_container_width=True, type="primary")
    with col2:
        clear_button = st.button("🗑️ Clear History", use_container_width=True)
    
    if clear_button:
        st.session_state.conversation_history = []
        st.session_state.current_conversation_id = None
        st.rerun()
    
    if send_button:
        if not api_key:
            st.error("⚠️ Please enter your API Key in the sidebar")
        elif not message:
            st.error("⚠️ Please enter a message")
        elif not agent_id:
            st.error("⚠️ Please enter an Agent ID")
        else:
            with st.spinner("🔄 Sending request..."):
                url = f"{base_url}/agent-handler"
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
                
                payload = {
                    "message": message,
                    "agentId": agent_id,
                    "useRAG": use_rag
                }
                
                if user_id:
                    payload["userId"] = user_id
                
                if continue_conversation and st.session_state.current_conversation_id:
                    payload["conversationId"] = st.session_state.current_conversation_id
                
                try:
                    response = requests.post(url, json=payload, headers=headers)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Store conversation ID
                        if "conversationId" in result:
                            st.session_state.current_conversation_id = result["conversationId"]
                        
                        # Add to history
                        st.session_state.conversation_history.append({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "user_message": message,
                            "agent_response": result.get("message", "No response"),
                            "metadata": result
                        })
                        
                        st.success("✅ Response received!")
                    else:
                        st.error(f"❌ Error {response.status_code}: {response.text}")
                        
                except Exception as e:
                    st.error(f"❌ Request failed: {str(e)}")
    
    # Display conversation history
    if st.session_state.conversation_history:
        st.markdown('<div class="sub-header">📜 Conversation History</div>', unsafe_allow_html=True)
        
        if st.session_state.current_conversation_id:
            st.info(f"🔗 Conversation ID: `{st.session_state.current_conversation_id}`")
        
        for idx, entry in enumerate(reversed(st.session_state.conversation_history)):
            with st.expander(f"💬 {entry['timestamp']}", expanded=(idx == 0)):
                st.markdown(f"**👤 You:** {entry['user_message']}")
                st.markdown(f"**🤖 Agent:** {entry['agent_response']}")
                
                # Show metadata
                with st.container():
                    st.markdown("**📊 Response Metadata:**")
                    col1, col2, col3 = st.columns(3)
                    
                    metadata = entry['metadata']
                    with col1:
                        st.metric("Model", metadata.get("model", "N/A"))
                    with col2:
                        st.metric("Tokens Used", metadata.get("usage", {}).get("tokens", "N/A"))
                    with col3:
                        st.metric("Context Used", metadata.get("contextUsed", {}).get("conversationHistory", "N/A"))
                    
                    if metadata.get("contextUsed", {}).get("ragResults"):
                        st.info(f"📚 RAG Context: {metadata['contextUsed']['ragResults']}")
                    
                    # Show full JSON
                    if st.checkbox(f"Show Full JSON {idx}", key=f"json_{idx}"):
                        st.json(metadata)

# ===========================
# TAB 2: Edge AI Agent (SQL)
# ===========================
with tab2:
    st.markdown('<div class="sub-header">Edge AI Agent - SQL Execution</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <strong>📝 Description:</strong> Execute SQL queries on your database through the AI agent.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        sql_user_id = st.text_input(
            "User ID *",
            value=default_user_id,
            placeholder="e.g., user-123",
            help="Required: User identifier for authorization",
            key="sql_user_id"
        )
    
    with col2:
        connection_id = st.text_input(
            "Connection ID",
            value=default_connection_id,
            placeholder="e.g., db-connection-uuid",
            help="Optional: ID of the database connection for SQL execution"
        )
    
    # SQL Query input
    sql_message = st.text_area(
        "SQL Query or Instruction *",
        placeholder="SELECT * FROM users LIMIT 10",
        height=150,
        help="Required: SQL query or natural language instruction"
    )
    
    # Example queries
    with st.expander("📖 Example Queries"):
        st.code("SELECT * FROM users LIMIT 10", language="sql")
        st.code("SELECT COUNT(*) FROM orders WHERE status = 'completed'", language="sql")
        st.code("Show me all active users created in the last 30 days", language="text")
    
    # Execute button
    col1, col2 = st.columns([1, 3])
    with col1:
        execute_button = st.button("⚡ Execute Query", use_container_width=True, type="primary")
    
    if execute_button:
        if not api_key:
            st.error("⚠️ Please enter your API Key in the sidebar")
        elif not sql_message:
            st.error("⚠️ Please enter a SQL query or instruction")
        elif not sql_user_id:
            st.error("⚠️ Please enter a User ID")
        else:
            with st.spinner("🔄 Executing query..."):
                url = f"{base_url}/edge-ai-agent"
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
                
                payload = {
                    "message": sql_message,
                    "userId": sql_user_id
                }
                
                if connection_id:
                    payload["connectionId"] = connection_id
                
                try:
                    response = requests.post(url, json=payload, headers=headers)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.markdown('<div class="success-box"><strong>✅ Query Executed Successfully</strong></div>', unsafe_allow_html=True)
                        
                        # Display results
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Action", result.get("action", "N/A"))
                        with col2:
                            st.metric("SQL Executed", result.get("sqlExecuted", "N/A"))
                        
                        # Execution result
                        if "executionResult" in result:
                            exec_result = result["executionResult"]
                            
                            st.markdown("**📊 Execution Result:**")
                            
                            if exec_result.get("success"):
                                st.success(exec_result.get("message", "Query executed successfully"))
                                
                                # Display SQL results
                                if "result" in exec_result and exec_result["result"]:
                                    st.markdown("**🔍 Query Results:**")
                                    
                                    results = exec_result["result"]
                                    if isinstance(results, list) and len(results) > 0:
                                        import pandas as pd
                                        df = pd.DataFrame(results)
                                        st.dataframe(df, use_container_width=True)
                                        
                                        # Download button
                                        csv = df.to_csv(index=False)
                                        st.download_button(
                                            label="📥 Download as CSV",
                                            data=csv,
                                            file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                            mime="text/csv"
                                        )
                                    else:
                                        st.info("No rows returned")
                            else:
                                st.error(f"⚠️ Execution failed: {exec_result.get('message', 'Unknown error')}")
                        
                        # Explanation
                        if "explanation" in result:
                            with st.expander("📖 Explanation"):
                                st.write(result["explanation"])
                        
                        # Full response
                        with st.expander("🔍 Full Response JSON"):
                            st.json(result)
                    else:
                        st.error(f"❌ Error {response.status_code}: {response.text}")
                        
                except Exception as e:
                    st.error(f"❌ Request failed: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #7f8c8d; padding: 1rem;">
    <p>🚀 AI Agent API Interface | Built with Streamlit</p>
    <p style="font-size: 0.9rem;">
        <strong>Endpoints:</strong><br>
        Agent Handler: <code>https://dhhwgviwnmzsfzbujchf.supabase.co/functions/v1/agent-handler</code><br>
        Edge AI Agent: <code>https://dhhwgviwnmzsfzbujchf.supabase.co/functions/v1/edge-ai-agent</code>
    </p>
</div>
""", unsafe_allow_html=True)
