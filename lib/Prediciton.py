from datetime import datetime, timedelta
import numpy as np
import pandas as pd

class Prediciton:
    def __init__(self, database):
        """ (object) -> void
        Contructor of the Prediction class.
        """
        # store the constructor parameter in a private variable
        self.database = database

    def predict_temp(self):
        """ (void) -> object
        TODO comment
        """
        historic_match_data = self.database.get_data_comparison()
        current_match_data = self.database.get_last_five_hours()
        if current_match_data is None:
            return None
        date_now = datetime.utcnow()
        date_now = self.database.get_time_rounded(date_now)
        date_now_seven = datetime.utcnow() + timedelta(days=7)
        date_now_seven = self.database.get_time_rounded(date_now_seven)
        date_op1 = ''
        date_op2 = ''
        difference_dict = {}
        for years in range(1, date_now.year - 2006):
            for days in range(14):
                difference = 0
                for ten_minute_interval in range(29):
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
            return "++"
        elif(pres_difference > 0):
            return "+"
        elif(pres_difference > -5):
            return "-"
        else:
            return "--"