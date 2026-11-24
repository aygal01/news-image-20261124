#!/usr/bin/env python3
"""make.fun entrypoint: deliver the finished news image to the output dir.

The repository ships the completed front page as entry.png (composited by
build_image.py from the panel art in assets/). This program copies that
file to entry.png inside the output directory named by MAKEFUN_OUTPUT_DIR
(the grader's convention), falling back to ENTRY_OUTPUT, then /output.
It verifies the copy before reporting success, so two runs with no
network and no clock dependence produce byte-identical output.
"""

import hashlib
import os
import shutil
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / "entry.png"
MAX_BYTES = 1_048_576  # 1 MiB cap for the delivered image
JPEG_MAGIC = b"\xff\xd8"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def looks_like_image(data: bytes) -> bool:
    return data.startswith(JPEG_MAGIC) or data.startswith(PNG_MAGIC)


def output_path() -> Path:
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if out_dir:
        return Path(out_dir) / "entry.png"
    single = os.environ.get("ENTRY_OUTPUT")
    if single:
        return Path(single)
    return Path("/output/entry.png")


def main() -> int:
    if not SOURCE.is_file():
        print(f"error: source image missing: {SOURCE}", file=sys.stderr)
        return 1

    src = SOURCE.read_bytes()
    if len(src) > MAX_BYTES:
        print(f"error: source is {len(src)} bytes, over the 1 MiB cap",
              file=sys.stderr)
        return 1
    if not looks_like_image(src):
        print("error: source is neither JPEG nor PNG", file=sys.stderr)
        return 1

    dest = output_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, dest)

    written = dest.read_bytes()
    if digest(written) != digest(src):
        print("error: written file hash does not match source",
              file=sys.stderr)
        return 1
    if len(written) > MAX_BYTES or not looks_like_image(written):
        print("error: written file failed verification", file=sys.stderr)
        return 1

    print(f"wrote {dest} ({len(written)} bytes, sha256 {digest(written)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
