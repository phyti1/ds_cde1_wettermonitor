from datetime import datetime, timedelta
import numpy as np
import pandas as pd

class Prediction:
    def __init__(self, database):
        """ (object) -> void
        Contructor of the Prediction class.
        """
        # store the constructor parameter in a private variable
        self.database = database

    def predict_temp(self):
        """ (void) -> object
        Function predicts the temperature with 30 data points in the future, corresponding to 5 hours from now.
        Prediction/Forecast is based on past years. Number of past years to use can easily be edited in this function.
        For a quick howto, have a look in the software documentation.
        """
        # load the data of all past years that is used for further comparison in the prediction
        historic_match_data = self.database.get_data_comparison()
        # load the data of the last 5 hours from now
        current_match_data = self.database.get_last_five_hours()
        # just in case there is a None occuring instead of regular data...
        if current_match_data is None:
            return None

        # initialize the date variable with current date & time, rounded to 10 minute intervals
        date_now = datetime.utcnow()
        date_now = self.database.get_time_rounded(date_now)
        # get timestamp + 7 days from now so it is possible to count back 14 days to iterate through +/- 7 days
        date_now_seven = datetime.utcnow() + timedelta(days=7)
        date_now_seven = self.database.get_time_rounded(date_now_seven)
        # create empty dictionary for appending difference values later
        difference_dict = {}

        # find the best matching 5 hours in a timespan of +/- 7 days (14 days total)from now in the last 8 years
        # YOU CAN CHANGE THE NUMBER (n) USED FOR PREDICTION IN: "for years in range(n)" according to your preferences
        # but be aware of the fact that there is only data available back to 2006 and not further back!
        # insert (1, date_now.year - 2006) for (n) if you always want to use the full range of available years.
        # CHANGES MAY SLOW DOWN THE SYSTEM!
        for years in range(8):
            for days in range(14):
                difference = 0
                # compare all 30 available datapoints for each specific days in the past
                for ten_minute_interval in range(29):
                    # calculate a 10-minute interval datapoint from last 5 hours
                    current_datapoint = (date_now - timedelta(minutes=ten_minute_interval*10)).strftime('%Y-%m-%d %H:%M:%S')
                    # calculate same date intervals in specific date from past years
                    past_datapoint = (date_now_seven - timedelta(days=years*365+days, minutes=ten_minute_interval*10)).strftime('%Y-%m-%d %H:%M:%S')
                    # get airtemperature values from the past with the same timestamps like +/- 7 days from now in current year
                    if past_datapoint in historic_match_data.index and current_datapoint in current_match_data.index:
                        # check if temperature is existent in both stations and has the right format
                        if isinstance(historic_match_data['air_temperature'][past_datapoint], np.float64):
                            # take the only available temperature for this date
                            past_temperature = historic_match_data['air_temperature'][past_datapoint]
                        else:
                            # take the mean of both stations temperature for this date
                            past_temperature = historic_match_data['air_temperature'][past_datapoint].mean(skipna=True)
                        # check if temperature is existent in both stations and has the right format
                        if isinstance(current_match_data['air_temperature'][current_datapoint], np.float64):
                            # take the only available temperature for this date
                            current_temperature = current_match_data['air_temperature'][current_datapoint]
                        else:
                            # take the mean of both stations temperature for this date
                            current_temperature = current_match_data['air_temperature'][current_datapoint].mean(skipna=True)
                        # get the absolute difference between each two data points between years and weight according to elapsed time
                        difference += abs(past_temperature - current_temperature) * (30 - ten_minute_interval)
                # write these differences in a dictionary of all differences with absolute time as index (if existent)
                if difference > 0:
                    difference_dict[date_now_seven - timedelta(days=years*365+days)] = difference
        # find the minimum occuring difference in the difference dictionary
        result = min(difference_dict, key=difference_dict.get)
        return result

    def predict_press(self):
        """ (void) -> string
        This function evaluates whether the weather might be going to get better, 
        a lot better, worse or a lot worse based on the change in air pressure.
        """
        # read the last five hours of data
        last_hours_data = self.database.get_last_five_hours()
        # return an empty string if the data could not be loaded
        if last_hours_data is None or not 'barometric_pressure_qfe' in last_hours_data.columns:
            return ""
        # extract pressure data from the data
        pressure_data = last_hours_data['barometric_pressure_qfe']
        # convert the pandas dataset to a numpy array
        pressure_values = pressure_data.to_numpy()
        # remove nans for the data to use
        pressure_values_nonan = pressure_values[np.logical_not(np.isnan(pressure_values))]
        # take the first and oldest valid pressure measurement as the reference
        first_pressure = pressure_values_nonan[0]
        # take the last and newest valid pressure measurement to compare with
        last_pressure = pressure_values_nonan[len(pressure_values_nonan) - 1]
        # get the pressure difference of the newest and oldest value
        pres_difference = last_pressure - first_pressure
        # return the forecast string based on the splitting criteria 
        if(pres_difference > 5):
            # pressure rises > +5 hPa
            return "☀️"
        elif(pres_difference > 0):
            # pressure rises between 0 and +5 hPa
            return "⛅"
        elif(pres_difference > -5):
            # pressure falls between 0 and -5 hPa
            return "🌦"
        else:
            # pressure falls < -5 hPa
            return "⛈"