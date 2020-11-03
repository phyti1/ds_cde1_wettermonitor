import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
#import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import sync
import threading
from influxdb import DataFrameClient
from datetime import datetime, timedelta
import sys

# global exception handling
def my_except_hook(exctype, value, traceback):
    if exctype == AttributeError:
        sync.import_data()
        main()
    else:
        sys.__excepthook__(exctype, value, traceback)
sys.excepthook = my_except_hook

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Wettermonitor"
#app._favicon = "Icons8-Ios7-Weather-Partly-Cloudy-Rain.ico"


def query(sql):
    client = DataFrameClient(host = 'localhost', port = 8086)
    client.create_database('meteorology')
    client.switch_database('meteorology')
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

def get_data_year_ago():
    date_year_ago = datetime.utcnow()
    date_year_ago = date_year_ago.replace(year=date_year_ago.year-1)
    date_year_ago_string = date_year_ago.strftime('%Y-%m-%d %H:%M:%S')
    result = query_all(f'''
                            SELECT
                            air_temperature,
                            water_temperature,
                            wind_speed_avg_10min,
                            wind_force_avg_10min,
                            wind_direction
                            FROM /^(tiefenbrunnen|mythenquai)/
                            WHERE time > '{date_year_ago_string}' 
                            ORDER BY ASC LIMIT 20
                    ''')
    return result

def load_last_year():
    global fig_temperature
    overview_data = get_data_year_ago()
    fig_temperature = px.scatter(overview_data, x=overview_data.index, y="air_temperature", color="station", 
        labels=dict(index="Time", air_temperature="Air Temperature", station="Wetter Station"))

def check_if_last_entry_time_is_more_than_sixteen_minutes_ago_or_not_existent(last_data):
    if last_data.empty or last_data.index < datetime.now('Europe/Berlin') - timedelta(minutes = 16): 
        return True
    return False

# initially load old data to be able to show ui
load_last_year()

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
                    'flex-grow': '1',
                    'min-width': '300px'
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
                                dcc.Graph(
                                    id='temperature-graph',
                                    figure=fig_temperature
                                ),
                            ])
                        ]
                    )
                ],
                style={
                    'flex-grow': '1',
                    'padding-left': '10px'
                }
            ),
        ],
        style={
            'display': 'flex',
            'fxLayoutGap': '200px'
        }
    ),

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
    load_last_year()
    last_data = get_last_data()

    threading.Thread(target=sync.import_latest_data).start()

    #if check_if_last_entry_time_is_more_than_sixteen_minutes_ago_or_not_existent(last_data):
    #    print('nicht gut')
    return last_data['air_temperature'], last_data['water_temperature'], last_data['wind_speed_avg_10min'], last_data['wind_force_avg_10min'], last_data['wind_direction']



def main():
    try:
        app.run_server(debug=True)
    except AttributeError as err:
        print(err)
        #try again after loading data
        sync.import_data()
        app.run_server(debug=True)

if __name__ == '__main__':
    main()
