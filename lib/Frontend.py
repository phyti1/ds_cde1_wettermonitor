import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import threading
from datetime import datetime, timedelta

from lib.Database import Database
from lib.Prediciton import Prediciton
from lib.Sync import Sync

class Frontend:

    def __init__(self):
        self.database = Database()
        self.sync = Sync()
        self.prediction = Prediciton(self.database)
        self.fig_temperature = {}
        self.forecast_graph_data = {}

    def run(self):
        # import all historic data and continously load latest data
        self.sync.import_data_async(True)

        external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
        self.app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
        self.app.title = "Wettermonitor"
        #app._favicon = "Icons8-Ios7-Weather-Partly-Cloudy-Rain.ico"

        self.app.callback(Output('air-temperature', 'children'),
                Output('water-temperature', 'children'),
                Output('forecast-pressure', 'children'),
                Output('wind-speed', 'children'),
                Output('wind-force', 'children'),
                Output('wind-direction', 'children'),
                [Input('interval-component', 'n_intervals')])(self.update_text)

        self.app.layout = html.Div(children=[
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
                            html.H2(children=[
                                html.Span(children='Forecast: '),
                                html.Span(id='forecast-pressure'),
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
                                            figure=self.fig_temperature
                                        ),
                                    ])
                                ]
                            ),
                            html.Div(
                                children=[
                                    html.H2(children=[
                                        dcc.Graph(
                                            id='temperature-graph-forecast',
                                            figure=self.forecast_graph_data
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

    # Use this function for weather forecast viz
    def load_day(self, date):
        if date != None:
            overview_data = self.database.get_data_specific_date(date)
            #only update view if there is any data
            if not overview_data is None and overview_data.empty == False:
                self.forecast_graph_data = px.scatter(overview_data, x=overview_data.index, y="air_temperature", color="station",
                    labels=dict(index="Time", air_temperature="Air Temperature", station="Weather Forecast"))

    def load_last_year(self):
        overview_data = self.database.get_data_year_ago()

        #only update view if there is any data
        if not overview_data is None and overview_data.empty == False:
            self.fig_temperature = px.scatter(overview_data, x=overview_data.index, y="air_temperature", color="station",
                labels=dict(index="Time", air_temperature="Air Temperature", station="Last Year"))

    def check_if_last_entry_time_is_more_than_sixteen_minutes_ago_or_not_existent(self, last_data):
        if last_data is None or last_data.empty or last_data.index < datetime.now('Europe/Berlin') - timedelta(minutes = 16):
            return True
        return False

    def update_text(self, n):
        self.load_last_year()
        last_data = self.database.get_last_data()

        # Show forecast
        self.load_day(self.prediction.calculate_best_match())

        prediction = self.prediction.predict_press()

        #if check_if_last_entry_time_is_more_than_sixteen_minutes_ago_or_not_existent(last_data):
        #    print('nicht gut')

        if last_data.empty:
            return '', '', prediction, '', '', ''
        else:
            return last_data['air_temperature'], last_data['water_temperature'], prediction, last_data['wind_speed_avg_10min'], last_data['wind_force_avg_10min'], last_data['wind_direction']