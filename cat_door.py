# библиотеки
from bluepy.btle import Scanner, DefaultDelegate
import logging
import time
import serial

import numpy

from http.server import BaseHTTPRequestHandler, HTTPServer
import datetime 
import json

import threading 

# настройки и параметры
httpPort = 8000 # порт веб сервера

# catLabelAddr = u'20:c3:8f:d1:57:ba'
catLabelAddr = [u'20:c3:8f:d1:57:ba', u'72:64:6c:28:ff:ff']
catRSSImin = -60 # предельное значение уровня сигнала метки для срабатывания двери
catLabelRSSI = -200 # переменная для текущего значения уровня сигнала метки
catLabelTxPower = 0

doorWayCatStatus = "none" 	# inside, outside
doorWayCatStatusTimeLast = time.time() # время срабатывания датчиков

usb = serial.Serial("/dev/ttyUSB0", 9600, timeout=2)

doorTimeKeepOpen = 15 # время ожидания до закрытия двери
doorTimeCatLastInRange = time.time() # время, когда кот последний раз был рядом
catLabelRSSITimeLast = time.time() # время, когда был последний раз получен сигнал от кота
doorStatus = "closed"
doorOperateTimeLast = time.time() # время срабатывания двери
subDoorTimer4LoggingClose = time.time() # переменная для отображения времений до закрытия двери раз в секунду, а не по частоте цикла

logging.basicConfig(
    level=logging.INFO,
#    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("cat_door.log"),
        logging.StreamHandler()
    ]
)

# классы, подпрограммы
# общие
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)


def door(command):
	global doorStatus, doorTimeCatLastInRange, subDoorTimer4LoggingClose, doorOperateTimeLast
	if command == "open":
		if doorStatus == "closed":
			# открываем
			logging.info("открываем дверь")
			doorStatus = "open"
			usb.write('door open\n'.encode())
			doorOperateTimeLast = time.time()
		else:
			if int(time.time() - subDoorTimer4LoggingClose) >= 1:
				logging.debug("дверь закроется через %s секунд" % (int(doorTimeKeepOpen - (time.time() - doorTimeCatLastInRange))))			# дверь открываем
				subDoorTimer4LoggingClose = time.time()
		
	else:
		if doorStatus == "open":
			logging.info("закрываем дверь")
			doorStatus = "closed"
			usb.write('door close\n'.encode())
			doorOperateTimeLast = time.time()
#		else:
	return

def doorController():
	global catLabelRSSI, catLabelRSSITimeLast, catLabelRSSI, doorTimeCatLastInRange, doorTimeKeepOpen, catLabelTxPower, doorStatus
	scanner = Scanner().withDelegate(ScanDelegate()) # подключение ble сканера
	door("open")

#try:
	while True:
		# проверка наличия метки поблизости
#		devices = scanner.scan(0.35)
		devices = scanner.scan(2, passive=True)
		for dev in devices:
			# if dev.addr == catLabelAddr:
			if dev.addr in catLabelAddr:
				catLabelRSSI = dev.rssi
				catLabelRSSITimeLast = time.time()
				if catLabelRSSI > catRSSImin: # если кот рядом, то обновляем счетчик удержания двери открытой
					doorTimeCatLastInRange = time.time()
#				logging.debug("Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
				for (adtype, desc, value) in dev.getScanData():
					if desc == "Tx Power":
						catLabelTxPower = value
#						logging.debug("  %s = %s" % (desc, value))
				# logging.info("RSSI = %s dB    TxPower = %s" % (dev.rssi, catLabelTxPower))
				logging.info("RSSI = %s dB" % (dev.rssi))

		if time.time() - doorTimeCatLastInRange < doorTimeKeepOpen:
			# doorTimeCatLastInRange = time.time()	# кот рядом, обновляем счетчик удержания двери открытой
			
			door("open")
		else:
			# дверь закрываем
			door("close")

#except KeyboardInterrupt:
#	pass
		
# http
htmlCatStatusHome = '''<div class="alert alert-success text-center" role="alert"><h2>КОТ ДОМА</h2></div>'''
htmlCatStatusStreet = '''<div class="alert alert-danger text-center" role="alert"><h2>КОТ ГУЛЯЕТ</h2></div>'''
htmlDoorStatusOpen = '''открыта'''
htmlDoorStatusClosed = '''закрыта'''
htmlTemplate = '''<!DOCTYPE html> <html>
<head><meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no"><meta charset = 'utf-8'>
<link href="https://fonts.googleapis.com/css?family=Open+Sans:300,400,600" rel="stylesheet">
<title>модуль "КОТОДВЕРЬ"</title>
<style>html { font-family: 'Open Sans', sans-serif; display: block; margin: 0px auto; text-align: center;color: #333333;}
body{margin-top: 50px;}
h1 {margin: 50px auto 30px;}
.side-by-side{display: inline-block;vertical-align: middle;position: relative;}
.humidity-icon{background-color: #3498db;width: 30px;height: 30px;border-radius: 50%%;line-height: 36px;}
.humidity-text{font-weight: 600;padding-left: 15px;font-size: 19px;width: 160px;text-align: left;}
.humidity{font-weight: 300;font-size: 60px;color: #3498db;}
.temperature-icon{background-color: #f39c12;width: 30px;height: 30px;border-radius: 50%%;line-height: 40px;}
.temperature-text{font-weight: 600;padding-left: 15px;font-size: 19px;width: 160px;text-align: left;}
.temperature{font-weight: 300;font-size: 60px;color: #f39c12;}
.superscript{font-size: 17px;font-weight: 600;position: absolute;right: -20px;top: 15px;}
.data{padding: 10px;}
</style>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css" integrity="sha384-TX8t27EcRE3e/ihU7zmQxVncDAy5uIKz4rEkgIXeMed4M0jlfIDPvg6uqKI2xXr2" crossorigin="anonymous">
<meta http-equiv="refresh" content="60;URL=">
</head>
<body>

<div class="container-sm">
	<h1 class="text-center">Где наш Буба</h1>
	%s
	
	<dl class="row">
		<dt class="col-sm-6">Дверь сейчас:</dt>
		<dd class="col-sm-6">%s
			<footer class="blockquote-footer">%s</footer>
		</dd>

		<dt class="col-sm-6">Уровень сигнала:</dt>
		<dd class="col-sm-6">%s dB
			<footer class="blockquote-footer">%s</footer>
		</dd>

		<dt class="col-sm-6">Датчик:</dt>
		<dd class="col-sm-6">%s
			<footer class="blockquote-footer">%s</footer>
		</dd>
	</dl>

	<p class="text-center"><small>%s</small></p>
</div>
</body>
</html>''' 

def timestamp2date(timestamp):
	value = datetime.datetime.fromtimestamp(timestamp)
	return value.strftime('%Y-%m-%d %H:%M:%S')
	

class ServerHandler(BaseHTTPRequestHandler):
	global doorStatus, catLabelRSSITimeLast, doorOperateTimeLast, doorWayCatStatus

	def log_message(self, format, *args):
		return
		
	def do_GET(self):
		if (self.path == "/json" or self.path == "/cat/json"):
			self.send_response(200)
			self.send_header('Content-type','application/json')
			self.end_headers()

			if (doorWayCatStatus == "none"):
				if ((catLabelRSSITimeLast - doorOperateTimeLast) > 3*60) and ((catLabelRSSITimeLast - doorOperateTimeLast) > 0):
					catStatus = "home"
				else:
					catStatus = "street"
			elif (doorWayCatStatus == "inside"):
					catStatus = "home"
			elif (doorWayCatStatus == "outside"):
					catStatus = "street"
			
			json_data = {'catStatus':catStatus, 'doorOperateTimeLast':timestamp2date(doorOperateTimeLast),'catLabelRSSI':catLabelRSSI,'catLabelRSSITimeLast':timestamp2date(catLabelRSSITimeLast),'doorWayCatStatus':doorWayCatStatus,'doorWayCatStatusTimeLast':timestamp2date(doorWayCatStatusTimeLast),'timestampOfCreation':timestamp2date(time.time())}
			json_dumps = json.dumps(json_data)
			self.wfile.write(json_dumps.encode('utf-8'))
		
		else:
			self.send_response(200)
			self.send_header('Content-type','text/html')
			self.end_headers()
			
			htmlDoorStatus = (htmlDoorStatusOpen if doorStatus == "open" else htmlDoorStatusClosed)
			
			if (doorWayCatStatus == "none"):
				if ((catLabelRSSITimeLast - doorOperateTimeLast) > 3*60) and ((catLabelRSSITimeLast - doorOperateTimeLast) > 0):
					htmlCatStatus = htmlCatStatusHome
				else:
					htmlCatStatus = htmlCatStatusStreet
			elif (doorWayCatStatus == "inside"):
				htmlCatStatus = htmlCatStatusHome
			elif (doorWayCatStatus == "outside"):
				htmlCatStatus = htmlCatStatusStreet
			
			html = htmlTemplate % (htmlCatStatus,htmlDoorStatus,timestamp2date(doorOperateTimeLast),catLabelRSSI,timestamp2date(catLabelRSSITimeLast),doorWayCatStatus,timestamp2date(doorWayCatStatusTimeLast),timestamp2date(time.time()))
			self.wfile.write(html.encode('utf-8'))
			
def server_thread(port):
	server_address = ('', port)
	httpd = HTTPServer(server_address, ServerHandler)
	httpd.serve_forever()

def doorWayController():
	global doorWayCatStatus, doorWayCatStatusTimeLast
	logging.info("DoorWay thread start")
	while True:
		serialRead = usb.read_until().decode().rstrip("\n")
		if (len(serialRead) > 0):
			logging.debug("serial: %s (%s)" % (serialRead, len(serialRead)))
		
		if (len(serialRead) > 7):
			if (serialRead[0:8] == "door: in"):
				doorWayCatStatus = "inside"
				logging.info("Буба вошел домой")
				doorWayCatStatusTimeLast = time.time()
			elif (serialRead[0:9] == "door: out"):
				doorWayCatStatus = "outside"
				logging.info("Буба вышел на улицу")
				doorWayCatStatusTimeLast = time.time()
	
# основной блок
def main():
	door_thread = threading.Thread(target=doorController)
	door_thread.start()

	doorway_thread = threading.Thread(target=doorWayController)
	doorway_thread.start()

	logging.info("Starting server at port %d" % httpPort)
	webserver_thread = threading.Thread(target=server_thread(httpPort))
	webserver_thread.start()

	try:
		while 1:
			time.sleep(.1)

	except KeyboardInterrupt:
		door_thread.join()
		doorway_thread.join()
		webserver_thread.join()

if __name__ == '__main__':
	main()
