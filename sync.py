# import the library
import data_import as weather
import os

# DB and CSV config
config = weather.Config()
# define CSV path (you need to define this based on your environment)
config.historic_data_folder='.'+os.sep+'data'
# set batch size for DB inserts (decrease for raspberry pi)
config.historic_data_chunksize=10000
# define DB host
config.db_host='localhost'

# connect to DB
weather.connect_db(config)
# clean DB
weather.clean_db(config)
# import historic data
weather.import_historic_data(config)
# import latest data (delta between last data point in DB and current time)
weather.import_latest_data(config, True)