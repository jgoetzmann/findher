#!/usr/bin/env python3
"""Strip metadata from photographs before they leave the machine.

    python3 scripts/strip_exif.py IMAGE [IMAGE...] --out DIR

Raw camera files carry the GPS of wherever they were taken, including home.
JPEG APPn and comment segments and PNG text and eXIf chunks are dropped. Pixels
are copied byte for byte. No dependencies, so this runs on a fresh machine.
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

JPEG_DROP = set(range(0xE0, 0xF0)) | {0xFE}  # APP0..APP15 and COM
PNG_DROP = {b"tEXt", b"zTXt", b"iTXt", b"eXIf", b"tIME", b"iCCP"}


def strip_jpeg(data: bytes) -> bytes:
    if data[:2] != b"\xff\xd8":
        raise ValueError("not a JPEG")
    out, i = bytearray(b"\xff\xd8"), 2
    while i < len(data) - 1:
        if data[i] != 0xFF:
            out += data[i:]
            break
        marker = data[i + 1]
        if marker == 0xDA:  # start of scan: the rest is pixels
            out += data[i:]
            break
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        if marker not in JPEG_DROP:
            out += data[i:i + 2 + length]
        i += 2 + length
    return bytes(out)


def strip_png(data: bytes) -> bytes:
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    out, i = bytearray(data[:8]), 8
    while i < len(data):
        length = struct.unpack(">I", data[i:i + 4])[0]
        kind = data[i + 4:i + 8]
        if kind not in PNG_DROP:
            out += data[i:i + 12 + length]
        i += 12 + length
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    failed = 0
    for src in args.images:
        raw = src.read_bytes()
        try:
            clean = strip_jpeg(raw) if raw[:2] == b"\xff\xd8" else strip_png(raw)
        except ValueError as err:
            print(f"{src.name}: {err}. Convert it first; this only handles JPEG and PNG.", file=sys.stderr)
            failed += 1
            continue
        dest = args.out / src.name
        dest.write_bytes(clean)
        print(f"{src.name}: {len(raw)} -> {len(clean)} bytes, {len(raw) - len(clean)} stripped")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
