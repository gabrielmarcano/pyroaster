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
    if "+" in name:
        name = name.replace("+", " ")

    if "%20" in name:
        name = name.replace("%20", " ")

    if "%2F" in name:
        name = name.replace("%2F", "/")

    if "%3A" in name:
        name = name.replace("%3A", ":")

    if "%3D" in name:
        name = name.replace("%3D", "=")

    if "%3F" in name:
        name = name.replace("%3F", "?")

    if "%23" in name:
        name = name.replace("%23", "#")

    if "%26" in name:
        name = name.replace("%26", "&")

    if "%2B" in name:
        name = name.replace("%2B", "+")

    if "%25" in name:
        name = name.replace("%25", "%")

    return name


def connect_to_network():
    """
    Starts WiFi connection in background - does NOT block.
    Use start_wifi_manager() for async background reconnection.
    """
    import network
    from machine import Pin

    internal_led = Pin(2, Pin.OUT, value=0)
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print(f"Network already connected. IP: {wlan.ipconfig('addr4')}")
        internal_led.on()
        return True

    try:
        import env
        print("Starting WiFi connection in background...")
        wlan.connect(env.WIFI_SSID, env.WIFI_PASSWD)
    except Exception as e:
        print(f"WiFi connection error: {e}")
        return False

    return True


async def wifi_manager_task():
    """
    Background task that ensures WiFi stays connected.
    Retries every WIFI_RETRY_INTERVAL seconds if disconnected.
    """
    import network
    import asyncio
    from machine import Pin

    internal_led = Pin(2, Pin.OUT, value=0)

    while True:
        try:
            wlan = network.WLAN(network.STA_IF)
            if not wlan.isconnected():
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
                internal_led.on()
            else:
                internal_led.off()

        except Exception as e:
            print(f"WiFi manager error: {e}")

        await asyncio.sleep(WIFI_RETRY_INTERVAL)
