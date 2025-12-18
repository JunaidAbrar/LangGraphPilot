from database.schema import get_database_schema_string
from agent.validation import validate_sql

print("--- TEST 1: IMPROVED RELATIONSHIP DETECTION ---")
schema = get_database_schema_string()
# Check if we see the new relationships
if "Inferred Relationships" in schema:
    print("✅ Relationships detected!")
    print(schema.split("--- Inferred Relationships (JOIN Hints) ---")[1])
else:
    print("❌ Still no relationships detected.")

print("\n--- TEST 2: SQL VALIDATION ---")
bad_sql = "DELETE FROM customers WHERE id = 1"
good_sql = "SELECT * FROM customers"

valid, msg = validate_sql(bad_sql)
print(f"Bad SQL ('{bad_sql}'): {msg}")

valid, msg = validate_sql(good_sql)
print(f"Good SQL: {msg}")