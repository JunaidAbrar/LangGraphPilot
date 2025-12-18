import pandas as pd
import os
from sqlalchemy import text
from database.connection import get_db_engine

def sanitize_column_name(col_name: str) -> str:
    """
    Converts 'Order Date' -> 'order_date', 'Total ($)' -> 'total_dollars'
    """
    return (
        col_name.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("$", "dollars")
    )

def ingest_csv_directory(directory_path: str):
    """
    Reads all .csv files in the directory and loads them into SQLite.
    """
    engine = get_db_engine()
    loaded_tables = []

    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory {directory_path} not found.")

    files = [f for f in os.listdir(directory_path) if f.endswith('.csv')]
    
    print(f"📂 Found {len(files)} CSV files. Starting ingestion...")

    for file in files:
        table_name = os.path.splitext(file)[0].lower().replace(" ", "_")
        file_path = os.path.join(directory_path, file)
        
        try:
            # Read CSV
            df = pd.read_csv(file_path)
            
            # Sanitize columns
            df.columns = [sanitize_column_name(c) for c in df.columns]
            
            # Load to DB (Replace ensures fresh start)
            df.to_sql(table_name, engine, if_exists='replace', index=False)
            
            loaded_tables.append(table_name)
            print(f"   ✅ Loaded table: '{table_name}' ({len(df)} rows)")
            
        except Exception as e:
            print(f"   ❌ Failed to load {file}: {e}")

    return loaded_tables