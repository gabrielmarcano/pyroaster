WIFI_RETRY_INTERVAL = 15
WIFI_RETRY_MAX = 120  # cap for exponential backoff when the router is unreachable


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


def connect_to_network():
    """
    Starts WiFi STA + AP. STA connects to router, AP creates direct-connect network.
    STA connection is non-blocking — use wifi_manager_task() for background reconnection.
    """
    import network

    # --- STA mode (connect to router) ---
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print(f"Network already connected. IP: {wlan.ipconfig('addr4')}")
    else:
        try:
            import env
            print("Starting WiFi connection in background...")
            wlan.connect(env.WIFI_SSID, env.WIFI_PASSWD)
        except Exception as e:
            print(f"WiFi connection error: {e}")

    # --- AP mode (direct connection) ---
    try:
        import env
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=env.AP_SSID, password=env.AP_PASSWD, authmode=3)
        print(f"AP started: {env.AP_SSID} (IP: {ap.ifconfig()[0]})")
    except Exception as e:
        print(f"AP setup error: {e}")

    return True


async def wifi_manager_task(on_connect=None):
    """
    Keep the STA connection alive WITHOUT destabilizing the AP.

    On the ESP32 the STA and AP share a single radio. A STA stuck retrying (router
    out of range) makes the radio scan/channel-hop constantly, which drops AP
    clients -- the AP is the priority here, so we keep STA retries gentle:

    1. Never call connect() while the driver is already CONNECTING. Re-issuing it
       there is exactly what raised "sta is connecting, cannot set config" /
       "Wifi Internal State Error", and it keeps the radio busy.
    2. Back off exponentially (up to WIFI_RETRY_MAX) when the router can't be
       reached, so an unreachable router doesn't starve the AP of airtime.
    Calls on_connect(ip_str) when WiFi transitions from disconnected to connected.
    """
    import network
    import asyncio

    wlan = network.WLAN(network.STA_IF)
    was_connected = wlan.isconnected()
    backoff = WIFI_RETRY_INTERVAL

    while True:
        try:
            if wlan.isconnected():
                if not was_connected:
                    backoff = WIFI_RETRY_INTERVAL  # reset on success
                    if on_connect:
                        try:
                            on_connect(wlan.ipconfig('addr4')[0])
                        except Exception as e:
                            print(f"on_connect callback error: {e}")
                was_connected = True
            else:
                was_connected = False
                status = wlan.status()
                if status == network.STAT_CONNECTING:
                    # Already trying -- leave it alone (touching it here is what
                    # caused the error storm). Just wait and let the AP breathe.
                    pass
                else:
                    print("WiFi not connected (status={}), reconnecting...".format(status))
                    try:
                        import env
                        wlan.connect(env.WIFI_SSID, env.WIFI_PASSWD)
                    except Exception as e:
                        print(f"WiFi reconnection failed: {e}")
                    backoff = min(backoff * 2, WIFI_RETRY_MAX)

        except Exception as e:
            print(f"WiFi manager error: {e}")

        await asyncio.sleep(backoff)


async def led_status_task(get_error_blinks):
    """LED status indicator.

    get_error_blinks: callable returning the current blink code, re-evaluated
    every cycle. Evaluating live (instead of latching a boot-time value) means a
    transient sensor glitch at startup no longer pins the fault indication on
    forever -- the LED follows the sensors' real current state.

    code == 0: solid off (no WiFi) / solid on (WiFi connected)
    code  > 0: blink N times, 3s pause, repeat
    """
    import network
    import asyncio
    from machine import Pin

    led = Pin(2, Pin.OUT, value=0)
    wlan = network.WLAN(network.STA_IF)

    while True:
        error_blinks = get_error_blinks()
        if error_blinks == 0:
            led.value(1 if wlan.isconnected() else 0)
            await asyncio.sleep(1)
        else:
            for _ in range(error_blinks):
                led.on()
                await asyncio.sleep(0.2)
                led.off()
                await asyncio.sleep(0.2)
            await asyncio.sleep(3)
