import json
import plotly.express as px
import pandas as pd
import plotly.io as pio

def generate_plot_config(data: list, plot_type: str, x_axis: str, y_axis: str, title: str):
    """
    Generates a Plotly JSON artifact.
    """
    if not data:
        return None

    df = pd.DataFrame(data)
    
    try:
        # Convert numeric columns if they are strings (common SQLite issue)
        try:
            df[y_axis] = pd.to_numeric(df[y_axis])
        except:
            pass

        if plot_type == 'bar':
            fig = px.bar(df, x=x_axis, y=y_axis, title=title, text_auto=True)
        
        elif plot_type == 'pie':
            # For Pie: x_axis = names (labels), y_axis = values
            fig = px.pie(df, names=x_axis, values=y_axis, title=title)
            fig.update_traces(textposition='inside', textinfo='percent+label')
        
        elif plot_type == 'line':
            fig = px.line(df, x=x_axis, y=y_axis, title=title, markers=True)
            
        elif plot_type == 'scatter':
            fig = px.scatter(df, x=x_axis, y=y_axis, title=title)
        
        else:
            return None

        # Return JSON string
        return json.loads(pio.to_json(fig))
    except Exception as e:
        print(f"Plotting Error: {e}")
        return None