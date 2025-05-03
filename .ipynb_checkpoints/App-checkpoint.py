import dash
from dash import html, dcc, Input, Output, State
from dash.dcc import send_data_frame
import pandas as pd
import plotly.express as px

# Load and prepare dataset
df = pd.read_csv("Downloads/NYPD_Arrests_Data__Historic__2020-2025.csv")
df = df[df['LAW_CAT_CD'] == 'F']
df = df.dropna(subset=['Latitude', 'Longitude', 'OFNS_DESC', 'ARREST_BORO'])
df['ARREST_DATE'] = pd.to_datetime(df['ARREST_DATE'], errors='coerce')
df['Year'] = df['ARREST_DATE'].dt.year

top_crimes = df['OFNS_DESC'].value_counts().nlargest(6).index.tolist()
df = df[df['OFNS_DESC'].isin(top_crimes)]

# Create app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div([
    html.H2("🚓 NYC Felony Arrest Dashboard", style={'textAlign': 'center'}),

    html.Div([
        html.Div([
            html.Label("Select Crime Type(s):"),
            dcc.Dropdown(
                id='crime_filter',
                options=[{'label': crime, 'value': crime} for crime in top_crimes],
                value=[top_crimes[0]],
                multi=True,
                style={'width': '300px'}
            )
        ]),
        html.Div([
            html.Label("Select Borough:"),
            dcc.Dropdown(
                id='boro_filter',
                options=[{'label': b, 'value': b} for b in sorted(df['ARREST_BORO'].unique())],
                value='K',
                style={'width': '300px'}
            )
        ])
    ], style={'display': 'flex', 'gap': '30px', 'justifyContent': 'center'}),

    html.Div([
        html.Button("📥 Download Filtered Arrests CSV", id="download_btn", n_clicks=0),
        dcc.Download(id="download_csv")
    ], style={'textAlign': 'center', 'margin': '20px'}),

    html.Div(id='total_count', style={'textAlign': 'center', 'margin': '20px', 'fontSize': '18px'}),

    dcc.Graph(id='trend_plot'),
    dcc.Graph(id='map_plot')
])

@app.callback(
    Output('trend_plot', 'figure'),
    [Input('crime_filter', 'value'),
     Input('boro_filter', 'value')]
)
def update_trend(selected_crimes, selected_boro):
    dff = df[(df['OFNS_DESC'].isin(selected_crimes)) & (df['ARREST_BORO'] == selected_boro)]
    trend = dff.groupby(['Year']).size().reset_index(name='Arrests')
    fig = px.line(trend, x='Year', y='Arrests', markers=True,
                  title=f'Felony Arrest Trends in Borough {selected_boro}')
    return fig

@app.callback(
    Output('map_plot', 'figure'),
    [Input('crime_filter', 'value'),
     Input('boro_filter', 'value')]
)
def update_map(selected_crimes, selected_boro):
    dff = df[(df['OFNS_DESC'].isin(selected_crimes)) & (df['ARREST_BORO'] == selected_boro)]
    map_df = dff.sample(min(1000, len(dff)))  # sample for performance
    fig = px.scatter_mapbox(map_df,
                            lat="Latitude", lon="Longitude",
                            color="Year",
                            zoom=10,
                            mapbox_style="carto-positron",
                            title=f"Arrest Locations Colored by Year — Borough {selected_boro}")
    return fig

@app.callback(
    Output('total_count', 'children'),
    [Input('crime_filter', 'value'),
     Input('boro_filter', 'value')]
)
def update_count(selected_crimes, selected_boro):
    count = df[(df['OFNS_DESC'].isin(selected_crimes)) & (df['ARREST_BORO'] == selected_boro)].shape[0]
    return f"📊 Total Arrests: {count:,} felony cases in borough {selected_boro}"

@app.callback(
    Output("download_csv", "data"),
    Input("download_btn", "n_clicks"),
    State("crime_filter", "value"),
    State("boro_filter", "value"),
    prevent_initial_call=True,
)
def trigger_download(n_clicks, selected_crimes, selected_boro):
    dff = df[(df['OFNS_DESC'].isin(selected_crimes)) & (df['ARREST_BORO'] == selected_boro)]
    return send_data_frame(dff.to_csv, filename="filtered_felony_arrests.csv")

if __name__ == '__main__':
    app.run(debug=True)
