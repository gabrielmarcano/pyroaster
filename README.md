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
- [How it works](#how-it-works)
- [Project structure](#project-structure)
- [Hardware](#hardware)
- [Wiring](#wiring)
- [Software](#software)
- [Setup](#setup)
- [API](#api)
- [Resources](#resources)

## Summary

All logic depends on the data given by the **Thermocouple (MAX6675)** & **AHT20** sensors. It's intention is to control 3 motors, which will turn on or off based on the temperature that it reaches.

When the temperature reaches the value set on the config, it feeds a relay that controls the first motor,
and also starts a timer that was set on the config. Extra configs can be saved.

When the timer stops, the other 2 relays feed the second & third motor.

> Motors can only be stopped manually through the app interface.

## How it works

The firmware runs four cooperative async tasks on a single core:

1. **Logic loop** (1s interval) — reads sensors, runs the controller, updates the LCD
2. **Web server** — HTTP REST API + Server-Sent Events (SSE) for real-time updates
3. **WiFi manager** (15s interval) — monitors connection and reconnects automatically
4. **LED status** — blink codes for hardware errors, solid on/off for WiFi state

The logic loop runs independently from the network. If WiFi drops or the web server crashes, sensor reads, motor control, and LCD updates continue uninterrupted. When WiFi reconnects, the IP is shown on the LCD for 5 seconds.

### Networking

The ESP32 runs in dual WiFi mode (STA + AP simultaneously):

- **STA** — connects to your home router for network access
- **AP** — creates a `PyRoaster-AP` network for direct connection (always available at `192.168.4.1`)

This means the device is reachable even when the router signal is weak — just connect your phone directly to the AP network.

### Startup diagnostics

On boot, the firmware prints a status report for all hardware components and sets the built-in LED to indicate the highest priority error:

| LED behavior | Meaning |
|---|---|
| Off | Everything OK, no WiFi |
| Solid on | Everything OK, WiFi connected |
| 1 blink, 3s pause | LCD not connected |
| 2 blinks, 3s pause | AHT20 not connected |
| 3 blinks, 3s pause | MAX6675 not connected |

Individual sensor failures are graceful — if the MAX6675 is absent, AHT20 readings and LCD updates continue normally.

### Roasting flow

1. User sets a **starting temperature** and **roast time** via the API or saved configs
2. User activates the controller
3. When the temperature reaches the threshold → **Motor A** starts and the **timer** begins counting down
4. When the timer reaches zero → **Motors B & C** start, controller deactivates
5. Motors can only be stopped manually (API or physical button)

## Project structure

```
├── boot.py              # Runs on boot: starts WiFi + WebREPL
├── main.py              # Entry point: async tasks, HTTP routes, pin setup
├── controller.py        # Roasting controller (temp threshold → motor → timer logic)
├── logger.py            # Simple timestamped logger (DEBUG/INFO/WARNING/ERROR)
├── utils.py             # WiFi manager, LED status, time formatting, URL decoding
├── config.json          # Saved roasting presets
├── env.py               # WiFi + AP credentials (not committed)
├── env.template.py      # Credentials template
├── build.py             # Cross-compiles to .mpy and uploads via mpremote
├── api.yaml             # OpenAPI spec
│
├── lib/
│   ├── sensors.py       # MAX6675 + AHT20 sensor aggregation
│   ├── motors.py        # 3 motor (relay) control
│   ├── timer.py         # Hardware timer with countdown
│   └── lcd.py           # 2x16 I2C LCD display
│
├── drivers/
│   ├── max6675.py       # MAX6675 thermocouple SPI driver
│   ├── ahtx0.py         # AHT20 humidity/temperature I2C driver
│   ├── machine_i2c_lcd.py  # I2C LCD driver (PCF8574)
│   └── lcd_api.py       # LCD API abstraction
│
├── microdot/            # Microdot web framework (vendored)
│   ├── microdot.py
│   ├── cors.py
│   ├── sse.py
│   └── helpers.py
│
├── test/
│   ├── sse.html         # SSE test client
│   └── sse.js
│
└── out/                 # Build output (compiled .mpy files)
```

## Hardware

| Component | Description |
|-----------|-------------|
| ESP32 DevKit | Main microcontroller |
| MAX6675 + K-type thermocouple | Temperature sensor (0-1024°C) |
| AHT20 | Humidity & temperature sensor (I2C) |
| 16x2 LCD + PCF8574 | I2C character display |
| 3x Relay modules | Motor control (one per motor) |

## Wiring

| ESP-32 | MAX6675 | AHT20 I2C | LCD I2C | R1  | R2  | R3  |
| ------ | ------- | --------- | ------- | --- | --- | --- |
| GPIO2  |         |           |         |     |     |     | (built-in LED)
| GPIO5  | SCK     |           |         |     |     |     |
| GPIO16 |         | SCL       |         |     |     |     |
| GPIO17 |         | SDA       |         |     |     |     |
| GPIO19 | SO      |           |         |     |     |     |
| GPIO21 |         |           | SDA     |     |     |     |
| GPIO22 |         |           | SCL     |     |     |     |
| GPIO23 | CS      |           |         |     |     |     |
| GPIO25 |         |           |         | x   |     |     |
| GPIO26 |         |           |         |     | x   |     |
| GPIO27 |         |           |         |     |     | x   |

> R: Relay

The two I2C buses use hardware peripherals: `I2C(0)` for the AHT20 sensor and `I2C(1)` for the LCD.

## Software

- **MicroPython** on ESP32
- **Microdot** — lightweight async web framework for REST API and SSE
- **mpy-cross** — cross-compiler for `.mpy` bytecode (faster load, less RAM)
- **mpremote** — file transfer to the ESP32

## Setup

1. Flash MicroPython firmware to the ESP32

2. Copy `env.template.py` to `env.py` and set your credentials:
   ```python
   WIFI_SSID = "your-ssid"
   WIFI_PASSWD = "your-password"
   AP_SSID = "PyRoaster-AP"
   AP_PASSWD = "your-ap-password"
   ```

3. Build and upload:
   ```bash
   python build.py
   ```
   This cross-compiles all library files to `.mpy`, copies everything to the `out/` directory, and prompts to upload via `mpremote`.

4. The device boots, connects to WiFi, starts the AP network, and runs the web server on port 80. The AP IP (`192.168.4.1`) and router IP are shown on the LCD.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/events` | SSE stream (sensors, timer, motors, controller) |
| `GET` | `/controller_config` | Get controller settings |
| `PATCH` | `/controller_config` | Update starting temperature / time |
| `POST` | `/controller` | Activate, deactivate, or stop the controller |
| `POST` | `/time` | Add, reduce, or change the timer |
| `POST` | `/motors` | Control individual motors (on/off) |
| `GET` | `/config` | List saved roasting presets |
| `POST` | `/config` | Save a new preset |
| `DELETE` | `/config/<name>` | Delete a preset |
| `POST` | `/reset` | Reboot the device |

See `api.yaml` for the full OpenAPI specification.

### SSE events

The `/events` endpoint streams four event types:

- **`sensors`** — `{"temperature": int, "humidity": int}`
- **`time`** — `{"total_time": int, "current_time": int, "timer_active": bool}`
- **`states`** — `{"motor_a": bool, "motor_b": bool, "motor_c": bool}`
- **`controller`** — `{"active": bool, "starting_temperature": int, "time": int}`

Events are only sent when data changes (change detection).

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
