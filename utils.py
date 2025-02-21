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


def connect_to_network():
    """
    Connects to a wireless network using the given SSID and password
    """
    try:
        import env
        import network
        from machine import Pin

        internal_led = Pin(2, Pin.OUT, value=0)

        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            print("Connecting to the network...")
            wlan.connect(env.WIFI_SSID, env.WIFI_PASSWD)
            while not wlan.isconnected():
                pass
        print(f"Network connected. IP config: {wlan.ipconfig("addr4")}")
        internal_led.on()  # Turn on the built-in LED to indicate that the device is connected to the network
    except Exception as e:
        import machine
        import time

        print("ERROR:", e)
        print("Failed to connect to network. Rebooting...")
        time.sleep(5)
        machine.reset()
