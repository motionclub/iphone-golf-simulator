"""Profile silhouettes (|x|<=0.12) of several V files over the profile plates (left+right), zoomed on a window.
python3.13 neckcmp2.py <out.png> <zlo> <zhi> <ylo> <yhi> <scale> <V1.npy> [V2.npy ...]   (first = START yellow, then cyan, magenta, green)"""
import sys; sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1k-head')
from j_lib import *
out = sys.argv[1]; zlo, zhi, ylo, yhi, S = (float(v) for v in sys.argv[2:7]); files = sys.argv[7:]
_, F, _ = load_start(); E = edges_of(F)
cols = [(255, 220, 0), (0, 255, 255), (255, 90, 255), (120, 255, 120)]
tiles = []
for panel in ('left', 'right'):
    box = BOXES[panel]; r0 = int(rowz(zhi)); r1 = int(rowz(zlo)); c0 = int(prof_col(ylo, panel)); c1 = int(prof_col(yhi, panel))
    crop = PLATE.crop((c0, r0, c1, r1)).resize((int((c1 - c0) * S), int((r1 - r0) * S)), Image.LANCZOS); d = ImageDraw.Draw(crop)
    X = lambda y: (prof_col(y, panel) - c0) * S; Z = lambda z: (rowz(z) - r0) * S
    for zz in np.arange(np.ceil(zlo * 100) / 100, zhi, 0.01): d.line((0, Z(zz), 24, Z(zz)), fill=(255, 255, 255)); d.text((28, Z(zz) - 5), f'{zz:.2f}', fill=(255, 255, 0))
    for yy in np.arange(np.ceil(ylo * 100) / 100, yhi, 0.01): d.line((X(yy), crop.height - 20, X(yy), crop.height), fill=(255, 255, 255)); d.text((X(yy) + 2, crop.height - 32), f'{yy*1000:.0f}', fill=(150, 200, 255))
    for k, fpath in enumerate(files):
        V = np.load(fpath); head = (V[:, 2] > 1.30) & (np.abs(V[:, 0]) < 0.12)
        for zz in np.arange(zlo, zhi, 0.0007):
            pz = plane_section(V, E, 2, zz, head)
            if len(pz) < 2: continue
            for yv in (pz[:, 1].min(), pz[:, 1].max()): d.ellipse((X(yv) - 1.3, Z(zz) - 1.3, X(yv) + 1.3, Z(zz) + 1.3), fill=cols[k % 4])
    tiles.append(crop)
sheet = Image.new('RGB', (sum(t.width for t in tiles) + 6, max(t.height for t in tiles))); x = 0
for t in tiles: sheet.paste(t, (x, 0)); x += t.width + 6
sheet.save(out); print(out, sheet.size)
