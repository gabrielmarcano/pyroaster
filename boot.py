# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)
import webrepl
from utils import connect_to_network

connect_to_network()
webrepl.start()
