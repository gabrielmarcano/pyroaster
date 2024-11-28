# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)
import webrepl

webrepl.start()


def do_connect():
    """
    Connects to a wireless network using the given SSID and password
    """
    import config
    import network

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("connecting to network...")
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWD)
        while not wlan.isconnected():
            pass
    print("network config:", wlan.ipconfig("addr4"))


# Connect to WLAN
do_connect()
