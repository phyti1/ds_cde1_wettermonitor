from datetime import datetime, timedelta
import numpy as np
import pandas as pd

class Prediciton:
    def __init__(self, database, sync):
        self.database = database
        self.sync = sync
        self.is_repeating = False

    def calculate_best_match(self):
        historic_match_data = self.database.get_data_comparison()
        current_match_data = self.database.get_last_five_hours()
        if current_match_data is None and self.is_repeating == False:
            self.is_repeating = True
            # sync not ready yet
            self.sync.import_latest_data()
            return self.calculate_best_match()
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
        last_hours_data = self.database.get_last_five_hours()
        pressure_data = last_hours_data['barometric_pressure_qfe']
        pressure_values = pressure_data.to_numpy()
        #remove nans
        pressure_values_nonan = pressure_values[np.logical_not(np.isnan(pressure_values))] 
        first_pressure = pressure_values_nonan[0]

        last_pressure = pressure_values_nonan[len(pressure_values_nonan) - 1]

        pres_difference = last_pressure - first_pressure
        if(pres_difference > 5):
            return "++"
        elif(pres_difference > 0):
            return "+"
        elif(pres_difference > -5):
            return "-"
        else:
            return "--"