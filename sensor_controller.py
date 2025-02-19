from max6675 import MAX6675
import dht


class SensorController:
    def __init__(self, DHT_PIN, MAX_SCK, MAX_CS, MAX_SO):
        self.__max = MAX6675(MAX_SCK, MAX_CS, MAX_SO)
        self.__dht = dht.DHT22(DHT_PIN)

        self.__temperature = 0
        self.__humidity = 0

    def read_sensor_data(self):
        """
        Read sensor data and return as a dictionary
        """
        try:
            self.__dht.measure()
            self.__temperature = int(self.__max.read())
            self.__humidity = int(self.__dht.humidity())

            return self.__temperature, self.__humidity
        except Exception as e:
            print(f"Failed to read sensor data:\n{e}")
            return None

    def get_temperature(self):
        return self.__temperature

    def get_humidity(self):
        return self.__humidity
