#!/usr/bin/env python3
"""board_whole.py <out.jpg>: why the figure looked wrong (measured) and the whole-body rebuild, bare and in the three kits."""
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFont
import armio, posed, fit, figure
OUT = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
TGT = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/targets-2026-10-12/tier1/01_male_body_turnaround.jpg"
def font(n, bold=False):
    try: return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", n, index=1 if bold else 0)
    except Exception: return ImageFont.load_default()
CW, CH, GAP, PAD, LAB = 316, 470, 14, 18, 30
FULL = (190, 150, 570, 716); UP = (95, 110, 665, 958); Q3 = (140, 150, 620, 864)
def cell(path, box): return Image.open(os.path.join(HERE, "renders", path)).convert("RGB").crop(box).resize((CW, CH), Image.LANCZOS)
def target(box):
    im = Image.open(TGT).convert("RGB").crop(box); h = CH; w = round(im.width * h / im.height); im = im.resize((w, h), Image.LANCZOS)
    out = Image.new("RGB", (CW, CH), (166, 166, 166)); out.paste(im.crop((max(0, (w - CW) // 2), 0, max(0, (w - CW) // 2) + min(w, CW), h)), (max(0, (CW - w) // 2), 0)); return out
rows = [
    ("The body", [(cell("r17/base_down_bare_front.png", FULL), "base body"), (cell("r17/chest_down_bare_front.png", FULL), "last version (looked wrong)"), (cell("r18/whole_down_bare_front.png", FULL), "NEW: whole body"), (cell("r18/whole_down_bare_side.png", FULL), "NEW, side"), (cell("r18/whole_down_bare_back.png", FULL), "NEW, back")]),
    ("Tennis", [(cell("r9/build_down_dressed_upper.png", UP), "in the game today"), (cell("r16/tennisfit_down_dressed_upper.png", UP), "last version (looked wrong)"), (cell("r18/tennisfit_down_dressed_upper.png", UP), "NEW"), (cell("r18/tennisfit_down_dressed_chest3q.png", Q3), "NEW, three-quarter"), (target((112, 62, 334, 392)), "target (tier 1)")]),
    ("Golf and bowling", [(cell("r16/golffit_down_dressed_upper.png", UP), "golf, last version"), (cell("r18/golffit_down_dressed_upper.png", UP), "NEW: golf"), (cell("r18/golffit_down_dressed_chest3q.png", Q3), "NEW: golf, three-quarter"), (cell("r16/bowlfit_down_dressed_upper.png", UP), "bowling, last version"), (cell("r18/bowlfit_down_dressed_upper.png", UP), "NEW: bowling")]),
]
base = posed.load("male_build0"); base['Kit_Bottom'] = armio.read("export/male_build0/Kit_Bottom.bin")
mb = figure.measure(base); mt = figure.measure(posed.load("male_build1")); mn = figure.measure(fit.dress(base, posed.B, posed.mL, posed.mR, fit=False))
# the last version (the 11-11 build's torso + the first arm and chest fields), as measured by figure.py before this set replaced it
ml = dict(chest_g=121.5, waist_g=80.1, hip_g=109.5, uparm_g=45.8, forearm_g=35.7, shoulders=57.9, waist_w=28.8, chest_w=40.0, neck_w=14.0)
T = [("Waist, girth", lambda m: f"{m['waist_g']:.0f}", "the old build pulled it in to 80 between a big chest and wide hips"),
     ("Chest ÷ waist", lambda m: f"{m['chest_g'] / m['waist_g']:.2f}", "an hourglass at 1.5; about 1.3 reads as a strong man"),
     ("Hips ÷ waist", lambda m: f"{m['hip_g'] / m['waist_g']:.2f}", "the hips did not change; the waist had gone"),
     ("Shoulders ÷ waist, width", lambda m: f"{m['shoulders'] / m['waist_w']:.2f}", ""),
     ("Upper arm, girth", lambda m: f"{m['uparm_g']:.1f}", "his upper arm is 24 cm long: at 46 round it was nearly a ball"),
     ("Upper arm ÷ forearm", lambda m: f"{m['uparm_g'] / m['forearm_g']:.2f}", ""),
     ("Chest, girth", lambda m: f"{m['chest_g']:.0f}", ""), ("Neck, width", lambda m: f"{m['neck_w']:.1f}", "")]
W = PAD * 2 + 5 * CW + 4 * GAP; H = 64 + len(rows) * (34 + CH + LAB + 10) + 36 + 30 * (len(T) + 1) + 60
im = Image.new("RGB", (W, H), "#fcfcfb"); d = ImageDraw.Draw(im)
d.text((PAD, 18), "Why he looked wrongly built, and the whole body rebuilt as one  (Blender studio renders, not in game yet)", font=font(25, True), fill="#0b0b0b")
y = 64
for title, cells in rows:
    d.text((PAD, y), title, font=font(20, True), fill="#0b0b0b"); y += 34
    for k, (c, label) in enumerate(cells):
        x = PAD + k * (CW + GAP); im.paste(c, (x, y))
        if label.startswith("NEW"): d.rectangle((x - 3, y - 3, x + CW + 2, y + CH + 2), outline="#1f6feb", width=4)
        d.text((x + 2, y + CH + 6), label, font=font(18, label.startswith("NEW")), fill="#0b0b0b")
    y += CH + LAB + 10
y += 8; d.text((PAD, y), "What was out of proportion (measured on the mesh, cm)", font=font(20, True), fill="#0b0b0b"); y += 34
xs = [PAD, PAD + 290, PAD + 410, PAD + 590, PAD + 760, PAD + 880]
for x, name in zip(xs, ("", "base body", "in the game today", "last version", "NEW", "")): d.text((x, y), name, font=font(17, True), fill="#52514e")
y += 28
for name, f, note in T:
    for x, s, b in zip(xs, (name, f(mb), f(mt), f(ml), f(mn), note), (False, False, False, False, True, False)): d.text((x, y), s, font=font(18 if x != xs[-1] else 16, b), fill="#0b0b0b" if x != xs[-1] else "#52514e")
    y += 30
im.save(OUT, quality=90); print(OUT, im.size)
for name, f, note in T: print(f"{name:28} {f(mb):>7} {f(mt):>7} {f(ml):>7} {f(mn):>7}")
