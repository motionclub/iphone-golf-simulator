"""relit luminance profiles vs z at |x| columns: plate vs candidates (quick.py renders r/<tag>_q[h]/back@4:846_283_985_415.png).
python3 lumprof3.py out.png h|n tag1,tag2,.. [u list]"""
import sys, json, numpy as np
from PIL import Image, ImageDraw
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
CAM = {c['name']: c for c in json.load(open(R + '/work/male-silhouette/reference-cameras.json'))['views']}
out = sys.argv[1]; relit = sys.argv[2] == 'h'; tags = sys.argv[3].split(','); us = [float(v) for v in sys.argv[4].split(',')] if len(sys.argv) > 4 else [0, 10, 20, 30, 45, 60, 80, 100]
c = CAM['bald_back']; mpp = c['metres_per_pixel']; cx = c['centre_x']; sy = c['sole_y']; X0, Y0, K = 846, 283, 4
plate = np.asarray(Image.open(R + '/ArtDir/hero/base_lock/male_body_bald.jpg').convert('L'), float)
def prof_plate(u, zs):
    o = []
    for z in zs:
        row = sy - z / mpp; v = []
        for s in (1, -1):
            col = cx + s * u / 1000 / mpp; r0, c0 = int(round(row)), int(round(col)); v.append(plate[r0 - 1:r0 + 2, c0 - 1:c0 + 2].mean())
        o.append(np.mean(v))
    return np.array(o)
def prof_img(img, u, zs):
    o = []
    for z in zs:
        row = (sy - z / mpp - Y0) * K; v = []
        for s in (1, -1):
            col = (cx + s * u / 1000 / mpp - X0) * K; r0, c0 = int(round(row)), int(round(col))
            if 0 <= r0 < img.shape[0] and 0 <= c0 < img.shape[1]: v.append(img[max(r0 - 2, 0):r0 + 3, max(c0 - 2, 0):c0 + 3].mean())
        o.append(np.mean(v) if v else np.nan)
    return np.array(o)
zs = np.arange(0.72, 0.93, 0.002)
imgs = {t: np.asarray(Image.open(f'r/{t}_q{"h" if relit else ""}/back@4:846_283_985_415.png').convert('L'), float) for t in tags}
cols = [(90, 170, 255), (90, 255, 140), (255, 190, 60), (255, 90, 90), (230, 120, 255)]
H = 280; W = int(len(zs) * 3)
S = Image.new('RGB', (W * 2 + 10, (H + 30) * ((len(us) + 1) // 2)), (16, 16, 16)); d = ImageDraw.Draw(S)
for i, u in enumerate(us):
    ox = (i % 2) * (W + 10); oy = (i // 2) * (H + 30)
    pp = prof_plate(u, zs); mu, sd = np.nanmean(pp), np.nanstd(pp) + 1e-6
    d.text((ox + 4, oy + 2), f'|x| = {u:.0f} mm  luminance (z-score vs plate) z .72 -> .93', fill=(255, 200, 80))
    d.line([(ox + j * 3, oy + 20 + H / 2 - (pp[j] - mu) / sd * 55) for j in range(len(zs))], fill=(255, 255, 255), width=2)
    for ti, t in enumerate(tags):
        p = prof_img(imgs[t], u, zs); ok = np.isfinite(p)
        # match mean/std over the window to the plate's (lighting differs)
        pn = (p - np.nanmean(p)) / (np.nanstd(p) + 1e-6)
        d.line([(ox + j * 3, oy + 20 + H / 2 - pn[j] * 55) for j in range(len(zs)) if ok[j]], fill=cols[ti % len(cols)], width=2)
        d.text((ox + W - 120, oy + 4 + 12 * ti), t, fill=cols[ti % len(cols)])
    for zz in (0.74, 0.76, 0.78, 0.80, 0.85, 0.90):
        xx = ox + (zz - 0.72) / 0.002 * 3; d.line([(xx, oy + 20), (xx, oy + 20 + H)], fill=(55, 55, 70)); d.text((xx + 2, oy + 20 + H - 12), f'{zz:.2f}', fill=(130, 130, 150))
S.save(out); print(out, S.size)
