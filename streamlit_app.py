import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ──────────────────────────────────────────────
# Page configuration
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="ETLAS Agent Interface",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .platform-ask  { background:#0f4c81; color:#ffffff; padding:.3rem .8rem; border-radius:20px; font-size:.8rem; font-weight:700; letter-spacing:.05em; }
    .platform-ent  { background:#1a1a2e; color:#e0b84d; padding:.3rem .8rem; border-radius:20px; font-size:.8rem; font-weight:700; letter-spacing:.05em; }
    .info-box    { background:#e8f4f8; padding:1rem; border-radius:6px; border-left:4px solid #1f77b4; margin-bottom:1rem; }
    .success-box { background:#d4edda; padding:1rem; border-radius:6px; border-left:4px solid #28a745; margin-bottom:1rem; }
    .error-box   { background:#f8d7da; padding:1rem; border-radius:6px; border-left:4px solid #dc3545; margin-bottom:1rem; }
    .sub-header  { font-size:1.3rem; font-weight:700; color:#2c3e50; margin-top:1.5rem; margin-bottom:.75rem; }
    .tool-card   { background:#f8f9fa; border:1px solid #dee2e6; border-radius:6px; padding:.75rem 1rem; margin-bottom:.5rem; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Session state defaults
# ──────────────────────────────────────────────
for key, default in {
    "platform":          "ASK.IO",
    "conv_history":      [],
    "composio_history":  [],
    "current_conv_id":   None,
    "composio_conv_id":  None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ──────────────────────────────────────────────
# Load BOTH platform configs from secrets upfront
# ──────────────────────────────────────────────
secrets_loaded = False
configs = {
    "ASK.IO": {
        "key":           "",
        "base_url":      "https://mlrunhzylyfxhtwhexjx.supabase.co/functions/v1",
        "agent_id":      "",
        "user_id":       "",
        "connection_id": "",
    },
    "Enterprise.IO": {
        "key":           "",
        "base_url":      "https://dhhwgviwnmzsfzbujchf.supabase.co/functions/v1",
        "agent_id":      "",
        "user_id":       "",
        "connection_id": "",
    },
}

try:
    configs["ASK.IO"].update({
        "key":           st.secrets["askio"]["key"],
        "base_url":      st.secrets["askio"].get("base_url", configs["ASK.IO"]["base_url"]),
        "agent_id":      st.secrets["askio"].get("agent_id", ""),
        "user_id":       st.secrets["askio"].get("user_id", ""),
        "connection_id": st.secrets["askio"].get("connection_id", ""),
    })
    configs["Enterprise.IO"].update({
        "key":      st.secrets["enterprise"]["key"],
        "base_url": st.secrets["enterprise"].get("base_url", configs["Enterprise.IO"]["base_url"]),
        "agent_id": st.secrets["enterprise"].get("agent_id", ""),
        "user_id":  st.secrets["enterprise"].get("user_id", ""),
    })
    secrets_loaded = True
except Exception:
    secrets_loaded = False

# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 ETLAS Agent Interface")

    selected_platform = st.radio(
        "Platform",
        options=["ASK.IO", "Enterprise.IO"],
        index=0 if st.session_state.platform == "ASK.IO" else 1,
        horizontal=True,
    )

    # Reset history when platform switches
    if selected_platform != st.session_state.platform:
        st.session_state.platform         = selected_platform
        st.session_state.conv_history     = []
        st.session_state.composio_history = []
        st.session_state.current_conv_id  = None
        st.session_state.composio_conv_id = None
        st.rerun()

    platform = st.session_state.platform
    cfg      = configs[platform]

    st.markdown("---")
    st.markdown("### ⚙️ Configuration")

    if secrets_loaded:
        st.success("✅ Credentials loaded from secrets")
        st.caption(f"**Base URL:** `{cfg['base_url']}`")
        if st.checkbox("Override API Key"):
            cfg["key"] = st.text_input("Custom API Key", type="password")
    else:
        st.warning("⚠️ No secrets found — manual input")
        cfg["key"]      = st.text_input("API Key",  type="password", key="manual_key")
        cfg["base_url"] = st.text_input("Base URL", value=cfg["base_url"], key="manual_url")

    st.markdown("---")
    if platform == "ASK.IO":
        st.markdown('<span class="platform-ask">● ASK.IO</span>', unsafe_allow_html=True)
        st.caption("`mlrunhzylyfxhtwhexjx.supabase.co`")
        st.caption("agent-handler · composio-enabled-agent · process-knowledge · semantic-search · db-query-handler")
    else:
        st.markdown('<span class="platform-ent">● Enterprise.IO</span>', unsafe_allow_html=True)
        st.caption("`dhhwgviwnmzsfzbujchf.supabase.co`")
        st.caption("agent-handler · composio-enabled-agent · process-knowledge-file · embed · search-knowledge")

# Active config shortcuts
api_key       = cfg["key"]
base_url      = cfg["base_url"]
default_agent = cfg["agent_id"]
default_user  = cfg["user_id"]
default_conn  = cfg["connection_id"]

# ──────────────────────────────────────────────
# Helper: POST
# ──────────────────────────────────────────────
def post(endpoint: str, payload: dict):
    url     = f"{base_url}/{endpoint}"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    resp    = requests.post(url, json=payload, headers=headers, timeout=60)
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, {"error": resp.text}

# ──────────────────────────────────────────────
# Helper: render tool executions
# ──────────────────────────────────────────────
def render_tool_executions(executions: list):
    if not executions:
        return
    st.markdown("**🔧 Tool Executions:**")
    for ex in executions:
        icon = "✅" if ex.get("status") == "success" else "❌"
        st.markdown(f"""
        <div class="tool-card">
            {icon} <strong>{ex.get('tool', 'unknown')}</strong>
            &nbsp;·&nbsp; <code>{ex.get('latency_ms', '?')} ms</code>
            &nbsp;·&nbsp; status: <em>{ex.get('status', '?')}</em>
        </div>
        """, unsafe_allow_html=True)
        with st.expander(f"Details — {ex.get('tool', '')}"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Arguments**")
                st.json(ex.get("arguments", {}))
            with c2:
                st.markdown("**Result**")
                st.json(ex.get("result", {}))

# ──────────────────────────────────────────────
# Helper: render conversation history
# ──────────────────────────────────────────────
def render_conv_history(history_key: str, conv_id_key: str):
    history = st.session_state[history_key]
    if not history:
        return
    st.markdown('<div class="sub-header">📜 Conversation History</div>', unsafe_allow_html=True)
    conv_id = st.session_state[conv_id_key]
    if conv_id:
        st.info(f"🔗 Conversation ID: `{conv_id}`")
    for idx, entry in enumerate(reversed(history)):
        with st.expander(f"💬 {entry['timestamp']}", expanded=(idx == 0)):
            st.markdown(f"**👤 You:** {entry['user_message']}")
            st.markdown(f"**🤖 Agent:** {entry['agent_response']}")
            meta = entry["metadata"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Model",        meta.get("model", "N/A"))
            c2.metric("Tokens",       meta.get("usage", {}).get("tokens", "N/A"))
            ctx = meta.get("contextUsed", {})
            c3.metric("Conv History", ctx.get("conversationHistory", "N/A"))
            if ctx.get("ragResults"):
                st.info(f"📚 RAG: {ctx['ragResults']}")
            render_tool_executions(ctx.get("toolExecutions", []))
            if st.checkbox("Show full JSON", key=f"json_{history_key}_{idx}"):
                st.json(meta)

# ──────────────────────────────────────────────
# Tabs
# ──────────────────────────────────────────────
if platform == "ASK.IO":
    tabs = st.tabs(["💬 Agent Handler", "🔧 Composio Agent", "📚 Knowledge Base", "🗄️ DB Query"])
else:
    tabs = st.tabs(["💬 Agent Handler", "🔧 Composio Agent", "📚 Knowledge Base"])

# ══════════════════════════════════════════════
# TAB 1 — Agent Handler
# ══════════════════════════════════════════════
with tabs[0]:
    st.markdown('<div class="sub-header">Agent Handler</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
    <strong>📝</strong> General-purpose agent conversations with optional RAG knowledge-base context.
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        ah_agent_id = st.text_input("Agent ID *", value=default_agent, key="ah_agent")
        ah_user_id  = st.text_input("User ID",    value=default_user,  key="ah_user")
    with c2:
        ah_use_rag  = st.checkbox("Enable RAG",            value=True,  key="ah_rag")
        ah_continue = st.checkbox("Continue Conversation", value=False, key="ah_cont")

    ah_message = st.text_area("Your Message *", height=110, key="ah_msg")

    b1, b2, _ = st.columns([1, 1, 3])
    with b1:
        ah_send = st.button("📤 Send", use_container_width=True, type="primary", key="ah_send")
    with b2:
        if st.button("🗑️ Clear", use_container_width=True, key="ah_clear"):
            st.session_state.conv_history    = []
            st.session_state.current_conv_id = None
            st.rerun()

    if ah_send:
        if not api_key:
            st.error("⚠️ Enter your API Key in the sidebar")
        elif not ah_agent_id:
            st.error("⚠️ Agent ID is required")
        elif not ah_message:
            st.error("⚠️ Message cannot be empty")
        else:
            payload = {"message": ah_message, "agentId": ah_agent_id, "useRAG": ah_use_rag}
            if ah_user_id:
                payload["userId"] = ah_user_id
            if ah_continue and st.session_state.current_conv_id:
                payload["conversationId"] = st.session_state.current_conv_id

            with st.spinner("🔄 Waiting for agent…"):
                try:
                    code, result = post("agent-handler", payload)
                    if code == 200:
                        if "conversationId" in result:
                            st.session_state.current_conv_id = result["conversationId"]
                        st.session_state.conv_history.append({
                            "timestamp":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "user_message":   ah_message,
                            "agent_response": result.get("message", "No response"),
                            "metadata":       result,
                        })
                        st.success("✅ Response received!")
                        st.rerun()
                    else:
                        st.error(f"❌ Error {code}: {result}")
                except Exception as e:
                    st.error(f"❌ Request failed: {e}")

    render_conv_history("conv_history", "current_conv_id")

# ══════════════════════════════════════════════
# TAB 2 — Composio Agent
# ══════════════════════════════════════════════
with tabs[1]:
    st.markdown('<div class="sub-header">Composio-Enabled Agent</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
    <strong>🔧</strong> Enterprise agent that invokes real third-party tools — Gmail, Slack, GitHub,
    Notion, Linear, HubSpot, and 250+ more via the Composio gateway.
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        ca_agent_id = st.text_input("Agent ID *", value=default_agent, key="ca_agent",
                                    help="Must have Composio tool assignments configured")
    with c2:
        ca_use_rag  = st.checkbox("Enable RAG",            value=True,  key="ca_rag")
        ca_continue = st.checkbox("Continue Conversation", value=False, key="ca_cont")

    ca_message = st.text_area("Instruction *", height=110, key="ca_msg",
                               placeholder='e.g. "Send a Slack message to #general: Deploy complete ✅"')

    with st.expander("📖 Example instructions"):
        st.markdown("""
- `Send a Slack message to #general: "Deploy complete ✅"`
- `Create a Linear issue: Fix checkout bug — High priority`
- `Email team@company.com: subject Q2 Report`
- `Create a GitHub issue in my-repo: Authentication timeout`
        """)

    b1, b2, _ = st.columns([1, 1, 3])
    with b1:
        ca_send = st.button("📤 Send", use_container_width=True, type="primary", key="ca_send")
    with b2:
        if st.button("🗑️ Clear", use_container_width=True, key="ca_clear"):
            st.session_state.composio_history = []
            st.session_state.composio_conv_id = None
            st.rerun()

    if ca_send:
        if not api_key:
            st.error("⚠️ Enter your API Key in the sidebar")
        elif not ca_agent_id:
            st.error("⚠️ Agent ID is required")
        elif not ca_message:
            st.error("⚠️ Instruction cannot be empty")
        else:
            payload = {"message": ca_message, "agentId": ca_agent_id, "useRAG": ca_use_rag}
            if ca_continue and st.session_state.composio_conv_id:
                payload["conversationId"] = st.session_state.composio_conv_id

            with st.spinner("🔄 Agent executing tools…"):
                try:
                    code, result = post("composio-enabled-agent", payload)
                    if code == 200:
                        if "conversationId" in result:
                            st.session_state.composio_conv_id = result["conversationId"]
                        ctx   = result.get("contextUsed", {})
                        execs = ctx.get("toolExecutions", [])
                        st.session_state.composio_history.append({
                            "timestamp":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "user_message":   ca_message,
                            "agent_response": result.get("message", "No response"),
                            "metadata":       result,
                        })
                        st.success("✅ Agent completed!")
                        if execs:
                            st.info(f"🔧 {len(execs)} tool(s) executed · {ctx.get('toolsAvailable', '?')} available")
                        st.rerun()
                    else:
                        st.error(f"❌ Error {code}: {result}")
                except Exception as e:
                    st.error(f"❌ Request failed: {e}")

    render_conv_history("composio_history", "composio_conv_id")

# ══════════════════════════════════════════════
# TAB 3 — Knowledge Base
# ══════════════════════════════════════════════
with tabs[2]:
    st.markdown('<div class="sub-header">Knowledge Base</div>', unsafe_allow_html=True)

    if platform == "ASK.IO":
        st.markdown("""
        <div class="info-box">
        <strong>📚 ASK.IO:</strong> Ingest via <code>process-knowledge</code>,
        search via <code>semantic-search</code> (pgvector + Cloudflare embeddings).
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="info-box">
        <strong>📚 Enterprise.IO:</strong> Upload via <code>process-knowledge-file</code>,
        embed via <code>embed</code> (OpenAI <em>text-embedding-3-small</em>),
        search via <code>search-knowledge</code>.
        </div>
        """, unsafe_allow_html=True)

    kb_ingest_tab, kb_search_tab = st.tabs(["⬆️ Ingest / Process", "🔍 Semantic Search"])

    # ── INGEST ────────────────────────────────
    with kb_ingest_tab:
        kb_agent_id = st.text_input("Agent ID *", value=default_agent, key="kb_agent")

        if platform == "ASK.IO":
            st.markdown("#### Process Knowledge (`process-knowledge`)")
            kb_knowledge_id  = st.text_input("Knowledge ID *", key="kb_kid",
                                              placeholder="UUID of the knowledge item")
            kb_content       = st.text_area("Content *", height=150, key="kb_content",
                                             placeholder="Paste document text to ingest…")
            c1, c2           = st.columns(2)
            kb_chunk_size    = c1.number_input("Chunk Size",    value=512, min_value=64,  max_value=4096)
            kb_chunk_overlap = c2.number_input("Chunk Overlap", value=50,  min_value=0,   max_value=512)

            if st.button("⬆️ Process Knowledge", type="primary", key="kb_process_ask"):
                if not all([api_key, kb_agent_id, kb_knowledge_id, kb_content]):
                    st.error("⚠️ Agent ID, Knowledge ID and Content are required")
                else:
                    payload = {
                        "knowledgeId":  kb_knowledge_id,
                        "content":      kb_content,
                        "agentId":      kb_agent_id,
                        "chunkSize":    kb_chunk_size,
                        "chunkOverlap": kb_chunk_overlap,
                    }
                    with st.spinner("🔄 Ingesting…"):
                        try:
                            code, result = post("process-knowledge", payload)
                            if code == 200:
                                st.success("✅ Knowledge processed!")
                                st.json(result)
                            else:
                                st.error(f"❌ Error {code}: {result}")
                        except Exception as e:
                            st.error(f"❌ {e}")

        else:  # Enterprise.IO
            st.markdown("#### Process Knowledge File (`process-knowledge-file`)")
            kb_file_path = st.text_input("File Path *", key="kb_fp",
                                          placeholder="Path inside knowledge-base storage bucket")
            kb_title     = st.text_input("Title *", key="kb_title",
                                          placeholder="Display title for the document")

            if st.button("⬆️ Process File", type="primary", key="kb_process_ent"):
                if not all([api_key, kb_agent_id, kb_file_path, kb_title]):
                    st.error("⚠️ Agent ID, File Path and Title are required")
                else:
                    payload = {"filePath": kb_file_path, "agentId": kb_agent_id, "title": kb_title}
                    with st.spinner("🔄 Processing file…"):
                        try:
                            code, result = post("process-knowledge-file", payload)
                            if code == 200:
                                st.success("✅ File processed!")
                                st.json(result)
                            else:
                                st.error(f"❌ Error {code}: {result}")
                        except Exception as e:
                            st.error(f"❌ {e}")

            st.markdown("---")
            st.markdown("#### Generate Embeddings (`embed`)")
            embed_content = st.text_area("Content to embed *", height=100, key="kb_embed_content")
            if st.button("🧮 Generate Embeddings", key="kb_embed"):
                if not all([api_key, embed_content]):
                    st.error("⚠️ Content is required")
                else:
                    with st.spinner("🔄 Generating embeddings…"):
                        try:
                            code, result = post("embed", {"content": embed_content, "agentId": kb_agent_id})
                            if code == 200:
                                st.success("✅ Embeddings generated!")
                                st.json(result)
                            else:
                                st.error(f"❌ Error {code}: {result}")
                        except Exception as e:
                            st.error(f"❌ {e}")

    # ── SEARCH ────────────────────────────────
    with kb_search_tab:
        ks_agent_id  = st.text_input("Agent ID", value=default_agent, key="ks_agent")
        ks_query     = st.text_area("Search Query *", height=80, key="ks_query",
                                     placeholder="e.g. refund policy for enterprise plans")
        c1, c2       = st.columns(2)
        ks_threshold = c1.slider("Match Threshold", 0.0, 1.0, 0.7, 0.05, key="ks_thresh")
        ks_count     = c2.number_input("Max Results", 1, 20, 5, key="ks_count")

        search_endpoint = "semantic-search" if platform == "ASK.IO" else "search-knowledge"

        if st.button("🔍 Search", type="primary", key="ks_search"):
            if not all([api_key, ks_query]):
                st.error("⚠️ Query is required")
            else:
                payload = {"query": ks_query, "matchThreshold": ks_threshold, "matchCount": ks_count}
                if ks_agent_id:
                    payload["agentId"] = ks_agent_id
                with st.spinner("🔄 Searching…"):
                    try:
                        code, result = post(search_endpoint, payload)
                        if code == 200:
                            st.success("✅ Search complete!")
                            rows = result if isinstance(result, list) else result.get("results", [])
                            if rows:
                                df  = pd.DataFrame(rows)
                                st.dataframe(df, use_container_width=True)
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    "📥 Download CSV", csv,
                                    file_name=f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv",
                                )
                            else:
                                st.info("No matching results found")
                            with st.expander("Full JSON response"):
                                st.json(result)
                        else:
                            st.error(f"❌ Error {code}: {result}")
                    except Exception as e:
                        st.error(f"❌ {e}")

# ══════════════════════════════════════════════
# TAB 4 — DB Query  (ASK.IO only)
# ══════════════════════════════════════════════
if platform == "ASK.IO":
    with tabs[3]:
        st.markdown('<div class="sub-header">DB Query Handler</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
        <strong>🗄️</strong> Natural-language → SELECT-only SQL on connected external databases
        via <code>db-query-handler</code>.
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            db_user_id   = st.text_input("User ID *",      value=default_user,  key="db_user")
            db_agent_id  = st.text_input("Agent ID",       value=default_agent, key="db_agent")
        with c2:
            db_config_id = st.text_input("DB Config ID *", value=default_conn,  key="db_config",
                                          placeholder="Database connection config UUID")

        db_message = st.text_area(
            "Query or Instruction *", height=130, key="db_msg",
            placeholder="SELECT * FROM users LIMIT 10\nor: Show me all active users in the last 30 days",
        )

        with st.expander("📖 Example queries"):
            st.code("SELECT * FROM users LIMIT 10", language="sql")
            st.code("SELECT COUNT(*) FROM orders WHERE status = 'completed'", language="sql")
            st.code("Show me all active users created in the last 30 days", language="text")

        if st.button("⚡ Execute", type="primary", key="db_exec"):
            if not all([api_key, db_user_id, db_config_id, db_message]):
                st.error("⚠️ User ID, DB Config ID and Query are required")
            else:
                payload = {"message": db_message, "dbConfigId": db_config_id}
                if db_user_id:
                    payload["userId"] = db_user_id
                if db_agent_id:
                    payload["agentId"] = db_agent_id

                with st.spinner("🔄 Executing query…"):
                    try:
                        code, result = post("db-query-handler", payload)
                        if code == 200:
                            exec_result = result.get("executionResult", {})
                            c1, c2 = st.columns(2)
                            c1.metric("Action",      result.get("action",      "N/A"))
                            c2.metric("SQL Executed", result.get("sqlExecuted", "N/A"))

                            if exec_result.get("success"):
                                st.success(exec_result.get("message", "Query executed successfully"))
                                rows = exec_result.get("result", [])
                                if isinstance(rows, list) and rows:
                                    df  = pd.DataFrame(rows)
                                    st.dataframe(df, use_container_width=True)
                                    csv = df.to_csv(index=False)
                                    st.download_button(
                                        "📥 Download CSV", csv,
                                        file_name=f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                        mime="text/csv",
                                    )
                                else:
                                    st.info("No rows returned")
                            else:
                                st.error(f"⚠️ {exec_result.get('message', 'Execution failed')}")

                            if "explanation" in result:
                                with st.expander("📖 Explanation"):
                                    st.write(result["explanation"])

                            with st.expander("🔍 Full JSON response"):
                                st.json(result)
                        else:
                            st.error(f"❌ Error {code}: {result}")
                    except Exception as e:
                        st.error(f"❌ {e}")

# ──────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"""
    <div style="text-align:center;color:#95a5a6;font-size:.85rem;padding:.5rem 0;">
        🧠 ETLAS Agent Interface &nbsp;·&nbsp; Platform: <strong>{platform}</strong><br>
        <code>{base_url}</code>
    </div>
    """,
    unsafe_allow_html=True,
)
