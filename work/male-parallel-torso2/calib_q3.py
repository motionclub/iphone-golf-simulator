"""Calibrate yaw / column offset / scale of the sheet's four 3/4 panels by silhouette IoU against the current mesh. python3.13 calib_q3.py"""
import sys, json, math
sys.path.insert(0, '.')
import numpy as np
from PIL import Image
V = np.load('data/V_base.npy')
Vb = V[(V[:, 2] < 1.66)]
PAN = {'q3FL': (30, 375, 340, 690), 'q3FR': (350, 375, 640, 690), 'q3BL': (650, 375, 930, 690), 'q3BR': (950, 375, 1240, 690)}
def splat(col, row, shape, r=1):
    m = np.zeros(shape, bool); ci = np.round(col).astype(int); ri = np.round(row).astype(int)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            c2 = ci + dx; r2 = ri + dy; ok = (c2 >= 0) & (c2 < shape[1]) & (r2 >= 0) & (r2 < shape[0]); m[r2[ok], c2[ok]] = True
    return m
def dil(m, k): 
    out = m.copy()
    for dy in range(-k, k + 1):
        for dx in range(-k, k + 1): out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out
def ero(m, k): return ~dil(~m, k)
res = {}
for name, box in PAN.items():
    pm = np.array(Image.open(f'r/mask_{name}.png')) > 127; bb = np.load(f'r/mask_{name}.npy'); x0, y0, x1, y1 = box
    full = np.zeros((720, 1280), bool); full[y0:y1, x0:x1] = pm
    best = None
    az_list = list(range(20, 61, 2)) + list(range(-60, -19, 2)) + list(range(120, 161, 2)) + list(range(-160, -119, 2))
    for az in az_list:
        a = math.radians(az)
        for mpp in (0.00572, 0.00580, 0.00588):
            sole = bb[3]; u = V[:, 0] * math.cos(a) + V[:, 1] * math.sin(a)
            # centre columns of the splatted silhouette on the plate mask bbox centre
            col0 = u / mpp; row = sole - (V[:, 2] - V[:, 2].min()) / mpp
            off = 0.5 * (bb[0] + bb[2]) - 0.5 * (col0.min() + col0.max())
            for dc in (-6, -3, 0, 3, 6):
                col = col0 + off + dc
                sm = splat(col, row, full.shape, 2); sm = ero(dil(sm, 2), 2)
                inter = (sm & full).sum(); uni = (sm | full).sum(); iou = inter / uni
                if best is None or iou > best[0]: best = (iou, az, mpp, off + dc, sole)
    res[name] = dict(iou=float(best[0]), yaw=best[1], mpp=best[2], col_off=float(best[3]), sole_row=int(best[4]))
    print(name, res[name])
json.dump(res, open('data/q3_calib.json', 'w'), indent=1)
