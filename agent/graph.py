import os
import json
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from agent.guardrails import obfuscate_pii
from agent.state import AgentState
from agent.prompting import get_system_prompt
from agent.validation import validate_sql, generate_repair_prompt
from tools.execute_sql import execute_sql_query
from tools.plot import generate_plot_config

# Load Environment
load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY not found in .env file.")

# Initialize LLM (Using 3.3 as 3.1 is deprecated)
llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)

# --- NODES ---

def generate_query_node(state: AgentState):
    question = state["question"]
    system_prompt = get_system_prompt()
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Question: {question}")
    ]
    
    response = llm.invoke(messages)
    content = response.content
    
    # Extract SQL
    import re
    sql_match = re.search(r"```sql\n(.*?)\n```", content, re.DOTALL)
    sql = sql_match.group(1).strip() if sql_match else content.strip()
    
    return {"sql_query": sql, "retry_count": 0, "sql_error": None}

def validate_node(state: AgentState):
    sql = state["sql_query"]
    is_valid, msg = validate_sql(sql)
    if not is_valid:
        return {"sql_error": msg}
    return {"sql_error": None}

def execute_node(state: AgentState):
    sql = state["sql_query"]
    result = execute_sql_query(sql)
    if isinstance(result, str) and result.startswith("Error:"):
        return {"sql_error": result}
    return {"query_result": result, "sql_error": None}

def repair_node(state: AgentState):
    error = state["sql_error"]
    sql = state["sql_query"]
    retry_count = state["retry_count"]
    
    if retry_count >= 3:
        return {"final_answer": f"I tried 3 times but failed. Last error: {error}"}
    
    repair_prompt = generate_repair_prompt(sql, error)
    messages = [
        SystemMessage(content=get_system_prompt()),
        HumanMessage(content=repair_prompt)
    ]
    response = llm.invoke(messages)
    content = response.content
    
    import re
    sql_match = re.search(r"```sql\n(.*?)\n```", content, re.DOTALL)
    new_sql = sql_match.group(1).strip() if sql_match else content.strip()
    
    return {"sql_query": new_sql, "sql_error": None, "retry_count": retry_count + 1}

def summarize_node(state: AgentState):
    result = state["query_result"]
    question = state["question"]
    sql = state["sql_query"]
    
    if not result:
        return {"final_answer": "Query executed successfully but returned no data.", "visualization_spec": None}
    
    # 1. Generate Summary
    summary_prompt = (
        f"User Question: {question}\n"
        f"SQL Query Used: {sql}\n"
        f"Data Retrieved: {str(result[:10])} ... (truncated)\n\n"
        "Provide a concise summary of the data."
    )
    response = llm.invoke([HumanMessage(content=summary_prompt)])
    final_text = response.content
    safe_text = obfuscate_pii(final_text)

    # 2. Heuristic Auto-Plotter
    plot_spec = None
    # Trigger if user asked for plot OR if the data structure screams "chart" (2 cols)
    if "plot" in question.lower() or "chart" in question.lower() or "graph" in question.lower():
        try:
            if len(result) > 0:
                keys = list(result[0].keys())
                if len(keys) >= 2:
                    # Assume Col 0 = X, Col -1 = Y
                    plot_spec = generate_plot_config(
                        data=result, 
                        plot_type="bar", 
                        x_axis=keys[0], 
                        y_axis=keys[-1], 
                        title=f"Visualization: {question}"
                    )
        except Exception:
            pass # Fail silently on plot, deliver text

    return {"final_answer": safe_text, "visualization_spec": plot_spec}
 

# --- FLOW ---

def should_retry(state: AgentState):
    if state.get("sql_error"):
        if state["retry_count"] >= 3:
            return "end_fail"
        return "repair"
    return "execute"

def check_execution(state: AgentState):
    if state.get("sql_error"):
        return "repair"
    return "summarize"

workflow = StateGraph(AgentState)
workflow.add_node("generate", generate_query_node)
workflow.add_node("validate", validate_node)
workflow.add_node("execute", execute_node)
workflow.add_node("repair", repair_node)
workflow.add_node("summarize", summarize_node)

workflow.set_entry_point("generate")
workflow.add_edge("generate", "validate")
workflow.add_conditional_edges("validate", should_retry, {"execute": "execute", "repair": "repair", "end_fail": END})
workflow.add_conditional_edges("execute", check_execution, {"summarize": "summarize", "repair": "repair"})
workflow.add_edge("repair", "validate")
workflow.add_edge("summarize", END)

app = workflow.compile()