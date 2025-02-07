# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)
import webrepl
import utils

utils.connect_to_network()
webrepl.start()
