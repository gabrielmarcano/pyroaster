from drivers.max6675 import MAX6675
from drivers.ahtx0 import AHT20
from machine import SoftI2C


class SensorController:
    def __init__(self, AHT_SDA, AHT_SCL, MAX_SCK, MAX_CS, MAX_SO):

        self.__i2c = SoftI2C(sda=AHT_SDA, scl=AHT_SCL, freq=400000)

        try:
            self.__max = MAX6675(MAX_SCK, MAX_CS, MAX_SO)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize MAX6675: {e}")

        try:
            self.__aht = AHT20(self.__i2c)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AHT20: {e}")

        self.__temperature = 0
        self.__humidity = 0

    def read_sensor_data(self):
        """
        Read sensor data individually and return as tuple
        """

        self.__humidity = int(self.__aht.relative_humidity)
        self.__temperature = int(self.__max.read())

    def get_temperature(self):
        return self.__temperature

    def get_humidity(self):
        return self.__humidity

    def get_json(self):
        """
        Get sensor data in json format
        """
        return {"temperature": self.__temperature, "humidity": self.__humidity}
