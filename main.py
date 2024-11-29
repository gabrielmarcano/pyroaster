import machine
from machine_i2c_lcd import I2cLcd
from max6675 import MAX6675
from dht import DHT22
import network
import _thread
import time
import random
import utils

from http_server import HttpServer
from logger import SimpleLogger

logger = SimpleLogger()

MAX_SCK = machine.Pin(5, machine.Pin.OUT)
MAX_CS = machine.Pin(23, machine.Pin.OUT)
MAX_SO = machine.Pin(19, machine.Pin.IN)

DHT_PIN = machine.Pin(18)

I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16
LCD_SDA = machine.Pin(21)
LCD_SCL = machine.Pin(22)

MOTOR1_PIN = machine.Pin(25, machine.Pin.OUT)
MOTOR2_PIN = machine.Pin(26, machine.Pin.OUT)
MOTOR3_PIN = machine.Pin(27, machine.Pin.OUT)

BUZZER_PIN = machine.Pin(14, machine.Pin.OUT)

TIME_A = machine.Pin(36, machine.Pin.IN)
TIME_B = machine.Pin(34, machine.Pin.IN)
TIME_C = machine.Pin(35, machine.Pin.IN)
TIME_ADDER = machine.Pin(12, machine.Pin.IN)
TIME_REDUCER = machine.Pin(13, machine.Pin.IN)

server = HttpServer()
server.add_route("/events", server.handle_sse)
server.add_route("/reset", lambda r: machine.reset(), ["POST"])

try:
    max = MAX6675(MAX_SCK, MAX_CS, MAX_SO)
except Exception as e:
    logger.error(f"Failed to initialize the thermocouple with MAX6675: {e}")
    logger.info(f"Rebooting...")
    machine.reset()

try:
    dht = DHT22(DHT_PIN)
except Exception as e:
    logger.error(f"Failed to initialize the DHT22: {e}")
    logger.info(f"Rebooting...")
    machine.reset()

try:
    i2c = machine.SoftI2C(sda=LCD_SDA, scl=LCD_SCL, freq=400000)
    lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

    lcd.clear()
    lcd.putstr("IP:")  # By default, it will start at (0,0) if the display is empty
    lcd.move_to(0, 1)
    lcd.putstr(f"{network.WLAN(network.STA_IF).ipconfig("addr4")[0]}")
    time.sleep(5)
except Exception as e:
    logger.error(f"Failed to initialize LCD: {e}")
    logger.info(f"Rebooting...")
    machine.reset()

try:
    utils.play_melody(BUZZER_PIN)
except Exception as e:
    logger.error(f"Failed to play melody: {e}")


def read_sensor_data():
    """
    Read sensor data and return as a dictionary
    """
    try:
        # dht.measure()
        # temperature = max.read()
        # humidity = dht.measure().humidity()
        temperature = random.randint(10, 40)
        humidity = random.randint(30, 80)
        return {"temperature": temperature, "humidity": humidity}
    except Exception as e:
        logger.error(f"Failed to read sensor data: {e}")
        return None


def get_time_values():
    pass


def get_motor_states():
    pass


def add_time():
    pass


def reduce_time():
    pass


def refresh_lcd_data():
    lcd.clear()
    lcd.putstr("foo")
    lcd.move_to(0, 1)
    lcd.putstr("bar")


def send_updates_to_server(server: HttpServer):
    """
    Send sensor data to the server every second
    """
    while True:
        sensor_data = read_sensor_data()
        time_values = get_time_values()
        motor_states = get_motor_states()
        refresh_lcd_data()

        if sensor_data is not None:
            server.send_sse(sensor_data, "sensors")

        if time_values is not None:
            server.send_sse(time_values, "time")

        if motor_states is not None:
            server.send_sse(motor_states, "states")

        time.sleep(1)


# Start the update function in a new thread
_thread.start_new_thread(send_updates_to_server, (server,))

server.start()
