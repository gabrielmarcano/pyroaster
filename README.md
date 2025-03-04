<h1 align="center">ESP32 Roaster Project</h1>
<p align="center">
  A project to control a peanut, coffee & cocoa roaster with an ESP32
</p>

<div align="center">

<!-- [![Build](https://img.shields.io/github/actions/workflow/status/gabrielmarcano/esp32-roaster/build.yml?logo=github)](https://github.com/gabrielmarcano/esp32-roaster/blob/master/.github/workflows/build.yml) -->
<!-- [![OTA Update](https://img.shields.io/github/actions/workflow/status/gabrielmarcano/esp32-roaster/ota-update.yml?logo=github&label=OTA)](https://github.com/gabrielmarcano/esp32-roaster/blob/master/.github/workflows/ota-update.yml) -->
<!-- [![GitHub release](https://img.shields.io/github/v/release/gabrielmarcano/esp32-roaster?filter=*alpha&logo=github)](https://github.com/gabrielmarcano/esp32-roaster/releases) -->

[![python](https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![micropython](https://img.shields.io/badge/built%20for-MicroPython-3776AB?logo=micropython)](https://micropython.org/)

</div>

## Contents

- [Summary](#summary)
- [Project structure](#project-structure) (WIP)
- [Hardware](#hardware) (WIP)
- [Software](#software) (WIP)
- [Wiring](#wiring) (WIP)
- [Resources](#resources)

## Summary

All logic depends on the data given by the **Thermocouple (MAX6675)** & **AHT20** sensors. It's intention is to control 3 motors, which will turn on or off based on the temperature that it reaches.

When the temperature reaches the value set on the config, it feeds a relay that controls the first motor,
and also starts a timer that was set on the config. Extra configs can be saved.

There will be two push buttons, one will add +1min to the time (and start the timer if there isn't one already), and the other will reduce -1min to the time.

When the timer stops, a buzzer\* starts making noise and also feeds the other 2 relays that controls the second & third motor.

> Motors can only be stopped manually by either the security button or through the app interface.

## Wiring

| ESP-32 | MAX6675 | AHT20 i2C | LCD i2C | R1  | R2  | R3  | BUZZ |
| ------ | ------- | --------- | ------- | --- | --- | --- | ---- |
| GPIO5  | SCK     |           |         |     |     |     |      |
| GPIO12 |         | SCL       |         |     |     |     |      |
| GPIO13 |         |           |         |     |     |     | x    |
| GPIO14 |         | SDA       |         |     |     |     |      |
| GPIO19 | SO      |           |         |     |     |     |      |
| GPIO21 |         |           | SDA     |     |     |     |      |
| GPIO22 |         |           | SCL     |     |     |     |      |
| GPIO23 | CS      |           |         |     |     |     |      |
| GPIO25 |         |           |         | x   |     |     |      |
| GPIO26 |         |           |         |     | x   |     |      |
| GPIO27 |         |           |         |     |     | x   |      |

> R: Relay

## Resources

### AHTx0

MicroPython AHT20 driver library.

https://github.com/targetblank/micropython_ahtx0

### MAX6675

https://github.com/BetaRavener/micropython-hw-lib/blob/master/MAX6675/max6675.py

### LCD

Uses both the API (lcd_api) and the machine module (machine_i2c_lcd).

https://github.com/dhylands/python_lcd

### Web Server

Uses the Microdot framework https://github.com/miguelgrinberg/microdot
