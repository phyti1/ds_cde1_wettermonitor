# import the library
import fhnw_ds_weatherstation_client as weather
import os
import threading
import socket


class Sync:
    def __init__(self):
        """ (object) -> void
        Contructor of Snyc. Will initialize the weatherstation api and connect to the database. 
        """
        self.is_syncing = False
        # DB and CSV config
        self.config = weather.Config()

        # connect to DB
        weather.connect_db(self.config)

    def import_data_async(self, historic_data = False):
        """ (object, bool) -> void
        This function loads the latest or historing weather data. 
        The data capturing process runs in a seperate thread.
        """
        # only execute if no syncing is running
        if not self.is_syncing:
            self.is_syncing = True
            if historic_data:
                # load historic and latest data in new thread
                threading.Thread(target = self.import_historic_data, args = [True]).start()
            else:
                # load latest data in new thread
                threading.Thread(target = self.import_latest_data, args = [True]).start()

    def import_historic_data(self, periodic = False):
        """ (object, bool) -> void
        This function loads the latest or historing weather data. 
        The data capturing process runs in a seperate thread.
        """
        # check if the database is up to date
        if not weather.db_is_up_to_date(self.config):
            print('Syncing historic data...')

            # wipe the database for a fresh start
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
        """ (object, bool) -> void
        This function loads the latest weather data from the api.
        """
        try:
            # import latest data (delta between last data point in DB and current time)
            weather.import_latest_data(self.config, True, periodic)
        except AttributeError as err:
            print(err)
        except Exception as err:
            print("No Internet")

        # allow for new syncing to take place, loading historic and latest data will always end here
        self.is_syncing = False

    def has_internet_connection(self):
        """ (object) -> bool
        This function returns true if there is a connection to the internet.
        """
        try:
            # check if host is reachable
            host = socket.gethostbyname("1.1.1.1")

            # connect to the host -- tells us if the host is actually reachable
            socket_connection = socket.create_connection((host, 80), 2)
            socket_connection.close()
            return True
        except:
            pass
        return False       