import sys, json, subprocess, os, pickle
sys.path.insert(0, '.')
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from edges_ref import cam
from ff_common import *
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
W_ = R + '/work/male-legs-feet-form2'
BL = '/Applications/Blender.app/Contents/MacOS/Blender'
pass_blend, form_blend, name = sys.argv[1], sys.argv[2], sys.argv[3]
bald = Image.open(R + '/ArtDir/hero/base_lock/male_body_bald.jpg').convert('RGB')
sheet = Image.open(R + '/ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB')
# ---------------------------------------------------------------- 06 calf / knee (plate | PASS | FORM), autocontrast on all three
def crop_view(img, v, z0, z1, xc, xhalf, scale=3):
    mpp, sole, cx = cam(v)
    sgn = 1 if v in ('bald_front', 'left') else -1
    pxc = cx + (xc if v.startswith('bald') else xc) / mpp * (1 if v == 'bald_front' else -1)
    y0 = int(sole - z1 / mpp); y1 = int(sole - z0 / mpp); x0 = int(pxc - xhalf / mpp); x1 = int(pxc + xhalf / mpp)
    return img.crop((x0, y0, x1, y1)).resize(((x1 - x0) * scale, (y1 - y0) * scale), Image.LANCZOS)
def comp(path):
    im = Image.open(path).convert('RGBA'); bg = Image.new('RGBA', im.size, (54, 54, 58, 255)); bg.alpha_composite(im); return bg.convert('RGB')
rows = []
for v, z0, z1, xc, xh, ttl in (('bald_front', 0.10, 0.62, 0.0, 0.31, 'FRONT: knee, shin, ankle'), ('bald_back', 0.10, 0.62, 0.0, 0.31, 'BACK: calf heads, Achilles, heel')):
    pl = crop_view(bald, v, z0, z1, xc, xh)
    a = crop_view(comp(f'{W_}/proof/r_base2/{v}.png'), v, z0, z1, xc, xh); b = crop_view(comp(f'{W_}/proof/r_f1/{v}.png'), v, z0, z1, xc, xh)
    tiles = [ImageOps.autocontrast(t, cutoff=1) for t in (pl, a, b)]
    row = Image.new('RGB', (sum(t.width for t in tiles) + 12, tiles[0].height + 18), (10, 10, 12))
    x = 0
    for t, lab in zip(tiles, ('PLATE', 'PASS (current ArtDir)', 'FORM2')):
        row.paste(t, (x, 18)); ImageDraw.Draw(row).text((x + 6, 4), f'{lab}  {ttl}  (autocontrast)', fill=(255, 255, 0)); x += t.width + 6
    rows.append(row)
S = Image.new('RGB', (rows[0].width, sum(r.height for r in rows) + 6), (10, 10, 12)); y = 0
for r in rows: S.paste(r, (0, y)); y += r.height + 6
S.save(f'{W_}/proof/LEGSF2_06_calf_knee_closeups.png'); print('06', S.size)
# ---------------------------------------------------------------- 08 zone map
V0 = np.load(f'{W_}/data/V_4287.npy'); Vn = np.load(f'{W_}/tmp/V_{name}.npy'); n0 = len(V0)
d = np.linalg.norm(Vn[:n0] - V0, axis=1) * 1000
zone = zone_mask_eff(n0)
panels = []
def plot(ax_x, ax_y, lim, title, size=(520, 700)):
    img = Image.new('RGB', size, (22, 22, 26)); dr = ImageDraw.Draw(img)
    (x0, x1), (y0, y1) = lim
    sx = size[0] / (x1 - x0); sy = size[1] / (y1 - y0)
    def pt(a, b): return ((a - x0) * sx, size[1] - (b - y0) * sy)
    sel = (np.abs(V0[:, 0]) < 0.6)
    for i in np.where(~zone[:n0] & sel)[0]:
        p = pt(V0[i, ax_x], V0[i, ax_y]); dr.point(p, fill=(70, 70, 76))
    for i in np.where(zone[:n0])[0]:
        t = min(d[i] / 8.0, 1.0)
        col = (int(40 + 215 * t), int(120 * (1 - abs(2 * t - 1)) + 40), int(220 * (1 - t) + 30)) if d[i] > 1e-6 else (60, 60, 66)
        p = pt(V0[i, ax_x], V0[i, ax_y]); dr.ellipse((p[0] - 1.2, p[1] - 1.2, p[0] + 1.2, p[1] + 1.2), fill=col)
    for k in range(n0, len(Vn)):
        p = pt(Vn[k, ax_x], Vn[k, ax_y]); dr.ellipse((p[0] - 1.2, p[1] - 1.2, p[0] + 1.2, p[1] + 1.2), fill=(255, 0, 220))
    dr.text((6, 4), title, fill=(255, 255, 0))
    return img
fr = plot(0, 2, ((-0.30, 0.30), (-0.01, 0.80)), 'front (x,z)')
sd = plot(1, 2, ((-0.27, 0.12), (-0.01, 0.80)), 'side (y,z)', size=(400, 700))
tp = plot(0, 1, ((0.10, 0.30), (-0.25, 0.10)), 'feet from above (x,y)', size=(400, 700))
Z = Image.new('RGB', (520 + 400 + 400 + 20, 740), (10, 10, 12)); Z.paste(fr, (0, 40)); Z.paste(sd, (530, 40)); Z.paste(tp, (940, 40))
ImageDraw.Draw(Z).text((6, 6), 'LEGS+FEET FORM2: displacement of the base vertices inside the job zone (blue 0 mm -> red >= 8 mm); grey = bit-identical / outside the zone; magenta = new forefoot vertices', fill=(255, 255, 255))
Z.save(f'{W_}/proof/LEGSF2_08_zone_map.png'); print('08', Z.size)
