import os
import json
import re # Added for parsing
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

# Initialize LLM (Using 3.3)
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
    

    sql_match = re.search(r"```sql\n(.*?)\n```", content, re.DOTALL)
    new_sql = sql_match.group(1).strip() if sql_match else content.strip()
    
    return {"sql_query": new_sql, "sql_error": None, "retry_count": retry_count + 1}

def summarize_node(state: AgentState):
    result = state["query_result"]
    question = state["question"]
    sql = state["sql_query"]
    
    if not result:
        return {"final_answer": "Query executed successfully but returned no data.", "visualization_spec": None}
    
    # 1. Ask LLM to Summarize AND confirm Plot Type based on actual data
    summary_prompt = (
        f"User Question: {question}\n"
        f"SQL Query Used: {sql}\n"
        f"Data Retrieved: {str(result[:10])} ... (truncated)\n\n"
        "1. Provide a concise summary of the data.\n"
        "2. If the user asked for a visualization, output the JSON block for the best plot type (Bar vs Pie) based on this data.\n"
        "Format:\n"
        "Summary text here...\n"
        "```json\n{...}\n```"
    )
    
    response = llm.invoke([HumanMessage(content=summary_prompt)])
    raw_content = response.content

    # 2. Extract JSON spec if LLM provided it
    plot_spec = None
    json_match = re.search(r"```json\n(.*?)\n```", raw_content, re.DOTALL)
    
    if json_match:
        try:
            plot_config = json.loads(json_match.group(1))
            # Validate keys exist
            if "plot_type" in plot_config and "x_axis" in plot_config:
                plot_spec = generate_plot_config(
                    data=result,
                    plot_type=plot_config["plot_type"],
                    x_axis=plot_config["x_axis"],
                    y_axis=plot_config["y_axis"],
                    title=plot_config.get("title", "Data Visualization")
                )
        except Exception as e:
            print(f"JSON Parsing failed: {e}")

    # 3. FALLBACK: Smart Heuristic if LLM failed but User asked for it
    trigger_words = ["plot", "graph", "chart", "visualize", "visualization"]
    if not plot_spec and any(word in question.lower() for word in trigger_words):
        try:
            if len(result) > 0:
                keys = list(result[0].keys())
                if len(keys) >= 2:
                    # Smart Logic: If < 8 categories, maybe Pie? Otherwise Bar.
                    x_col = keys[0]
                    y_col = keys[-1]
                    
                    # Check cardinality of X column (to decide pie vs bar)
                    unique_x = set(row[x_col] for row in result)
                    
                    if len(unique_x) < 8 and "share" in question.lower() or "percentage" in question.lower():
                        chart_type = "pie"
                    else:
                        chart_type = "bar"
                        
                    plot_spec = generate_plot_config(
                        data=result, 
                        plot_type=chart_type, 
                        x_axis=x_col, 
                        y_axis=y_col, 
                        title=f"Visualization: {question}"
                    )
        except Exception:
            pass 

    # 4. Clean Text (Remove the JSON block from the final answer text)
    final_text = re.sub(r"```json\n.*?\n```", "", raw_content, flags=re.DOTALL).strip()
    safe_text = obfuscate_pii(final_text)

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