"""Side-by-side plate crop | mesh render (Unity-like, plate framing) for the jaw/neck zone.
python3.13 platecmp.py <render_dir> <out.png> [view=left|right|q3L|q3R|front] [zlo zhi] [up=3]"""
import sys; sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1k-head')
from j_lib import *
d = Path(sys.argv[1]); out = sys.argv[2]; view = sys.argv[3] if len(sys.argv) > 3 else 'left'
zlo = float(sys.argv[4]) if len(sys.argv) > 4 else 1.40; zhi = float(sys.argv[5]) if len(sys.argv) > 5 else 1.58; up = float(sys.argv[6]) if len(sys.argv) > 6 else 3.0
box = BOXES[view]
if view in ('q3L', 'q3R'): r0 = int(397 + (TOP - zhi) / K); r1 = int(397 + (TOP - zlo) / K)
else: r0 = int(rowz(zhi)); r1 = int(rowz(zlo))
pl = PLATE.crop((box[0], r0, box[2], r1)); pl = pl.resize((int(pl.width * up), int(pl.height * up)), Image.LANCZOS)
rn = Image.open(d / f'plate_{view}.png').convert('RGB')           # 2 px per plate px, same panel box
rr = rn.crop((0, int((r0 - box[1]) * 2), rn.width, int((r1 - box[1]) * 2))); rr = rr.resize((int(pl.width), int(pl.height)), Image.LANCZOS)
sheet = Image.new('RGB', (pl.width * 2 + 8, pl.height), (0, 0, 0)); sheet.paste(pl, (0, 0)); sheet.paste(rr, (pl.width + 8, 0))
sheet.save(out); print(out, sheet.size)
