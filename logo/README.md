# Brass Knuckle Gang boot logo

How to put the Brass Knuckle Gang logo on your UV-K1 / UV-K5 V3, from a stock
radio to a logo on boot and as a screensaver.

The logo is **not** part of the firmware. It lives in a separate area of the
radio's external flash memory, so it is uploaded once with its own tool. The
upside is that it survives firmware updates — you only do steps 2 and 3 once,
even if you reflash later.

Total time is about ten minutes.

---

## What you need

- A UV-K1 or UV-K5 V3 radio
- A USB programming cable (USB-C, or a Baofeng/Kenwood style double-jack cable)
- **Chrome, Chromium, or Edge** on the desktop — [UVTools2](https://armel.github.io/uvtools2/)
  uses WebSerial, which Firefox and Safari do not support
- Nothing to install: UVTools2 runs in the browser

---

## Step 0 — Back up your calibration data (strongly recommended)

Each radio is calibrated individually at the factory. If that data is ever
lost, your radio will transmit and receive off-frequency and at the wrong
power. Backing it up takes thirty seconds and it is worth doing before you
flash anything.

1. Connect the radio to your computer with the programming cable, radio
   **turned on**.
2. Open [UVTools2](https://armel.github.io/uvtools2/) and choose **Dump
   Calibration**.
3. Click the button, pick the serial port for your radio, and save the `.dat`
   file somewhere you will not lose it.

Keep that file. UVTools2's **Restore Calibration** can put it back.

---

## Step 1 — Install the firmware

The logo option only exists in firmware built with it enabled, which is what
this repository's releases are.

1. Go to the
   [Releases page](https://github.com/wishbone1138/uv-k1-k5v3-firmware-custom/releases)
   and download the `.bin` file from the newest release — for example
   `nr7y.k1-k5v3.v1.3.1-logo1.bin`.
2. Put the radio into **DFU mode (flash mode)**: turn the radio **off**, hold
   the **PTT** button, and turn it **on** while still holding PTT. The
   flashlight LED lights and the screen stays dark — that is DFU mode.

   > DFU mode is handled by the radio's bootloader, not by this firmware, so
   > if that combination does not work on your radio, check the
   > [documentation site](https://github.com/briand/cw-firmware-docs) for your
   > exact model. Do **not** confuse it with PTT + the **upper side button**,
   > which boots this firmware's hidden menu instead.
3. Connect the programming cable.
4. In [UVTools2](https://armel.github.io/uvtools2/), choose **Flash Firmware**.
5. Select the `.bin` file you downloaded.
6. Click **Flash Firmware** and pick the serial port for your radio.
7. Wait for the progress bar to finish. The radio restarts on its own.

> The release also contains a `.uf2` of the same build, for the drag-and-drop
> UF2 bootloader method. If you are using UVTools2, you want the `.bin`.

> **A CHIRP driver matching this release** is attached to the same release as
> `nr7y.k1-k5v3.chirp.*.py`. If you program this radio with CHIRP, use that
> file — a mismatched driver reads settings from the wrong addresses.

### After flashing, check your POnMsg setting

This firmware adds `LOGO` to the list of power-on display options, which
shifts the position of `NONE` in that list. If your radio was set to
`POnMsg = NONE` before the update, it now reads as `LOGO` — so you may see a
**blank or garbled splash screen** on the first boot. Nothing is broken and no
settings are corrupted. Either continue with the steps below to put a real
logo there, or set `POnMsg` to whatever you prefer using the menu instructions
in step 4.

---

## Step 2 — Download the logo image

Get `brass-knuckle-gang.png` from this folder:

**[⬇ Download brass-knuckle-gang.png](https://raw.githubusercontent.com/wishbone1138/uv-k1-k5v3-firmware-custom/main/logo/brass-knuckle-gang.png)**

Or from the repository: open `logo/brass-knuckle-gang.png` on GitHub and click
the download button.

The image is sized for the radio's display (128 × 64 pixels, its exact
resolution) and is already pure black-and-white, so it needs no cropping,
scaling, or editing — upload it as is.

It is stored as **white artwork on a black background**, which matters for one
setting in the next step.

---

## Step 3 — Upload the logo to the radio

1. Turn the radio **on** (normal mode this time, **not** DFU mode) and connect
   the programming cable.
2. Open [UVTools2](https://armel.github.io/uvtools2/) and choose **Upload
   Logo**.
3. Select the `brass-knuckle-gang.png` file you downloaded.
4. **Turn the invert option on.** Because this image is white-on-black, the
   radio would otherwise draw it as a negative — a dark screen with the
   knuckles and lettering knocked out of it. With invert on, you get solid
   dark artwork on a clear background, which is how it is meant to look.

   > Prefer the bold, dark-screen version? Leave invert off. Both upload
   > equally well — it is purely a matter of taste.
5. Leave the **threshold** slider alone. The image is already pure
   black-and-white, so there is nothing for it to decide. The on-screen
   preview is what the radio will actually display — trust it over the
   original image.
6. Click upload and pick the serial port for your radio.
7. Wait for it to finish.

To confirm it worked, use **Download Logo** — it reads the logo back off the
radio as a PNG. If you get the Brass Knuckle Gang image back, it is stored
correctly.

---

## Step 4 — Show the logo at boot

Set the power-on display mode to `LOGO`.

1. Press the **M** key (menu).
2. Scroll with the **up/down** arrows to **`POnMsg`**.
3. Press **M** to enter it.
4. Scroll to **`LOGO`**.
5. Press **M** to confirm.
6. Press **EXIT** until you are back on the main screen.

Turn the radio off and back on. The Brass Knuckle Gang logo now shows while
the radio starts up, with the backlight on.

The other `POnMsg` options, for reference:

| Setting | Shows at power-on |
|---|---|
| `ALL` | Your message lines, voltage, and the startup sound |
| `SOUND` | Two short beeps, no display |
| `MESSAGE` | Your two custom text lines |
| `VOLTAGE` | Battery voltage |
| `LOGO` | **The uploaded logo** |
| `NONE` | Nothing |

---

## Step 5 — Use the logo as a screensaver

The same logo can fill the screen when the radio goes idle, through the
`SetSav` menu.

1. Press **M**, scroll to **`SetSav`**, press **M**.
2. Pick one of:

| Setting | What it does |
|---|---|
| `OFF` | No screensaver |
| `LOGO` | Shows the uploaded logo, stationary |
| `LOGO+` | Shows the logo, slowly scrolling |
| `MATRIX` | Falling-code animation — does **not** use your logo |

3. Press **M** to confirm, then **EXIT** out.

### The screensaver needs a backlight timeout set

This catches people out. The screensaver appears **when the backlight turns
off**, so it never appears if the backlight never turns off:

- Press **M**, go to **`BLTime`**
- Set it to a **timed value** (a number of seconds)
- If `BLTime` is `OFF` or always-on, the screensaver will never show, no
  matter what `SetSav` says

The screensaver also only appears on the main screen (or the FM radio screen),
and it steps aside immediately when anything happens — a key press, incoming
traffic, or pressing PTT. It will not hide an active conversation from you.

---

## Troubleshooting

**The splash screen is blank, black, or random noise.**
No logo has been uploaded yet, or the upload did not complete. Repeat step 3.
The firmware draws whatever is in that flash area; on a radio that has never
had a logo uploaded, that is empty space.

**The logo looks like a negative — dark screen, artwork knocked out of it.**
The **invert** option was off. Re-upload with it on (step 3).

**`POnMsg` has no `LOGO` option.**
The radio is running firmware built without the logo feature. Reinstall from
this repository's [Releases](https://github.com/wishbone1138/uv-k1-k5v3-firmware-custom/releases)
(step 1). Upstream builds do not include it.

**There is no `SetSav` in the menu.**
Same cause as above — `SetSav` only exists in builds with the screensaver
compiled in.

**The screensaver never appears.**
Check `BLTime` is set to a timed value, not `OFF` or always-on. See step 5.

**UVTools2 cannot see my radio / no serial port is listed.**
Use Chrome, Chromium, or Edge on a desktop — WebSerial does not exist in
Firefox or Safari. Check the cable is seated fully; these jacks need a firm
push. For flashing, the radio must be in DFU mode; for the logo upload, it
must be powered on normally.

**I want the stock logo back.**
`archive/quansheng.stock.logo.png` in this repository is the original
Quansheng boot picture. Upload it the same way, but with **invert off** — that
one is dark artwork on a light background, the opposite of this logo. To turn
the splash off entirely, set `POnMsg` to `NONE`.

---

## Replacing the logo with your own artwork

Any image works — UVTools2 accepts PNG, JPG, and BMP, and will scale and
threshold it for you. For the sharpest result, supply it the way the display
wants it:

- **128 × 64 pixels** exactly
- Pure black and white, no grey — the display has no greyscale
- Bold shapes and thick strokes. Fine detail and thin lines disappear at this
  size, and anti-aliased edges turn into speckle.

To see exactly what the radio will show before uploading anything, this folder
includes a converter:

```sh
python3 logo/png2logo.py my-logo.png --preview
```

It prints the encoded bitmap as ASCII art, pixel for pixel as the radio
renders it, and reports how much of the screen ends up lit. Add `--invert` to
compare both polarities before you commit to one. It needs no dependencies
beyond Python 3, and reads 1-, 2-, 4- and 8-bit PNGs. It can also write the
raw flash blob or a C array (`--help` lists everything), which are useful for
development but not needed for the UVTools2 workflow above.
