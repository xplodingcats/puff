import serial
import time
import logging

class SDS011:
    def __init__(self, port='/dev/ttyUSB0'):
        self.ser = serial.Serial()
        self.ser.port = port
        self.ser.baudrate = 9600
        self.ser.timeout = 2
        self.ser.open()
        self.last_read = time.time()
        logging.info("SDS011 initialized")

    def read_data(self):
        while time.time() - self.last_read < 5:
            time.sleep(0.1)
            
        self.last_read = time.time()
        data = []
        while len(data) < 10:
            byte = self.ser.read()
            if byte:
                data.append(byte)
        
        if self._validate_checksum(data):
            pm25 = (data[2][0] + data[3][0] * 256) / 10.0
            pm10 = (data[4][0] + data[5][0] * 256) / 10.0
            return pm25, pm10
        return None, None

    def _validate_checksum(self, data):
        if len(data) != 10:
            return False
        checksum = sum([b[0] for b in data[2:8]]) % 256
        return checksum == data[9][0]
