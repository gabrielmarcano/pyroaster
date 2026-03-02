from micropython import const
from drivers.max6675 import MAX6675
from drivers.ahtx0 import AHT20
from machine import I2C

_AHT_STATUS_BUSY = const(0x80)


class SensorController:
    def __init__(self, AHT_SDA, AHT_SCL, MAX_SCK, MAX_CS, MAX_SO):

        self.__i2c = I2C(0, sda=AHT_SDA, scl=AHT_SCL, freq=400000)

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
        self.__has_error = False
        self.__aht_measurement_triggered = False

        # Trigger first AHT20 measurement immediately
        try:
            self.__aht._trigger_measurement()
            self.__aht_measurement_triggered = True
        except Exception:
            pass

    def read_sensor_data(self):
        """
        Read sensor data individually and return as tuple.
        On failure, returns 0 for failed sensor (never stops).
        """
        error = False

        try:
            if not self.__aht_measurement_triggered:
                self.__aht._trigger_measurement()
                self.__aht_measurement_triggered = True
            else:
                # status property reads 6 bytes into _buf, including measurement data
                status = self.__aht.status
                if not (status & _AHT_STATUS_BUSY):
                    # Compute humidity from buffer BEFORE triggering next measurement
                    # (_trigger_measurement overwrites _buf[0:3])
                    buf = self.__aht._buf
                    raw = (buf[1] << 12) | (buf[2] << 4) | (buf[3] >> 4)
                    self.__humidity = int((raw * 100) / 0x100000)
                    # Trigger next measurement
                    self.__aht._trigger_measurement()
                # If busy, keep cached self.__humidity
        except Exception:
            self.__humidity = 0
            self.__aht_measurement_triggered = False
            error = True

        try:
            self.__temperature = int(self.__max.read())
        except Exception:
            self.__temperature = 0
            error = True

        self.__has_error = error

    def has_error(self):
        return self.__has_error

    def get_temperature(self):
        return self.__temperature

    def get_humidity(self):
        return self.__humidity

    def get_json(self):
        """
        Get sensor data in json format
        """
        return {"temperature": self.__temperature, "humidity": self.__humidity}
