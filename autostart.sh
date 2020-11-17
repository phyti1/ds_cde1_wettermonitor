#!/bin/bash

#python3.8 app.py

#@xscreensaver -no-splash  # comment this line out to disable screensaver
#@xset s off
#@xset -dpms
#@xset s noblank
#chromium-browser --incognito --kiosk http://localhost:8050/
#chromium-browser http://www.google.com/ --start-fullscreen --no-sandbox
#wait for os to fully load
sleep 10s

python3 Main.py &

