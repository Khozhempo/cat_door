# cat_door
Cat door control.

!!! PERMANENTLY MOVED TO NEW ADDRESS: http://git.khoz.ru/Khoz/cat_door.git

Program part of project for cat. 
Details in my article on reddit.com (https://www.reddit.com/r/smarthome/comments/l8mj15/catdoor_project/).

There are two components: 
1. cat_door.py 
Server. Python script runs on raspberry pi 3. Monitoring BLE signal level and do commands to close or open the cat door. Also report on website and json (to control status in telegram bot).

2. cad_door_arduino.ino
Mechanism. Runs on arduino with servo and sensors. Connected with raspberry by USB, but have separate power supply.
