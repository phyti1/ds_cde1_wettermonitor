# import the library
import fhnw_ds_weatherstation_client as weather
import os


class Sync:
    def __init__(self):
        self.is_syncing = False
        # DB and CSV config
        self.config = weather.Config()
        # connect to DB
        weather.connect_db(self.config)

    def import_data(self):
        if not self.is_syncing:
            self.is_syncing = True

            # clean DB
            weather.clean_db(self.config)
            # import historic data
            weather.import_historic_data(self.config)
            # import latest data (delta between last data point in DB and current time)
            weather.import_latest_data(self.config, True)
            self.is_syncing = False

    def import_latest_data(self):
        try:
            if not self.is_syncing:
                self.is_syncing = True

                # import latest data (delta between last data point in DB and current time)
                weather.import_latest_data(self.config, True)
                self.is_syncing = False

        except AttributeError as err:
            print(err)
            self.import_data()
            self.is_syncing = False
        except:
            print("No Internet")
            self.is_syncing = False
            return