
import sys
import time
import threading

from selenium import webdriver
from selenium.webdriver.support import ui
from selenium.webdriver.chrome.options import Options

from lib.Sync import Sync
from lib.Frontend import Frontend


class Main:

    # global exception handling
    def my_except_hook(self, exctype, value, traceback):
        if exctype == AttributeError:
            Sync().import_data()
            self.run()
        else:
            sys.__excepthook__(exctype, value, traceback)

    def __init__(self):
        sys.excepthook = self.my_except_hook
        self.frontend = Frontend()

    def refresh_page(self):
        try:
            time.sleep(10)
            self.driver.get("localhost:8050")
            #driver.refresh()
        except:
            pass

    def open_chromium(self):
        # TODO only execute if driver is not defined yet
        # start chromium
        option = webdriver.ChromeOptions()
        # must be on top
        option.add_argument("--no-sandbox")
        option.add_argument("--start-maximized")
        option.add_argument("--disable-web-security")
        option.add_argument("--ignore-certificate-errors")
        option.add_argument("--kiosk")
        option.add_argument("--disable-password-manager-reauthentication")
        option.add_argument("--incognito")
        option.add_argument('--disable-infobars')
        option.add_argument("--remote-debugging-port=9222")
        # find binary with "which chromium" or "which chromium-browser" in bash
        option.binary_location = "/usr/bin/chromium-browser"
        # overcome problem python executed as root
        option.add_argument("--disable-dev-shm-usage")
        # option.add_argument('--headless')

        self.driver = webdriver.Chrome(options=option)
        threading.Thread(target=self.refresh_page).start()

    def run(self):
        #self.open_chromium()
        try:
            self.frontend.app.run_server(debug=False)
        except AttributeError as err:
            print(err)
            #try again after loading data
            self.frontend.sync.import_data()
            self.frontend.app.run_server(debug=False)

if __name__ == '__main__':
    main = Main()
    main.run()
