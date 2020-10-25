# import the library
import fhnw_ds_weatherstation_client as weather
import os


def import_data():
    # DB and CSV config
    config = weather.Config()

    # connect to DB
    weather.connect_db(config)
    # clean DB
    weather.clean_db(config)
    # import historic data
    weather.import_historic_data(config)
    # import latest data (delta between last data point in DB and current time)
    weather.import_latest_data(config, True)

def import_latest_data(a):
    # DB and CSV config
    config = weather.Config()

    # import latest data (delta between last data point in DB and current time)
    weather.import_latest_data(config, True)