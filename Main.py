
import sys
import time
import threading
import sys

from selenium import webdriver
from selenium.webdriver.support import ui
from selenium.webdriver.chrome.options import Options

from lib.Frontend import Frontend


class Main:

    def __init__(self):
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
        option.add_argument("disable-extensions")
        # find binary with "which chromium" or "which chromium-browser" in bash
        option.binary_location = "/snap/bin/chromium"
        # overcome problem python executed as root
        option.add_argument("--disable-dev-shm-usage")
        option.add_experimental_option("excludeSwitches", ['enable-automation'])
        # option.add_argument('--headless')

        self.driver = webdriver.Chrome("./assets/chromedriver", options=option)
        threading.Thread(target=self.refresh_page).start()

    def run(self):
        self.frontend.run()
        #TODO test
        if(sys.platform == "Ubuntu 20.04"):
            self.open_chromium()
        self.frontend.app.run_server(debug=False)

if __name__ == '__main__':
    main = Main()
    main.run()
