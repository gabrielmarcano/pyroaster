import time
import machine
from drivers.machine_i2c_lcd import I2cLcd

from utils import format_time


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
            self.__ip_override = ip_str.ljust(self.__I2C_NUM_COLS)
            self.__ip_override_until = time.ticks_add(time.ticks_ms(), 5000)
            self.__lcd.move_to(0, 1)
            self.__lcd.putstr(self.__ip_override)
            self.__last_line1 = self.__ip_override
        except Exception as e:
            print(f"Failed to write IP to LCD:\n{e}")

    def show_data(self, temperature, humidity, time_in_seconds):
        """
        Write sensor data and time to the LCD
        """
        try:
            line0 = f"T: {temperature}C H: {humidity}%".ljust(self.__I2C_NUM_COLS)

            if self.__ip_override is not None:
                if time.ticks_diff(self.__ip_override_until, time.ticks_ms()) > 0:
                    line1 = self.__ip_override
                else:
                    self.__ip_override = None
                    self.__last_line1 = None
                    line1 = format_time(time_in_seconds).ljust(self.__I2C_NUM_COLS)
            else:
                line1 = format_time(time_in_seconds).ljust(self.__I2C_NUM_COLS)

            if line0 != self.__last_line0:
                self.__lcd.move_to(0, 0)
                self.__lcd.putstr(line0)
                self.__last_line0 = line0

            if line1 != self.__last_line1:
                self.__lcd.move_to(0, 1)
                self.__lcd.putstr(line1)
                self.__last_line1 = line1
        except Exception as e:
            print(f"Failed to write to LCD:\n{e}")
            return None
