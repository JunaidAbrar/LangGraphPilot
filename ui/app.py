import streamlit as st
import pandas as pd
import json
import plotly.io as pio
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.graph import app as agent_app

st.set_page_config(page_title="Data Cadet Agent", layout="wide")
st.title("🤖 Delivery Cadet Challenge: AI Data Agent")
st.markdown("---")

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
            
            # Accumulate state here because stream() gives partial updates
            full_state = {} 
            
            for output in agent_app.stream(inputs):
                for key, value in output.items():
                    # Merge new value into full_state
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