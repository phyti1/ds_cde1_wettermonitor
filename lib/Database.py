
from datetime import datetime, timedelta
from influxdb import DataFrameClient
import pandas as pd


class Database:

    def __init__(self, client = DataFrameClient(host = 'localhost', port = 8086)):
        self.client = client


    def query(self, sql):
        self.client.create_database('meteorology')
        self.client.switch_database('meteorology')
        try:
            return self.client.query(sql)
        except Exception as err:
            print (err)
        return pd.DataFrame()

    def query_all(self, sql):
        result = self.query(sql)
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

    def query_combine(self, sql):
        # query all stations
        result = self.query_all(sql)
        if result is None:
            return pd.DataFrame()

        # only get latest (filter out stations without new data)
        latest = result[result.index == result.index.max()]

        # get mean of all values
        return latest.mean(skipna=True)

    def get_last_data(self):
        return self.query_combine('''
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
    def get_data_specific_date(self, date):
        date_string = date.strftime('%Y-%m-%d %H:%M:%S')
        result = self.query_all(f'''
                                SELECT
                                air_temperature
                                FROM /^(tiefenbrunnen|mythenquai)/
                                WHERE time > '{date_string}'
                                ORDER BY ASC LIMIT 30
                        ''')
        return result

    def get_data_year_ago(self):
        date_year_ago = datetime.utcnow()
        date_year_ago = date_year_ago.replace(year=date_year_ago.year-1)
        date_year_ago_string = date_year_ago.strftime('%Y-%m-%d %H:%M:%S')
        result = self.query_all(f'''
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

    def get_last_five_hours(self):
        date_now = datetime.utcnow()
        start_date = date_now - timedelta(hours=5)
        start_date_string = start_date.strftime('%Y-%m-%d %H:%M:%S')
        end_date_string = date_now.strftime('%Y-%m-%d %H:%M:%S')
        result = self.query_all(f'''
                            SELECT
                            air_temperature,
                            barometric_pressure_qfe
                            FROM /^(tiefenbrunnen|mythenquai)/
                            WHERE time > '{start_date_string}' AND time < '{end_date_string}'
                            ORDER BY ASC
                    ''')
        return result

    def get_data_comparison(self):
        date_now = datetime.utcnow()
        result = None
        for x in range(1, date_now.year - 2006):
            date_x_years_ago = date_now.replace(year=date_now.year-x)
            start_date = date_x_years_ago - timedelta(days=7)
            end_date = date_x_years_ago + timedelta(days=7)
            start_date_string = start_date.strftime('%Y-%m-%d %H:%M:%S')
            end_date_string = end_date.strftime('%Y-%m-%d %H:%M:%S')
            data = self.query_all(f'''
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
        if not result is None:
            result.sort_index(inplace=True)
        return result

    def get_time_rounded(self, time):
        rounded_time = time - timedelta(minutes=time.minute % 10,
        seconds=time.second,
        microseconds=time.microsecond)
        return rounded_time