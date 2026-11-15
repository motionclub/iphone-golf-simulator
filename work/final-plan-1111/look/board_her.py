#!/usr/bin/env python3
"""board_her.py <out.jpg>: her in every outfit as the game renders her today (game-shader turnaround stills, look/turnaround_new)."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
OUT = sys.argv[1]; L = os.path.dirname(os.path.abspath(__file__))
def font(n, bold=False):
    try: return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", n, index=1 if bold else 0)
    except Exception: return ImageFont.load_default()
PAD, GAP, CW, CH = 18, 10, 228, 304
def fit(path, w, h):
    im = Image.open(os.path.join(L, "turnaround_new", path)).convert("RGB"); s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS); x, y = (im.width - w) // 2, (im.height - h) // 2; return im.crop((x, y, x + w, y + h))
KITS = [("Tennis: tank, skirt, socks, shoes, cap", "MatchHero_Female"), ("Golf: polo, skort, belt, glove, shoes, cap", "GolfKitHero_Female"), ("Bowling: shirt, cropped trousers, socks, shoes, cap", "BowlingKitHero_Female")]
SHOTS = [("ready_full_front", "front"), ("ready_full_front_left", "three-quarter"), ("ready_full_left", "side"), ("ready_full_back", "back"), ("ready_top_front", "top"), ("ready_bottom_front", "bottom"), ("ready_shoes_front", "shoes")]
REST = [("rest_full_front", "standing, front"), ("rest_full_left", "standing, side"), ("rest_full_back", "standing, back"), ("rest_top_back", "top, back"), ("ready_shoes_left", "shoes, side"), ("ready_face_front", "face"), ("ready_face_three_quarter", "face, three-quarter")]
W = PAD * 2 + 7 * CW + 6 * GAP; H = 64 + len(KITS) * (36 + 2 * (CH + 28) + 8) + 20
im = Image.new("RGB", (W, H), "#fcfcfb"); d = ImageDraw.Draw(im)
d.text((PAD, 18), "Her in every outfit, as the game renders her today  (game shaders, studio backdrop, 2026-11-12)", font=font(24, True), fill="#0b0b0b")
y = 64
for title, hero in KITS:
    d.text((PAD, y), title, font=font(19, True), fill="#0b0b0b"); y += 34
    for shots in (SHOTS, REST):
        for k, (s, lab) in enumerate(shots):
            x = PAD + k * (CW + GAP); p = f"{hero}/{s}.png"
            if os.path.exists(os.path.join(L, "turnaround_new", p)): im.paste(fit(p, CW, CH), (x, y))
            d.text((x + 2, y + CH + 5), lab, font=font(15), fill="#0b0b0b")
        y += CH + 28
    y += 10
im.save(OUT, quality=90); print(OUT, im.size)
