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

    def __init__(self, app):
        self.is_loading_prediction = False

        self.database = Database()
        self.sync = Sync()
        self.prediction = Prediciton(self.database)
        self.forecast_graph = {}
        self.app = app

    def run(self):
        # import all historic data and continously load latest data
        self.sync.import_data_async(True)

        self.app.callback(Output('air-temperature', 'children'),
                Output('water-temperature', 'children'),
                Output('wind-speed', 'children'),
                Output('wind-force', 'children'),
                Output('wind-direction', 'children'),
                [Input('interval-component', 'n_intervals')])(self.update_text)

        self.app.callback(Output('forecast-pressure', 'children'),
                [Input('interval-component', 'n_intervals')])(self.update_prediction_text)

        self.app.callback(Output('forecast-graph', 'figure'),
                [Input('interval-component', 'n_intervals')])(self.update_prediction_graph)
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
                                            id='forecast-graph',
                                            figure=self.forecast_graph
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
                self.forecast_graph = px.scatter(overview_data, x=overview_data.index, y="air_temperature", color="station",
                    labels=dict(index="Time", air_temperature="Air Temperature", station="Weather Forecast"))

        return self.forecast_graph

    def check_if_last_entry_time_is_more_than_sixteen_minutes_ago_or_not_existent(self, last_data):
        if last_data is None or last_data.empty or last_data.index < datetime.now('Europe/Berlin') - timedelta(minutes = 16):
            return True
        return False

    def load_prediction(self):
        if not self.is_loading_prediction:
            # Show forecast
            self.is_loading_prediction = True
            self.load_day(self.prediction.calculate_best_match())
            self.is_loading_prediction = False

    def update_text(self, n):
        last_data = self.database.get_last_data()

        threading.Thread(target=self.load_prediction).start()

        # import latest data
        self.sync.import_data_async()

        prediction = self.prediction.predict_press()

        #if check_if_last_entry_time_is_more_than_sixteen_minutes_ago_or_not_existent(last_data):
        #    print('nicht gut')

        if last_data.empty:
            return '', '', '', '', ''
        else:
            return last_data['air_temperature'], last_data['water_temperature'], last_data['wind_speed_avg_10min'], last_data['wind_force_avg_10min'], last_data['wind_direction']

    def update_prediction_text(self, n):
        prediction = self.prediction.predict_press()
        return prediction

    def update_prediction_graph(self, n):
        # Show forecast
        forecast = self.load_day(self.prediction.calculate_best_match())
        return forecast
