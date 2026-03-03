WIFI_RETRY_INTERVAL = 15


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
    Background task that ensures WiFi stays connected.
    Retries every WIFI_RETRY_INTERVAL seconds if disconnected.
    Calls on_connect(ip_str) when WiFi transitions from disconnected to connected.
    """
    import network
    import asyncio

    wlan = network.WLAN(network.STA_IF)
    was_connected = wlan.isconnected()

    while True:
        try:
            if not wlan.isconnected():
                was_connected = False
                print("WiFi disconnected, retrying connection...")
                try:
                    import env
                    wlan.connect(env.WIFI_SSID, env.WIFI_PASSWD)
                    for _ in range(30):
                        await asyncio.sleep(1)
                        if wlan.isconnected():
                            break
                except Exception as e:
                    print(f"WiFi reconnection failed: {e}")

            if wlan.isconnected():
                if not was_connected and on_connect:
                    try:
                        on_connect(wlan.ipconfig('addr4')[0])
                    except Exception as e:
                        print(f"on_connect callback error: {e}")
                was_connected = True

        except Exception as e:
            print(f"WiFi manager error: {e}")

        await asyncio.sleep(WIFI_RETRY_INTERVAL)


async def led_status_task(error_blinks):
    """LED status indicator.

    error_blinks=0: solid off (no WiFi) / solid on (WiFi connected)
    error_blinks>0: blink N times, 3s pause, repeat
    """
    import network
    import asyncio
    from machine import Pin

    led = Pin(2, Pin.OUT, value=0)
    wlan = network.WLAN(network.STA_IF)

    while True:
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
