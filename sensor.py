import serial
import time
import logging

class SDS011:
    def __init__(self, port='/dev/ttyUSB0'):
        self.ser = serial.Serial(port, 9600, timeout=2)
        logging.info("SDS011 initialized")

    def read_data(self):
        while True:
            data = self.ser.read(10)
            if len(data) == 10 and data[0] == 0xAA and data[1] == 0xC0:
                pm25 = (data[2] + data[3]*256)/10.0
                pm10 = (data[4] + data[5]*256)/10.0
                return pm25, pm10
            time.sleep(1)
