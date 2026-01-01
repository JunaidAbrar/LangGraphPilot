import json
import plotly.express as px
import pandas as pd
import plotly.io as pio

def generate_plot_config(data: list, plot_type: str, x_axis: str, y_axis: str, title: str):
    """
    Generates a Plotly JSON artifact.
    data: List of dicts (from the SQL result)
    plot_type: 'bar', 'line', 'scatter', 'pie'
    """
    if not data:
        return None

    df = pd.DataFrame(data)
    
    try:
        if plot_type == 'bar':
            fig = px.bar(df, x=x_axis, y=y_axis, title=title)
        elif plot_type == 'line':
            fig = px.line(df, x=x_axis, y=y_axis, title=title)
        elif plot_type == 'scatter':
            fig = px.scatter(df, x=x_axis, y=y_axis, title=title)
        elif plot_type == 'pie':
            fig = px.pie(df, names=x_axis, values=y_axis, title=title)
        else:
            return {"error": f"Unsupported plot type: {plot_type}"}

        # Return the JSON string representation of the figure
        return json.loads(pio.to_json(fig))
    except Exception as e:
        return {"error": str(e)}