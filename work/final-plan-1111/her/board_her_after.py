#!/usr/bin/env python3
"""board_her_after.py <out.jpg>: her as the game renders her today against her with the walk, arm, hand and top-fit changes loaded
in the project copy. Game renders: ../look/turnaround_new (today), turnaround_fit (new), walk_before and f4 (walk films)."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
OUT = sys.argv[1]; L = os.path.dirname(os.path.abspath(__file__))
def font(n, bold=False):
    try: return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", n, index=1 if bold else 0)
    except Exception: return ImageFont.load_default()
PAD, GAP, CW, CH = 18, 10, 264, 352
def fit(path, w, h):
    im = Image.open(os.path.join(L, path)).convert("RGB"); s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS); x, y = (im.width - w) // 2, (im.height - h) // 2; return im.crop((x, y, x + w, y + h))
B, A = "../look/turnaround_new", "turnaround_fit"
rows = [(t, [(f"{B}/{h}/rest_full_front.png", "today"), (f"{A}/{h}/rest_full_front.png", "NEW"), (f"{B}/{h}/rest_top_front.png", "today: top"), (f"{A}/{h}/rest_top_front.png", "NEW: top"), (f"{B}/{h}/ready_full_front_left.png", "today"), (f"{A}/{h}/ready_full_front_left.png", "NEW")])
        for t, h in (("Tennis", "MatchHero_Female"), ("Golf", "GolfKitHero_Female"), ("Bowling", "BowlingKitHero_Female"))]
rows.append(("Walking  (the game's own walk)", [("walk_before/female_tennis_body_005.png", "today"), ("f4/female_tennis_body_005.png", "NEW"), ("walk_before/female_golf_body_016.png", "today"), ("f4/female_golf_body_016.png", "NEW"), ("walk_before/female_bowling_body_026.png", "today"), ("f4/female_bowling_body_026.png", "NEW")]))
W = PAD * 2 + 6 * CW + 5 * GAP; H = 64 + len(rows) * (34 + CH + 30) + 16
im = Image.new("RGB", (W, H), "#fcfcfb"); d = ImageDraw.Draw(im)
d.text((PAD, 18), "Her: today against the changes  (rendered by the game; the changes are loaded in a project copy)", font=font(24, True), fill="#0b0b0b")
y = 64
for title, cells in rows:
    d.text((PAD, y), title, font=font(19, True), fill="#0b0b0b"); y += 34
    for k, (p, lab) in enumerate(cells):
        x = PAD + k * (CW + GAP); im.paste(fit(p, CW, CH), (x, y))
        if lab.startswith("NEW"): d.rectangle((x - 2, y - 2, x + CW + 1, y + CH + 1), outline="#1f6feb", width=3)
        d.text((x + 2, y + CH + 5), lab, font=font(16, lab.startswith("NEW")), fill="#0b0b0b")
    y += CH + 30
im.save(OUT, quality=90); print(OUT, im.size)
