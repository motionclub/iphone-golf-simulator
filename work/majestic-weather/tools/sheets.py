#!/usr/bin/env python3
"""sheets.py <run dir> [<out dir>] — REF_MATCH sheets: per weather ref, target | today (legacy WeatherView) | Majestic,
from the harness's 1920x1080 stills (<id>_legacy.png, <id>_majestic.png). Also all.jpg (one row per slot) and
per-slot 1920x1080 side-by-side pairs (<id>_pair.jpg: target left, Majestic right) for Adnan's eye."""
import glob, os, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
REFS = os.path.join(ROOT, "work/majestic-all-maps/refs/weather")
NAMES = {
    "W01": "rain h07", "W02": "rain clearing h08", "W03": "thunderstorm h13", "W04": "sea fog h15", "W05": "gusty h20",
    "W06": "snow h17", "W07": "blizzard h17", "W08": "freezing fog h17", "W09": "ashfall h22", "W10": "eruption h23",
    "W11": "volcanic smoke h21", "W12": "tennis resort rain", "W13": "tennis resort sea fog", "W14": "tennis skyscraper storm",
    "W15": "tennis skyscraper gusty", "W16": "tennis volcano smoke", "X10": "h10 storm (ash family now)", "X16": "h16 rain (ash family now)",
}


def font(size):
    for f in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def fit(img, w, h):
    iw, ih = img.size
    s = max(w / iw, h / ih)
    img = img.resize((round(iw * s), round(ih * s)), Image.LANCZOS)
    l, t = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((l, t, l + w, t + h))


def label(img, text, size=26):
    d = ImageDraw.Draw(img); f = font(size)
    box = d.textbbox((0, 0), text, font=f)
    d.rectangle((0, 0, box[2] + 16, box[3] + 12), fill=(18, 18, 22))
    d.text((8, 4), text, font=f, fill=(255, 255, 255))
    return img


def ref_for(slot):
    hits = glob.glob(os.path.join(REFS, slot + "_*.jpg"))
    return Image.open(hits[0]).convert("RGB") if hits else None


def main():
    run = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(run, "sheets")
    os.makedirs(out, exist_ok=True)
    slots = sorted({os.path.basename(p).split("_")[0] for p in glob.glob(os.path.join(run, "*_majestic.png"))})
    cw, ch = 640, 360
    rows = []
    for s in slots:
        ref = ref_for(s)
        cells = []
        for title, img in (("target " + s, ref), ("today", os.path.join(run, s + "_legacy.png")), ("Majestic weather", os.path.join(run, s + "_majestic.png"))):
            if isinstance(img, str):
                img = Image.open(img).convert("RGB") if os.path.exists(img) else None
            cell = fit(img, cw, ch) if img else Image.new("RGB", (cw, ch), (40, 40, 44))
            cells.append(label(cell, f"{title} · {NAMES.get(s, '')}" if title.startswith("target") else title, 20))
        row = Image.new("RGB", (cw * 3, ch), (0, 0, 0))
        for i, c in enumerate(cells):
            row.paste(c, (i * cw, 0))
        row.save(os.path.join(out, f"{s}_sheet.jpg"), quality=88)
        rows.append(row)
        mj = os.path.join(run, s + "_majestic.png")
        if ref and os.path.exists(mj):
            pair = Image.new("RGB", (1920, 540), (0, 0, 0))
            pair.paste(label(fit(ref, 960, 540), "target " + s + " · " + NAMES.get(s, ""), 22), (0, 0))
            pair.paste(label(fit(Image.open(mj).convert("RGB"), 960, 540), "in game (Majestic weather, 1920x1080 frame)", 22), (960, 0))
            pair.save(os.path.join(out, f"{s}_pair.jpg"), quality=88)
    if rows:
        allimg = Image.new("RGB", (cw * 3, ch * len(rows)), (0, 0, 0))
        for i, r in enumerate(rows):
            allimg.paste(r, (0, i * ch))
        allimg.save(os.path.join(out, "all.jpg"), quality=85)
    print(out, slots)


if __name__ == "__main__":
    main()
