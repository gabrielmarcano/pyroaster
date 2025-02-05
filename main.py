import json
import machine

# from machine_i2c_lcd import I2cLcd
# import network
import _thread
import time

# import utils

from http_server import HttpServer
from logger import SimpleLogger
from timer_controller import TimerController
from motor_controller import MotorController
from sensor_controller import SensorController
from controller import Controller

# Pins

MAX_SCK = machine.Pin(5, machine.Pin.OUT)
MAX_CS = machine.Pin(23, machine.Pin.OUT)
MAX_SO = machine.Pin(19, machine.Pin.IN)

DHT_PIN = machine.Pin(18)

# I2C_ADDR = 0x27
# I2C_NUM_ROWS = 2
# I2C_NUM_COLS = 16
# LCD_SDA = machine.Pin(21)
# LCD_SCL = machine.Pin(22)

MOTOR1_PIN = machine.Pin(25, machine.Pin.OUT, value=0)
MOTOR2_PIN = machine.Pin(26, machine.Pin.OUT, value=0)
MOTOR3_PIN = machine.Pin(27, machine.Pin.OUT, value=0)

BUZZER_PIN = machine.Pin(14, machine.Pin.OUT)

TIME_A = machine.Pin(36, machine.Pin.IN)
TIME_B = machine.Pin(34, machine.Pin.IN)
TIME_C = machine.Pin(35, machine.Pin.IN)
TIME_ADDER = machine.Pin(12, machine.Pin.IN)
TIME_REDUCER = machine.Pin(13, machine.Pin.IN)

logger = SimpleLogger()

try:
    server = HttpServer()
    server.add_route("/events", server.handle_sse)
    server.add_route("/reset", lambda r: machine.reset(), ["POST"])
except Exception as e:
    logger.error(f"Failed to initialize the server:\n{e}\n")
    logger.info(f"Rebooting...")
    machine.reset()

# try:
#     i2c = machine.SoftI2C(sda=LCD_SDA, scl=LCD_SCL, freq=400000)
#     lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

#     lcd.clear()
#     lcd.putstr("IP:")  # By default, it will start at (0,0) if the display is empty
#     lcd.move_to(0, 1)
#     lcd.putstr(f"{network.WLAN(network.STA_IF).ipconfig("addr4")[0]}")
#     time.sleep(5)
# except Exception as e:
#     print(f"Failed to initialize LCD:\n{e}\n")
#     print(f"Rebooting...")
#     machine.reset()

# try:
#     utils.play_melody(BUZZER_PIN)
# except Exception as e:
#     print(f"Failed to play melody:\n{e}\n")

try:
    timerc = TimerController()
except Exception as e:
    logger.error(f"Failed to initialize the timer controller:\n{e}\n")
    logger.info(f"Rebooting...")
    machine.reset()

try:
    motorc = MotorController(MOTOR1_PIN, MOTOR2_PIN, MOTOR3_PIN)
except Exception as e:
    logger.error(f"Failed to initialize motor controller:\n{e}\n")
    logger.info(f"Rebooting...")
    machine.reset()

try:
    sensorc = SensorController(DHT_PIN, MAX_SCK, MAX_CS, MAX_SO)
except Exception as e:
    logger.error(f"Failed to initialize the sensor controller:\n{e}\n")
    logger.info(f"Rebooting...")
    machine.reset()

try:
    controller = Controller(sensorc, timerc, motorc)
except Exception as e:
    logger.error(f"Failed to initialize the logic controller:\n{e}\n")
    logger.info(f"Rebooting...")
    machine.reset()


def handle_config(request):
    if "GET" in request:
        response = json.dumps(controller.get_config())
        server.send_response(response, 200, "application/json")

    if "PATCH" in request:
        data = server.parse_json_body(request)
        if data is not None:
            response = json.dumps(
                controller.set_config(
                    data.get("mode"), data.get("starting_temperature"), data.get("time")
                )
            )
            return server.send_response(response, 200, "application/json")

        server.send_response("error", http_code=400)


def handle_time_change(request):
    data = server.parse_json_body(request)
    if data is not None:
        action = data.get("action")
        if action == "add":
            timerc.increase_current_time(None)
        if action == "reduce":
            timerc.decrease_current_time(None)

        time_values = timerc.get_time_values()
        time_json = {"total_time": time_values[0], "current_time": time_values[1]}
        response = json.dumps(time_json)
        return server.send_response(response, 200, "application/json")

    return server.send_response("error", http_code=400)


def handle_controller(request):
    data = server.parse_json_body(request)
    if data is not None:
        action = data.get("action")
        if action == "activate":
            controller.activate()
            return server.send_response("Controller activated")
        if action == "deactivate":
            controller.deactivate()
            return server.send_response("Controller deactivated")
        if action == "stop":
            controller.stop()
            return server.send_response("Controller stopped")

    return server.send_response("error", http_code=400)


# def refresh_lcd_data():
#     lcd.clear()
#     lcd.putstr("foo")
#     lcd.move_to(0, 1)
#     lcd.putstr("bar")


def send_updates_to_server(server: HttpServer):
    """
    Send sensor data to the server every second
    """
    while True:
        sensor_data = sensorc.read_sensor_data()
        time_values = timerc.get_time_values()
        motor_states = motorc.read_motor_states()
        # refresh_lcd_data()
        controller.run()

        sensor_json = {"temperature": sensor_data[0], "humidity": sensor_data[1]}
        time_json = {"total_time": time_values[0], "current_time": time_values[1]}
        motor_json = {
            "motor_a": motor_states[0],
            "motor_b": motor_states[1],
            "motor_c": motor_states[2],
        }

        if sensor_data is not None:
            server.send_sse(sensor_json, "sensors")

        if time_values is not None:
            server.send_sse(time_json, "time")

        if motor_states is not None:
            server.send_sse(motor_json, "states")

        controller_status = {
            "active": controller.__is_active,
            "mode": controller.__mode,
            "time": controller.__time,
            "starting_temperature": controller.__starting_temperature,
        }
        server.send_sse(controller_status, "controller")

        time.sleep(1)


# Attach interrupt handlers
TIME_ADDER.irq(
    trigger=machine.Pin.IRQ_RISING, handler=lambda p: timerc.increase_current_time(p)
)
TIME_REDUCER.irq(
    trigger=machine.Pin.IRQ_RISING, handler=lambda p: timerc.decrease_current_time(p)
)

# Add routes to the server
server.add_route("/time", handle_time_change, ["POST"])
server.add_route("/config", handle_config, ["GET", "PATCH"])
server.add_route("/controller", handle_controller, ["POST"])


# Start the update function in a new thread
_thread.start_new_thread(send_updates_to_server, (server,))

server.start()
