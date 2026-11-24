#!/usr/bin/env python3
"""Build the 24 Nov 2026 world-news front page as one 1024x1024 image.

The panel artwork lives in assets/ (text-free, generated for this entry).
This script composites it into a newspaper front page: masthead with the
date, one hero panel, six captioned story panels and a news ticker along
the bottom. The result is written to entry.png (JPEG bytes) at the repo
root. The build is deterministic: same inputs, same output bytes.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUT = ROOT / "entry.png"

W = H = 1024
MARGIN = 12
GAP = 8

BG = (9, 20, 38)            # dark navy page
GOLD = (212, 175, 55)
WHITE = (255, 255, 255)
BAR = (0, 0, 0, 190)        # semi-transparent caption bar
TICKER_BG = (122, 18, 32)   # deep red ticker strip
BORDER = (140, 160, 190)    # thin light panel border

# Vertical crop focus per panel (0 = top of art, 1 = bottom)
ANCHORS = {
    "nvidia": 0.45,
    "merkury": 0.50,
    "denmark": 0.50,
    "candy": 0.50,
    "fifa": 0.45,
    "trump": 0.50,
    "gaza": 0.50,
}

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

CAPTIONS = {
    "nvidia": "HUANG IS BACK - NVIDIA SOARS 31% IN A DAY, ADDING "
              "$952 BILLION AS TECH STOCKS ROAR BACK",
    "merkury": "ZELENSKYY CONFIRMS UKRAINIAN SEA DRONES SANK "
               "RUSSIAN CORVETTE OFF LIBYA",
    "denmark": "DENMARK'S TOP COURT BACKS 'GHETTO LAW' EVICTIONS "
               "IN IMMIGRATION HARD LINE",
    "candy": "34 WORKERS STILL MISSING AFTER DEADLY CANDY FACTORY "
             "FIRE IN INDONESIA",
    "fifa": "FIFA CONFIRMS 2031 WOMEN'S WORLD CUP FOR US, MEXICO, "
            "COSTA RICA AND JAMAICA",
    "trump": "TRUMP GETS PATH TO ERASE HUSH MONEY CONVICTION",
    "gaza": "OXFAM: GAZA'S AIR, SOIL AND WATER POISONED FOR DECADES",
}
TICKER = ("ALSO TODAY - O'HARE GROUND STOP SNARLS THANKSGIVING "
          "TRAVEL \u00b7 US SANCTIONS DOZENS OF IRANIAN EXCHANGE "
          "HOUSES")


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    """Greedy word-wrap to pixel width; returns list of lines."""
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit(img, w, h, anchor_y=0.5):
    """Scale image to cover (w, h) and crop, anchor_y 0=top .. 1=bottom."""
    scale = max(w / img.width, h / img.height)
    nw, nh = round(img.width * scale), round(img.height * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    x = (nw - w) // 2
    y = int((nh - h) * anchor_y)
    return img.crop((x, y, x + w, y + h))


def caption_bar(draw, box, text, size):
    """Draw a semi-transparent black bar at the bottom of box with text."""
    x0, y0, x1, y1 = box
    fnt = font(FONT_BOLD, size)
    lines = wrap(draw, text, fnt, (x1 - x0) - 20)
    line_h = int(size * 1.28)
    bar_h = line_h * len(lines) + 14
    bar_y = y1 - bar_h
    draw.rectangle([x0, bar_y, x1, y1], fill=BAR)
    ty = bar_y + 7
    for line in lines:
        draw.text((x0 + 10, ty), line, font=fnt, fill=WHITE)
        ty += line_h


def panel(canvas, draw, name, box, cap_size):
    x0, y0, x1, y1 = box
    art = Image.open(ASSETS / f"{name}.webp").convert("RGB")
    canvas.paste(fit(art, x1 - x0, y1 - y0, ANCHORS.get(name, 0.5)),
                 (x0, y0))
    draw.rectangle(box, outline=BORDER, width=2)
    caption_bar(draw, box, CAPTIONS[name], cap_size)


def tracked(draw, cx, y, text, fnt, tracking, fill):
    """Draw centered text with letter tracking; returns total width."""
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, wch in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += wch + tracking
    return total


def main():
    canvas = Image.new("RGBA", (W, H), BG + (255,))
    draw = ImageDraw.Draw(canvas, "RGBA")

    # --- Masthead -------------------------------------------------------
    tracked(draw, W / 2, 12, "THE WORLD IN ONE DAY", font(FONT_BOLD, 25),
            7, GOLD)
    date_fnt = font(FONT_BOLD, 54)
    date = "TUESDAY 24 NOVEMBER 2026"
    dw = draw.textlength(date, font=date_fnt)
    draw.text(((W - dw) / 2, 46), date, font=date_fnt, fill=WHITE)
    draw.rectangle([MARGIN, 112, W - MARGIN, 115], fill=GOLD)

    inner_w = W - 2 * MARGIN            # 1000
    col_w = (inner_w - GAP) // 2        # 496

    # --- Hero ------------------------------------------------------------
    hero = (MARGIN, 124, W - MARGIN, 452)
    panel(canvas, draw, "nvidia", hero, 27)

    # --- Grid: merkury / denmark, candy / fifa ---------------------------
    rows = [(460, 630), (638, 808)]
    grid = [["merkury", "denmark"], ["candy", "fifa"]]
    for (gy0, gy1), row in zip(rows, grid):
        for i, name in enumerate(row):
            x0 = MARGIN + i * (col_w + GAP)
            panel(canvas, draw, name, (x0, gy0, x0 + col_w, gy1), 24)

    # --- Bottom row: trump / gaza ----------------------------------------
    for i, name in enumerate(["trump", "gaza"]):
        x0 = MARGIN + i * (col_w + GAP)
        panel(canvas, draw, name, (x0, 816, x0 + col_w, 948), 24)

    # --- Ticker ------------------------------------------------------------
    draw.rectangle([0, 956, W, H], fill=TICKER_BG + (255,))
    draw.rectangle([0, 956, W, 959], fill=GOLD)
    tfnt = font(FONT_BOLD, 22)
    lines = wrap(draw, TICKER, tfnt, W - 28)
    line_h = int(22 * 1.3)
    ty = 956 + (68 - line_h * len(lines)) // 2 + 2
    for line in lines:
        lw = draw.textlength(line, font=tfnt)
        draw.text(((W - lw) / 2, ty), line, font=tfnt, fill=WHITE)
        ty += line_h

    out = canvas.convert("RGB")
    out.save(OUT, format="JPEG", quality=88)
    print(f"wrote {OUT} {OUT.stat().st_size} bytes")


if __name__ == "__main__":
    main()
