def format_time(minutes, seconds):
    """
    Formats time in minutes and seconds
    """
    return f"{minutes:02d}:{seconds:02d}"


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
        import config
        import network

        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            print("Connecting to the network...")
            wlan.connect(config.WIFI_SSID, config.WIFI_PASSWD)
            while not wlan.isconnected():
                pass
        print(f"Network connected. IP config: {wlan.ipconfig("addr4")}")
    except Exception as e:
        import machine
        import time

        print("ERROR:", e)
        print("Failed to connect to network. Rebooting...")
        time.sleep(5)
        machine.reset()


def ota_update(url, filename):
    """
    Updates the firmware using OTA
    """
    import urequests as requests

    try:
        print("Downloading the new firmware...")
        response = requests.get(url)
        with open(filename, "wb") as f:
            f.write(response.content)
        print("Firmware downloaded successfully.")
    except Exception as e:
        print("ERROR:", e)
        print("Failed to download the new firmware.")
        return
