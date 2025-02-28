from drivers.max6675 import MAX6675
import dht


class SensorController:
    def __init__(self, DHT_PIN, MAX_SCK, MAX_CS, MAX_SO):
        self.__max = MAX6675(MAX_SCK, MAX_CS, MAX_SO)
        self.__dht = dht.DHT22(DHT_PIN)

        self.__temperature = 0
        self.__humidity = 0

    def read_sensor_data(self):
        """
        Read sensor data individually and return as tuple
        """
        try:
            self.__dht.measure()
            self.__humidity = int(self.__dht.humidity())
        except Exception as e:
            print(f"Failed to read DHT22 data:\n{e}")

        try:
            self.__temperature = int(self.__max.read())
        except Exception as e:
            print(f"Failed to read MAX6675 data:\n{e}")

        return self.__temperature, self.__humidity

    def get_temperature(self):
        return self.__temperature

    def get_humidity(self):
        return self.__humidity

    def get_json(self):
        """
        Get sensor data in json format
        """
        self.read_sensor_data()
        return {"temperature": self.__temperature, "humidity": self.__humidity}
