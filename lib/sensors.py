from micropython import const
from drivers.max6675 import MAX6675
from drivers.ahtx0 import AHT20
from machine import I2C

_AHT_STATUS_BUSY = const(0x80)


def _friendly_error(e):
    s = str(e)
    if "ENODEV" in s:
        return "not connected (no device found on I2C bus)"
    if "thermocouple" in s.lower() or "loosely" in s.lower():
        return "not connected (no signal on data pin)"
    return s


class SensorController:
    def __init__(self, AHT_SDA, AHT_SCL, MAX_SCK, MAX_CS, MAX_SO,
                 enable_aht=True, enable_max=True):

        self.__aht_enabled = enable_aht
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

        # I2C(0) is only created when the AHT is enabled, so a faulty AHT bus
        # (e.g. SDA stuck low) can be bypassed entirely in software.
        self.__i2c = None
        self.__aht = None
        self.__aht_error = None
        if enable_aht:
            try:
                self.__i2c = I2C(0, sda=AHT_SDA, scl=AHT_SCL, freq=400000)
                self.__aht = AHT20(self.__i2c)
            except Exception as e:
                self.__aht_error = _friendly_error(e)

        self.__temperature = 0
        self.__humidity = 0
        self.__has_error = False
        self.__aht_live_error = False
        self.__max_live_error = False
        self.__aht_measurement_triggered = False

        # Trigger first AHT20 measurement immediately
        if self.__aht is not None:
            try:
                self.__aht._trigger_measurement()
                self.__aht_measurement_triggered = True
            except Exception:
                pass

    def report(self):
        """Per-device startup labels: (aht_label, aht_detail, max_label, max_detail).

        label is 'OK' | 'FAIL' | 'DISABLED'; detail carries the error string on FAIL.
        """
        def lbl(enabled, obj, err):
            if not enabled:
                return ("DISABLED", None)
            return ("OK", None) if obj is not None else ("FAIL", err)

        a_lbl, a_det = lbl(self.__aht_enabled, self.__aht, self.__aht_error)
        m_lbl, m_det = lbl(self.__max_enabled, self.__max, self.__max_error)
        return (a_lbl, a_det, m_lbl, m_det)

    def read_sensor_data(self):
        """
        Read sensor data individually and return as tuple.
        On failure, returns 0 for failed sensor (never stops).
        """
        error = False

        if self.__aht is not None:
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
                self.__aht_live_error = False
            except Exception:
                self.__humidity = 0
                self.__aht_measurement_triggered = False
                self.__aht_live_error = True
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
        """Live per-sensor health as (aht_ok, max_ok).

        Reflects the *current* runtime state: an enabled sensor is ok only if it
        initialized and its last read did not error. A disabled sensor counts as
        ok (intentional, not a fault). Unlike report() (a fixed boot-time
        snapshot), this recovers once a transient glitch clears.
        """
        aht_ok = (not self.__aht_enabled) or (self.__aht is not None and not self.__aht_live_error)
        max_ok = (not self.__max_enabled) or (self.__max is not None and not self.__max_live_error)
        return (aht_ok, max_ok)

    def get_temperature(self):
        return self.__temperature

    def get_humidity(self):
        return self.__humidity

    def get_json(self):
        """
        Get sensor data in json format
        """
        return {"temperature": self.__temperature, "humidity": self.__humidity}
