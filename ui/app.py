import streamlit as st
import pandas as pd
import json
import plotly.io as pio
import sys
import os

# --- PATH SETUP ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- IMPORTS ---
from agent.graph import app as agent_app
from database.ingestion import ingest_directory 

# --- CONFIG ---
st.set_page_config(page_title="Data Cadet Agent", page_icon="🤖", layout="wide")

st.title("🤖 Delivery Cadet Agent")
st.markdown("##### *LangGraph Orchestration • Llama 3.3 • SQLite*")

# --- SIDEBAR ---
with st.sidebar:
    st.header("🗄️ Data Control")
    st.info("Supported: .csv, .xlsx")
    
    if st.button("🔄 Reset & Reload Data", type="primary"):
        with st.status("Reloading Data...", expanded=True) as status:
            try:
                st.write("🧹 Clearing Database...")
                tables = ingest_directory("./data", reset_db=True)
                if tables:
                    st.write(f"✅ Ingested {len(tables)} tables.")
                    status.update(label="Data Reloaded Successfully!", state="complete", expanded=False)
                    st.success(f"Ready: {', '.join(tables)}")
                else:
                    status.update(label="No Data Found", state="error")
                    st.error("Folder /data is empty.")
                st.session_state.messages = [] 
            except Exception as e:
                status.update(label="Error", state="error")
                st.error(str(e))

# --- CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "plot" in message and message["plot"]:
            st.plotly_chart(pio.from_json(json.dumps(message["plot"])))
        if "sql" in message and message["sql"]:
            with st.expander("🛠️ View SQL Query"):
                st.code(message["sql"], language="sql")

# --- MAIN INTERACTION ---
if prompt := st.chat_input("Ask a question about your data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Variables to hold final state
        full_state = {}
        error_occurred = False
        
        # 1. THE THINKING CONTAINER (Collapsible)
        with st.status("🤖 Agent is thinking...", expanded=True) as status:
            try:
                inputs = {"question": prompt, "retry_count": 0}
                
                for output in agent_app.stream(inputs):
                    for key, value in output.items():
                        full_state.update(value)
                        
                        # Log steps INSIDE the dropdown
                        if key == "generate":
                            st.write("📝 Drafting SQL...")
                        elif key == "validate":
                            st.write("🛡️ Validating Query Safety...")
                        elif key == "execute":
                            st.write("⚡ Executing against SQLite...")
                        elif key == "repair":
                            st.write("🔧 Self-Correction Triggered...")
                            st.warning(f"Fixing error: {value.get('sql_error', 'Unknown Error')}")
                
                status.update(label="Processing Complete!", state="complete", expanded=False)
            
            except Exception as e:
                status.update(label="System Error", state="error")
                st.error(f"Critical Failure: {e}")
                error_occurred = True

        # 2. THE FINAL ANSWER (OUTSIDE the dropdown, visible immediately)
        if not error_occurred:
            response_text = full_state.get("final_answer", "No response generated.")
            sql_used = full_state.get("sql_query", "")
            plot_json = full_state.get("visualization_spec", None)

            st.markdown(response_text)
            
            if plot_json:
                st.plotly_chart(pio.from_json(json.dumps(plot_json)))
            
            # Optional: Show SQL in a small expander below the answer
            if sql_used:
                with st.expander("🛠️ View SQL Query"):
                    st.code(sql_used, language="sql")
            
            # Save to history
            msg_data = {
                "role": "assistant", 
                "content": response_text,
                "sql": sql_used,
                "plot": plot_json
            }
            st.session_state.messages.append(msg_data)