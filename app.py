import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
from influxdb import DataFrameClient

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

def query(sql):
    client = DataFrameClient(host = 'localhost', port = 8086, database = 'meteorology')
    return client.query(sql)

def query_all(sql):
    result = query(sql)
    all_data = None

    # combine all stations into single dataframe
    for measurement in result:
        data = result[measurement]
        data['station'] = measurement
        data.index = data.index.tz_convert('Europe/Berlin')
        data.index = data.index.tz_localize(None)
        if all_data is None:
            all_data = data
        else:
            all_data = all_data.append(data, sort=False)
    return all_data

def query_combine(sql):
    # query all stations
    result = query_all(sql)

    # only get latest (filter out stations without new data)
    latest = result[result.index == result.index.max()]

    # get mean of all values
    return latest.mean(skipna=True)

def get_last_data():
    return query_combine('''
                            SELECT
                            air_temperature,
                            water_temperature,
                            wind_speed_avg_10min,
                            wind_force_avg_10min,
                            wind_direction
                            FROM /^(tiefenbrunnen|mythenquai)/
                            ORDER BY DESC LIMIT 1
                        ''')

# fig_temperature = px.scatter(overview_data, x=overview_data.index, y="temp", color="station")

# fig_wind = px.scatter(overview_data, x=overview_data.index, y="wind", color="station")

app.layout = html.Div(children=[
    html.H1(children='Weatherstation'),

    html.Div(
        children=[
            html.Div(
                children=[
                    html.H2(children=[
                        html.Span(children='Air: '),
                        html.Span(id='air-temperature'),
                        html.Span(children=' °C')
                    ]),

                    html.H2(children=[
                        html.Span(children='Water: '),
                        html.Span(id='water-temperature'),
                        html.Span(children=' °C')
                    ]),
                ],
                style={
                    'border-right': '1px solid black',
                    'flex-grow': '1'
                }
            ),
            html.Div(
                children=[
                    html.Div(
                        children=[
                            html.H2(children=[
                                html.Span(children='Windspeed: '),
                                html.Span(id='wind-speed'),
                                html.Span(children=' m/s')
                            ]),

                            html.H2(children=[
                                html.Span(children='Windforce: '),
                                html.Span(id='wind-force'),
                                html.Span(children=' BFT')
                            ]),

                            html.H2(children=[
                                html.Span(children='Winddirection: '),
                                html.Span(id='wind-direction'),
                                html.Span(children='°')
                            ]),
                        ],
                        style={
                            'border-bottom': '1px solid black'
                        }
                    ),
                    html.Div(
                        children=[
                            html.H2(children=[
                                html.Span(children='Test'),
                            ])
                        ]
                    )
                ],
                style={
                    'flex-grow': '1'
                }
            ),
        ],
        style={
            'display': 'flex'
        }
    ),

    # dcc.Graph(
    #     id='temperature-graph',
    #     figure=fig_temperature
    # ),

    # dcc.Graph(
    #     id='wind-graph',
    #     figure=fig_wind
    # ),

    dcc.Interval(
        id='interval-component',
        interval=60000, # in milliseconds
        n_intervals=0
    )
])

@app.callback(Output('air-temperature', 'children'),
              Output('water-temperature', 'children'),
              Output('wind-speed', 'children'),
              Output('wind-force', 'children'),
              Output('wind-direction', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_text(n):
    last_data = get_last_data()
    return last_data['air_temperature'], last_data['water_temperature'], last_data['wind_speed_avg_10min'], last_data['wind_force_avg_10min'], last_data['wind_direction']

if __name__ == '__main__':
    app.run_server(debug=True)