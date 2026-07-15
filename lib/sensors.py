from math import log
from drivers.max6675 import MAX6675
from drivers.sht31 import SHT31
from machine import I2C


def _friendly_error(e):
    s = str(e)
    if "ENODEV" in s:
        return "not connected (no device found on I2C bus)"
    if "thermocouple" in s.lower() or "loosely" in s.lower():
        return "not connected (no signal on data pin)"
    if "CRC" in s:
        return "CRC error (marginal bus or bad module)"
    return s


def _dew_point(temp_c, rh):
    """Magnus-formula dew point (C) from air temperature (C) and RH (%).

    In hot exhaust air, RH% alone reads misleadingly low; dew point is the
    temperature-independent measure of how much moisture the air actually carries.
    """
    if rh <= 0:
        return None
    a, b = 17.625, 243.04
    g = log(rh / 100.0) + (a * temp_c) / (b + temp_c)
    return (b * g) / (a - g)


class SensorController:
    def __init__(self, SHT_SDA, SHT_SCL, MAX_SCK, MAX_CS, MAX_SO,
                 enable_sht=True, enable_max=True):

        self.__sht_enabled = enable_sht
        self.__max_enabled = enable_max

        self.__max = None
        self.__max_error = None
        if enable_max:
            try:
                m = MAX6675(MAX_SCK, MAX_CS, MAX_SO)
                m.refresh()
                import time
                time.sleep_ms(m.MEASUREMENT_PERIOD_MS + 50)
                m.read()
                self.__max = m
            except Exception as e:
                self.__max_error = _friendly_error(e)

        # I2C(0) is only created when the humidity sensor is enabled, so a faulty
        # bus can be bypassed entirely in software.
        self.__i2c = None
        self.__sht = None
        self.__sht_error = None
        if enable_sht:
            try:
                self.__i2c = I2C(0, sda=SHT_SDA, scl=SHT_SCL, freq=100000)
                self.__sht = SHT31(self.__i2c)
            except Exception as e:
                self.__sht_error = _friendly_error(e)

        self.__temperature = 0    # roast temperature (MAX6675 thermocouple)
        self.__humidity = 0       # exhaust relative humidity % (SHT31)
        self.__exhaust_temp = 0   # exhaust air temperature C (SHT31)
        self.__dew_point = 0      # dew point C, derived from exhaust temp + RH
        self.__has_error = False
        self.__sht_live_error = False
        self.__max_live_error = False

    def report(self):
        """Per-device startup labels: (sht_label, sht_detail, max_label, max_detail).

        label is 'OK' | 'FAIL' | 'DISABLED'; detail carries the error string on FAIL.
        """
        def lbl(enabled, obj, err):
            if not enabled:
                return ("DISABLED", None)
            return ("OK", None) if obj is not None else ("FAIL", err)

        s_lbl, s_det = lbl(self.__sht_enabled, self.__sht, self.__sht_error)
        m_lbl, m_det = lbl(self.__max_enabled, self.__max, self.__max_error)
        return (s_lbl, s_det, m_lbl, m_det)

    def read_sensor_data(self):
        """
        Read sensor data individually. On failure, returns 0 for the failed
        sensor (never stops).
        """
        error = False

        if self.__sht is not None:
            try:
                t, rh = self.__sht.measure()
                self.__exhaust_temp = round(t, 1)
                self.__humidity = int(rh)
                dp = _dew_point(t, rh)
                self.__dew_point = round(dp, 1) if dp is not None else 0
                self.__sht_live_error = False
            except Exception:
                self.__humidity = 0
                self.__dew_point = 0
                self.__sht_live_error = True
                error = True

        if self.__max is not None:
            try:
                self.__temperature = int(self.__max.read())
                self.__max_live_error = False
            except Exception:
                self.__temperature = 0
                self.__max_live_error = True
                error = True

        self.__has_error = error

    def has_error(self):
        return self.__has_error

    def health(self):
        """Live per-sensor health as (sht_ok, max_ok).

        An enabled sensor is ok only if it initialized and its last read did not
        error. A disabled sensor counts as ok (intentional, not a fault). Unlike
        report() (a fixed boot-time snapshot), this recovers once a glitch clears.
        """
        sht_ok = (not self.__sht_enabled) or (self.__sht is not None and not self.__sht_live_error)
        max_ok = (not self.__max_enabled) or (self.__max is not None and not self.__max_live_error)
        return (sht_ok, max_ok)

    def get_temperature(self):
        return self.__temperature

    def get_humidity(self):
        return self.__humidity

    def get_json(self):
        """
        Get sensor data in json format. `temperature` is the roast temperature
        (thermocouple); `exhaust_temp`/`humidity`/`dew_point` come from the SHT31.
        """
        return {
            "temperature": self.__temperature,
            "humidity": self.__humidity,
            "exhaust_temp": self.__exhaust_temp,
            "dew_point": self.__dew_point,
        }
