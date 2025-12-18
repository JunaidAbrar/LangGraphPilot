from sqlalchemy import inspect, text
from database.connection import get_db_engine

def get_table_samples(engine, table_name, limit=3):
    with engine.connect() as conn:
        try:
            # Fetch samples to help LLM understand data formats
            query = text(f"SELECT * FROM {table_name} LIMIT {limit}")
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]
        except Exception:
            return []

def infer_relationships(inspector, table_names):
    """
    Improved Heuristic: Detects both 'customer_id' and 'customerid'.
    """
    relationships = []
    
    # Map 'customers' -> 'customer', 'sales_customers' -> 'customer'
    # This helps link 'customerid' to 'sales_customers'
    # Logic: If table name contains the ID base, it's a candidate.
    
    for table in table_names:
        columns = inspector.get_columns(table)
        for col in columns:
            col_name = col['name'].lower()
            
            # Check for 'id' suffix
            if col_name.endswith('id') and col_name != 'id':
                # extraction: 'customer_id' -> 'customer', 'customerid' -> 'customer'
                target_base = col_name.replace('_id', '').replace('id', '')
                
                # Search for a table that contains this base name
                # e.g. base 'customer' matches table 'sales_customers'
                for candidate_table in table_names:
                    if candidate_table == table:
                        continue # Skip self
                        
                    # Loose match: if 'customer' is in 'sales_customers'
                    if target_base in candidate_table:
                        relationships.append(
                            f"Inferred Link: {table}.{col_name} -> {candidate_table} (likely JOIN key)"
                        )
                        break # Found a match for this column
    return relationships

def get_database_schema_string():
    engine = get_db_engine()
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    
    schema_lines = []
    
    for table in table_names:
        schema_lines.append(f"Table: {table}")
        columns = inspector.get_columns(table)
        col_desc = []
        for col in columns:
            col_type = str(col['type'])
            col_desc.append(f"{col['name']} ({col_type})")
        
        schema_lines.append(f"  Columns: {', '.join(col_desc)}")
        
        samples = get_table_samples(engine, table)
        if samples:
            # Show just the first sample for brevity
            schema_lines.append(f"  Samples: {str(samples[0])}")
        schema_lines.append("") 

    relationships = infer_relationships(inspector, table_names)
    if relationships:
        schema_lines.append("--- Inferred Relationships (JOIN Hints) ---")
        for rel in relationships:
            schema_lines.append(rel)
    
    return "\n".join(schema_lines)