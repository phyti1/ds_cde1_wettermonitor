#!/bin/bash

# wait for a few seconds to be sure python is fully loaded
sleep 5s

# run wettermonitor
python3 /home/user/wettermonitor/Main.py &

# wait a few seconds for the server to start
sleep 3s

# start chromium browser in fullscreen and display the application
chromium --kiosk http://localhost:8050/ &
