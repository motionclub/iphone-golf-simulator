"""python3.13 silgate.py <renderdir> [json out] : gate % + torso row profile (mm) front/back/left/right"""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work')
M = R / 'male-silhouette'
cams = json.load(open(M / 'reference-cameras.json'))['views']; CAM = {c['name']: c for c in cams}
def mask(p):
    a = np.array(Image.open(p).convert('RGBA'))
    return (a[:, :, 3] > 127) if a[:, :, 3].min() < 250 else (a[:, :, 0] > 127)
def rows(m, x0, x1, y0, y1):
    """per image row: leftmost, rightmost foreground px inside the ROI x-range"""
    sub = m[:, x0:x1]; out = {}
    for y in range(y0, y1):
        xs = np.where(sub[y])[0]
        if len(xs): out[y] = (x0 + xs[0], x0 + xs[-1])
    return out
def run(d, outj=None):
    res = {}
    for v in ('bald_front', 'bald_back', 'left', 'right'):
        t = mask(M / f'{v}_target.png'); r = mask(Path(d) / f'{v}.png')
        res[v] = dict(diff=int((t != r).sum()), union=int((t | r).sum()), pct=100.0 * (t != r).sum() / (t | r).sum())
    if outj: json.dump(res, open(outj, 'w'), indent=1)
    return res
if __name__ == '__main__':
    r = run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print({k: round(v['pct'], 4) for k, v in r.items()})
