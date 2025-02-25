import json
import machine

import time

from microdot import Microdot
from microdot.cors import CORS
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

cors = CORS(app, allowed_origins="*", allow_credentials=True)


# Add routes to the server
@app.post("/time")
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

    return timerc.get_json()


@app.get("/controller_config")
async def handle_controller_config(request):
    return controller.get_config()


@app.patch("/controller_config")
async def handle_controller_config(request):
    data = request.json
    if data is not None:
        return controller.set_config(data.get("starting_temperature"), data.get("time"))


@app.post("/controller")
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


@app.post("/motors")
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

        return motorc.get_json()


@app.get("/config")
async def handle_saved_config(request):
    config_json = open("config.json", "r")
    response = config_json.read()
    config_json.close()
    return json.loads(response)


@app.post("/config")
async def handle_saved_config(request):
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
            return json.loads(response)


@app.delete("/config/<name>")
async def handle_saved_config(request, name):
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
        return json.loads(response)


@app.post("/reset")
async def handle_reset(request):
    logger.info("Rebooting...")
    time.sleep(3)
    machine.reset()


@app.get("/events")
@with_sse
async def handle_events(request, sse):
    logger.info("Client connected")
    try:
        while True:
            sensor_data = sensorc.get_json()
            time_values = timerc.get_json()
            motor_states = motorc.get_json()
            lcd.show_data(
                sensor_data["temperature"],
                sensor_data["humidity"],
                time_values["current_time"],
            )
            controller.run()

            await sse.send(sensor_data, event="sensors")
            await sse.send(time_values, event="time")
            await sse.send(motor_states, event="states")
            await sse.send(controller.get_config(), event="controller")

            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    logger.info("Client disconnected")


app.run(port=80, debug=True)
