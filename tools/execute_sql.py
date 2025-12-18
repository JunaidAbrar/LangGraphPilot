from sqlalchemy import text
from database.connection import get_db_engine

def execute_sql_query(query: str):
    """
    Executes the SQL query and returns the result as a list of dicts.
    Handles exceptions gracefully by returning the error string.
    """
    engine = get_db_engine()
    try:
        with engine.connect() as conn:
            # text() is required for SQLAlchemy 2.0+
            result = conn.execute(text(query))
            # Convert to list of dicts
            return [dict(row._mapping) for row in result]
    except Exception as e:
        return f"Error: {str(e)}"