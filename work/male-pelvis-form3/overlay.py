"""Overlay the mesh silhouette edge (red) on the plate panel crops (6x).  python3 overlay.py render <tag> | sheet out.png panels tag
panels as panel_cmp.BOX"""
import sys, os, subprocess
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import panel_cmp as PC
W = PC.W; R = PC.R; M = PC.M
def render(tag):
    src = f'data/V_{tag}.npy' if tag != 'start' else 'baseline/HeroBase_Male_Silhouette.blend'
    views = ','.join(PC.vname(p) for p in PC.BOX)
    env = dict(os.environ, PYTHONPATH=str(R / 'work/male-micro1i/pylib'))
    r = subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', '--python', 'rig.py', '--', src, f'r/{tag}_s', views, 'sil'], cwd=W, env=env, capture_output=True, text=True)
    if 'Traceback' in r.stdout or 'Error' in r.stderr[-300:]: print(r.stdout[-1500:], r.stderr[-800:])
def edge(mask):
    m = mask.astype(np.uint8); e = np.zeros_like(m)
    e[1:-1, 1:-1] = (m[1:-1, 1:-1] != m[:-2, 1:-1]) | (m[1:-1, 1:-1] != m[2:, 1:-1]) | (m[1:-1, 1:-1] != m[1:-1, :-2]) | (m[1:-1, 1:-1] != m[1:-1, 2:])
    return e.astype(bool)
def sheet(out, panels, tags):
    cols = []
    for p in panels:
        t, c0, c1, r0, r1 = PC.BOX[p][:5]; MM = PC._mag(p); base = PC.get(p, 'PLATE').convert('RGB'); a = np.asarray(base).copy()
        for k, tag in enumerate(tags):
            im = Image.open(W / f'r/{tag}_s/{PC.vname(p)}.png').convert('RGBA')
            if t.startswith(('left@', 'right@', 'sheet_back@', 'sheet_front@')): im = im.crop((c0 * MM, r0 * MM, c1 * MM, r1 * MM))
            m = np.asarray(im)[..., 3] > 127; e = edge(m)
            col = [(255, 60, 60), (60, 255, 120), (80, 160, 255)][k % 3]
            for dy in (0, 1):
                for dx in (0, 1):
                    ee = np.roll(np.roll(e, dy, 0), dx, 1); a[ee] = col
        cols.append(Image.fromarray(a))
    S = Image.new('RGB', (sum(c.width for c in cols) + 8 * (len(cols) + 1), max(c.height for c in cols) + 8), (16, 16, 16)); x = 8
    for c in cols: S.paste(c, (x, 4)); x += c.width + 8
    S.save(out); print(out, S.size)
if __name__ == '__main__':
    if sys.argv[1] == 'render': render(sys.argv[2])
    else: sheet(sys.argv[2], sys.argv[3].split(','), sys.argv[4:])
