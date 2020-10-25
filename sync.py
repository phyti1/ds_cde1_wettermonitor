# import the library
import fhnw_ds_weatherstation_client as weather
import os

is_syncing = False

def import_data():
    global is_syncing
    if not is_syncing:
        is_syncing = True
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
        is_syncing = False

def import_latest_data():
    global is_syncing
    try:
        if not is_syncing:
            is_syncing = True
            # DB and CSV config
            config = weather.Config()

            # import latest data (delta between last data point in DB and current time)
            weather.import_latest_data(config, True)
            is_syncing = False

    except AttributeError as err:
        print(err)
        import_data()
    except:
        print("No Internet")
        return