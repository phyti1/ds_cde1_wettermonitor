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
import numpy as np

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

# Gets data from 'date' + 5 hours
def get_data_specific_date(date):
    date_string = date.strftime('%Y-%m-%d %H:%M:%S')
    result = query_all(f'''
                            SELECT
                            air_temperature
                            FROM /^(tiefenbrunnen|mythenquai)/
                            WHERE time >= '{date_string}' 
                            ORDER BY ASC LIMIT 30
                    ''')
    return result

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

def get_last_five_hours():
    date_now = datetime.utcnow()
    start_date = date_now - timedelta(hours=5)
    start_date_string = start_date.strftime('%Y-%m-%d %H:%M:%S')
    end_date_string = date_now.strftime('%Y-%m-%d %H:%M:%S')
    result = query_all(f'''
                        SELECT
                        air_temperature
                        FROM /^(tiefenbrunnen|mythenquai)/
                        WHERE time > '{start_date_string}' AND time < '{end_date_string}'
                        ORDER BY ASC
                ''')
    return result

def get_data_comparison():
    date_now = datetime.utcnow()
    result = None
    for x in range(1, date_now.year - 2006):
        date_x_years_ago = date_now.replace(year=date_now.year-x)
        start_date = date_x_years_ago - timedelta(days=7)
        end_date = date_x_years_ago + timedelta(days=7)
        start_date_string = start_date.strftime('%Y-%m-%d %H:%M:%S')
        end_date_string = end_date.strftime('%Y-%m-%d %H:%M:%S')
        data = query_all(f'''
                            SELECT
                            air_temperature
                            FROM /^(tiefenbrunnen|mythenquai)/
                            WHERE time > '{start_date_string}' AND time < '{end_date_string}'
                            ORDER BY ASC
                    ''')
        if result is None:
            result = data
        else:
            result = result.append(data, sort=False)
    result.sort_index(inplace=True)
    return result

def get_time_rounded(time):
    rounded_time = time - timedelta(minutes=time.minute % 10,
    seconds=time.second,
    microseconds=time.microsecond)
    return rounded_time

def calculate_best_match():
    historic_match_data = get_data_comparison()
    current_match_data = get_last_five_hours()
    date_now = datetime.utcnow()
    date_now = get_time_rounded(date_now)
    date_now_seven = datetime.utcnow() + timedelta(days=7)
    date_now_seven = get_time_rounded(date_now_seven)
    date_op1 = ''
    date_op2 = ''
    difference_dict = {}
    for years in range(1, date_now.year - 2006):
        for days in range(14):
            difference = 0
            for ten_minute_interval in range(30):
                date_op1 = (date_now_seven - timedelta(days=years*365+days, minutes=ten_minute_interval*10)).strftime('%Y-%m-%d %H:%M:%S')
                date_op2 = (date_now - timedelta(minutes=ten_minute_interval*10)).strftime('%Y-%m-%d %H:%M:%S')
                if date_op1 in historic_match_data.index and date_op2 in current_match_data.index:
                    if isinstance(historic_match_data['air_temperature'][date_op1], np.float64):
                        data_op1 = historic_match_data['air_temperature'][date_op1]
                    else:
                        data_op1 = historic_match_data['air_temperature'][date_op1].mean(skipna=True)

                    if isinstance(current_match_data['air_temperature'][date_op2], np.float64):
                        data_op2 = current_match_data['air_temperature'][date_op2]
                    else:
                        data_op2 = current_match_data['air_temperature'][date_op2].mean(skipna=True)

                    difference += abs(data_op1 - data_op2)
            if difference > 0:
                difference_dict[date_now_seven - timedelta(days=years*365+days)] = difference
    result = min(difference_dict, key=difference_dict.get)
    return result

# Use this function for weather forecast viz
def load_day(date):
    global forecast_graph_data
    overview_data = get_data_specific_date(date)
    #only update view if there is any data
    if(overview_data.empty == False):
        forecast_graph_data = px.scatter(overview_data, x=overview_data.index, y="air_temperature", color="station", 
            labels=dict(index="Time", air_temperature="Air Temperature", station="Weather Forecast"))

def load_last_year():
    global fig_temperature
    overview_data = get_data_year_ago()
    #only update view if there is any data
    if(overview_data.empty == False):
        fig_temperature = px.scatter(overview_data, x=overview_data.index, y="air_temperature", color="station", 
            labels=dict(index="Time", air_temperature="Air Temperature", station="Last Year"))

def check_if_last_entry_time_is_more_than_sixteen_minutes_ago_or_not_existent(last_data):
    if last_data.empty or last_data.index < datetime.now('Europe/Berlin') - timedelta(minutes = 16): 
        return True
    return False

# initially load old data to be able to show ui
load_last_year()
# initially load forecast data
load_day(calculate_best_match())

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
                    ),
                    html.Div(
                        children=[
                            html.H2(children=[
                                dcc.Graph(
                                    id='temperature-graph-forecast',
                                    figure=forecast_graph_data
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

    # Show forecast
    load_day(calculate_best_match())

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
