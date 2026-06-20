# This file is executed on every boot (including wake-boot from deepsleep)
import webrepl
from utils import start_access_point

start_access_point()
webrepl.start()
