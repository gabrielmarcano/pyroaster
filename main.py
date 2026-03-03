import gc
import json
import machine

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
from utils import decode, format_time, wifi_manager_task, led_status_task

# Pins

MAX_SCK = machine.Pin(5, machine.Pin.OUT)
MAX_CS = machine.Pin(23, machine.Pin.OUT)
MAX_SO = machine.Pin(19, machine.Pin.IN, machine.Pin.PULL_UP)

AHT_SDA = machine.Pin(17)
AHT_SCL = machine.Pin(16)

LCD_SDA = machine.Pin(21)
LCD_SCL = machine.Pin(22)

MOTOR1_PIN = machine.Pin(25, machine.Pin.OUT, value=0)
MOTOR2_PIN = machine.Pin(26, machine.Pin.OUT, value=0)
MOTOR3_PIN = machine.Pin(27, machine.Pin.OUT, value=0)

# BUZZER_PIN = machine.Pin(13, machine.Pin.OUT)

# try:
#     utils.play_melody(BUZZER_PIN)
# except Exception as e:
#     print(f"Failed to play melody:\n{e}\n")

logger = SimpleLogger()

lcd_ok = False
lcd_err = None
try:
    lcd = LcdController(LCD_SDA, LCD_SCL)
    lcd_ok = True
    import network
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        lcd.show_ip(wlan.ipconfig('addr4')[0])
except Exception as e:
    lcd_err = "not connected (no device found on I2C bus)" if "ENODEV" in str(e) else str(e)
    logger.error(f"Failed to initialize LCD: {lcd_err}")
    lcd = type(
        "DummyLCD",
        (),
        {
            "show_data": lambda self, temperature, humidity, time_in_seconds: None,
            "show_ip": lambda self, ip_str: None,
        },
    )()

sensorc = SensorController(AHT_SDA, AHT_SCL, MAX_SCK, MAX_CS, MAX_SO)
timerc = TimerController()
motorc = MotorController(MOTOR1_PIN, MOTOR2_PIN, MOTOR3_PIN)
controller = Controller(sensorc, timerc, motorc)

# --- Startup status report ---
aht_ok, aht_err, max_ok, max_err = sensorc.status()
print("\n" + "=" * 40)
print("  PYROASTER - Startup Status")
print("=" * 40)
print("  LCD      : {}".format("OK" if lcd_ok else "FAIL - " + str(lcd_err)))
print("  AHT20    : {}".format("OK" if aht_ok else "FAIL - " + str(aht_err)))
print("  MAX6675  : {}".format("OK" if max_ok else "FAIL - " + str(max_err)))
print("  Motors   : configured (pins 25,26,27)")
# LED blink code: highest priority error only (3=MAX, 2=AHT, 1=LCD, 0=all OK)
error_blinks = 3 if not max_ok else 2 if not aht_ok else 1 if not lcd_ok else 0
if error_blinks:
    print("  LED      : {} blink(s) = {}".format(
        error_blinks,
        {1: "LCD error", 2: "AHT20 error", 3: "MAX6675 error"}[error_blinks],
    ))
else:
    print("  LED      : WiFi indicator (off/on)")
print("=" * 40 + "\n")

app = Microdot()
cors = CORS(app, allowed_origins="*", allow_credentials=True)


# Add routes to the server
@app.post("/time")
async def change_time(request):
    data = request.json
    if data is None:
        return {"error": "Missing request body"}, 400

    action = data.get("action")
    if action == "add":
        timerc.increase_current_time()
    elif action == "reduce":
        timerc.decrease_current_time()
    elif action == "change":
        t = data.get("time")
        if not isinstance(t, int) or t < 0:
            return {"error": "time must be a non-negative integer"}, 400
        timerc.set_timer_values(t)

    return timerc.get_json()


@app.get("/controller_config")
async def get_controller_config(request):
    return controller.get_config()


@app.patch("/controller_config")
async def change_controller_config(request):
    data = request.json
    if data is None:
        return {"error": "Missing request body"}, 400

    t = data.get("time")
    if t is not None and (not isinstance(t, int) or t < 0):
        return {"error": "time must be a non-negative integer"}, 400

    return controller.set_config(data.get("starting_temperature"), t)


@app.post("/controller")
async def handle_controller(request):
    data = request.json
    if data is None:
        return {"error": "Missing request body"}, 400

    action = data.get("action")
    if action == "activate":
        controller.activate()
    elif action == "deactivate":
        controller.deactivate()
    elif action == "stop":
        controller.stop()

    return controller.get_config()


@app.post("/motors")
async def handle_motors(request):
    data = request.json
    if data is None:
        return {"error": "Missing request body"}, 400

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
async def get_saved_configs(request):
    try:
        with open("config.json", "r") as config_file:
            return json.load(config_file)
    except (OSError, ValueError):
        return {"error": "Failed to read config file"}, 500


@app.post("/config")
async def save_new_config(request):
    data = request.json
    if data is None:
        return {"error": "Missing request body"}, 400

    try:
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
    except (OSError, ValueError):
        return {"error": "Failed to read config file"}, 500

    data["name"] = decode(data["name"])
    if data["name"] in [item["name"] for item in config]:
        return {"error": "Name already exists"}, 400
    config.append(data)

    try:
        with open("config.json", "w") as config_file:
            json.dump(config, config_file)
    except OSError:
        return {"error": "Failed to write config file"}, 500

    return config


@app.delete("/config/<name>")
async def delete_saved_config(request, name):
    if name is None:
        return {"error": "Missing name"}, 400

    name = decode(name)

    try:
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
    except (OSError, ValueError):
        return {"error": "Failed to read config file"}, 500

    config = [item for item in config if item["name"] != name]

    try:
        with open("config.json", "w") as config_file:
            json.dump(config, config_file)
    except OSError:
        return {"error": "Failed to write config file"}, 500

    return config


@app.post("/reset")
async def handle_reset(request):
    logger.info("Rebooting...")
    await asyncio.sleep(3)
    machine.reset()


@app.get("/events")
@with_sse
async def handle_events(request, sse):
    logger.info("Client connected")
    last_sensor = None
    last_timer = None
    last_motor = None
    last_controller = None
    try:
        while True:
            sensor_data = sensorc.get_json()
            timer_data = timerc.get_json()
            motor_data = motorc.get_json()
            controller_data = controller.get_config()

            if sensor_data != last_sensor:
                await sse.send(sensor_data, event="sensors")
                last_sensor = sensor_data

            if timer_data != last_timer:
                await sse.send(timer_data, event="time")
                last_timer = timer_data

            if motor_data != last_motor:
                await sse.send(motor_data, event="states")
                last_motor = motor_data

            if controller_data != last_controller:
                await sse.send(controller_data, event="controller")
                last_controller = controller_data

            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    logger.info("Client disconnected")


async def logic_loop():
    """Core logic: sensor reads, motor control, LCD - runs always."""
    while True:
        try:
            sensorc.read_sensor_data()
            motorc.read_motor_states()

            sensor_data = sensorc.get_json()
            timer_data = timerc.get_json()

            lcd.show_data(
                sensor_data["temperature"],
                sensor_data["humidity"],
                timer_data["current_time"],
            )

            logger.debug(
                "T: {}C H: {}%".format(
                    sensor_data["temperature"],
                    sensor_data["humidity"],
                )
            )
            logger.debug(format_time(timer_data["current_time"]))

            controller.run()
        except Exception as e:
            logger.error(f"Logic loop error: {e}")

        gc.collect()
        await asyncio.sleep(1)


async def server_task():
    """Web server task - doesn't block if it fails."""
    try:
        await app.run(port=80, debug=True)
    except Exception as e:
        logger.error(f"Web server error: {e}")
        logger.info("Web server stopped, continuing without it...")


async def main():
    task_logic = asyncio.create_task(logic_loop())
    task_wifi = asyncio.create_task(wifi_manager_task(on_connect=lcd.show_ip))
    task_server = asyncio.create_task(server_task())
    task_led = asyncio.create_task(led_status_task(error_blinks))

    try:
        await asyncio.gather(task_logic, task_wifi, task_server, task_led)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Shutting down...")
        task_logic.cancel()
        task_wifi.cancel()
        task_server.cancel()
        task_led.cancel()
        await task_logic
        await task_wifi
        await task_server
        await task_led
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
