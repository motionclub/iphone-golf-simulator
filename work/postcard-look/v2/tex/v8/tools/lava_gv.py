#!/usr/bin/env python3
"""v8 (area T): Game-view lava statistics of a still, using the PostcardProofMasks id mask (exact lava pixels) and, for crater.jpg, a hue/sat mask.
usage: python3 lava_gv.py [still.png id.png meta.json name]   (default: the installed lavarim / approach / tee stills in ArtDir)"""
import json, sys
import numpy as np
from PIL import Image
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
P = R + "/work/postcard-look/v2/proof"

def rgb2hsv(a):
    a = a.astype(np.float64) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1); mn = a.min(-1); d = mx - mn
    h = np.zeros_like(mx); m = d > 1e-9
    rm = m & (mx == r); gm = m & (mx == g) & ~rm; bm = m & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6; h[gm] = (b - r)[gm] / d[gm] + 2; h[bm] = (r - g)[bm] / d[bm] + 4
    return h * 60.0, np.where(mx > 1e-9, d / np.maximum(mx, 1e-9), 0.0), mx

def lum(a): return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]

def comps(mask):
    from scipy import ndimage  # may not exist
    lab, n = ndimage.label(mask); return lab, n

def label(mask):
    h, w = mask.shape; lab = np.zeros((h, w), np.int32); n = 0; sizes = [0]
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not lab[y, x]:
                n += 1; st = [(y, x)]; lab[y, x] = n; c = 0
                while st:
                    cy, cx = st.pop(); c += 1
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                            lab[ny, nx] = n; st.append((ny, nx))
                sizes.append(c)
    return lab, np.array(sizes)

def stats(px, m, name, crop=None, comp=True):
    hh, ss, vv = rgb2hsv(px)
    if crop is not None:
        cm = np.zeros(m.shape, bool); x0, y0, x1, y1 = crop; cm[y0:y1, x0:x1] = True; m = m & cm
    p = px[m].astype(float); hm, sm_, vm = hh[m], ss[m], vv[m]; L = lum(p)
    out = dict(name=name, n=int(m.sum()), mean=[round(float(x), 1) for x in p.mean(0)],
               lum_mean=round(float(L.mean()), 1), lum_sd=round(float(L.std()), 1), lum_p10=round(float(np.percentile(L, 10)), 1), lum_p50=round(float(np.percentile(L, 50)), 1), lum_p90=round(float(np.percentile(L, 90)), 1), lum_p99=round(float(np.percentile(L, 99)), 1),
               V_lt_025=round(float((vm < .25).mean()), 4), V_lt_040=round(float((vm < .40).mean()), 4), V_lt_055=round(float((vm < .55).mean()), 4),
               G_gt_120=round(float((p[:, 1] > 120).mean()), 4), G_gt_150=round(float((p[:, 1] > 150).mean()), 4), G_gt_170=round(float((p[:, 1] > 170).mean()), 4),
               hot_R240_G170=round(float(((p[:, 0] > 240) & (p[:, 1] > 170)).mean()), 4),
               in_band=round(float(((hm >= 8) & (hm <= 28) & (sm_ >= .75) & (vm >= .70)).mean()), 4), hue_mean=round(float(hm.mean()), 1))
    if comp:
        d = np.zeros(m.shape, bool); d[m] = vv[m] < .40
        lab, sizes = label(d)
        if len(sizes) > 1:
            s = sizes[1:]; out["dark_comps"] = int(len(s)); out["dark_largest_px"] = int(s.max()); out["dark_comps_ge_400"] = int((s >= 400).sum())
    return out

if __name__ == "__main__":
    ids = json.load(open(f"{P}/masks/9/masks_meta.json"))
    meta = {s["name"]: s for s in ids["shots"]}
    for name, crop in (("hole10_3_lavarim", (250, 650, 900, 1600)), ("hole10_2_approach", None), ("hole10_1_tee", None)):
        still = np.asarray(Image.open(f"{R}/ArtDir/screenshots/golf_postcards/look/{name}.png").convert("RGB"))
        full = np.asarray(Image.open(f"{P}/masks/9/{name}.full.png").convert("RGB"))
        idm = np.asarray(Image.open(f"{P}/masks/9/{name}.id.png").convert("RGB")).astype(int)
        m = np.abs(idm - np.array(meta[name]["id_colors"]["lava"])).max(2) <= 3
        print(json.dumps(stats(still, m, name, crop)))
    ref = np.asarray(Image.open(R + "/ArtDir/environments/refs/crater.jpg").convert("RGB"))
    hh, ss, vv = rgb2hsv(ref)
    m = (hh >= 5) & (hh <= 45) & (ss > .55) & (vv > .25)
    m[:300] = False
    print(json.dumps(stats(ref, m, "crater.jpg pool (hue 5-45, S>.55, y>=300)", None)))
