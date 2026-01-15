import streamlit as st
import pandas as pd
import json
import plotly.io as pio
import sys
import os

# --- CRITICAL: FIX PYTHON PATH ---
# We must do this BEFORE importing local modules like 'agent' or 'database'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- LOCAL IMPORTS ---
from agent.graph import app as agent_app
from database.ingestion import ingest_directory 

# --- APP CONFIG ---
st.set_page_config(page_title="Data Cadet Agent", layout="wide")

st.title("🤖 Delivery Cadet Challenge: AI Data Agent")
st.markdown("---")

# --- SIDEBAR: DATA CONTROLS ---
with st.sidebar:
    st.header("🗄️ Data Management")
    st.info("Supported formats: .csv, .xlsx, .xls")
    
    if st.button("🔄 Reset & Reload Data", type="primary"):
        with st.spinner("Flushing database and reloading from /data..."):
            try:
                # Force reset_db=True to clear old CSV tables
                # Ensure you have run: pip install openpyxl
                tables = ingest_directory("./data", reset_db=True)
                if tables:
                    st.success(f"Loaded {len(tables)} tables: {', '.join(tables)}")
                else:
                    st.warning("No files found in /data!")
                
                # Clear chat history so the agent doesn't get confused by old context
                st.session_state.messages = []
            except Exception as e:
                st.error(f"Error loading data: {e}")

# --- CHAT INTERFACE ---

# Initialize History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "plot" in message and message["plot"]:
            st.plotly_chart(pio.from_json(json.dumps(message["plot"])))
        if "sql" in message and message["sql"]:
            with st.expander("View SQL"):
                st.code(message["sql"], language="sql")

# Input Handling
if prompt := st.chat_input("Ask a question about your data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status_placeholder = st.empty()
        status_placeholder.text("🤔 Thinking & Querying...")
        
        try:
            inputs = {"question": prompt, "retry_count": 0}
            full_state = {} 
            
            for output in agent_app.stream(inputs):
                for key, value in output.items():
                    full_state.update(value)
                    
                    if key == "generate":
                        status_placeholder.text("📝 Generating SQL...")
                    elif key == "validate":
                        status_placeholder.text("🛡️ Validating Security...")
                    elif key == "execute":
                        status_placeholder.text("⚡ Executing Query...")
                    elif key == "repair":
                        status_placeholder.text("🔧 Fixing Error...")
            
            # Final Rendering
            response_text = full_state.get("final_answer", "No response generated.")
            sql_used = full_state.get("sql_query", "")
            plot_json = full_state.get("visualization_spec", None)
            
            message_placeholder.markdown(response_text)
            status_placeholder.empty()
            
            if plot_json:
                st.plotly_chart(pio.from_json(json.dumps(plot_json)))
                
            if sql_used:
                with st.expander("View Generated SQL"):
                    st.code(sql_used, language="sql")
            
            # Save to history
            msg_data = {
                "role": "assistant", 
                "content": response_text,
                "sql": sql_used,
                "plot": plot_json
            }
            st.session_state.messages.append(msg_data)

        except Exception as e:
            st.error(f"An error occurred: {e}")
            status_placeholder.empty()