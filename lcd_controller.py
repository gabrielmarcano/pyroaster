import machine
from machine_i2c_lcd import I2cLcd
import network
import time

from utils import format_time


class LcdController:
    def __init__(self, LCD_SDA, LCD_SCL):
        self.__I2C_ADDR = 0x27
        self.__I2C_NUM_ROWS = 2
        self.__I2C_NUM_COLS = 16

        self.__i2c = machine.SoftI2C(sda=LCD_SDA, scl=LCD_SCL, freq=400000)
        self.__lcd = I2cLcd(
            self.__i2c, self.__I2C_ADDR, self.__I2C_NUM_ROWS, self.__I2C_NUM_COLS
        )

    def clear(self):
        self.__lcd.clear()

    def show_ip(self):
        """
        Write the IP address to the LCD
        """
        try:
            self.__lcd.clear()
            self.__lcd.putstr(
                "IP:"
            )  # By default, it will start at (0,0) if the display is empty
            self.__lcd.move_to(0, 1)
            self.__lcd.putstr(f"{network.WLAN(network.STA_IF).ipconfig("addr4")[0]}")
            time.sleep(5)
        except Exception as e:
            print(f"Failed to write to LCD:\n{e}")
            return None

    def show_data(self, temperature, humidity, time_in_seconds):
        """
        Write sensor data and time to the LCD
        """
        try:
            self.__lcd.clear()
            self.__lcd.putstr(f"T: {temperature}°C H: {humidity}%")
            self.__lcd.move_to(0, 1)
            self.__lcd.putstr(format_time(time_in_seconds))
        except Exception as e:
            print(f"Failed to write to LCD:\n{e}")
            return None
