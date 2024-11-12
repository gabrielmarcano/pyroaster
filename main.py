from machine import Pin, SoftI2C # type: ignore
from machine_i2c_lcd import I2cLcd
from max6675 import MAX6675
from dht import DHT22 # type: ignore
from time import sleep

# Define MAX6675 pins
MAX_SCK = Pin(5, Pin.OUT)
MAX_CS = Pin(23, Pin.OUT)
MAX_SO = Pin(19, Pin.IN)

# Define DHT22 pin
DHT_PIN = Pin(18)

# Define the LCD I2C address, dimensions and pins
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16
LCD_SDA = Pin(21)
LCD_SCL = Pin(22)

# Define motor pins
MOTOR1_PIN = Pin(25) # use internal LED (2) for debugging
MOTOR2_PIN = Pin(26)
MOTOR3_PIN = Pin(27)

# Define buzzer pin
BUZZER_PIN = Pin(14)

# Define time selector pins
TIME_A = Pin(36)
TIME_B = Pin(34)
TIME_C = Pin(35)

# Define time control pins
TIME_ADDER = Pin(12)
TIME_REDUCER = Pin(13)

# Initialize objects
max = MAX6675(MAX_SCK, MAX_CS, MAX_SO)

dht = DHT22(DHT_PIN)

i2c = SoftI2C(sda=Pin(21), scl=Pin(22), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

def do_connect():
    """
    Connects to a wireless network using the given SSID and password
    """
    import config
    import network # type: ignore
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWD)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ipconfig('addr4'))

# Connect to WLAN
do_connect()

while True:
    # Themperature
    print(max.read()) # eg. ??? (% RH)

    # Humidity
    dht.measure()
    print(dht.humidity()) # eg. 41.3 (% RH)

    # Clear the LCD
    lcd.clear()
    # Display two different messages on different lines
    # By default, it will start at (0,0) if the display is empty
    lcd.putstr("Hello World!")
    sleep(2)
    lcd.clear()
    # Starting at the second line (0, 1)
    lcd.move_to(0, 1)
    lcd.putstr("Hello World!")

    sleep(2)


