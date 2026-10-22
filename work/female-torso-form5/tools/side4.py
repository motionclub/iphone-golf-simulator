"""side4.py: side-profile overlay (model silhouette edge on the plate profile panel) for several variants + contour error vs the sub-pixel plate contour.
python3 tools/side4.py out.png tag=coords.npy ..."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/gate7')
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
from sil import raster
from viz3 import font
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = HERE.rsplit('/work/', 1)[0] + '/'
d0 = np.load(HERE + '/data/orig.npz'); tri = d0['tri']
SHEET = Image.open(ROOT + 'ArtDir/hero/base_lock/female_multiangle_body.jpg').convert('RGB')
S2 = 1.7039 / 288.5; V0 = 338.5; X0 = 791.5
FF = np.load(HERE + '/data/plate_front_fine4.npy')
def side_uv(co): return np.stack([X0 + co[:, 1] / S2, V0 - co[:, 2] / S2], 1)
def edge(mask):
    mi = Image.fromarray((mask * 255).astype(np.uint8)); mx = np.asarray(mi.filter(ImageFilter.MaxFilter(3))) > 0; mn = np.asarray(mi.filter(ImageFilter.MinFilter(3))) > 0; return mx & ~mn
def panel(co, col, title, box=(745, 92, 850, 215), sc=8):
    base = SHEET.crop(box).resize(((box[2] - box[0]) * sc, (box[3] - box[1]) * sc), Image.LANCZOS); base = ImageEnhance.Contrast(base).enhance(1.6)
    M = raster(side_uv(co), tri, size=(1280, 720), ss=6); E = Image.fromarray((edge(M) * 255).astype(np.uint8)).crop(box).resize(base.size, Image.NEAREST)
    arr = np.asarray(base).copy(); e = np.asarray(E) > 0; arr[e] = col; im = Image.fromarray(arr); dr = ImageDraw.Draw(im)
    for z in np.arange(1.10, 1.40, 0.01):                                 # sub-pixel plate contour (yellow dots)
        v = (V0 - z / S2 - box[1]) * sc; yv = np.interp(z, FF[0], FF[1]); u = (X0 + yv / S2 - box[0]) * sc
        dr.ellipse([u - 3, v - 3, u + 3, v + 3], outline=(255, 215, 0), width=2)
    dr.rectangle([0, 0, 300, 28], fill=(0, 0, 0)); dr.text((6, 4), title, fill=(255, 255, 255), font=font(18)); return im
if __name__ == '__main__':
    out = sys.argv[1]; items = [a.split('=', 1) for a in sys.argv[2:]]
    cols = [(255, 60, 60), (40, 230, 90), (70, 150, 255), (255, 160, 40)]
    ps = [panel(np.load(p).astype(np.float64), cols[i % 4], t) for i, (t, p) in enumerate(items)]
    W = Image.new('RGB', (sum(p.width for p in ps), ps[0].height)); x = 0
    for p in ps: W.paste(p, (x, 0)); x += p.width
    W.save(out); print(out, W.size)
