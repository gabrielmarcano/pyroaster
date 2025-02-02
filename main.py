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
from timer import TimerController

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

try:
    timer = TimerController(TIME_A, TIME_B, TIME_C)
except Exception as e:
    logger.error(f"Failed to initialize the timer: {e}")
    logger.info(f"Rebooting...")
    machine.reset()


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
    """
    Get time values from the timer and return as a dictionary
    """
    try:
        total, current = timer.read_time_values()

        return {"total": total, "current": current}
    except Exception as e:
        logger.error(f"Failed to read time data: {e}")
        return None


def get_motor_states():
    """
    Get the states of the motors and return as a dictionary
    """
    try:
        motor1_state = MOTOR1_PIN.value()
        motor2_state = MOTOR2_PIN.value()
        motor3_state = MOTOR3_PIN.value()

        return {"motor1": motor1_state, "motor2": motor2_state, "motor3": motor3_state}
    except Exception as e:
        logger.error(f"Failed to read motor states: {e}")
        return None


def add_time():
    timer._current_time += 1


def reduce_time():
    timer._current_time -= 1


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


# Attach interrupt handlers
TIME_ADDER.irq(trigger=machine.Pin.IRQ_RISING, handler=add_time)
TIME_REDUCER.irq(trigger=machine.Pin.IRQ_RISING, handler=reduce_time)

# Add routes to the server to also control the timer by client
server.add_route("/add_time", add_time, ["POST"])
server.add_route("/reduce_time", reduce_time, ["POST"])

# Start the update function in a new thread
_thread.start_new_thread(send_updates_to_server, (server,))

server.start()
