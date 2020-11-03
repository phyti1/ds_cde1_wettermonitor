#python3.8 app.py

#@xscreensaver -no-splash  # comment this line out to disable screensaver
#@xset s off
#@xset -dpms
#@xset s noblank
#chromium-browser --incognito --kiosk http://localhost:8050/

#wait for os to fully load
sleep 10s

python3 /home/pi/wettermonitor/app.py &

