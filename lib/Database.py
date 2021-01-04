
from datetime import datetime, timedelta
from influxdb import DataFrameClient
import pandas as pd
import numpy as np


class Database:

    def __init__(self, client = DataFrameClient(host = 'localhost', port = 8086)):
        """ (object, object) -> void
        Constructor of Database. Sets the database client.
        """
        self.client = client


    def query(self, query_string):
        """ (object, string) -> object
        This function queries the given query string.
        It also creates (if not exist) and switches to the database meteorology.
        It returns the result as a dataframe.
        """
        self.client.create_database('meteorology')
        self.client.switch_database('meteorology')
        try:
            # execute query
            return self.client.query(query_string)
        except Exception as err:
            print (err)
        # return data frame result
        return pd.DataFrame()

    def query_all(self, query_string):
        """ (object, string) -> object
        This function queries the given query string through the query function.
        It combines the results into one single dataframe.
        The return value is the combined dataframe.
        """
        result = self.query(query_string)
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

        # return combined dataframe
        return all_data

    def query_combine(self, query_string):
        """ (object, string) -> object
        This function queries the given query string through the query function.
        It combines the results into one single dataframe.
        The return value is the combined dataframe.
        """
        # query all stations
        result = self.query_all(query_string)
        if result is None:
            return pd.DataFrame()

        # only get latest (filter out stations without new data)
        latest = result[result.index == result.index.max()]

        if 'wind_direction' in latest:
            wind_direction = latest['wind_direction']

            # calculate mean wind direction based on formula from: https://en.wikipedia.org/wiki/Mean_of_circular_quantities#Mean_of_angles
            mean_wind = np.round(np.arctan2(sum(np.sin(wind_direction)), sum(np.cos(wind_direction))) * 180 / np.pi) % 360

            # convert direction to string
            if 292.5 < mean_wind <= 337.5:
                mean_wind = 'NW'
            elif 247.5 < mean_wind <= 292.5:
                mean_wind = 'W'
            elif 202.5 < mean_wind <= 247.5:
                mean_wind = 'SW'
            elif 157.5 < mean_wind <= 202.5:
                mean_wind = 'S'
            elif 112.5 < mean_wind <= 157.5:
                mean_wind = 'SE'
            elif 67.5 < mean_wind <= 112.5:
                mean_wind = 'E'
            elif 22.5 < mean_wind <= 67.5:
                mean_wind = 'NE'
            else:
                mean_wind = 'N'

        # get mean of all values
        latest = latest.mean(skipna=True).round(1)

        if 'wind_direction' in latest:
            latest['wind_direction'] = mean_wind

        return latest

    def get_last_data(self):
        """ (object) -> object
        This function returns the latest available observation.
        """
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

    def get_data_specific_date(self, date):
        """ (object, object) -> object
        This function returns a dataframe containing the closest 30 obervations after 'date'.
        """
        # convert date to string in the specified date format
        date_string = date.strftime('%Y-%m-%d %H:%M:%S')

        # run query
        result = self.query_all(f'''
                                SELECT
                                air_temperature
                                FROM /^(tiefenbrunnen|mythenquai)/
                                WHERE time > '{date_string}'
                                ORDER BY ASC LIMIT 30
                        ''')
        return result

    # gets data from exactly one year ago
    def get_data_year_ago(self):
        """ (object) -> object
        This function returns a dataframe containing the closest 20 obervations one year ago.
        """
        # get date now in utc
        date_year_ago = datetime.utcnow()

        # get date now - 1 year in utc
        date_year_ago = date_year_ago.replace(year=date_year_ago.year - 1)

        # convert date to string in the specified date format
        date_year_ago_string = date_year_ago.strftime('%Y-%m-%d %H:%M:%S')

        # run query
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
        """ (object) -> object
        This function returns all data between now and now - 5 hours.
        """
        # get date now
        date_now = datetime.utcnow()

        # get date now - 5 hours
        start_date = date_now - timedelta(hours=5)

        # convert dates to string in the specified date format
        start_date_string = start_date.strftime('%Y-%m-%d %H:%M:%S')
        end_date_string = date_now.strftime('%Y-%m-%d %H:%M:%S')

        # run query
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
        """ (object) -> object
        This function returns all observations around +/- 7 days from every year except the current year.
        """
        # get date now
        date_now = datetime.utcnow()
        result = None

        # iterate through all years
        for x in range(1, date_now.year - 2006):
            date_x_years_ago = date_now.replace(year=date_now.year-x)

            # get dates +/- 7 days
            start_date = date_x_years_ago - timedelta(days=7)
            end_date = date_x_years_ago + timedelta(days=7)

            # convert dates to string of given format
            start_date_string = start_date.strftime('%Y-%m-%d %H:%M:%S')
            end_date_string = end_date.strftime('%Y-%m-%d %H:%M:%S')

            # run query
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
        """ (object, object) -> object
        This function returns the date and time when the last 10 minute mark passed.
        """
        rounded_time = time - timedelta(minutes=time.minute % 10, seconds=time.second, microseconds=time.microsecond)
        return rounded_time