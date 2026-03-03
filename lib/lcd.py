import time
import machine
from drivers.machine_i2c_lcd import I2cLcd

from utils import format_time


def _pad(s, width):
    """ljust replacement for MicroPython (str.ljust is not available)."""
    n = width - len(s)
    return s + " " * n if n > 0 else s


class LcdController:
    def __init__(self, LCD_SDA, LCD_SCL):
        self.__I2C_ADDR = 0x27
        self.__I2C_NUM_ROWS = 2
        self.__I2C_NUM_COLS = 16

        self.__i2c = machine.I2C(1, sda=LCD_SDA, scl=LCD_SCL, freq=400000)
        self.__lcd = I2cLcd(
            self.__i2c, self.__I2C_ADDR, self.__I2C_NUM_ROWS, self.__I2C_NUM_COLS
        )

        self.__last_line0 = None
        self.__last_line1 = None
        self.__ip_override = None
        self.__ip_override_until = 0
        self.__error_logged = False

    def clear(self):
        self.__lcd.clear()
        self.__last_line0 = None
        self.__last_line1 = None
        self.__ip_override = None

    def show_ip(self, ip_str):
        """
        Show IP on 2nd row for 5 seconds, then resume normal display.
        Non-blocking — the override expires automatically in show_data().
        """
        try:
            self.__ip_override = _pad(ip_str, self.__I2C_NUM_COLS)
            self.__ip_override_until = time.ticks_add(time.ticks_ms(), 5000)
            self.__lcd.move_to(0, 1)
            self.__lcd.putstr(self.__ip_override)
            self.__last_line1 = self.__ip_override
        except Exception as e:
            if not self.__error_logged:
                print(f"LCD error: {e}")
                self.__error_logged = True

    def show_data(self, temperature, humidity, time_in_seconds):
        """
        Write sensor data and time to the LCD
        """
        try:
            line0 = _pad(f"T: {temperature}C H: {humidity}%", self.__I2C_NUM_COLS)

            if self.__ip_override is not None:
                if time.ticks_diff(self.__ip_override_until, time.ticks_ms()) > 0:
                    line1 = self.__ip_override
                else:
                    self.__ip_override = None
                    self.__last_line1 = None
                    line1 = _pad(format_time(time_in_seconds), self.__I2C_NUM_COLS)
            else:
                line1 = _pad(format_time(time_in_seconds), self.__I2C_NUM_COLS)

            if line0 != self.__last_line0:
                self.__lcd.move_to(0, 0)
                self.__lcd.putstr(line0)
                self.__last_line0 = line0

            if line1 != self.__last_line1:
                self.__lcd.move_to(0, 1)
                self.__lcd.putstr(line1)
                self.__last_line1 = line1

            if self.__error_logged:
                print("LCD reconnected")
                self.__error_logged = False
        except Exception as e:
            if not self.__error_logged:
                print(f"LCD error: {e}")
                self.__error_logged = True
