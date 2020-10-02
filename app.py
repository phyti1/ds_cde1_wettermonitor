import dash
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

def query_combine(sql):
    result = query(sql)
    all_data = False
    for measurement in result:
        data = result[measurement]
        data['station'] = measurement
        data.index = data.index.tz_convert('Europe/Berlin')
        data.index = data.index.tz_localize(None)
        if isinstance(all_data, bool):
            all_data = data
        else:
            all_data = all_data.append(data, sort=False)
    return all_data

def get_overview_data():
    return query_combine('''
                            SELECT
                            MAX(air_temperature) as max_air,
                            MIN(air_temperature) as min_air,
                            MAX(wind_speed_avg_10min) as mean_wind
                            FROM /^(tiefenbrunnen|mythenquai)/
                            GROUP BY TIME(1w)
                            ORDER BY DESC LIMIT 300
                        ''')

def get_last_week():
    return query_combine('''
                            SELECT
                            air_temperature as temp,
                            wind_speed_avg_10min as wind
                            FROM /^(tiefenbrunnen|mythenquai)/
                            WHERE wind_speed_avg_10min > 8
                            ORDER BY ASC LIMIT 1000
                        ''')



# overview_data = get_overview_data()
# fig_temperature = px.scatter(overview_data, x=overview_data.index, y=["min_air", "max_air"])

# fig_wind = px.scatter(overview_data, x=overview_data.index, y="mean_wind", color="station")

overview_data = get_last_week()
fig_temperature = px.scatter(overview_data, x=overview_data.index, y="temp", color="station")

fig_wind = px.scatter(overview_data, x=overview_data.index, y="wind", color="station")


app.layout = html.Div(children=[
    html.H1(children='Weatherstation'),

    dcc.Graph(
        id='temperature-graph',
        figure=fig_temperature
    ),

    dcc.Graph(
        id='wind-graph',
        figure=fig_wind
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)