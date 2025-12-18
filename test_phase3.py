from agent.graph import app

print("--- TEST: FULL AGENT FLOW ---")

# Question designed to force a JOIN
input_data = {
    "question": "What is the total sales amount for the customer named 'Kayla Barrett'?", 
    "retry_count": 0
}

try:
    for output in app.stream(input_data):
        for key, value in output.items():
            print(f"Finished Node: {key}")
            if "sql_query" in value:
                print(f"  SQL: {value['sql_query']}")
            if "sql_error" in value and value['sql_error']:
                print(f"  Error: {value['sql_error']}")
            if "final_answer" in value:
                print(f"\n🤖 FINAL ANSWER:\n{value['final_answer']}")
except Exception as e:
    print(f"CRITICAL ERROR: {e}")