#!/usr/bin/env python3
"""board_fit.py <renders dir> <out.jpg>: tops as tailored (loose) against refitted, for the tennis, golf and bowling kits."""
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFont
import armio, posed, fit, fitcheck
R, OUT = sys.argv[1], sys.argv[2]
def font(n, bold=False):
    try: return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", n, index=1 if bold else 0)
    except Exception: return ImageFont.load_default()
CW, CH, GAP, PAD, LAB = 316, 470, 14, 18, 30
def cell(path, box=(95, 110, 665, 958)): return Image.open(os.path.join(R, path)).convert("RGB").crop(box).resize((CW, CH), Image.LANCZOS)
KITS = [("Tennis polo", "tennis", "male_torso"), ("Golf polo", "golf", "male_golfkit"), ("Bowling shirt", "bowl", "male_bowlingkit")]
rows = [(title, [(cell(f"{k}loose_down_dressed_upper.png"), "as it was: loose"), (cell(f"{k}fit_down_dressed_upper.png"), "NEW: fitted"), (cell(f"{k}loose_down_dressed_chest3q.png", (140, 150, 620, 864)), "as it was"),
                 (cell(f"{k}fit_down_dressed_chest3q.png", (140, 150, 620, 864)), "NEW: fitted"), (cell(f"{k}fit_down_dressed_upperback.png"), "NEW: fitted, back")]) for title, k, tag in KITS]
M = []
for title, k, tag in KITS:
    parts = {n[:-4]: armio.read(f"export/{tag}/{n}") for n in sorted(os.listdir(f"export/{tag}")) if n.endswith(".bin")}
    a = fit.dress(parts, posed.B, posed.mL, posed.mR, fit=False, under=("Kit_Bottom", "Kit_Belt")); b = fit.dress(parts, posed.B, posed.mL, posed.mR, fit=True, under=("Kit_Bottom", "Kit_Belt"))
    g0, g1 = fitcheck.gap(a), fitcheck.gap(b); reg = dict(fitcheck.regions(parts['Kit_Top']['pos']))
    vis = reg["sleeve"] | reg["chest"] | reg["back"] | reg["stomach"] | reg["lower back and sides"]
    M.append((title, np.median(g0[reg["sleeve"]]), np.median(g1[reg["sleeve"]]), np.median(g0[reg["chest"]]), np.median(g1[reg["chest"]]), np.median(g0[reg["back"]]), np.median(g1[reg["back"]]), g1[vis].min(), int((g1[vis] < 0).sum())))
W = PAD * 2 + 5 * CW + 4 * GAP; H = 64 + len(rows) * (34 + CH + LAB + 10) + 36 + 30 * (len(M) + 1) + 56
im = Image.new("RGB", (W, H), "#fcfcfb"); d = ImageDraw.Draw(im)
d.text((PAD, 18), "Tops refitted to hug the muscular arm and chest: tennis, golf, bowling  (Blender studio renders, not in game yet)", font=font(25, True), fill="#0b0b0b")
y = 64
for title, cells in rows:
    d.text((PAD, y), title, font=font(20, True), fill="#0b0b0b"); y += 34
    for k, (c, label) in enumerate(cells):
        x = PAD + k * (CW + GAP); im.paste(c, (x, y))
        if label.startswith("NEW"): d.rectangle((x - 3, y - 3, x + CW + 2, y + CH + 2), outline="#1f6feb", width=4)
        d.text((x + 2, y + CH + 6), label, font=font(18, label.startswith("NEW")), fill="#0b0b0b")
    y += CH + LAB + 10
y += 8; d.text((PAD, y), "Cloth to skin, measured on the mesh (cm, middle value; loose to fitted)", font=font(20, True), fill="#0b0b0b"); y += 34
cols = [("", 220), ("sleeve", 240), ("chest", 240), ("upper back", 240), ("nearest point, fitted", 260), ("cloth under the skin, fitted", 300)]
x = PAD
for name, w in cols: d.text((x, y), name, font=font(17, True), fill="#52514e"); x += w
y += 28
for t, s0, s1, c0, c1, b0, b1, mn, under in M:
    x = PAD
    for (name, w), s in zip(cols, (t, f"{s0:.1f} to {s1:.1f}", f"{c0:.1f} to {c1:.1f}", f"{b0:.1f} to {b1:.1f}", f"{mn:.2f}", f"{under} vertices")):
        d.text((x, y), s, font=font(18), fill="#0b0b0b"); x += w
    y += 30
d.text((PAD, y + 8), "Nearest point and under-the-skin count leave out the collar and the armpit hollow, which are left as tailored. Rest pose only: nothing here has been checked in motion.", font=font(15), fill="#52514e")
im.save(OUT, quality=90); print(OUT, im.size)
for m in M: print(m[0], [round(float(v), 2) for v in m[1:]])
