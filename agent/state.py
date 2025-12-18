from typing import TypedDict, List, Any, Optional

class AgentState(TypedDict):
    question: str                   # User's initial question
    chat_history: List[Any]         # Context
    sql_query: Optional[str]        # Generated SQL
    sql_error: Optional[str]        # Error message if execution fails
    query_result: Optional[List]    # Rows returned from DB
    retry_count: int                # To prevent infinite loops (max 3)
    visualization_needed: bool      # Does user want a chart?
    visualization_spec: Optional[dict] # Plotly JSON artifact
    final_answer: Optional[str]     # Text response