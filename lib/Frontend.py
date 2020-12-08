from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import threading
from datetime import datetime, timedelta
import time

from lib.Database import Database
from lib.Prediction import Prediction
from lib.Sync import Sync

class Frontend:

    def __init__(self, app):
        """ (object) -> void
        Contructor of Frontend. Will initialize other classes and set default values.
        """
        self.is_loading_prediction = False
        # instanciate Database, Sync and Prediction classes and store in private variables
        self.database = Database()
        self.sync = Sync()
        self.prediction = Prediction(self.database)
        # create empty graph data to be able to display in UI
        self.forecast_graph = {}
        # store dash instance in private variable
        self.app = app

    def run(self):
        """ (void) -> void
        Function to run the weatherstation UI.
        """
        # import all historic data and continously load latest data
        self.sync.import_data_async(True)
        # start the prediction calculation loop in new thread
        threading.Thread(target = self.run_prediction_periodic).start()
        # define dash callback function, runs self.update_text
        self.app.callback(Output('air-temperature', 'children'),
                Output('water-temperature', 'children'),
                Output('wind-speed', 'children'),
                Output('wind-force', 'children'),
                Output('wind-direction', 'children'),
                [Input('interval-component', 'n_intervals')])(self.update_text)

        # define dash callback function, runs self.update_prediction_text
        self.app.callback(Output('forecast-pressure', 'children'),
                [Input('interval-component', 'n_intervals')])(self.update_prediction_text)

        # define dash callback function, runs self.update_prediction_graph
        self.app.callback(Output('forecast-graph', 'figure'),
                [Input('interval-component', 'n_intervals')])(self.update_prediction_graph)

        # set dash's user interface layout in html like style
        self.app.layout = html.Div(children=[
            html.H1(children='Weatherstation Lake of Zurich'),

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
                                    dcc.Graph(
                                        id='forecast-graph',
                                        figure=self.forecast_graph
                                    )
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

    # Use this function for weather forecast visualization
    def load_day(self, date):
        """ (TODO whats that?) -> px.scatter
        Loads a specific day from the database, displays it in the forecast graph and returns it.
        """
        if date != None:
            # load specific date from database
            overview_data = self.database.get_data_specific_date(date)
            # only update view if there is any data
            if not overview_data is None and overview_data.empty == False:
                # create and set new forecast graph
                grouped_overview_data = overview_data.groupby(overview_data.index)
                mean_overview_data = grouped_overview_data.mean()
                #mean_overview_data = mean_overview_data.reset_index()
                self.forecast_graph = px.scatter(mean_overview_data, x=mean_overview_data.index, y="air_temperature",
                    color_discrete_sequence=['red'], labels=dict(index="Time", air_temperature="Air Temperature"),
                    title="Temperature Forecast based on past 8 years (Mean of Mythenquai & Tiefenbrunnen)")
        return self.forecast_graph

    def is_data_uptodate(self, last_data):
        """ (TODO whats that?) -> bool
        Determines whether the latest data could be loaded and returns true if it was.
        """
        if last_data is None or last_data.empty or last_data.index < datetime.now('Europe/Berlin') - timedelta(minutes = 16):
            return True
        return False

    def update_text(self, n):
        """ (int) -> string, string, string, string
        Callback function for the UI measurement values.
        """
        # read the latest data observation from the database
        last_data = self.database.get_last_data()
        # check if the loaded data is empty
        if last_data.empty:
            # return empty values to UI to be able to show the UI before the database connection works
            return '', '', '', '', ''
        else:
            # return the newly read data
            return last_data['air_temperature'], last_data['water_temperature'], last_data['wind_speed_avg_10min'], last_data['wind_force_avg_10min'], last_data['wind_direction']

    def update_prediction_text(self, n):
        """ (int) -> string
        Callback function for calculating the air pressure prediction.
        """
        # calculate the prediction
        prediction = self.prediction.predict_press()
        # return the prediction outcome sign to display in the UI
        return prediction

    def update_prediction_graph(self, n):
        """ (int) -> string
        Callback function to return the periodically calculated prediction graph.
        """
        # return the graph from the private variable
        return self.forecast_graph

    def run_prediction_periodic(self):
        """ (void) -> void
        Function to periodically calculate the temperature prediction. 
        It is meant to be called once and will run until the sofware is shut down.
        """
        # loop runs until the software is closed down
        while(True):
            # calulcates and shows the temperature prediction in the forecast_graph (TODO Takes 2min 10sec! on raspberry pi 4)
            self.load_day(self.prediction.predict_temp())
            # wait some time to reevaluate with new data
            time.sleep(10)
