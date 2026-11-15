#!/usr/bin/env python3
"""board_chest2.py <out.jpg>: the chest rebuilt after "looks like female breasts from the side ... disfiguration": the rejected
version (r19), the plain base body (r19) and the new one (r21), close up; then the three kits over it."""
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFont
OUT = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
def font(n, bold=False):
    try: return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", n, index=1 if bold else 0)
    except Exception: return ImageFont.load_default()
CW, CH, GAP, PAD, LAB = 316, 470, 14, 18, 30
CB = (140, 150, 620, 864); UP = (95, 110, 665, 958)
def cell(path, box=CB): return Image.open(os.path.join(HERE, "renders", path)).convert("RGB").crop(box).resize((CW, CH), Image.LANCZOS)
rows = [
    ("From the side", [(cell("r19/base_down_bare_chestside.png"), "base body"), (cell("r19/whole_down_bare_chestside.png"), "last version (rejected)"), (cell("r21/whole_down_bare_chestside.png"), "NEW"), (cell("r21/tennisfit_down_dressed_chestside.png"), "NEW, in the polo"), (cell("r21/golffit_down_dressed_chestside.png"), "NEW, golf")]),
    ("Front and three-quarter", [(cell("r19/whole_down_bare_chestfront.png"), "last version (rejected)"), (cell("r21/whole_down_bare_chestfront.png"), "NEW"), (cell("r19/whole_down_bare_chest3q.png"), "last version (rejected)"), (cell("r21/whole_down_bare_chest3q.png"), "NEW"), (cell("r19/base_down_bare_chest3q.png"), "base body, for the dents")]),
    ("In the three tops", [(cell("r21/tennisfit_down_dressed_upper.png", UP), "NEW: tennis"), (cell("r21/tennisfit_down_dressed_chest3q.png"), "NEW: tennis"), (cell("r21/golffit_down_dressed_upper.png", UP), "NEW: golf"), (cell("r21/bowlfit_down_dressed_upper.png", UP), "NEW: bowling"), (cell("r21/bowlfit_down_dressed_chest3q.png"), "NEW: bowling")]),
]
PROF = [("Height on the body (m)", "1.33", "1.30", "1.27", "1.24", "1.21", "1.18", "1.15", "1.10"),
        ("base body", 12.1, 15.0, 16.8, 17.9, 18.1, 18.2, 18.5, 18.6), ("last version (rejected)", 13.8, 17.9, 19.7, 19.8, 19.4, 18.0, 17.9, 17.4), ("NEW", 14.8, 17.2, 18.6, 19.3, 19.4, 18.9, 18.9, 18.3)]
W = PAD * 2 + 5 * CW + 4 * GAP; H = 64 + len(rows) * (34 + CH + LAB + 10) + 36 + 30 * len(PROF) + 60
im = Image.new("RGB", (W, H), "#fcfcfb"); d = ImageDraw.Draw(im)
d.text((PAD, 18), "Male chest rebuilt: one broad chest instead of two mounds  (Blender studio renders, not in game yet)", font=font(25, True), fill="#0b0b0b")
y = 64
for title, cells in rows:
    d.text((PAD, y), title, font=font(20, True), fill="#0b0b0b"); y += 34
    for k, (c, label) in enumerate(cells):
        x = PAD + k * (CW + GAP); im.paste(c, (x, y))
        if label.startswith("NEW"): d.rectangle((x - 3, y - 3, x + CW + 2, y + CH + 2), outline="#1f6feb", width=4)
        d.text((x + 2, y + CH + 6), label, font=font(18, label.startswith("NEW")), fill="#0b0b0b")
    y += CH + LAB + 10
y += 8; d.text((PAD, y), "Side profile: how far the front of the chest stands forward at each height (cm from the body's axis line)", font=font(20, True), fill="#0b0b0b"); y += 34
for r in PROF:
    x = PAD
    for k, v in enumerate(r):
        d.text((x, y), v if isinstance(v, str) else f"{v:.1f}", font=font(17 if r is PROF[0] else 18, r is PROF[0] or r[0] == "NEW"), fill="#52514e" if r is PROF[0] else "#0b0b0b"); x += 300 if k == 0 else 110
    y += 30
d.text((PAD, y + 8), "The rejected chest dropped 1.8 cm in 6 cm under the pectorals (an undercut); the new one runs on over the ribs and loses 1.1 cm over 11 cm.", font=font(15), fill="#52514e")
im.save(OUT, quality=90); print(OUT, im.size)
