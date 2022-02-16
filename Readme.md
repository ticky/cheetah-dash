# Cheetah Dash

Dynamic hotkey dashboard, using off-the-shelf parts

_**NOTE**: This is a work in progress!_

## Hardware

### Components

- 1 × **[Adafruit Feather](https://www.adafruit.com/category/943)**  
  I used a [Feather RP2040](https://www.adafruit.com/product/4884) for its USB-C and speedy chip, but any which support CircuitPython and STEMMA QT ought to work
- 1 × **USB Cable**  
  The exact type depends on your computer and your choice of Feather; I already had a USB-C to USB-C 2.0 cable!
- 1 × **[Adafruit 2.9" Grayscale eInk Display FeatherWing](https://www.adafruit.com/product/4777)**
- 2 × **[Adafruit NeoKey 1x4 QT](https://www.adafruit.com/product/4980)**
- 8 × **Cherry MX-compatible Key Switches**  
  The [Kalih models](https://www.adafruit.com/product/4954) Adafruit sell work just fine for this
- 8 × **Cherry MX-compatible Keycaps**  
  Mine is using [these windowed ones](https://www.adafruit.com/product/5112) but any will do.
  Bear in mind there are RGB LEDs under them!
- 3 × **STEMMA QT Cables**  
  I wound up with three [100mm cables](https://www.adafruit.com/product/4210) but I would suggest getting two 100mm and one [50mm cable](https://www.adafruit.com/product/4399) instead!
- 1 × **[Adafruit QT Rotary Encoder Breakout with NeoPixel](https://www.adafruit.com/product/4991)**  
  Important to note that this doesn't come with a rotary encoder, you'll need to get that separately!
- 1 × **[Rotary Encoder](https://www.adafruit.com/product/377)**

At this time, I do not have a design for an enclosure for this - I built mine into a recycled cardboard box!

### Soldering

Some fairly easy soldering is required for this build;

- Solder headers to the Feather's pins.  
  The Feather itself may not come with enough, but the rest of the components should supply enough if you don't already have some. You'll want the header pins' long end to be on the opposite side of the board to the USB port, connectors and other components.
- Solder the rotary encoder to the rotary encoder breakout.  
  You can read [Adafruit's instructions](https://learn.adafruit.com/adafruit-i2c-qt-rotary-encoder) for this.
- Solder the `A0` address jumper on _one_ of the NeoKey boards  
  Adafruit describe the pins [in these instructions](https://learn.adafruit.com/neokey-1x4-qt-i2c/pinouts#address-jumpers-3098419-13).

### Assembly

Once the soldering is done, the remainder of the assembly is very easy.

1. Plug the **Feather**, with headers attached, into the socket on the underside of the **eInk Display Featherwing**
2. Use the **STEMMA QT Cables** to connect the **Feather**, two **NeoKey 1x4 QTs** and **Rotary Encoder Breakout** via their STEMMA QT connectors.  
   The order in which they are connected does not matter, but in my assembly I connected the **Rotary Encoder Breakout** directly to the **Feather**, and the two **NeoKey 1x4 QTs** followed after that.
3. Connect the **Feather** to your comptuer with your USB cable

And then it's time to move on to software! ☺️

## Software

Because the Feather range generally ship with it, the software for this is written in CircuitPython!

You may need to update to the latest CircuitPython - instructions vary somewhat by Feather board, but [here's the guide for the Feather RP2040](https://learn.adafruit.com/adafruit-feather-rp2040-pico/circuitpython).

### Libraries

You will also need to install these libraries from the [Adafruit CircuitPython Library Bundle](https://learn.adafruit.com/welcome-to-circuitpython/circuitpython-libraries#downloading-the-adafruit-circuitpython-library-bundle-2977982-6);

- `adafruit_bitmap_font/`
- `adafruit_display_shapes/`
- `adafruit_display_text/`
- `adafruit_displayio_layout/`
- `adafruit_hid/`
- `adafruit_il0373.mpy`
- `adafruit_itertools/`
- `adafruit_neokey/`
- `adafruit_seesaw/`

_**NOTE**: If you are on macOS, copying these in Finder may result in them taking up more than the total storage available on your Feather due to Finder metadata - you may need to run `find /Volumes/CIRCUITPY -name '._*' -exec rm {} \;` to remove that excess metadata._

### Fonts

The dashboard can optionally use any `bdf` format bitmap font. Some good options include [Galmuri](https://github.com/quiple/galmuri) and the modified Chicago from [danfe/fonts](https://github.com/danfe/fonts).

Place your preferred font in a `fonts` folder on the `CIRCUITPY` drive, and update `default.json` with its file name.

If your font fails to load for any reason, it will fall back to the built-in font.

### Python Code

Finally, copy `code.py` and `default.json` to the `CIRCUITPY` drive. If everyhing went to plan, LEDs under each key should light up as it gets things set up, and it should then show a series of labels on the eInk screen.

## Configuration

The key mapping and labels are controlled by the `default.json` file.

Each input can have a `label` which is displayed on the screen, and either a `consumer_control_code`, `keycode` or `write` value.

The first two will send the corresponding input as defined in [`adafruit_hid.consumer_control_code.ConsumerControlCode`](adafruit_hid.consumer_control_code.ConsumerControlCode) or [`adafruit_hid.keycode.Keycode`](https://circuitpython.readthedocs.io/projects/hid/en/latest/api.html#adafruit_hid.keycode.Keycode) respectively.

`write` accepts an ASCII string and will type that string as a series of keystrokes when the input is used.
