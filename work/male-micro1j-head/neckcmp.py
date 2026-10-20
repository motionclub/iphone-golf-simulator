"""Profile plates (left, right) with the mesh sagittal section (x=0, cyan), mesh silhouette (|x|<=0.12, yellow) overlaid; z 1.33..1.72.
python3.13 neckcmp.py <V.npy> <out.png> [zlo zhi scale]"""
import sys; sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head')
from j_lib import *
V = np.load(sys.argv[1]) if sys.argv[1].endswith('.npy') else None
out = sys.argv[2]; zlo = float(sys.argv[3]) if len(sys.argv) > 3 else 1.33; zhi = float(sys.argv[4]) if len(sys.argv) > 4 else 1.72; S = float(sys.argv[5]) if len(sys.argv) > 5 else 3.0
ylo = float(sys.argv[6]) if len(sys.argv) > 6 else -0.30; yhi = float(sys.argv[7]) if len(sys.argv) > 7 else 0.20
_, F, _ = load_start(); E = edges_of(F)
head = (V[:, 2] > 1.30) & (np.abs(V[:, 0]) < 0.30)
tiles = []
for panel in ('left', 'right'):
    box = BOXES[panel]; r0 = rowz(zhi); r1 = rowz(zlo)
    c0 = int(prof_col(ylo, panel)); c1 = int(prof_col(yhi, panel)); box = (c0, box[1], c1, box[3])
    crop = PLATE.crop((c0, int(r0), c1, int(r1))).resize((int((c1 - c0) * S), int((int(r1) - int(r0)) * S)), Image.LANCZOS)
    d = ImageDraw.Draw(crop)
    X = lambda y: (prof_col(y, panel) - box[0]) * S
    Z = lambda z: (rowz(z) - int(r0)) * S
    for zz in np.arange(np.ceil(zlo * 20) / 20, zhi, 0.05):
        d.line((0, Z(zz), crop.width, Z(zz)), fill=(255, 255, 255), width=1); d.text((3, Z(zz) - 11), f'{zz:.2f}', fill=(255, 255, 0))
    for yy in np.arange(np.ceil(ylo*100)/100, yhi, 0.01 if S >= 6 else 0.05):
        d.line((X(yy), 0, X(yy), crop.height), fill=(90, 90, 120), width=1); d.text((X(yy) + 2, crop.height - 12), f'y{yy:+.2f}', fill=(150, 150, 200))
    # sagittal x=0 section: edges crossing x=0 -> (y,z) points sorted by z segments
    pts = plane_section(V, E, 0, 0.0, head)
    for p in pts: d.ellipse((X(p[1]) - 1.5, Z(p[2]) - 1.5, X(p[1]) + 1.5, Z(p[2]) + 1.5), fill=(0, 255, 255))
    # silhouette: per z band, min/max y over verts within |x|<=0.12 (and body below 1.40 limited to |x|<=0.12 too)
    for zz in np.arange(zlo, zhi, 0.0015):
        pz = plane_section(V, E, 2, zz, head & (np.abs(V[:, 0]) < 0.12))
        if len(pz) < 2: continue
        for yv in (pz[:, 1].min(), pz[:, 1].max()): d.ellipse((X(yv) - 1.4, Z(zz) - 1.4, X(yv) + 1.4, Z(zz) + 1.4), fill=(255, 220, 0))
    tiles.append(crop)
sheet = Image.new('RGB', (sum(t.width for t in tiles) + 6, max(t.height for t in tiles)), (0, 0, 0))
x = 0
for t in tiles: sheet.paste(t, (x, 0)); x += t.width + 6
sheet.save(out); print('saved', out, sheet.size)
