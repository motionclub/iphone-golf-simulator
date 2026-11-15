#!/usr/bin/env python3
"""board.py <renders dir> <out.jpg>: the proof board for the resized male arm (arms hanging, so it reads like the target)."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
import posed
R, OUT = sys.argv[1], sys.argv[2]
TGT = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/targets-2026-10-12/tier1/01_male_body_turnaround.jpg"
def font(n, bold=False):
    try: return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", n, index=1 if bold else 0)
    except Exception: return ImageFont.load_default()
CW, CH, GAP, PAD, LAB = 316, 500, 14, 18, 30
def cell(path, box=(95, 70, 665, 972)):
    im = Image.open(os.path.join(R, path)).convert("RGB").crop(box); return im.resize((CW, CH), Image.LANCZOS)
def target(box):
    im = Image.open(TGT).convert("RGB").crop(box); h = CH; w = round(im.width * h / im.height); im = im.resize((w, h), Image.LANCZOS)
    out = Image.new("RGB", (CW, CH), (166, 166, 166)); out.paste(im.crop((max(0, (w - CW) // 2), 0, max(0, (w - CW) // 2) + min(w, CW), h)), (max(0, (CW - w) // 2), 0)); return out
PREV = os.path.join(os.path.dirname(os.path.abspath(R)), "r9")     # the version before the sleeve fix (the muscle's growth added on top of the sleeve's slack)
def prev(path, box=(95, 70, 665, 972)): return Image.open(os.path.join(PREV, path)).convert("RGB").crop(box).resize((CW, CH), Image.LANCZOS)
rows = [
    ("In the polo, from the front", [(cell("base_down_dressed_upper.png"), "base body"), (cell("build_down_dressed_upper.png"), "in the game today"), (prev("muscles_down_dressed_upper.png"), "last version (shoulder pads)"), (cell("muscles_down_dressed_upper.png"), "NEW"), (target((112, 62, 334, 412)), "target (tier 1)")]),
    ("The new polo from the side, the back and close up", [(cell("muscles_down_dressed_upperside.png"), "NEW, side"), (cell("muscles_down_dressed_upperback.png"), "NEW, back"), (cell("muscles_down_dressed_shfront.png", (0, 0, 760, 1000)), "NEW, shoulder close up"), (target((680, 62, 902, 412)), "target, side"), (target((940, 62, 1162, 412)), "target, back")]),
    ("The arm underneath (same as the last board)", [(cell("base_down_bare_upper.png"), "base body"), (cell("build_down_bare_upper.png"), "in the game today"), (cell("muscles_down_bare_upper.png"), "NEW"), (cell("muscles_down_bare_upperside.png"), "NEW, side"), (cell("muscles_down_bare_upperback.png"), "NEW, back")]),
]
M = [r for r in posed.rows() if r['name'] != "first muscle model"]
M.insert(2, dict(M[-1], name="last version", polo=66.1))
W = PAD * 2 + 5 * CW + 4 * GAP
H = 64 + len(rows) * (34 + CH + LAB + 10) + 36 + 30 * (len(M) + 2) + 64
im = Image.new("RGB", (W, H), "#fcfcfb"); d = ImageDraw.Draw(im)
d.text((PAD, 18), "Male arm in the polo: the muscle now fills the sleeve instead of pushing it out  (Blender studio renders, not in game yet)", font=font(25, True), fill="#0b0b0b")
y = 64
for title, cells in rows:
    d.text((PAD, y), title, font=font(20, True), fill="#0b0b0b"); y += 34
    for k, (c, label) in enumerate(cells):
        x = PAD + k * (CW + GAP); im.paste(c, (x, y))
        if label.startswith("NEW"): d.rectangle((x - 3, y - 3, x + CW + 2, y + CH + 2), outline="#1f6feb", width=4)
        d.text((x + 2, y + CH + 6), label, font=font(18, label.startswith("NEW")), fill="#0b0b0b")
    y += CH + LAB + 10
y += 8; d.text((PAD, y), "Measured on the mesh with the arms hanging (cm)", font=font(20, True), fill="#0b0b0b"); y += 34
cols = [("", 200, None), ("shoulders, bare", 150, 'bare'), ("shoulders, in polo", 170, 'polo'), ("upper arm", 110, 'up'), ("elbow", 80, 'el'), ("forearm", 100, 'fo'), ("wrist", 80, 'wr'),
        ("upper arm, side", 150, 'upd'), ("forearm, side", 130, 'fod'), ("upper ÷ forearm (front)", 240, None), ("girth: upper, forearm", 200, None)]
x = PAD
for name, w, _ in cols: d.text((x, y), name, font=font(17, True), fill="#52514e"); x += w
d.text((PAD + 200 + 320, y - 24), "seen from the front", font=font(15), fill="#52514e")
y += 28
label = {"base": "base body", "11-11 build": "in the game today", "last version": "last version (pads)", "muscle model": "NEW"}
for r in M + [posed.TARGET]:
    x = PAD; new = r['name'] == "muscle model"
    for name, w, key in cols:
        if not name: s = label.get(r['name'], r['name'])
        elif key: s = f"{r[key]:.1f}" if key in r else "–"
        elif name.startswith("upper ÷"): s = f"{r['up'] / r['fo']:.2f}" + ("  (forearm wider)" if r['up'] < r['fo'] and 'gup' in r else "")
        else: s = f"{r['gup']:.1f}, {r['gfo']:.1f}" if 'gup' in r else "–"
        d.text((x, y), s, font=font(18, new), fill="#0b0b0b"); x += w
    y += 30
d.text((PAD, y + 8), "Target numbers are read off the turnaround picture (3.27 px per cm); its upper arm is hidden by the sleeve and is measured at the cuff.", font=font(15), fill="#52514e")
im.save(OUT, quality=90); print(OUT, im.size)
