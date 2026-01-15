import pandas as pd
import os
from sqlalchemy import text
from database.connection import get_db_engine, DB_NAME

def sanitize_column_name(col_name: str) -> str:
    return (
        str(col_name).strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("$", "dollars")
        .replace("/", "_per_")
    )

def ingest_directory(directory_path: str, reset_db: bool = False):
    """
    Reads CSV and Excel files.
    reset_db: If True, deletes the existing .db file to ensure a clean slate.
    """
    # 1. Reset Database if requested
    if reset_db and os.path.exists(DB_NAME):
        try:
            os.remove(DB_NAME)
            print("🗑️ Old database deleted.")
        except PermissionError:
            print("⚠️ Could not delete DB file (it might be in use). Proceeding with overwrite...")

    engine = get_db_engine()
    loaded_tables = []

    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"⚠️ Created missing directory: {directory_path}")
        return []

    # 2. Scan for files
    files = [f for f in os.listdir(directory_path) if f.endswith(('.csv', '.xlsx', '.xls'))]
    
    print(f"📂 Found {len(files)} data files.")

    for file in files:
        table_name = os.path.splitext(file)[0].lower().replace(" ", "_")
        file_path = os.path.join(directory_path, file)
        
        try:
            # Detect format
            if file.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                # Read Excel (default to first sheet)
                df = pd.read_excel(file_path)
            
            # Sanitize columns
            df.columns = [sanitize_column_name(c) for c in df.columns]
            
            # Load to DB
            df.to_sql(table_name, engine, if_exists='replace', index=False)
            
            loaded_tables.append(table_name)
            print(f"   ✅ Loaded table: '{table_name}' ({len(df)} rows)")
            
        except Exception as e:
            print(f"   ❌ Failed to load {file}: {e}")

    return loaded_tables