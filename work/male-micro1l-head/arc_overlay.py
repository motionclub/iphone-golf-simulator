"""Overlay the plate-derived mandible arc (magenta) and the mesh natural-border arc used for the crest (cyan) on the plate and on a render (left profile).
python3.13 arc_overlay.py <out.png> <ul_dir> [<ul_dir2> ...]"""
import sys; sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from j_lib import *
import k_mand as KM
out = sys.argv[1]; dirs = sys.argv[2:]
view = 'left'; box = BOXES[view]; zlo, zhi = 1.40, 1.56
r0 = int(rowz(zhi)); r1 = int(rowz(zlo)); c0 = int(prof_col(-0.17, view)); c1 = int(prof_col(0.03, view)); up = 3
def poly(ctrl):
    return [((float(prof_col(c[1], view)) - c0) * up, (float(rowz(c[2])) - r0) * up) for c in ctrl]
tiles = []
pl = PLATE.crop((c0, r0, c1, r1)); pl = pl.resize((pl.width * up, pl.height * up), Image.LANCZOS); tiles.append(('PLATE', pl))
for d_ in dirs:
    rn = Image.open(Path(d_) / f'plate_{view}.png').convert('RGB')
    tiles.append((Path(d_).name, rn.crop(((c0 - box[0]) * 2, (r0 - box[1]) * 2, (c1 - box[0]) * 2, (r1 - box[1]) * 2)).resize(pl.size, Image.LANCZOS)))
sheet = Image.new('RGB', (pl.width * len(tiles) + 6 * (len(tiles) - 1), pl.height * 2 + 6))
for i, (lab, t) in enumerate(tiles):
    for r in range(2):
        im = t.copy(); dr = ImageDraw.Draw(im)
        if r == 1:
            dr.line(poly(KM.ARC_CTRL), fill=(255, 0, 255), width=2); dr.line(poly(KM.ARC_NAT), fill=(0, 255, 255), width=2)
        dr.text((6, 4), lab + (' | magenta = plate-derived mandible, cyan = crest arc' if r == 1 else ''), fill=(255, 255, 0)); sheet.paste(im, (i * (pl.width + 6), r * (pl.height + 6)))
sheet.save(out); print(out, sheet.size)
