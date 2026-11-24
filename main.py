#!/usr/bin/env python3
"""Entrypoint for the news-image-20261124 make.fun entry.

Copies the built front page (``entry.png``, shipped next to this file)
into the output directory and verifies the copy byte for byte.

The grader runs this as ``python3 -P -s main.py`` with no network on a
read-only repository: the only writable place is the output directory,
given by the ``MAKEFUN_OUTPUT_DIR`` environment variable (or
``--output-dir``). The output is deterministic: the same input always
produces the same bytes, because this script copies a fixed file and
writes nothing else.
"""

import argparse
import hashlib
import json
import os
import struct
import sys
from pathlib import Path

SOURCE_NAME = "entry.png"
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024
MAX_BYTES = 1 << 20  # 1 MiB cap, matching the bounty rules
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Copy entry.png into the output directory.")
    parser.add_argument(
        "--output-dir", default=None,
        help="Output directory (default: $MAKEFUN_OUTPUT_DIR or ./output)")
    parser.add_argument(
        "--verify-only", action="store_true",
        help="Only check the shipped entry.png; write nothing")
    return parser.parse_args(argv)


def resolve_output_dir(args):
    if args.output_dir:
        return Path(args.output_dir)
    env = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if env:
        return Path(env)
    return Path("output")


def png_dimensions(data):
    """Read (width, height) from a PNG's IHDR chunk, stdlib only.

    No image library is needed: the first 8 bytes are the magic, then
    a 4-byte length, the 4-byte chunk type "IHDR", then width and
    height as big-endian 32-bit integers.
    """
    if len(data) < 29 or data[12:16] != b"IHDR":
        raise ValueError("missing IHDR chunk")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv=None):
    args = parse_args(argv)
    here = Path(__file__).resolve().parent
    source = here / SOURCE_NAME
    out_dir = resolve_output_dir(args)
    target = out_dir / SOURCE_NAME

    if not source.is_file():
        print(f"error: source image not found: {source}", file=sys.stderr)
        return 1
    if not args.verify_only:
        out_dir.mkdir(parents=True, exist_ok=True)
        if target.resolve() == source.resolve():
            print("error: output directory is the repository itself; "
                  "refusing to copy the file onto itself", file=sys.stderr)
            return 1
    data = source.read_bytes()
    if len(data) > MAX_BYTES:
        print(f"error: {SOURCE_NAME} is {len(data)} bytes, over the "
              f"{MAX_BYTES} byte cap", file=sys.stderr)
        return 1
    if not data.startswith(PNG_MAGIC):
        print(f"error: {SOURCE_NAME} is not a PNG file", file=sys.stderr)
        return 1
    try:
        width, height = png_dimensions(data)
    except ValueError as exc:
        print(f"error: {SOURCE_NAME} is not a readable PNG: {exc}",
              file=sys.stderr)
        return 1
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        print(f"error: {SOURCE_NAME} is {width}x{height}, expected "
              f"{EXPECTED_WIDTH}x{EXPECTED_HEIGHT}", file=sys.stderr)
        return 1

    source_hash = hashlib.sha256(data).hexdigest()
    if args.verify_only:
        print(json.dumps({
            "file": SOURCE_NAME,
            "bytes": len(data),
            "width": width,
            "height": height,
            "sha256": source_hash,
            "status": "ok",
        }))
        return 0

    # Write atomically: a reader never sees a half-written file, and
    # fsync makes the copy durable before we report success.
    tmp = target.with_suffix(".tmp")
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, target)

    copy_hash = sha256_file(target)
    if copy_hash != source_hash:
        print("error: copy failed verification (sha256 mismatch)",
              file=sys.stderr)
        return 1

    print(json.dumps({
        "file": SOURCE_NAME,
        "bytes": len(data),
        "width": width,
        "height": height,
        "sha256": source_hash,
        "output": str(target),
        "status": "ok",
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
