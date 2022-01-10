import json
import time

import board
import busio
import displayio
import terminalio

from adafruit_bitmap_font import bitmap_font
# https://circuitpython.readthedocs.io/projects/display-shapes/
from adafruit_display_shapes import rect
from adafruit_display_text import wrap_text_to_pixels
import adafruit_display_text.bitmap_label as label
from adafruit_displayio_layout.layouts.grid_layout import GridLayout
# https://circuitpython.readthedocs.io/projects/hid/
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
# https://docs.python.org/3/library/functions.html#getattr
# getattr(Keycode, "CAPS_LOCK") == Keycode.CAPS_LOCK
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse
import adafruit_il0373
from adafruit_itertools import adafruit_itertools as itertools
import adafruit_neokey.neokey1x4 as neokey
from adafruit_seesaw import seesaw, neopixel, rotaryio, digitalio
# TODO: Adjust LED brightness based on ambient light sensor?
# https://learn.adafruit.com/adafruit-vcnl4040-proximity-sensor/python-circuitpython
# import adafruit_vcnl4040

from rainbowio import colorwheel

import usb_hid

start = time.monotonic()

print("Starting up at %.2f..." % (start))

with open("default.json", "r") as config_file:
    config = json.load(config_file)

print("[%.2f] Config file read" % (time.monotonic() - start))

print(config)

DISPLAY_ROTATION: 0|90|180|270 = config['rotation']
DISPLAY_INTRINSIC_WIDTH: int = 128
DISPLAY_INTRINSIC_HEIGHT: int = 296

FONT = config['font']

# Modified Nintendo DS fonts, from https://github.com/quiple/galmuri
# FONT = "Galmuri9"
# FONT = "Galmuri11"
# FONT = "Galmuri11-Bold"

# Modified Chicago BDF font, from https://github.com/danfe/fonts
# FONT = "Chicago-12"
# Other font ideas:
# - Playdate Sans

LED_COLOUR = int(config['led_colour'])
LED_BRIGHTNESS = float(config['led_brightness'])

# i2c Peripheral Setup
i2c = board.I2C()
neokey_a = neokey.NeoKey1x4(i2c, addr=0x30)
neokey_a.pixels.brightness = LED_BRIGHTNESS
neokey_a.pixels[0] = LED_COLOUR
print("[%.2f] NeoKey A ready" % (time.monotonic() - start))

neokey_b = neokey.NeoKey1x4(i2c, addr=0x31)
neokey_b.pixels.brightness = LED_BRIGHTNESS
neokey_b.pixels[0] = LED_COLOUR
print("[%.2f] NeoKey B ready" % (time.monotonic() - start))

neokeys = [neokey_a, neokey_b]

seesawio = seesaw.Seesaw(i2c, 0x36)

# proximity_sensor = adafruit_vcnl4040.VCNL4040(i2c)

neokey_a.pixels[1] = LED_COLOUR
print("[%.2f] i2c peripherals ready" % (time.monotonic() - start))

# Rotary Encoder Dial Setup
dial = rotaryio.IncrementalEncoder(seesawio)
seesawio.pin_mode(24, seesawio.INPUT_PULLUP)
dial_press = digitalio.DigitalIO(seesawio, 24)
dial_pixel = neopixel.NeoPixel(seesawio, 6, 1)
dial_pixel.brightness = LED_BRIGHTNESS

neokey_b.pixels[1] = LED_COLOUR
print("[%.2f] Rotary Encoder ready" % (time.monotonic() - start))

displayio.release_displays()

neokey_a.pixels[2] = LED_COLOUR
print("[%.2f] Displays released" % (time.monotonic() - start))

# USB HID Setup
mouse = Mouse(usb_hid.devices)
keyboard = Keyboard(usb_hid.devices)
keyboard_layout = KeyboardLayoutUS(keyboard)
consumer_control = ConsumerControl(usb_hid.devices)

neokey_b.pixels[2] = LED_COLOUR
print("[%.2f] USB HID ready" % (time.monotonic() - start))

last_position = None
colour = 0  # start at red

# Display Setup
display_bus = displayio.FourWire(busio.SPI(board.SCK, board.MOSI),
                                 command=board.D10,
                                 chip_select=board.D9,
                                 baudrate=1000000)

# TODO: This sleep seems to be before the display is drawn, not initiated, so we can probably guard it differently
time.sleep(1)

neokey_a.pixels[3] = LED_COLOUR
print("[%.2f] FourWire display protocol ready" % (time.monotonic() - start))

# Handle display rotation; we'll use the display routines in native orientation
# and adjust our layout based on it
display_width, display_height = (DISPLAY_INTRINSIC_WIDTH, DISPLAY_INTRINSIC_HEIGHT) if DISPLAY_ROTATION / 90 % 2 == 0 else (DISPLAY_INTRINSIC_HEIGHT, DISPLAY_INTRINSIC_WIDTH)

display = adafruit_il0373.IL0373(display_bus,
                                 width=display_width,
                                 height=display_height,
                                 rotation=DISPLAY_ROTATION,
                                 black_bits_inverted=False,
                                 color_bits_inverted=False,
                                 grayscale=True,
                                 refresh_time=1)

neokey_b.pixels[3] = LED_COLOUR
print("[%.2f] IL0373 e-ink display ready" % (time.monotonic() - start))

group = displayio.Group()

background = rect.Rect(0, 0, # x, y
                       display.width,
                       display.height,
                       fill=0xffffff,
                       stroke=0)
group.append(background)

# pic = displayio.OnDiskBitmap("display-ruler.bmp")
# tilegrid = displayio.TileGrid(pic, pixel_shader=pic.pixel_shader)
# group.append(tilegrid)

print("[%.2f] Background drawn" % (time.monotonic() - start))

# GridLayout: https://github.com/adafruit/Adafruit_CircuitPython_DisplayIO_Layout/blob/main/adafruit_displayio_layout/layouts/grid_layout.py
class KeyLayout(GridLayout):
    # TODO: Make these classes so they can hold more useful info
    # NOTE: (Column, Row)
    KEY_A0 = (0, 0)
    KEY_A1 = (1, 0)
    KEY_A2 = (2, 0)
    KEY_A3 = (3, 0)
    KEY_B0 = (0, 2)
    KEY_B1 = (1, 2)
    KEY_B2 = (2, 2)
    KEY_B3 = (3, 2)
    DIAL_CLOCKWISE = (3, 1)
    DIAL_COUNTERCLOCKWISE = (1, 1)
    DIAL_PRESS = (2, 1)

    def __init__(self, width: int, height: int, rotation: 0|90|180|270 = 0, cell_padding = 0):
        grid_size = (4, 3) if rotation / 90 % 2 == 1 else (3, 4)

        super().__init__(x=0, y=0, width=width, height=height,
                         grid_size=grid_size,
                         cell_anchor_point=(0.5, 0.5),
                         cell_padding=cell_padding,
                         divider_lines=True,
                         divider_line_color=0x999999)

        self.rotation = rotation
        self.grid_size = grid_size

    def add_content_for(self, key, content):
        self.add_content(content,
                         grid_position=key,
                         cell_size=(1, 1))

layout = KeyLayout(width=display.width,
                   height=display.height,
                   rotation=display.rotation)

group.append(layout)

print("[%.2f] Layout initialised" % (time.monotonic() - start))

try:
    font = bitmap_font.load_font("fonts/{}.bdf".format(FONT))
except OSError:
    print("Failed to load font \"{}\", falling back to built-in font".format(FONT))
    font = terminalio.FONT

print("[%.2f] Font loaded" % (time.monotonic() - start))

# TODO: Word wrap https://circuitpython.readthedocs.io/projects/display_text/en/latest/examples.html#wrap-pixel-test
#       Maybe make an automatically word-wrapping label class?
label_a = label.Label(font=font,
                      # text="...hi :^)\n{}".format(time.monotonic()),
                      text="\n".join(wrap_text_to_pixels("Navigation / Zoom", 74, font)),
                      color=0x333333,
                      anchor_point=(0.5, 0.5),
                      base_alignment=True)

print("[%.2f] Label A created" % (time.monotonic() - start))

layout.add_content_for(KeyLayout.KEY_A0, label_a)

print("[%.2f] Label A added to group" % (time.monotonic() - start))

label_b = label.Label(font=font,
                      text="\n".join(wrap_text_to_pixels("Current Job", 74, font)),
                      color=0x333333,
                      anchor_point=(0.5, 0.5),
                      base_alignment=True)

print("[%.2f] Label B created" % (time.monotonic() - start))

layout.add_content_for(KeyLayout.KEY_A1, label_b)

print("[%.2f] Label B added to group" % (time.monotonic() - start))

label_c = label.Label(font=font,
                      text="\n".join(wrap_text_to_pixels("Diagnostics & Call", 74, font)),
                      color=0x333333,
                      anchor_point=(0.5, 0.5),
                      base_alignment=True)

layout.add_content_for(KeyLayout.KEY_A2, label_c)

label_d = label.Label(font=font,
                      text="\n".join(wrap_text_to_pixels("Messages", 74, font)),
                      color=0x222222,
                      anchor_point=(0.5, 0.5),
                      base_alignment=True)

layout.add_content_for(KeyLayout.KEY_A3, label_d)

label_dial_clockwise = label.Label(font=font,
                                   text="\n".join(wrap_text_to_pixels("Radio Next", 74, font)),
                                   color=0x333333,
                                   anchor_point=(0.5, 0.5),
                                   base_alignment=True)

layout.add_content_for(KeyLayout.DIAL_CLOCKWISE,
                       label_dial_clockwise)

label_dial_press = label.Label(font=font,
                               text="\n".join(wrap_text_to_pixels("Radio Menu", 74, font)),
                               color=0x333333,
                               anchor_point=(0.5, 0.5),
                               base_alignment=True)

layout.add_content_for(KeyLayout.DIAL_PRESS,
                       label_dial_press)

label_dial_counterclockwise = label.Label(font=font,
                                          text="\n".join(wrap_text_to_pixels("Radio Previous", 74, font)),
                                          color=0x333333,
                                          anchor_point=(0.5, 0.5),
                                          base_alignment=True)

layout.add_content_for(KeyLayout.DIAL_COUNTERCLOCKWISE,
                       label_dial_counterclockwise)

label_empty = label.Label(font=font,
                          text="",
                          color=0x333333,
                          anchor_point=(0.5, 0.5),
                          base_alignment=True)

# TODO: Automatically ensure unpopulated cells are drawn anyway
layout.add_content_for((0, 1), label_empty)

label_w = label.Label(font=font,
                      text="\n".join(wrap_text_to_pixels("ESC", 74, font)),
                      color=0x333333,
                      anchor_point=(0.5, 0.5),
                      base_alignment=True)

layout.add_content_for(KeyLayout.KEY_B0, label_w)

label_x = label.Label(font=font,
                      text="\n".join(wrap_text_to_pixels("Enter", 74, font)),
                      color=0x333333,
                      anchor_point=(0.5, 0.5),
                      base_alignment=True)

layout.add_content_for(KeyLayout.KEY_B1, label_x)

label_y = label.Label(font=font,
                      text="\n".join(wrap_text_to_pixels("Trailer Coupling", 74, font)),
                      color=0x333333,
                      anchor_point=(0.5, 0.5),
                      base_alignment=True)

layout.add_content_for(KeyLayout.KEY_B2, label_y)

label_z = label.Label(font=font,
                      text="\n".join(wrap_text_to_pixels("Engine Start-Stop", 74, font)),
                      color=0x222222,
                      anchor_point=(0.5, 0.5),
                      base_alignment=True)

layout.add_content_for(KeyLayout.KEY_B3, label_z)

dial_pixel.fill(LED_COLOUR)
print("[%.2f] Layout ready" % (time.monotonic() - start))

display.show(group)

display.refresh()

print("[%.2f] Display refreshed" % (time.monotonic() - start))

# Turn off all pixels
dial_pixel.fill(0x0)
for neokey_index, neokey_button in itertools.product(range(2), range(4)):
    neokeys[neokey_index].pixels[neokey_button] = 0x0

print("[%.2f] Entering main loop" % (time.monotonic() - start))

while True:
    # negate the position to make clockwise rotation positive
    position = -dial.position

    if last_position is not None and position != last_position:
        print("Dial (0x36): {}, {}".format(dial_press.value, position))

        if dial_press.value:
            # mouse.move(wheel=position-last_position)

            for _ in range(abs(position-last_position)):
                if position > last_position:
                    if 'consumer_control_code' in config['controls']['dial']['clockwise']:
                        consumer_control.send(getattr(ConsumerControlCode, config['controls']['dial']['clockwise']['consumer_control_code']))
                    elif 'keycode' in config['controls']['dial']['clockwise']:
                        keyboard.send(getattr(Keycode, config['controls']['dial']['clockwise']['keycode']))
                    elif 'write' in config['controls']['dial']['clockwise']:
                        keyboard.write(config['controls']['dial']['clockwise']['write'])
                else:
                    if 'consumer_control_code' in config['controls']['dial']['counter_clockwise']:
                        consumer_control.send(getattr(ConsumerControlCode, config['controls']['dial']['counter_clockwise']['consumer_control_code']))
                    elif 'keycode' in config['controls']['dial']['counter_clockwise']:
                        keyboard.send(getattr(Keycode, config['controls']['dial']['counter_clockwise']['keycode']))
                    elif 'write' in config['controls']['dial']['counter_clockwise']:
                        keyboard_layout.write(config['controls']['dial']['counter_clockwise']['write'])

            # Change the LED colour.
            # if position > last_position:  # Advance forward through the colorwheel.
            #     colour += 1
            # else:
            #     colour -= 1  # Advance backward through the colorwheel.
            # colour = (colour + 256) % 256  # wrap around to 0-256
            # print(hex(colorwheel(colour)))
            # dial_pixel.fill(colorwheel(colour))

        # else:  # If the button is pressed...
        #     # ...change the brightness.
        #     if position > last_position:  # Increase the brightness.
        #         dial_pixel.brightness = min(1.0, dial_pixel.brightness + 0.0025)
        #     else:  # Decrease the brightness.
        #         dial_pixel.brightness = max(0, dial_pixel.brightness - 0.0025)

    if not dial_press.value:
        if 'consumer_control_code' in config['controls']['dial']['press']:
            consumer_control.send(getattr(ConsumerControlCode, config['controls']['dial']['press']['consumer_control_code']))
        elif 'keycode' in config['controls']['dial']['press']:
            keyboard.send(getattr(Keycode, config['controls']['dial']['press']['keycode']))
        elif 'write' in config['controls']['dial']['press']:
            keyboard_layout.write(config['controls']['dial']['press']['write'])

        # print("Brightness: {}".format(dial_pixel.brightness))

    last_position = position

    # Sync brightness of all NeoPixels
    neokey_a.pixels.brightness = dial_pixel.brightness
    neokey_b.pixels.brightness = dial_pixel.brightness

    # TODO: Should NeoPixel brightness be adjusted on a logarithmic scale?

    for board_idx, button_idx in itertools.product(range(len(neokeys)), range(4)):
        this_neokey = neokeys[board_idx]

        if this_neokey[button_idx]:
            if 'consumer_control_code' in config['controls']['key'][board_idx * 4 + button_idx]:
                consumer_control.send(getattr(ConsumerControlCode, config['controls']['key'][board_idx * 4 + button_idx]['consumer_control_code']))
            elif 'keycode' in config['controls']['key'][board_idx * 4 + button_idx]:
                keyboard.send(getattr(Keycode, config['controls']['key'][board_idx * 4 + button_idx]['keycode']))
            elif 'write' in config['controls']['key'][board_idx * 4 + button_idx]:
                keyboard_layout.write(config['controls']['key'][board_idx * 4 + button_idx]['write'])
            print("NeoKey {} ({}): button {}".format(board_idx, hex(0x30 + board_idx), button_idx))
            this_neokey.pixels[button_idx] = colorwheel(colour)
        else:
            this_neokey.pixels[button_idx] = 0x0

    # print("Proximity: %d, %d lux" % (proximity_sensor.proximity, proximity_sensor.lux))
