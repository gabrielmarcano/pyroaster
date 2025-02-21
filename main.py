import json
import machine

import time

from microdot import Microdot
from microdot.sse import with_sse
import asyncio

from lib.lcd import LcdController
from lib.timer import TimerController
from lib.motors import MotorController
from lib.sensors import SensorController
from controller import Controller

from logger import SimpleLogger

# Pins

MAX_SCK = machine.Pin(5, machine.Pin.OUT)
MAX_CS = machine.Pin(23, machine.Pin.OUT)
MAX_SO = machine.Pin(19, machine.Pin.IN)

DHT_PIN = machine.Pin(18)

LCD_SDA = machine.Pin(21)
LCD_SCL = machine.Pin(22)

MOTOR1_PIN = machine.Pin(25, machine.Pin.OUT, value=0)
MOTOR2_PIN = machine.Pin(26, machine.Pin.OUT, value=0)
MOTOR3_PIN = machine.Pin(27, machine.Pin.OUT, value=0)

# BUZZER_PIN = machine.Pin(14, machine.Pin.OUT)

logger = SimpleLogger()

try:
    lcd = LcdController(LCD_SDA, LCD_SCL)
    lcd.show_ip()
except Exception as e:
    logger.error(f"Failed to initialize LCD:\n{e}\n")
    logger.info(f"Rebooting...")
    machine.reset()

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


app = Microdot()


# Add routes to the server
@app.route("/time", methods=["POST"])
async def change_time(request):
    data = request.json
    action = data.get("action")
    if action == "add":
        timerc.increase_current_time(None)
    if action == "reduce":
        timerc.decrease_current_time(None)
    if action == "change":
        time = data.get("time")
        timerc.set_timer_values(time)

    time_values = (
        timerc.get_time_values()
    )  # TODO: change get_time_values to return json

    return {"total_time": time_values[0], "current_time": time_values[1]}


@app.route("/controller_config", methods=["GET", "PATCH"])
async def handle_controller_config(request):
    if request.method == "GET":
        return controller.get_config()
    elif request.method == "PATCH":
        data = request.json
        if data is not None:
            return controller.set_config(
                data.get("starting_temperature"), data.get("time")
            )


@app.route("/controller", methods=["POST"])
async def handle_controller(request):
    data = request.json
    if data is not None:
        action = data.get("action")

        if action == "activate":
            controller.activate()
        if action == "deactivate":
            controller.deactivate()
        if action == "stop":
            controller.stop()

        return controller.get_config()


@app.route("/motors", methods=["POST"])
async def handle_motor_change(request):
    data = request.json
    if data is not None:
        motor_a = data.get("motor_a")
        if motor_a is not None:
            motorc.start_motor_a() if motor_a else motorc.stop_motor_a()

        motor_b = data.get("motor_b")
        if motor_b is not None:
            motorc.start_motor_b() if motor_b else motorc.stop_motor_b()

        motor_c = data.get("motor_c")
        if motor_c is not None:
            motorc.start_motor_c() if motor_c else motorc.stop_motor_c()

        motor_states = (
            motorc.read_motor_states()
        )  # TODO: change get_time_values to return json

        return {
            "motor_a": motor_states[0],
            "motor_b": motor_states[1],
            "motor_c": motor_states[2],
        }


@app.route("/config/<name>", methods=["GET", "POST", "DELETE"])
async def handle_saved_config(request, name):
    if request.method == "GET":
        config_json = open("config.json", "r")
        response = config_json.read()
        config_json.close()
        return response

    elif request.method == "POST":
        data = request.json
        if data is not None:
            key = list(data.keys())

            if key[0] not in ["cacao", "cafe", "mani"]:
                config_json = open("config.json", "r")
                config = json.loads(config_json.read())
                config.update(data)
                config_json.close()
                # Start with an empty file
                config_json = open("config.json", "w")
                config_json.write(json.dumps(config))
                config_json.close()
                # Read new config
                config_json = open("config.json", "r")
                response = config_json.read()
                config_json.close()
                return response

    elif request.method == "DELETE":
        if name is not None:
            config_json = open("config.json", "r")
            config = json.loads(config_json.read())
            config.pop(name)
            config_json.close()
            # Start with an empty file
            config_json = open("config.json", "w")
            config_json.write(json.dumps(config))
            config_json.close()
            # Read new config
            config_json = open("config.json", "r")
            response = config_json.read()
            config_json.close()
            return response


@app.route("/reset", methods=["POST"])
async def handle_reset(request):
    logger.info("Rebooting...")
    time.sleep(3)
    machine.reset()


@app.route("/events", methods=["GET"])
@with_sse
async def handle_events(request, sse):
    logger.info("Client connected")
    try:
        while True:
            sensor_data = sensorc.read_sensor_data()
            time_values = timerc.get_time_values()
            motor_states = motorc.read_motor_states()
            lcd.show_data(sensor_data[0], sensor_data[1], time_values[1])
            controller.run()

            sensor_json = {"temperature": sensor_data[0], "humidity": sensor_data[1]}
            time_json = {"total_time": time_values[0], "current_time": time_values[1]}
            motor_json = {
                "motor_a": motor_states[0],
                "motor_b": motor_states[1],
                "motor_c": motor_states[2],
            }

            await sse.send(sensor_json, event="sensors")
            await sse.send(time_json, event="time")
            await sse.send(motor_json, event="states")
            await sse.send(controller.get_config(), event="controller")

            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    logger.info("Client disconnected")


app.run(port=80)
