import re

FORBIDDEN_KEYWORDS = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", "GRANT", "REVOKE"]

def validate_sql(sql_query: str):
    """
    Checks if the SQL is safe (Read-Only).
    Returns (is_valid: bool, error_message: str)
    """
    upper_sql = sql_query.upper()
    
    # 1. Keyword Check
    for keyword in FORBIDDEN_KEYWORDS:
        # Use regex to ensure we match whole words, not 'UPDATE_DATE' column
        if re.search(r'\b' + keyword + r'\b', upper_sql):
            return False, f"Security Alert: The keyword '{keyword}' is forbidden. Read-only access only."
    
    # 2. Basic Syntax Check (Empty)
    if not sql_query.strip():
        return False, "SQL query is empty."
        
    return True, "Valid"

def generate_repair_prompt(original_query: str, error_message: str):
    """
    Constructs a prompt to ask the LLM to fix the broken SQL.
    """
    return (
        f"The previous SQL query failed.\n"
        f"**Query:** {original_query}\n"
        f"**Error:** {error_message}\n\n"
        "Please examine the Schema again and correct the query. "
        "Check table names, column names, and JOIN keys carefully."
    )