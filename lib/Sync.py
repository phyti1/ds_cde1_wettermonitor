# import the library
import fhnw_ds_weatherstation_client as weather
import os
import threading


class Sync:
    def __init__(self):
        self.is_syncing = False
        # DB and CSV config
        self.config = weather.Config()
        # connect to DB
        weather.connect_db(self.config)

    def import_data_async(self, historic_data = False):
        if not self.is_syncing:
            self.is_syncing = True
            if historic_data:
                threading.Thread(target = self.import_historic_data, args = [True]).start()
            else:
                threading.Thread(target = self.import_latest_data, args = [True]).start()

    def import_historic_data(self, periodic = False):
        if not weather.db_is_up_to_date(self.config):
            print('Syncing historic data...')
            weather.clean_db(self.config)
            # import historic data
            weather.import_historic_data(self.config)
        else:
            print('Historic data already synced.')
        # import latest data (delta between last data point in DB and current time)
        self.import_latest_data()
        if periodic:
            self.import_latest_data(True)

    def import_latest_data(self, periodic = False):
        try:
            # import latest data (delta between last data point in DB and current time)
            weather.import_latest_data(self.config, True, periodic)

        except AttributeError as err:
            print(err)
            # self.import_data()
            # self.is_syncing = False
        except Exception as err:
            print("No Internet")
        self.is_syncing = False