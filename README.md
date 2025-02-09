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

All logic depends on the data given by the **Thermocouple** & **DHT22** sensors, and the selected mode in the **4 Position Rotary Switch**. It's intention is to control 3 motors, which will turn on or off based on the temperature that it reaches.

When the temperature reaches 140ºC, 170ºC or 180ºC (depending on the mode) it feeds a relay that controls the first motor,
and also starts a timer that can be 12, 20 or 33 minutes which also depends on the mode.

There will be two push buttons, one will add +1min to the time (and start the timer if there isn't one already), and the other will reduce -1min to the time.

When the timer stops, a buzzer starts making noise and also feeds the other 2 relays that controls the second & third motor.

> Motors can only be stopped manually by either the security button or through the web interface. If Motor 2 or Motor 3 are stopped via the web interface, they will stop any action taken after the timer stops.

## Resources

### DHT22

MicroPython built-in dht library.

### MAX6675

https://github.com/BetaRavener/micropython-hw-lib/blob/master/MAX6675/max6675.py

### LCD

Uses both the API (lcd_api) and the machine module (machine_i2c_lcd).

https://github.com/dhylands/python_lcd

### Web Server

I made my own module that supports sse based on https://github.com/troublegum/micropyserver and this fork https://github.com/ferdinandog/micropyserver/tree/new-utils
