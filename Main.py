
import sys
import time
import threading
import sys
import dash

from selenium import webdriver
from selenium.webdriver.support import ui
from selenium.webdriver.chrome.options import Options

from lib.Frontend import Frontend


class Main:

    def __init__(self):
        # initialize Dash
        app = dash.Dash(__name__, title = 'Wettermonitor')
        # instanciate Frontend
        self.frontend = Frontend(app)

    def run(self):
        # load user interface
        self.frontend.run()
        # start Dash server
        self.frontend.app.run_server(debug=False)

if __name__ == '__main__':
    # instanciate Main class
    main = Main()
    # Applikation starten
    main.run()
