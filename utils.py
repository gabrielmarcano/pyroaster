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


def make_buzzer_sound(pin):
    """
    Makes a sound using a buzzer
    """
    from machine import PWM

    beeper = PWM(pin, freq=440, duty=512)
    beeper.deinit()


def play_melody(buzzer_pin):
    """
    Plays a melody using a buzzer
    """
    from machine import PWM
    import time

    tempo = 5
    tones = {
        "c": 262,
        "d": 294,
        "e": 330,
        "f": 349,
        "g": 392,
        "a": 440,
        "b": 494,
        "C": 523,
        " ": 0,
    }
    beeper = PWM(buzzer_pin, freq=440, duty=512)
    melody = "cdefgabC"
    rhythm = [8, 8, 8, 8, 8, 8, 8, 8]

    for tone, length in zip(melody, rhythm):
        beeper.freq(tones[tone])
        time.sleep(tempo / length)
    beeper.deinit()


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
    Starts WiFi connection in background - does NOT block.
    Use start_wifi_manager() for async background reconnection.
    """
    import network

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print(f"Network already connected. IP: {wlan.ipconfig('addr4')}")
        return True

    try:
        import env
        print("Starting WiFi connection in background...")
        wlan.connect(env.WIFI_SSID, env.WIFI_PASSWD)
    except Exception as e:
        print(f"WiFi connection error: {e}")
        return False

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
