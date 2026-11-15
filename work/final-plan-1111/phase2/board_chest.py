#!/usr/bin/env python3
"""board_chest.py <out.jpg>: the proof board for the male chest (arms hanging). Renders: r9 (base, build), r10/r11 (arms only),
r13 (arms + chest)."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import posed, armfield as af, torso_measure as tm
OUT = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
TGT = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/targets-2026-10-12/tier1/01_male_body_turnaround.jpg"
def font(n, bold=False):
    try: return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", n, index=1 if bold else 0)
    except Exception: return ImageFont.load_default()
CW, CH, GAP, PAD, LAB = 316, 500, 14, 18, 30
def cell(path, box=(95, 70, 665, 972)): return Image.open(os.path.join(HERE, "renders", path)).convert("RGB").crop(box).resize((CW, CH), Image.LANCZOS)
CB = (140, 150, 620, 910)      # the chest close-ups
def target(box):
    im = Image.open(TGT).convert("RGB").crop(box); h = CH; w = round(im.width * h / im.height); im = im.resize((w, h), Image.LANCZOS)
    out = Image.new("RGB", (CW, CH), (166, 166, 166)); out.paste(im.crop((max(0, (w - CW) // 2), 0, max(0, (w - CW) // 2) + min(w, CW), h)), (max(0, (CW - w) // 2), 0)); return out
rows = [
    ("Bare, from the front", [(cell("r9/base_down_bare_upper.png"), "base body"), (cell("r9/build_down_bare_upper.png"), "in the game today"), (cell("r10/muscles_down_bare_upper.png"), "new arms, old chest (last board)"), (cell("r13/chest_down_bare_upper.png"), "NEW: arms + chest"), (target((112, 62, 334, 412)), "target (tier 1)")]),
    ("The chest close up", [(cell("r11/muscles_down_bare_chestfront.png", CB), "old chest"), (cell("r13/chest_down_bare_chestfront.png", CB), "NEW"), (cell("r13/chest_down_bare_chest3q.png", CB), "NEW, three-quarter"), (cell("r11/muscles_down_bare_chestside.png", CB), "old chest, side"), (cell("r13/chest_down_bare_chestside.png", CB), "NEW, side")]),
    ("In the polo", [(cell("r9/build_down_dressed_upper.png"), "in the game today"), (cell("r10/muscles_down_dressed_upper.png"), "new arms, old chest"), (cell("r13/chest_down_dressed_upper.png"), "NEW"), (cell("r13/chest_down_dressed_chestside.png", CB), "NEW, side"), (target((680, 62, 902, 412)), "target, side")]),
]
def numbers(name, parts):
    r = posed.measure(name, parts); pr = {round(y, 2): (w, d, g) for y, w, d, f, b, g in tm.profile(parts['Body']['pos'], [1.21, 1.03])}
    r.update(cw=pr[1.21][0], cd=pr[1.21][1], cg=pr[1.21][2], wg=pr[1.03][2]); return r
t = posed.load("male_torso")
M = [numbers("base body", posed.load("male_build0")), numbers("in the game today", posed.load("male_build1")), numbers("new arms, old chest", posed.muscles(t, af.P)), numbers("NEW", posed.muscles(t, af.P, chest=True))]
W = PAD * 2 + 5 * CW + 4 * GAP; H = 64 + len(rows) * (34 + CH + LAB + 10) + 36 + 30 * (len(M) + 1) + 56
im = Image.new("RGB", (W, H), "#fcfcfb"); d = ImageDraw.Draw(im)
d.text((PAD, 18), "Male chest, built up to match the shoulders and arms  (Blender studio renders, arms hanging, not in game yet)", font=font(25, True), fill="#0b0b0b")
y = 64
for title, cells in rows:
    d.text((PAD, y), title, font=font(20, True), fill="#0b0b0b"); y += 34
    for k, (c, label) in enumerate(cells):
        x = PAD + k * (CW + GAP); im.paste(c, (x, y))
        if label.startswith("NEW"): d.rectangle((x - 3, y - 3, x + CW + 2, y + CH + 2), outline="#1f6feb", width=4)
        d.text((x + 2, y + CH + 6), label, font=font(18, label.startswith("NEW")), fill="#0b0b0b")
    y += CH + LAB + 10
y += 8; d.text((PAD, y), "Measured on the mesh (cm)", font=font(20, True), fill="#0b0b0b"); y += 34
cols = [("", 230, lambda r: r['name']), ("shoulders", 120, lambda r: f"{r['bare']:.1f}"), ("chest width", 130, lambda r: f"{r['cw']:.1f}"), ("chest depth", 130, lambda r: f"{r['cd']:.1f}"),
        ("chest girth", 130, lambda r: f"{r['cg']:.0f}"), ("waist girth", 130, lambda r: f"{r['wg']:.0f}"), ("upper arm girth", 160, lambda r: f"{r['gup']:.1f}"),
        ("chest ÷ shoulders (width)", 240, lambda r: f"{r['cw'] / r['bare']:.2f}"), ("chest ÷ upper arm (girth)", 230, lambda r: f"{r['cg'] / r['gup']:.2f}"), ("polo shoulders", 130, lambda r: f"{r['polo']:.1f}")]
x = PAD
for name, w, _ in cols: d.text((x, y), name, font=font(17, True), fill="#52514e"); x += w
y += 28
for r in M:
    x = PAD; new = r['name'] == "NEW"
    for name, w, f in cols: d.text((x, y), f(r), font=font(18, new), fill="#0b0b0b"); x += w
    y += 30
d.text((PAD, y + 8), "Chest width and depth are taken at the fullest height of the chest with the arms left out; girths are approximate (outline of the cross-section).", font=font(15), fill="#52514e")
im.save(OUT, quality=90); print(OUT, im.size)
for r in M: print({k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items() if k in ('name', 'bare', 'polo', 'cw', 'cd', 'cg', 'wg', 'gup')})
