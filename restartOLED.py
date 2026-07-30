from time import sleep

import board
import displayio
import terminalio
from adafruit_display_text import label
from adafruit_displayio_ssd1306 import SSD1306
from i2cdisplaybus import I2CDisplayBus

displayio.release_displays()

i2c = board.I2C()
display_bus = I2CDisplayBus(i2c, device_address=0x3C)
display = SSD1306(display_bus, width=128, height=64)

splash = displayio.Group()
display.root_group = splash

text_area = label.Label(
    terminalio.FONT, text="Metro M0 Active", x=8, y=25, color=0xFFFF
)
splash.append(text_area)

while True:
    sleep(0.1)