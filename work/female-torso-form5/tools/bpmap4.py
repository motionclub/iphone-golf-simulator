"""2D band-passed shading maps of plate vs model(s) in the bust ROI (front view, plate pixel grid).  python3 tools/bpmap4.py out.png tag=coords.npy ...
Shows WHERE the plate has relief structure that the model lacks.  Pure visualisation (not a gate)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw
import photo3 as ph
from fplate import vertex_normals, BALD

def to_img(a, vmax, scale=5):
    v = np.clip(a / vmax, -1, 1)
    r = np.where(v > 0, 255, 255 * (1 + v)); b = np.where(v < 0, 255, 255 * (1 - v)); g = 255 * (1 - np.abs(v))
    im = Image.fromarray(np.stack([r, g, b], -1).astype(np.uint8))
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST)

def run(out, items, box_m=(-0.15, 0.15, 1.08, 1.34), s1=1.6, s2=9.0, vmax=22.0):
    box = ph.roi_box('front', *box_m)
    pb = ph.plate_bp('front', box, s1, s2)
    cols = [('PLATE', to_img(pb, vmax))]
    for tag, path in items:
        co = np.load(path).astype(np.float64)
        mb, mask, img = ph.model_bp(co, 'front', box, s1, s2)
        cols.append((tag, to_img(mb, vmax)))
    W = sum(c[1].width for c in cols); H = cols[0][1].height
    im = Image.new('RGB', (W, H + 20), (255, 255, 255)); d = ImageDraw.Draw(im); x = 0
    for t, c in cols:
        im.paste(c, (x, 20)); d.text((x + 4, 4), t + f'  (red=brighter than local mean, blue=darker, +-{vmax:.0f} grey)', fill=(0, 0, 0)); x += c.width
    im.save(out); print(out, im.size, 'box', box)

if __name__ == '__main__':
    out = sys.argv[1]
    items = [a.split('=', 1) for a in sys.argv[2:]]
    run(out, items)
