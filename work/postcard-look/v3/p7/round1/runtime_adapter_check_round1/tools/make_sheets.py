#!/usr/bin/env python3
"""POSTCARD_LOOK area I contact sheets (Game-view stills; nothing is written to ArtDir/screenshots):
  proof/sheet_hole08.jpg|09|10   reference still | tee | approach | landmark
  proof/sheet_all.jpg            the nine stills, rows = holes, columns = tee / approach / landmark
"""
import os
from PIL import Image, ImageDraw, ImageFont

R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
P = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v3/p7/round1/runtime_adapter_check_round1'
ART = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v3/p7/round1/runtime_adapter_check_round1/stills'
REF = R + "/ArtDir/environments/refs"
HOLES = [("08", "needle.jpg", ["hole08_1_tee", "hole08_2_approach", "hole08_3_arch"], "Hole 8 Needle", ["tee", "approach", "landmark: arch"]),
         ("09", "split.jpg", ["hole09_1_tee", "hole09_2_approach", "hole09_3_ruin"], "Hole 9 Split", ["tee", "approach", "landmark: ruin ridge"]),
         ("10", "crater.jpg", ["hole10_1_tee", "hole10_2_approach", "hole10_3_lavarim"], "Hole 10 Crater", ["tee", "approach", "landmark: lava rim"])]
try:
    F = ImageFont.load_default(size=22)
except TypeError:
    F = ImageFont.load_default()


def fit_h(im, h):
    return im.resize((int(round(im.width * h / im.height)), h), Image.LANCZOS)


def label(im, text):
    d = ImageDraw.Draw(im)
    w = d.textlength(text, font=F)
    d.rectangle([0, 0, w + 16, 34], fill=(0, 0, 0))
    d.text((8, 5), text, fill=(255, 255, 255), font=F)
    return im


def main():
    HGT = 800
    rows = []
    for n, ref, shots, title, names in HOLES:
        ims = [label(fit_h(Image.open(f"{REF}/{ref}").convert("RGB"), HGT), f"{title}: target {ref}")]
        for s, nm in zip(shots, names):
            p = f"{ART}/{s}.png"
            ims.append(label(fit_h(Image.open(p).convert("RGB"), HGT), f"{s} ({nm})") if os.path.exists(p) else Image.new("RGB", (450, HGT), (60, 0, 0)))
        gap = 12
        sheet = Image.new("RGB", (sum(i.width for i in ims) + gap * (len(ims) - 1), HGT), (24, 24, 24))
        x = 0
        for i in ims:
            sheet.paste(i, (x, 0)); x += i.width + gap
        sheet.save(f"{P}/sheet_hole{n}.jpg", quality=88)
        rows.append(ims[1:])
        print("wrote", f"sheet_hole{n}.jpg", sheet.size)
    T = 640
    grid_rows = []
    for r in rows:
        ims = [fit_h(i, T) for i in r]
        grid_rows.append(ims)
    gap = 10
    W_ = sum(i.width for i in grid_rows[0]) + gap * 2
    sheet = Image.new("RGB", (W_, T * 3 + gap * 2), (24, 24, 24))
    for ri, ims in enumerate(grid_rows):
        x = 0
        for i in ims:
            sheet.paste(i, (x, ri * (T + gap))); x += i.width + gap
    sheet.save(f"{P}/sheet_all.jpg", quality=88)
    print("wrote sheet_all.jpg", sheet.size)


if __name__ == "__main__":
    main()
