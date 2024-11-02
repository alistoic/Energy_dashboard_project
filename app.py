import pandas as pd
import dash
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pycountry

# ======================================================================================================
# Initialize Dash App with Bootstrap Theme
# ======================================================================================================

app = Dash(__name__, external_stylesheets=[dbc.themes.YETI], suppress_callback_exceptions=True)
server = app.server  # For deployment purposes

# =======================================================================================================
# Data Loading and Error Handling
# =======================================================================================================

def load_data(filepath):
    
    try:
        
        df = pd.read_csv(filepath)
        
        # Drop the 'Code' 
        df = df.drop(columns='Code')
        
        # Fill missing values for each energy column
        energy_columns = [
            'Electricity from wind - TWh',
            'Electricity from hydro - TWh',
            'Electricity from solar - TWh',
            'Other renewables including bioenergy - TWh'
        ]
        df[energy_columns] = df[energy_columns].fillna(0)
        
        # Ensure data types are correct
        df['Year'] = df['Year'].astype(int)
        df['Entity'] = df['Entity'].astype(str)
        
        return df

    except FileNotFoundError:
        raise FileNotFoundError("The data file 'modern-renewable-prod.csv' was not found.")
    except pd.errors.ParserError:
        raise ValueError("Error parsing the CSV file. Please check the file format.")
    except Exception as e:
        raise e

# Load data with error handling
try:
    energy_data = load_data("modern-renewable-prod.csv")
except Exception as e:
    # If there's an error loading data, display an error message in the app
    app.layout = dbc.Container([
        dbc.Alert(
            f"Error loading data: {e}",
            color="danger",
            dismissable=True
        )
    ], fluid=True)
else:
   
    # Define a custom theme for Plotly figures
    custom_theme = {
        'layout': go.Layout(
            paper_bgcolor='#FAFAFA',
            plot_bgcolor='#FAFAFA',
            font=dict(color='#333333'),
            xaxis=dict(gridcolor='#C9C9C9', linecolor='#C9C9C9', tickcolor='#C9C9C9'),
            yaxis=dict(gridcolor='#C9C9C9', linecolor='#C9C9C9', tickcolor='#C9C9C9')
        )
    }

    # Precompute unique entities and years for dropdowns and sliders
    energy_entities = sorted(energy_data['Entity'].unique())
    energy_year_min = energy_data['Year'].min()
    energy_year_max = energy_data['Year'].max()
    energy_year_marks = {year: str(year) for year in range(energy_year_min, energy_year_max + 1, 1)}

    # Define the energy types mapping for dropdown
    energy_types = {
        'Wind Power': 'Electricity from wind - TWh',
        'Solar Power': 'Electricity from solar - TWh',
        'Hydro Power': 'Electricity from hydro - TWh',
        'Other Renewables': 'Other renewables including bioenergy - TWh'
    }

    # Helper function to map country names to ISO Alpha-3 codes
    def get_iso_alpha3(entity_name):
        try:
            return pycountry.countries.lookup(entity_name).alpha_3
        except LookupError:
            return None  # or handle accordingly

    # Add ISO Alpha-3 codes to the dataframe
    energy_data['ISO_A3'] = energy_data['Entity'].apply(get_iso_alpha3)

    # Remove rows with invalid ISO codes
    energy_data = energy_data.dropna(subset=['ISO_A3'])

    # =====================================================================================================
    # Helper Functions for Figure Creation
    # =====================================================================================================

    def create_energy_trends_fig(data):
        fig = px.line(
            data,
            x='Year',
            y=list(energy_types.values()),
            color='Entity',
            title='Energy Consumption Trends by Entity',
            labels={
                'value': 'Electricity Consumption (TWh)',
                'variable': 'Energy Type'
            }
        )
        fig.update_layout(custom_theme['layout'])
        return fig

    def create_energy_bar_fig(data):
        fig = px.bar(
            data,
            x='Entity',
            y=list(energy_types.values()),
            title='Energy Consumption by Entity and Energy Type',
            labels={'value': 'Electricity Consumption (TWh)', 'Entity': 'Entity'},
            barmode='group'
        )
        fig.update_layout(custom_theme['layout'])
        return fig

    def create_energy_pie_fig(data, year):
        pie_data = data.groupby('Entity')[list(energy_types.values())].sum().reset_index()
        pie_sum = pie_data[list(energy_types.values())].sum().reset_index()
        pie_sum.columns = ['Energy Type', 'Total Consumption (TWh)']
        
        fig = px.pie(
            pie_sum,
            names='Energy Type',
            values='Total Consumption (TWh)',
            title=f'Energy Consumption Distribution in {year}',
            labels={'Energy Type': 'Energy Type', 'Total Consumption (TWh)': 'Electricity Consumption (TWh)'}
        )
        fig.update_layout(custom_theme['layout'])
        return fig

    def create_energy_area_fig(data, cumulative=True):
        if cumulative:
            area_data = data.groupby('Year')[list(energy_types.values())].sum().cumsum().reset_index()
            title = 'Cumulative Energy Consumption Over Years'
            y_label = 'Cumulative Electricity Consumption (TWh)'
        else:
            area_data = data.groupby('Year')[list(energy_types.values())].sum().reset_index()
            title = 'Annual Energy Consumption Over Years'
            y_label = 'Electricity Consumption (TWh)'

        fig = px.area(
            area_data,
            x='Year',
            y=list(energy_types.values()),
            title=title,
            labels={'value': y_label, 'variable': 'Energy Type'}
        )
        fig.update_layout(custom_theme['layout'])
        return fig

    def create_worldwide_map(data, energy_type):
        latest_year = data['Year'].max()
        map_data = data[data['Year'] == latest_year]
        map_data = map_data.groupby(['Entity', 'ISO_A3'], as_index=False).agg({
            energy_type: 'sum'
        })

        fig = px.choropleth(
            map_data,
            locations='ISO_A3',
            color=energy_type,
            hover_name='Entity',
            color_continuous_scale=px.colors.sequential.Plasma,
            title=f'Global {energy_type} Consumption in {latest_year}',
            labels={energy_type: 'Electricity Consumption (TWh)'}
        )
        fig.update_layout(custom_theme['layout'])
        return fig

    # ====================================================================================================================
    # Define Dashboard Layout
    # ====================================================================================================================

    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Energy Consumption Dashboard", className="text-center mb-4"),
                # Updated ButtonGroup: Removed 'Entities' button
                dbc.ButtonGroup([
                    dbc.Button("Worldwide", id="btn-worldwide", color="primary", className="me-1", n_clicks=0),
                    dbc.Button("Energy Types", id="btn-energy-types", color="primary", className="me-1", n_clicks=0),
                    dbc.Button("Search", id="btn-search", color="primary", className="me-1", n_clicks=0)
                ], className="mb-4"),
                html.Div(id='content')
            ], width=12)
        ], className="m-4")
    ], fluid=True)

    # ======================================================================================================================
    # Define Callbacks
    # ======================================================================================================================

    # Callback to update content based on button clicks
    @app.callback(
        Output('content', 'children'),
        [
            Input('btn-worldwide', 'n_clicks'),
            Input('btn-energy-types', 'n_clicks'),
            Input('btn-search', 'n_clicks')
        ]
    )
    def render_content(btn_worldwide, btn_energy_types, btn_search):
        ctx = dash.callback_context

        if not ctx.triggered:
            return html.Div([
                html.H4("Please select a section to view the data.")
            ], style={'textAlign': 'center', 'marginTop': '50px'})
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if button_id == 'btn-worldwide':
            return html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Label("Select Energy Type:", htmlFor="worldwide-energy-type-dropdown"),
                        dcc.Dropdown(
                            id='worldwide-energy-type-dropdown',
                            options=[{'label': key, 'value': value} for key, value in energy_types.items()],
                            value='Electricity from wind - TWh',
                            multi=False,
                            placeholder="Select energy type...",
                            clearable=False
                        )
                    ], width=4)
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col([
                        dcc.Loading(
                            id="loading-worldwide-map",
                            type="default",
                            children=dcc.Graph(id='fig-worldwide-map')
                        )
                    ], width=12)
                ])
            ])
        
        elif button_id == 'btn-energy-types':
            return html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Label("Select Year:", htmlFor="year-dropdown"),
                        dcc.Dropdown(
                            id='year-dropdown',
                            options=[{'label': year, 'value': year} for year in range(energy_year_min, energy_year_max + 1)],
                            value=energy_year_max,
                            multi=False,
                            placeholder="Select year...",
                            clearable=False
                        )
                    ], width=6),
                    dbc.Col([
                        html.Label("Select Entities:", htmlFor="entity-dropdown"),
                        dcc.Dropdown(
                            id='entity-dropdown',
                            options=[{'label': entity, 'value': entity} for entity in energy_entities],
                            value = ['Tunisia'],  # Default to all entities(Tunisia)
                            multi=True,
                            placeholder="Select entities...",
                            clearable=False
                        )
                    ], width=6)
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col([
                        dcc.Loading(
                            id="loading-energy-pie",
                            type="default",
                            children=dcc.Graph(id='fig-energy-pie')
                        )
                    ], width=6),
                    dbc.Col([
                        dcc.Loading(
                            id="loading-energy-area",
                            type="default",
                            children=dcc.Graph(id='fig-energy-area')
                        )
                    ], width=6)
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col([
                        dcc.Loading(
                            id="loading-energy-bar",
                            type="default",
                            children=dcc.Graph(id='fig-energy-bar')
                        )
                    ], width=12)
                ])
            ])
        
        elif button_id == 'btn-search':
            return html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H4("Search Energy Consumption Data", className="mb-4"),
                        html.Div([
                            html.Label("Select Year Range:", htmlFor="year-slider"),
                            dcc.RangeSlider(
                                id='year-slider',
                                min=energy_year_min,
                                max=energy_year_max,
                                value=[energy_year_min, energy_year_max],
                                marks=energy_year_marks,
                                step=1,
                                tooltip={"placement": "bottom", "always_visible": True}
                            ),
                            html.Br(),
                            html.Label("Select Regions:", htmlFor="region-dropdown"),
                            dcc.Dropdown(
                                id='region-dropdown',
                                options=[{'label': region, 'value': region} for region in energy_entities],
                                value= ['Tunisia'],  # Default energy entity (Tunisia)
                                multi=True,
                                placeholder="Select regions...",
                                clearable=False
                            ),
                            html.Br(),
                            html.Label("Select Energy Type:", htmlFor="energy-type-dropdown"),
                            dcc.Dropdown(
                                id='energy-type-dropdown',
                                options=[{'label': key, 'value': value} for key, value in energy_types.items()],
                                value='Electricity from wind - TWh',
                                multi=False,
                                placeholder="Select energy type...",
                                clearable=False
                            )
                        ], style={'marginBottom': '20px'})
                    ], width=12)
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col([
                        dcc.Loading(
                            id="loading-search-line",
                            type="default",
                            children=dcc.Graph(id='fig-search-line')
                        )
                    ], width=6),
                    dbc.Col([
                        dcc.Loading(
                            id="loading-search-bar",
                            type="default",
                            children=dcc.Graph(id='fig-search-bar')
                        )
                    ], width=6)
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col([
                        dcc.Loading(
                            id="loading-search-pie",
                            type="default",
                            children=dcc.Graph(id='fig-search-pie')
                        )
                    ], width=6),
                    dbc.Col([
                        dcc.Loading(
                            id="loading-search-area",
                            type="default",
                            children=dcc.Graph(id='fig-search-area')
                        )
                    ], width=6)
                ])
            ])

    # Callback for Worldwide section
    @app.callback(
        Output('fig-worldwide-map', 'figure'),
        [
            Input('worldwide-energy-type-dropdown', 'value')
        ]
    )
    def update_worldwide_map(selected_energy_type):
        if selected_energy_type is None:
            raise PreventUpdate

        fig = create_worldwide_map(energy_data, selected_energy_type)
        return fig

    # Callback for Energy Types section
    @app.callback(
        [
            Output('fig-energy-pie', 'figure'),
            Output('fig-energy-area', 'figure'),
            Output('fig-energy-bar', 'figure')
        ],
        [
            Input('year-dropdown', 'value'),
            Input('entity-dropdown', 'value')  # Existing Input for Entity Dropdown
        ]
    )
    def update_energy_types(selected_year, selected_entities):
        if selected_year is None or not selected_entities:
            # Return empty figures with messages
            empty_fig = go.Figure()
            empty_fig.update_layout(
                title="Please select a year and at least one entity to display the data.",
                paper_bgcolor='#FAFAFA',
                plot_bgcolor='#FAFAFA',
                font=dict(color='#333333')
            )
            return empty_fig, empty_fig, empty_fig

        # Filter data for the selected year and entities
        filtered_df = energy_data[
            (energy_data['Year'] == selected_year) &
            (energy_data['Entity'].isin(selected_entities))
        ]

        if filtered_df.empty:
            # Return empty figures with messages
            empty_fig = go.Figure()
            empty_fig.update_layout(
                title="No data available for the selected year and entities.",
                paper_bgcolor='#FAFAFA',
                plot_bgcolor='#FAFAFA',
                font=dict(color='#333333')
            )
            return empty_fig, empty_fig, empty_fig

        # Pie Chart
        pie_fig = create_energy_pie_fig(filtered_df, selected_year)

        # Area Chart (Cumulative up to selected year for selected entities)
        cumulative_data = energy_data[
            (energy_data['Year'] <= selected_year) &
            (energy_data['Entity'].isin(selected_entities))
        ]
        area_fig = create_energy_area_fig(cumulative_data, cumulative=True)

        # Bar Chart
        bar_fig = create_energy_bar_fig(filtered_df)

        return pie_fig, area_fig, bar_fig

    # Callback for Search section
    @app.callback(
        [
            Output('fig-search-line', 'figure'),
            Output('fig-search-bar', 'figure'),
            Output('fig-search-pie', 'figure'),
            Output('fig-search-area', 'figure')
        ],
        [
            Input('year-slider', 'value'),
            Input('region-dropdown', 'value'),
            Input('energy-type-dropdown', 'value')
        ]
    )
    def update_search_section(year_range, regions, energy_type):
        if not regions or energy_type is None:
            # Return empty figures with messages
            empty_fig = go.Figure()
            empty_fig.update_layout(
                title="Please select at least one region and an energy type to display the data.",
                paper_bgcolor='#FAFAFA',
                plot_bgcolor='#FAFAFA',
                font=dict(color='#333333')
            )
            return empty_fig, empty_fig, empty_fig, empty_fig

        # Filter the data based on selected year range and regions
        filtered_df = energy_data[
            (energy_data['Year'] >= year_range[0]) &
            (energy_data['Year'] <= year_range[1]) &
            (energy_data['Entity'].isin(regions))
        ]

        if filtered_df.empty:
            # Return empty figures with messages
            empty_fig = go.Figure()
            empty_fig.update_layout(
                title="No data available for the selected filters.",
                paper_bgcolor='#FAFAFA',
                plot_bgcolor='#FAFAFA',
                font=dict(color='#333333')
            )
            return empty_fig, empty_fig, empty_fig, empty_fig

        # Line Chart for selected energy type
        line_fig = px.line(
            filtered_df,
            x='Year',
            y=energy_type,
            color='Entity',
            title=f'{energy_type} Consumption Trends',
            labels={'value': 'Electricity Consumption (TWh)', 'Entity': 'Entity'},
            markers=True
        )
        line_fig.update_layout(custom_theme['layout'])

        # Bar Chart for comparing energy consumption across regions for the selected energy type
        bar_fig = px.bar(
            filtered_df,
            x='Entity',
            y=energy_type,
            title=f'Energy Consumption by Region for {energy_type}',
            labels={'Entity': 'Region', energy_type: 'Electricity Consumption (TWh)'},
            barmode='group'
        )
        bar_fig.update_layout(custom_theme['layout'])

        # Pie Chart for energy consumption distribution for the selected energy type
        pie_data = filtered_df.groupby('Entity')[energy_type].sum().reset_index()
        pie_fig = px.pie(
            pie_data,
            names='Entity',
            values=energy_type,
            title=f'Energy Consumption Distribution for {energy_type}',
            labels={'Entity': 'Region', energy_type: 'Electricity Consumption (TWh)'}
        )
        pie_fig.update_layout(custom_theme['layout'])

        # Area Chart for cumulative energy consumption based on selected energy type
        area_data = filtered_df.groupby('Year')[energy_type].sum().reset_index().cumsum()
        area_fig = px.area(
            area_data,
            x='Year',
            y=energy_type,
            title=f'Cumulative {energy_type} Consumption Over Years',
            labels={'Year': 'Year', energy_type: 'Cumulative Electricity Consumption (TWh)'}
        )
        area_fig.update_layout(custom_theme['layout'])

        return line_fig, bar_fig, pie_fig, area_fig

    # ==========================================================================================
    # Run the Dash App
    # ==========================================================================================

    if __name__ == '__main__':
        app.run_server(debug=True)
