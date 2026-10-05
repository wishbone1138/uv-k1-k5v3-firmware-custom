#!/usr/bin/env python3
#
# Convert a 128x64 image into the boot-logo blob the firmware expects in the
# PY25Q16 external flash sector at 0x011000 (EEPROM-mapped at 0xC000).
#
# Layout produced (see App/ui/welcome.c):
#
#   [0x000..0x007] 8-byte header, reserved for a future magic/version/flags.
#                  UI_LoadLogo() skips it without reading it, so it is filled
#                  with 0xFF (erased-flash value) unless --header-byte says
#                  otherwise.
#   [0x008..0x407] 1024-byte monochrome bitmap, ST7565-native order:
#                  8 pages * 128 columns, column-major, bit 0 = topmost pixel
#                  of the page. Page 0 is blitted to gStatusLine, pages 1..7
#                  to gFrameBuffer.
#
# A set bit lights the pixel, so dark image pixels become set bits. Use
# --invert for light-on-dark artwork.
#
# Pillow is used when available; otherwise a small built-in decoder handles
# non-interlaced 8-bit PNGs (grayscale, palette, RGB, and their alpha forms),
# which covers what image editors normally emit at this size.

import argparse
import struct
import sys
import zlib

WIDTH = 128
HEIGHT = 64
PAGES = HEIGHT // 8
BITMAP_SIZE = WIDTH * PAGES  # 1024
HEADER_SIZE = 8


def _load_with_pillow(path):
    try:
        from PIL import Image
    except ImportError:
        return None

    with Image.open(path) as im:
        im = im.convert("RGBA")
        if im.size != (WIDTH, HEIGHT):
            raise SystemExit(
                "Image is {}x{}, expected {}x{}".format(
                    im.size[0], im.size[1], WIDTH, HEIGHT
                )
            )
        return list(im.getdata())


def _decode_png(path):
    """Minimal PNG reader: non-interlaced, 8 bits per channel."""
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("{}: not a PNG file".format(path))

    width = height = depth = color = None
    palette = b""
    trns = b""
    idat = bytearray()

    pos = 8
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        ctype = data[pos + 4 : pos + 8]
        body = data[pos + 8 : pos + 8 + length]
        pos += 12 + length  # length + type + body + crc

        if ctype == b"IHDR":
            width, height, depth, color, _, _, interlace = struct.unpack(
                ">IIBBBBB", body
            )
            if interlace:
                raise SystemExit(
                    "Interlaced PNGs are not supported by the built-in decoder; "
                    "install Pillow (pip install pillow) or re-save without interlacing"
                )
            if depth not in (1, 2, 4, 8):
                raise SystemExit(
                    "{}-bit PNGs are not supported by the built-in decoder; "
                    "install Pillow (pip install pillow) or re-save as 8-bit".format(
                        depth
                    )
                )
        elif ctype == b"PLTE":
            palette = body
        elif ctype == b"tRNS":
            trns = body
        elif ctype == b"IDAT":
            idat.extend(body)
        elif ctype == b"IEND":
            break

    if width is None:
        raise SystemExit("{}: no IHDR chunk".format(path))
    if (width, height) != (WIDTH, HEIGHT):
        raise SystemExit(
            "Image is {}x{}, expected {}x{}".format(width, height, WIDTH, HEIGHT)
        )

    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color)
    if channels is None:
        raise SystemExit("Unsupported PNG color type {}".format(color))
    if depth != 8 and color not in (0, 3):
        raise SystemExit(
            "{}-bit color type {} is not valid PNG".format(depth, color)
        )

    raw = zlib.decompress(bytes(idat))
    maxval = (1 << depth) - 1
    # Scanlines are packed; sub-byte depths filter on single-byte distance.
    stride = (width * channels * depth + 7) // 8
    fbpp = max(1, (channels * depth) // 8)
    out = []
    prev = bytearray(stride)

    for y in range(height):
        base = y * (stride + 1)
        filt = raw[base]
        line = bytearray(raw[base + 1 : base + 1 + stride])

        # Undo the per-scanline filter (PNG spec section 9.2).
        for i in range(stride):
            a = line[i - fbpp] if i >= fbpp else 0
            b = prev[i]
            c = prev[i - fbpp] if i >= fbpp else 0
            x = line[i]
            if filt == 0:
                pass
            elif filt == 1:
                x += a
            elif filt == 2:
                x += b
            elif filt == 3:
                x += (a + b) // 2
            elif filt == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                x += a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
            else:
                raise SystemExit("Unknown PNG filter type {}".format(filt))
            line[i] = x & 0xFF

        prev = line

        # Unpack the scanline into one sample per channel per pixel.
        if depth == 8:
            samples = line
        else:
            samples = []
            per_byte = 8 // depth
            for i in range(width * channels):
                byte = line[i // per_byte]
                shift = 8 - depth * (i % per_byte + 1)
                samples.append((byte >> shift) & maxval)

        for x in range(width):
            px = samples[x * channels : (x + 1) * channels]
            if color == 0:
                g = px[0] * 255 // maxval
                out.append((g, g, g, 255))
            elif color == 4:
                out.append((px[0], px[0], px[0], px[1]))
            elif color == 2:
                out.append((px[0], px[1], px[2], 255))
            elif color == 6:
                out.append((px[0], px[1], px[2], px[3]))
            else:  # color == 3, palette
                idx = px[0]
                r, g, b = palette[idx * 3 : idx * 3 + 3]
                alpha = trns[idx] if idx < len(trns) else 255
                out.append((r, g, b, alpha))

    return out


def load_pixels(path):
    pixels = _load_with_pillow(path)
    if pixels is None:
        pixels = _decode_png(path)
    return pixels


def to_bitmap(pixels, threshold, invert):
    lit = []
    for r, g, b, a in pixels:
        # Transparent areas read as background.
        luma = (r * 299 + g * 587 + b * 114) // 1000
        on = a >= 128 and luma < threshold
        lit.append(not on if invert else on)

    bitmap = bytearray(BITMAP_SIZE)
    for page in range(PAGES):
        for col in range(WIDTH):
            byte = 0
            for bit in range(8):
                if lit[(page * 8 + bit) * WIDTH + col]:
                    byte |= 1 << bit
            bitmap[page * WIDTH + col] = byte
    return bitmap


def render(bitmap):
    """ASCII art of the encoded bitmap, to eyeball orientation and polarity."""
    lines = []
    for page in range(PAGES):
        for bit in range(8):
            row = "".join(
                "#" if bitmap[page * WIDTH + col] & (1 << bit) else "."
                for col in range(WIDTH)
            )
            lines.append(row)
    return "\n".join(lines)


def c_array(bitmap, name):
    out = [
        "// Generated by tools/logo/png2logo.py -- do not edit by hand.",
        "// 128x64 ST7565-native boot logo: 8 pages * 128 columns, bit 0 = top.",
        "#include <stdint.h>",
        "",
        "const uint8_t {}[{}] = {{".format(name, BITMAP_SIZE),
    ]
    for page in range(PAGES):
        out.append("    // page {}".format(page))
        row = bitmap[page * WIDTH : (page + 1) * WIDTH]
        for i in range(0, WIDTH, 16):
            out.append(
                "    " + " ".join("0x{:02X},".format(b) for b in row[i : i + 16])
            )
    out.append("};")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(
        description="Convert a {}x{} image to the radio's boot-logo blob.".format(
            WIDTH, HEIGHT
        )
    )
    ap.add_argument("input", help="input image (128x64; PNG without Pillow installed)")
    ap.add_argument(
        "-o",
        "--output",
        help="output blob (default: input name with .bin, omit to only preview)",
    )
    ap.add_argument(
        "--threshold",
        type=int,
        default=128,
        metavar="N",
        help="luminance below N counts as ink (0-255, default 128)",
    )
    ap.add_argument(
        "--invert", action="store_true", help="treat light pixels as ink instead"
    )
    ap.add_argument(
        "--no-header",
        action="store_true",
        help="emit the bare 1024-byte bitmap for writing at 0xC008 instead of "
        "the 1032-byte blob for 0xC000",
    )
    ap.add_argument(
        "--header-byte",
        default="0xFF",
        metavar="B",
        help="fill byte for the 8-byte reserved header (default 0xFF)",
    )
    ap.add_argument(
        "--preview", action="store_true", help="print the encoded bitmap as ASCII art"
    )
    ap.add_argument(
        "--c-array",
        metavar="FILE",
        help="also write the bitmap as a C array (for compiling a logo in)",
    )
    ap.add_argument(
        "--c-name",
        default="BITMAP_BootLogo",
        metavar="NAME",
        help="symbol name for --c-array (default BITMAP_BootLogo)",
    )
    args = ap.parse_args()

    pixels = load_pixels(args.input)
    bitmap = to_bitmap(pixels, args.threshold, args.invert)

    if args.preview:
        print(render(bitmap))

    lit = sum(bin(b).count("1") for b in bitmap)
    pct = 100.0 * lit / (WIDTH * HEIGHT)
    print(
        "{}: {} of {} pixels lit ({:.1f}%)".format(
            args.input, lit, WIDTH * HEIGHT, pct
        ),
        file=sys.stderr,
    )
    if pct > 70:
        print(
            "warning: most of the screen is lit -- if this looks like a negative, "
            "re-run with --invert",
            file=sys.stderr,
        )

    if args.c_array:
        open(args.c_array, "w").write(c_array(bitmap, args.c_name))
        print("wrote {} ({})".format(args.c_array, args.c_name), file=sys.stderr)

    out = args.output
    if out is None and not args.preview and not args.c_array:
        out = args.input.rsplit(".", 1)[0] + ".bin"
    if out:
        header = int(args.header_byte, 0)
        if not 0 <= header <= 0xFF:
            raise SystemExit("--header-byte must be a byte value")
        blob = bitmap if args.no_header else bytes([header]) * HEADER_SIZE + bitmap
        open(out, "wb").write(blob)
        print(
            "wrote {} ({} bytes, write at EEPROM 0x{:04X})".format(
                out, len(blob), 0xC008 if args.no_header else 0xC000
            ),
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
