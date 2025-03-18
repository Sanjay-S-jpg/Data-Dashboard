import base64
import io

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ---------- Initialize the app ---------- #
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],  # You can pick any Bootstrap theme
    suppress_callback_exceptions=True
)
server = app.server
app.title = "Fancy CSV Dashboard"

# A dcc.Store to hold the uploaded CSV data (in JSON) so multiple components can access it
store_data = dcc.Store(id='stored-data', storage_type='session')

# ---------- Navbar ---------- #
navbar = dbc.NavbarSimple(
    brand="Fancy CSV Dashboard",
    color="primary",
    dark=True,
    className="mb-2"
)

# ---------- KPI Cards Row ---------- #
# We will dynamically update these after the CSV is uploaded and parsed.
kpi_cards = dbc.Row([
    dbc.Col(
        dbc.Card(
            [
                dbc.CardHeader("KPI 1"),
                dbc.CardBody(
                    html.H4(id="kpi-1-value", className="card-title")
                ),
            ],
            className="mb-2"
        ), md=3
    ),
    dbc.Col(
        dbc.Card(
            [
                dbc.CardHeader("KPI 2"),
                dbc.CardBody(
                    html.H4(id="kpi-2-value", className="card-title")
                ),
            ],
            className="mb-2"
        ), md=3
    ),
    dbc.Col(
        dbc.Card(
            [
                dbc.CardHeader("KPI 3"),
                dbc.CardBody(
                    html.H4(id="kpi-3-value", className="card-title")
                ),
            ],
            className="mb-2"
        ), md=3
    ),
    dbc.Col(
        dbc.Card(
            [
                dbc.CardHeader("KPI 4"),
                dbc.CardBody(
                    html.H4(id="kpi-4-value", className="card-title")
                ),
            ],
            className="mb-2"
        ), md=3
    ),
], className="mb-2")

# ---------- CSV Upload Section ---------- #
upload_section = dbc.Row([
    dbc.Col([
        html.H5("Upload a CSV File"),
        dcc.Upload(
            id='upload-data',
            children=html.Div(['Drag and drop or ', html.A('Select a CSV File')]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'marginBottom': '10px'
            },
            multiple=False
        ),
        html.Div(id='upload-status', style={"marginBottom": "10px"})
    ], md=12)
], className="mb-2")

# ---------- Filters Section ---------- #
# We add a dropdown that lets the user pick which numeric column to focus on.
filters_section = dbc.Row([
    dbc.Col([
        html.H5("Select a Numeric Column:"),
        dcc.Dropdown(id="numeric-column-dropdown", placeholder="(Upload CSV first)"),
    ], md=4),
    dbc.Col([
        html.H5("Select Another Numeric Column (optional):"),
        dcc.Dropdown(id="numeric-column-dropdown-2", placeholder="(Upload CSV first)"),
    ], md=4),
], className="mb-2")

# ---------- Charts Section ---------- #
# We'll create 5 placeholders for our charts:
#  1) Bar or Histogram
#  2) Pie
#  3) Line
#  4) Scatter
#  5) Correlation Heatmap
charts_section = dbc.Row([
    dbc.Col(dcc.Graph(id="chart-1"), md=6),
    dbc.Col(dcc.Graph(id="chart-2"), md=6),
], className="mb-2")

charts_section_2 = dbc.Row([
    dbc.Col(dcc.Graph(id="chart-3"), md=6),
    dbc.Col(dcc.Graph(id="chart-4"), md=6),
], className="mb-2")

heatmap_section = dbc.Row([
    dbc.Col(dcc.Graph(id="heatmap-chart"), md=12),
], className="mb-2")

# ---------- Layout Assembly ---------- #
app.layout = dbc.Container([
    navbar,
    store_data,
    kpi_cards,
    upload_section,
    filters_section,
    charts_section,
    charts_section_2,
    heatmap_section
], fluid=True)


# ========== CALLBACKS ========== #

# 1) Parse the CSV on upload and store it in session memory
@app.callback(
    Output('stored-data', 'data'),
    Output('upload-status', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def store_csv(contents, filename):
    if contents is None:
        return None, ""

    # Basic check for CSV
    if 'csv' not in filename.lower():
        return None, dbc.Alert("Please upload a .csv file.", color="danger")

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    except Exception as e:
        return None, dbc.Alert(f"Error processing file: {e}", color="danger")

    if df.empty:
        return None, dbc.Alert("Uploaded CSV is empty.", color="warning")

    # Store entire DataFrame in JSON
    return df.to_json(date_format='iso', orient='split'), dbc.Alert("File uploaded successfully!", color="success")


# 2) Populate the numeric column dropdowns AFTER we have the stored data
@app.callback(
    Output("numeric-column-dropdown", "options"),
    Output("numeric-column-dropdown-2", "options"),
    Input("stored-data", "data")
)
def populate_numeric_dropdowns(json_data):
    if not json_data:
        return [], []
    df = pd.read_json(json_data, orient='split')

    # Identify numeric columns
    numeric_cols = df.select_dtypes(include='number').columns
    options = [{"label": col, "value": col} for col in numeric_cols]

    return options, options


# 3) Update the KPI cards based on the data
@app.callback(
    Output("kpi-1-value", "children"),
    Output("kpi-2-value", "children"),
    Output("kpi-3-value", "children"),
    Output("kpi-4-value", "children"),
    Input("stored-data", "data")
)
def update_kpis(json_data):
    if not json_data:
        return "-", "-", "-", "-"

    df = pd.read_json(json_data, orient='split')

    # Example KPI logic:
    # Just pick the first 4 numeric columns (if they exist) and show their mean
    numeric_cols = df.select_dtypes(include='number').columns
    values = []
    for i in range(4):
        if i < len(numeric_cols):
            col_mean = df[numeric_cols[i]].mean()
            values.append(f"{numeric_cols[i]} Avg: {col_mean:.2f}")
        else:
            values.append("-")

    return values[0], values[1], values[2], values[3]


# 4) Generate charts based on user selections
@app.callback(
    Output("chart-1", "figure"),
    Output("chart-2", "figure"),
    Output("chart-3", "figure"),
    Output("chart-4", "figure"),
    Output("heatmap-chart", "figure"),
    Input("stored-data", "data"),
    Input("numeric-column-dropdown", "value"),
    Input("numeric-column-dropdown-2", "value")
)
def update_charts(json_data, col1, col2):
    # Default empty figures
    empty_fig = go.Figure()
    empty_fig.update_layout(
        template="plotly_dark",
        annotations=[dict(text="No data", x=0.5, y=0.5, showarrow=False)]
    )
    if not json_data:
        return empty_fig, empty_fig, empty_fig, empty_fig, empty_fig

    df = pd.read_json(json_data, orient='split')
    numeric_cols = df.select_dtypes(include='number').columns

    # If user hasn't selected columns or if columns aren't numeric, default them
    if not col1 or col1 not in numeric_cols:
        if len(numeric_cols) > 0:
            col1 = numeric_cols[0]
        else:
            return empty_fig, empty_fig, empty_fig, empty_fig, empty_fig

    if not col2 or col2 not in numeric_cols:
        if len(numeric_cols) > 1:
            col2 = numeric_cols[1]
        else:
            col2 = None

    # 1) Chart-1: Bar or Histogram of col1
    fig1 = px.histogram(df, x=col1, nbins=20, title=f"Histogram of {col1}")
    fig1.update_layout(template="plotly_dark")

    # 2) Chart-2: Pie chart of col1 binned or value_counts?
    #    For numeric data, let's do a binned approach or just do a value_counts approach.
    #    Alternatively, if it's truly numeric, a pie might not be as meaningful, but let's try:
    df_pie = df[col1].value_counts().reset_index()
    df_pie.columns = [col1, "Count"]
    fig2 = px.pie(df_pie, names=col1, values="Count", title=f"Pie Chart of {col1}")
    fig2.update_layout(template="plotly_dark")

    # 3) Chart-3: Line chart of col1 over the index
    fig3 = px.line(df, y=col1, title=f"Line Chart of {col1} over Index")
    fig3.update_layout(template="plotly_dark")

    # 4) Chart-4: Scatter plot (col1 vs col2) if col2 exists
    if col2:
        fig4 = px.scatter(df, x=col1, y=col2, title=f"Scatter: {col1} vs {col2}")
        fig4.update_layout(template="plotly_dark")
    else:
        fig4 = go.Figure()
        fig4.update_layout(
            template="plotly_dark",
            annotations=[dict(text="Not enough numeric columns for Scatter Plot", 
                              x=0.5, y=0.5, showarrow=False)]
        )

    # 5) Correlation heatmap if at least 2 numeric columns exist
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr()
        fig5 = px.imshow(corr, text_auto=True, title="Correlation Heatmap")
        fig5.update_layout(template="plotly_dark")
    else:
        fig5 = go.Figure()
        fig5.update_layout(
            template="plotly_dark",
            annotations=[dict(text="Not enough numeric columns for Heatmap", 
                              x=0.5, y=0.5, showarrow=False)]
        )

    return fig1, fig2, fig3, fig4, fig5


# ---------- Run the App ---------- #
if __name__ == "__main__":
    app.run_server(debug=True)
