import time


class SHT31:
    """Minimal Sensirion SHT31 driver (single-shot, clock stretching disabled)."""

    def __init__(self, i2c, addr=0x44):
        self._i2c = i2c
        self._addr = addr
        # Presence check: raises (ENODEV / CRC) if the sensor isn't responding.
        self.measure()

    def _crc(self, data):
        crc = 0xFF
        for b in data:
            crc ^= b
            for _ in range(8):
                crc = ((crc << 1) ^ 0x31) & 0xFF if (crc & 0x80) else (crc << 1) & 0xFF
        return crc

    def measure(self):
        """Return (temperature_C, humidity_pct). Raises on I2C or CRC error."""
        self._i2c.writeto(self._addr, b"\x24\x00")  # high repeatability, no clock stretch
        time.sleep_ms(20)                            # high-rep conversion ~15ms
        d = self._i2c.readfrom(self._addr, 6)
        if self._crc(d[0:2]) != d[2] or self._crc(d[3:5]) != d[5]:
            raise Exception("SHT31 CRC error")
        t_raw = (d[0] << 8) | d[1]
        h_raw = (d[3] << 8) | d[4]
        temp = -45 + (175 * t_raw / 65535)
        hum = 100 * h_raw / 65535
        return temp, hum

    def heater(self, on):
        """Toggle the on-chip heater to burn off condensation / oils."""
        self._i2c.writeto(self._addr, b"\x30\x6d" if on else b"\x30\x66")

    def reset(self):
        self._i2c.writeto(self._addr, b"\x30\xa2")
        time.sleep_ms(2)
