# EcoPulse — Smart Plant Monitor

Final project for UC San Diego SIPP program, summer 2026.

- Terrence Chou (GitHub: [tchou1](https://github.com/tchou1))
- Sam Ban (GitHub: [SamBan2601](https://github.com/SamBan2601))
- Hoang Long Nguyen (GitHub: [longthannga](https://github.com/longthannga))
- James Watkins (GitHub: [j3watkins-star](https://github.com/j3watkins-star))

📊 [Project Presentation Slides](https://docs.google.com/presentation/d/1kA27opjdNMZtgQQBT74bYB2pfIoOZVbaUCo5qyDHC_Q/edit?slide=id.p#slide=id.p)

## Overview

EcoPulse is an automated plant care system built on the Adafruit Metro M0 Express (SAMD21). It monitors soil moisture and air conditions in real time, alerts on dry soil, automatically triggers a water pump via servo when humidity drops too low, and displays live readings on an OLED screen. A capacitive touch button lets the user cycle between display modes.

## Hardware

- Adafruit Metro M0 Express (SAMD21G18)
- SSD1306-based I2C OLED display (128x64)
- Soil moisture sensor (analog)
- DHT11 temperature/humidity sensor
- Touch sensor (mode switch button)
- Buzzer (dry-soil alarm)
- Red LED (dry-soil alert)
- Micro servo (pump/humidifier actuator)

## Pin Mapping

| Component        | Pin  |
|-------------------|------|
| Soil moisture     | A1   |
| Touch button       | D3   |
| DHT11 sensor       | D2   |
| Buzzer             | D6   |
| Red LED            | D7   |
| Servo (PWM)        | D5   |
| OLED (I2C)         | SCL/SDA |

## Why a Custom OLED Library

The Metro M0 Express has very limited RAM, and CircuitPython's standard display stack (`displayio`, `adafruit_display_text`, `adafruit_displayio_ssd1306`, etc.) is too heavy to run alongside our sensors and control logic without running out of memory.

To work around this, we wrote **`mini_oled.py`** — a lightweight, dependency-free SSD1306 driver that talks to the display directly over I2C using a minimal built-in font and framebuffer. It supports only what we need (`fill`, `text`, `pixel`, `show`), keeping the memory footprint small enough to leave room for the rest of the program.

For deployment, `mini_oled.py` is precompiled to `mini_oled.mpy` (CircuitPython's compiled bytecode format) to save even more RAM and flash space at import time.

`restartOLED.py` is a standalone diagnostic script using the standard `displayio`/`adafruit_displayio_ssd1306` libraries — useful for confirming the display is wired and addressed correctly before relying on the custom driver.

## Repository Structure

```
.
├── code.py            # Main program: sensor loop, alerts, pump control, OLED UI
├── mini_oled.py        # Custom lightweight SSD1306 driver (source)
├── restartOLED.py      # Standalone OLED wiring/sanity check (uses standard libs)
├── lib/
│   ├── mini_oled.py     # Copy of the driver as deployed
│   └── mini_oled.mpy    # Precompiled version for production use (saves RAM/flash)
└── boot_out.txt        # CircuitPython/board info dump (auto-generated on boot)
```

## How It Works

1. On startup, `code.py` attempts to initialize the OLED using `mini_oled`. If the display isn't connected or fails, the system continues without it.
2. The main loop continuously:
   - Reads soil moisture and computes a dryness percentage.
   - Triggers the red LED and a pulsing buzzer alarm if soil is too dry (>60%).
   - Reads air temperature/humidity from the DHT11 (if present).
   - Automatically actuates the servo to run a pump when humidity is too low (<40%), and stops when it recovers (>60%).
   - Updates the OLED with the current mode's readings (soil or air), toggled by the touch button.
   - Prints status to the serial console for debugging.

## Setup

1. Install CircuitPython on the Metro M0 Express.
2. Copy `code.py` to the root of the `CIRCUITPY` drive.
3. Copy `lib/mini_oled.mpy` (preferred) or `lib/mini_oled.py` into the `lib/` folder on the device.
4. If using the DHT11 sensor, ensure the `adafruit_dht` library is also present in `lib/`.
5. Wire up components per the pin mapping above.
6. Power on — the board will run `code.py` automatically.

To verify OLED wiring independently, run `restartOLED.py` instead of `code.py` (requires the standard `adafruit_displayio_ssd1306` and `adafruit_display_text` libraries in `lib/`).
