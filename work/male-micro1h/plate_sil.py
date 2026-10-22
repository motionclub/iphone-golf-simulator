"""Extract skin silhouettes from the head-detail plate panels (system python3 + Pillow, no numpy).
Writes plates/sil.json:  front: per-row (xmin,xmax) of skin (cols, full-plate coords); left/right profile: per-row (xmin,xmax).
Skin mask = warm pixels (r-b > 22, r > 95) ; shirt (grey) and background (dark grey) are excluded."""
import json
from PIL import Image
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
im = Image.open(R + '/ArtDir/hero/base_lock/male_head_detail.jpg').convert('RGB')
px = im.load()
PANELS = {'front': (5, 62, 433, 352), 'left': (433, 62, 834, 352), 'right': (834, 62, 1271, 352)}


def skin(p):
    r, g, b = p
    return (r - b > 22) and r > 95 and (r - g) > 6


out = {}
for name, (x0, y0, x1, y1) in PANELS.items():
    rows = {}
    for y in range(y0, y1):
        xs = [x for x in range(x0, x1) if skin(px[x, y])]
        if xs:
            # runs: split into contiguous segments (gap > 3 px)
            segs = []; s = xs[0]; prev = xs[0]
            for x in xs[1:]:
                if x - prev > 3:
                    segs.append((s, prev)); s = x
                prev = x
            segs.append((s, prev))
            rows[y] = segs
    out[name] = rows
json.dump(out, open(R + '/work/male-micro1h/plates/sil.json', 'w'))
# quick print: front widths every 6 rows
for y in range(76, 300, 6):
    print('front', y, out['front'].get(y))
