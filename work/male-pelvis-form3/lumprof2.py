"""luminance-vs-z profiles at |x| columns for plate / renders (registered back@4/front@4 crops from crop_cmp.render).
python3 lumprof2.py back|front out.png tag1,tag2 [u list mm]"""
import sys, json, numpy as np
from PIL import Image, ImageDraw
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
CAM = {c['name']: c for c in json.load(open(R + '/work/male-silhouette/reference-cameras.json'))['views']}
view = sys.argv[1]; out = sys.argv[2]; tags = sys.argv[3].split(','); us = [float(v) for v in sys.argv[4].split(',')] if len(sys.argv) > 4 else [0, 10, 20, 30, 45, 60, 80, 100]
c = CAM['bald_' + view]; mpp = c['metres_per_pixel']; cx = c['centre_x']; sy = c['sole_y']
plate = np.asarray(Image.open(R + '/ArtDir/hero/base_lock/male_body_bald.jpg').convert('L'), float)
def col_prof(img, k, u_mm, zs):
    """mean of +u and -u columns (+-1 px), sampled at heights zs; img at k x resolution"""
    out = []
    for z in zs:
        row = (sy - z / mpp) * k; vals = []
        for s in (+1, -1):
            col = (cx + s * u_mm / 1000 / mpp) * k
            r0, c0 = int(round(row)), int(round(col)); sub = img[max(r0 - 1, 0):r0 + 2, max(c0 - 1, 0):c0 + 2]; vals.append(sub.mean())
        out.append(np.mean(vals))
    return np.array(out)
zs = np.arange(0.70, 0.93, 0.002)
imgs = {'PLATE': (plate, 1)}
for t in tags: imgs[t] = (np.asarray(Image.open(f'r/{t}_c/{view}@4.png').convert('L'), float), 4)
cols = {'PLATE': (255, 255, 255), tags[0]: (90, 170, 255), (tags[1] if len(tags) > 1 else 'x'): (90, 255, 140)}
H = 300; W = int(len(zs) * 3)
S = Image.new('RGB', (W * 2 + 10, (H + 30) * ((len(us) + 1) // 2)), (16, 16, 16)); d = ImageDraw.Draw(S)
for i, u in enumerate(us):
    ox = (i % 2) * (W + 10); oy = (i // 2) * (H + 30)
    d.text((ox + 4, oy + 2), f'|x| = {u:.0f} mm  (luminance vs z; z .70 -> .93 left to right)', fill=(255, 200, 80))
    for name, (img, k) in imgs.items():
        p = col_prof(img, k, u, zs)
        # normalise: subtract mean over the window, scale by plate std
        if name == 'PLATE': ref_sd = p.std() + 1e-6
        pn = (p - p.mean()) / ref_sd
        pts = [(ox + j * 3, oy + 20 + H / 2 - pn[j] * 60) for j in range(len(zs))]
        d.line(pts, fill=cols.get(name, (200, 120, 255)), width=2)
    for zz in (0.72, 0.74, 0.76, 0.78, 0.80, 0.85, 0.90):
        xx = ox + (zz - 0.70) / 0.002 * 3; d.line([(xx, oy + 20), (xx, oy + 20 + H)], fill=(55, 55, 70)); d.text((xx + 2, oy + 20 + H - 12), f'{zz:.2f}', fill=(130, 130, 150))
S.save(out); print(out, S.size)
