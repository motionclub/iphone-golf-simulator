"""refpair.py out.jpg stills_dir [label]  -> reference panels vs current game hand renders (female right hand)"""
import sys
from PIL import Image, ImageDraw
out, H = sys.argv[1], sys.argv[2]; label = sys.argv[3] if len(sys.argv) > 3 else "CURRENT (game, full detail)"
R0 = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
ref = Image.open(f"{R0}/ArtDir/style/alive/hand-reference-2026-10-19/13-hands-relaxed-all-angles.png").convert("RGB")
k = 2048 / 2000
cols = [(28, 501), (518, 992), (1010, 1482), (1500, 1973)]; rows = [(84, 452), (470, 824), (842, 1213)]
def box(r, c): return tuple(int(v * k) for v in (cols[c][0], rows[r][0], cols[c][1], rows[r][1]))
pairs = [("DORSAL", (0, 0), "1_dorsal"), ("PALM (facing thigh)", (0, 1), "2_palm"), ("THUMB SIDE", (0, 2), "3_thumb"), ("PINKY SIDE", (0, 3), "4_pinky"),
         ("FRONT (fingertips to camera)", (1, 0), "5_front"), ("REAR (wrist to camera)", (1, 1), "6_rear"),
         ("3/4 DORSAL FRONT", (2, 0), "7_q_dorsal"), ("3/4 PALM FRONT", (2, 1), "8_q_palm"), ("3/4 THUMB BACK", (2, 2), "9_q_thumb_back"), ("3/4 PINKY BACK", (2, 3), "10_q_pinky_back")]
W = Hh = 360
def lab(d, x, y, t): d.rectangle((x, y, x + len(t) * 7 + 8, y + 14), fill=(0, 0, 0)); d.text((x + 4, y + 1), t, fill="yellow")
sh = Image.new("RGB", (W * 4, Hh * 5), "white"); d = ImageDraw.Draw(sh)
for i, (name, (r, c), f) in enumerate(pairs):
    row = i // 2; col = (i % 2) * 2
    a = ref.crop(box(r, c)); a.thumbnail((W, Hh)); canvas = Image.new("RGB", (W, Hh), (228, 228, 226)); canvas.paste(a, ((W - a.width) // 2, (Hh - a.height) // 2))
    b = Image.open(f"{H}/hands_female_{f}.jpg").resize((W, Hh))
    sh.paste(canvas, (col * W, row * Hh)); sh.paste(b, ((col + 1) * W, row * Hh))
    lab(d, col * W + 4, row * Hh + 4, "REFERENCE  " + name); lab(d, (col + 1) * W + 4, row * Hh + 4, label)
sh.save(out, quality=92)
