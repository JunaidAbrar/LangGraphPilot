import os
from sqlalchemy import create_engine

# Using a local file-based SQLite db
DB_NAME = "local_data.db"

def get_db_engine():
    """
    Returns a SQLAlchemy engine for the local SQLite database.
    """
    # Connects to 'local_data.db' in the project root
    return create_engine(f"sqlite:///{DB_NAME}")

def get_db_path():
    return DB_NAME