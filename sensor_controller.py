from max6675 import MAX6675
from dht import DHT22

import random


class SensorController:
    def __init__(self, DHT_PIN, MAX_SCK, MAX_CS, MAX_SO):
        self._max = MAX6675(MAX_SCK, MAX_CS, MAX_SO)
        self._dht = DHT22(DHT_PIN)

        self.temperature = 0
        self.humidity = 0

    def read_sensor_data(self):
        """
        Read sensor data and return as a dictionary
        """
        try:
            # self._dht.measure()
            # self.temperature = self._max.read()
            # self.humidity = self._dht.measure().humidity()
            self.temperature = random.randint(100, 180)
            self.humidity = random.randint(30, 60)

            return self.temperature, self.humidity
        except Exception as e:
            print(f"Failed to read sensor data:\n{e}")
            return None

    def get_temperature(self):
        return self.temperature

    def get_humidity(self):
        return self.humidity
