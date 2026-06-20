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
from utils import decode, format_time, validate_body, led_status_task

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

# --- Hardware enable flags (set False to disable a device for testing) ---
# A disabled device is never initialized (its I2C bus / pins are left untouched)
# and never triggers a fault LED -- useful to bring up one bus at a time.
ENABLE_AHT = True
ENABLE_MAX = True
ENABLE_LCD = True

logger = SimpleLogger()

# Map machine.reset_cause() codes to names for startup diagnostics. Not every
# build exposes every constant (e.g. BROWNOUT_RESET), so look them up defensively.
_RESET_CAUSES = {}
for _name in ("PWRON_RESET", "HARD_RESET", "WDT_RESET", "DEEPSLEEP_RESET", "SOFT_RESET", "BROWNOUT_RESET"):
    _code = getattr(machine, _name, None)
    if _code is not None:
        _RESET_CAUSES[_code] = _name

def _make_dummy_lcd():
    return type(
        "DummyLCD",
        (),
        {
            "show_data": lambda self, temperature, humidity, time_in_seconds: None,
            "show_ip": lambda self, ip_str: None,
        },
    )()


lcd_ok = False
lcd_err = None
if ENABLE_LCD:
    try:
        lcd = LcdController(LCD_SDA, LCD_SCL)
        lcd_ok = True
        import network
        ap = network.WLAN(network.AP_IF)
        if ap.active():
            lcd.show_ip(ap.ifconfig()[0])
    except Exception as e:
        lcd_err = "not connected (no device found on I2C bus)" if "ENODEV" in str(e) else str(e)
        logger.error(f"Failed to initialize LCD: {lcd_err}")
        lcd = _make_dummy_lcd()
else:
    lcd = _make_dummy_lcd()

sensorc = SensorController(AHT_SDA, AHT_SCL, MAX_SCK, MAX_CS, MAX_SO,
                           enable_aht=ENABLE_AHT, enable_max=ENABLE_MAX)
timerc = TimerController()
motorc = MotorController(MOTOR1_PIN, MOTOR2_PIN, MOTOR3_PIN)
controller = Controller(sensorc, timerc, motorc)

# --- Startup status report ---
def _fmt(label, detail):
    return label if detail is None else label + " - " + str(detail)

aht_lbl, aht_det, max_lbl, max_det = sensorc.report()
lcd_lbl = "DISABLED" if not ENABLE_LCD else ("OK" if lcd_ok else "FAIL - " + str(lcd_err))
_reset_cause = machine.reset_cause()
print("\n" + "=" * 40)
print("  PYROASTER - Startup Status")
print("=" * 40)
print("  Reset    : {} ({})".format(_RESET_CAUSES.get(_reset_cause, "UNKNOWN"), _reset_cause))
print("  LCD      : {}".format(lcd_lbl))
print("  AHT20    : {}".format(_fmt(aht_lbl, aht_det)))
print("  MAX6675  : {}".format(_fmt(max_lbl, max_det)))
print("  Motors   : configured (pins 25,26,27)")
import network
_ap = network.WLAN(network.AP_IF)
print("  AP       : {}".format(_ap.ifconfig()[0] if _ap.active() else "inactive"))
# LED blink code: highest priority *enabled* error (3=MAX, 2=AHT, 1=LCD, 0=ok/disabled)
error_blinks = 3 if max_lbl == "FAIL" else 2 if aht_lbl == "FAIL" else 1 if (ENABLE_LCD and not lcd_ok) else 0
if error_blinks:
    print("  LED      : {} blink(s) = {}".format(
        error_blinks,
        {1: "LCD error", 2: "AHT20 error", 3: "MAX6675 error"}[error_blinks],
    ))
else:
    print("  LED      : AP indicator (off/on)")
print("=" * 40 + "\n")

# A brownout or watchdog reset usually points to an unstable power supply (e.g.
# WiFi TX / relay-coil current spikes sagging the rail), not a code bug. Surface
# it so it's traceable even without a serial console at hand.
if _RESET_CAUSES.get(_reset_cause) in ("BROWNOUT_RESET", "WDT_RESET"):
    logger.warning("Unexpected reset cause: {} -- check power supply".format(_RESET_CAUSES[_reset_cause]))


def current_error_blinks():
    """Live LED blink code, re-evaluated each cycle by led_status_task.

    Highest-priority error wins (3=MAX, 2=AHT, 1=LCD, 0=all OK). Sensor health is
    read live (disabled devices count as OK); lcd_ok stays the boot-time value
    (no live LCD health probe exists).
    """
    aht_ok, max_ok = sensorc.health()
    return 3 if not max_ok else 2 if not aht_ok else 1 if (ENABLE_LCD and not lcd_ok) else 0


app = Microdot()
cors = CORS(app, allowed_origins="*", allow_credentials=True)


# Add routes to the server
@app.post("/time")
async def change_time(request):
    data = request.json
    if data is None:
        return {"error": "Missing request body"}, 400

    action = data.get("action")
    if action not in ("add", "reduce", "change"):
        return {"error": "'action' must be one of ['add', 'reduce', 'change']"}, 400

    if action == "add":
        timerc.increase_current_time()
    elif action == "reduce":
        timerc.decrease_current_time()
    elif action == "change":
        t = data.get("time")
        if not isinstance(t, int) or isinstance(t, bool) or t < 0:
            return {"error": "'time' must be a non-negative integer"}, 400
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

    err = validate_body(data, {
        "starting_temperature": (int, False, {"min": 0}),
        "time": (int, False, {"min": 0}),
    })
    if err:
        return {"error": err}, 400

    return controller.set_config(data.get("starting_temperature"), data.get("time"))


@app.post("/controller")
async def handle_controller(request):
    data = request.json
    if data is None:
        return {"error": "Missing request body"}, 400

    err = validate_body(data, {
        "action": (str, True, {"enum": ["activate", "deactivate", "stop"]}),
    })
    if err:
        return {"error": err}, 400

    action = data["action"]
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

    err = validate_body(data, {
        "motor_a": (bool, False, None),
        "motor_b": (bool, False, None),
        "motor_c": (bool, False, None),
    })
    if err:
        return {"error": err}, 400

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

    err = validate_body(data, {
        "name": (str, True, None),
        "starting_temperature": (int, True, {"min": 0}),
        "time": (int, True, {"min": 0}),
    })
    if err:
        return {"error": err}, 400

    try:
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
    except (OSError, ValueError):
        return {"error": "Failed to read config file"}, 500

    name = decode(data["name"])
    if name in config:
        return {"error": "Name already exists"}, 400
    config[name] = {
        "starting_temperature": data["starting_temperature"],
        "time": data["time"],
    }

    try:
        with open("config.json", "w") as config_file:
            json.dump(config, config_file)
    except OSError:
        return {"error": "Failed to write config file"}, 500

    return config


@app.delete("/config/<name>")
async def delete_saved_config(request, name):
    name = decode(name)

    try:
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
    except (OSError, ValueError):
        return {"error": "Failed to read config file"}, 500

    if name not in config:
        return {"error": "Config not found"}, 404

    del config[name]

    try:
        with open("config.json", "w") as config_file:
            json.dump(config, config_file)
    except OSError:
        return {"error": "Failed to write config file"}, 500

    return config


@app.post("/reset")
async def handle_reset(request):
    async def delayed_reset():
        await asyncio.sleep(1)
        machine.reset()
    logger.info("Rebooting...")
    asyncio.create_task(delayed_reset())
    return {"message": "Rebooting..."}


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
    task_server = asyncio.create_task(server_task())
    task_led = asyncio.create_task(led_status_task(current_error_blinks))

    try:
        await asyncio.gather(task_logic, task_server, task_led)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Shutting down...")
        task_logic.cancel()
        task_server.cancel()
        task_led.cancel()
        await task_logic
        await task_server
        await task_led
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
