def validate_body(data, rules):
    """Validate request body fields.
    rules: {field: (type, required, extra)}
    extra: None or dict with "enum", "min", "max" keys.
    Returns None on success, error string on failure."""
    for field, (typ, required, extra) in rules.items():
        val = data.get(field)
        if val is None:
            if required:
                return f"'{field}' is required"
            continue
        if not isinstance(val, typ) or (typ is int and isinstance(val, bool)):
            return f"'{field}' must be {typ.__name__}"
        if extra:
            if "enum" in extra and val not in extra["enum"]:
                return f"'{field}' must be one of {extra['enum']}"
            if "min" in extra and val < extra["min"]:
                return f"'{field}' must be >= {extra['min']}"
            if "max" in extra and val > extra["max"]:
                return f"'{field}' must be <= {extra['max']}"
    return None


def format_time(seconds):
    """
    Formats time in hours, minutes and seconds
    """
    if seconds is not None:
        hours = seconds // 3600 % 24
        minutes = seconds % 3600 // 60
        seconds = seconds % 3600 % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return "00:00:00"


def decode(name):
    name = name.replace("+", " ")
    name = name.replace("%20", " ")
    name = name.replace("%2F", "/")
    name = name.replace("%3A", ":")
    name = name.replace("%3D", "=")
    name = name.replace("%3F", "?")
    name = name.replace("%23", "#")
    name = name.replace("%26", "&")
    name = name.replace("%2B", "+")
    name = name.replace("%25", "%")
    return name


def start_access_point():
    """
    Start WiFi in AP-only mode (direct connection at 192.168.4.1).

    STA mode is intentionally disabled and forced off: the router isn't reachable
    in production, and a STA stuck scanning destabilizes the AP since both share a
    single radio. AP-only keeps the radio parked on the AP channel = stable.
    """
    import network

    # Force STA off so it never scans and steals the radio from the AP.
    sta = network.WLAN(network.STA_IF)
    sta.active(False)

    try:
        import env
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=env.AP_SSID, password=env.AP_PASSWD, authmode=3)
        print(f"AP started: {env.AP_SSID} (IP: {ap.ifconfig()[0]})")
    except Exception as e:
        print(f"AP setup error: {e}")

    return True


async def led_status_task(get_error_blinks):
    """LED status indicator.

    get_error_blinks: callable returning the current blink code, re-evaluated
    every cycle. Evaluating live (instead of latching a boot-time value) means a
    transient sensor glitch at startup no longer pins the fault indication on
    forever -- the LED follows the sensors' real current state.

    code == 0: solid on (AP up) / solid off (AP down)
    code  > 0: blink N times, 3s pause, repeat
    """
    import network
    import asyncio
    from machine import Pin

    led = Pin(2, Pin.OUT, value=0)
    ap = network.WLAN(network.AP_IF)

    while True:
        error_blinks = get_error_blinks()
        if error_blinks == 0:
            led.value(1 if ap.active() else 0)
            await asyncio.sleep(1)
        else:
            for _ in range(error_blinks):
                led.on()
                await asyncio.sleep(0.2)
                led.off()
                await asyncio.sleep(0.2)
            await asyncio.sleep(3)
