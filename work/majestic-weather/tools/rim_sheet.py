#!/usr/bin/env python3
"""rim_sheet.py <run dir> — the ball comet-rim variants side by side for Adnan's pick.

Per variant (rows A/B/C): 3x zoom on the ball at address in clear sun (W01 hole, weather off), rain (W01), gusty (W05)
and ash (X16), then frames of the moving ball from W01_rim<v>_move.mp4 (crossing the view, launched down the fairway).
Also a 'before' column (no rim) from proof/bug_after when present. Writes <run>/rim_variants.jpg and rim_moving.jpg."""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

run = sys.argv[1]
FRAMES = "/private/tmp/claude-501/frames"
CROP = (794, 776, 1034, 936)
NAMES = {"A": "A ember", "B": "B comet", "C": "C spark"}


def font(n): return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", n)


def tile(path, label, size=(360, 240)):
    if not os.path.exists(path):
        alt = path[:-4] + (".jpg" if path.endswith(".png") else ".png")
        path = alt if os.path.exists(alt) else None
    im = Image.open(path).convert("RGB").crop(CROP).resize(size, Image.LANCZOS) if path else Image.new("RGB", size, (40, 40, 44))
    d = ImageDraw.Draw(im); f = font(18)
    d.rectangle((0, 0, len(label) * 10 + 12, 26), fill=(18, 18, 22)); d.text((6, 3), label, font=f, fill="white")
    return im


cols = [("W01_rim{v}_clear", "clear sun"), ("W01_rim{v}", "rain"), ("W05_rim{v}", "gusty"), ("X16_rim{v}", "ash h16")]
sheet = Image.new("RGB", (160 + 360 * 4, 40 + 240 * 4), (18, 18, 22)); d = ImageDraw.Draw(sheet)
d.text((10, 8), "Ball comet rim at the iPhone tier (Medium), 3x zoom on the ball at address", font=font(22), fill="white")
before = os.path.join(os.path.dirname(run.rstrip("/")), "bug_after")
for c, (_, lab) in enumerate(cols):
    src = {"clear sun": "W01_clear", "rain": "W01_majestic", "gusty": "W05_majestic", "ash h16": "X16_majestic"}[lab]
    sheet.paste(tile(os.path.join(before, src + ".png"), f"no rim · {lab}"), (160 + c * 360, 40))
d.text((10, 40 + 110), "no rim\n(now)", font=font(20), fill="white")
for r, v in enumerate("ABC"):
    y = 40 + 240 * (r + 1)
    d.text((10, y + 100), NAMES[v], font=font(22), fill="white")
    for c, (pat, lab) in enumerate(cols):
        sheet.paste(tile(os.path.join(run, pat.format(v=v) + ".png"), f"{v} · {lab}"), (160 + c * 360, y))
sheet.save(os.path.join(run, "rim_variants.jpg"), quality=90)

# moving: frames from each variant's clip (rest, crossing, launch)
times = [(.3, "at rest"), (.95, "crossing"), (1.25, "crossing"), (2.35, "launched"), (2.7, "launched")]
mv = Image.new("RGB", (160 + 352 * len(times), 40 + 198 * 3), (18, 18, 22)); d = ImageDraw.Draw(mv)
d.text((10, 8), "Moving ball, rain hole 7, half speed (trail only while it moves fast)", font=font(22), fill="white")
tmp = os.path.join(run, "_frames"); os.makedirs(tmp, exist_ok=True)
for r, v in enumerate("ABC"):
    clip = os.path.join(run, f"W01_rim{v}_move.mp4")
    if not os.path.exists(clip):
        continue
    subprocess.run([FRAMES, clip, os.path.join(tmp, v)] + [str(t) for t, _ in times], check=True)
    d.text((10, 40 + r * 198 + 80), NAMES[v], font=font(22), fill="white")
    for c, (t, lab) in enumerate(times):
        im = Image.open(os.path.join(tmp, f"{v}_{c}.jpg")).resize((352, 198), Image.LANCZOS)
        ImageDraw.Draw(im).text((6, 172), f"{lab} {t:.2f}s", font=font(16), fill="white")
        mv.paste(im, (160 + c * 352, 40 + r * 198))
mv.save(os.path.join(run, "rim_moving.jpg"), quality=88)
print("sheets in", run)
