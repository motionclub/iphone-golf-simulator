"""Center-line + extents check of a head vs the plate profile/silhouette.  python3.13 (numpy only):
usage: python3.13 profile_check.py <Vfinal.npy> <Ffinal.pkl>"""
import sys, pickle
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H
V = np.load(sys.argv[1]); F = pickle.load(open(sys.argv[2], 'rb'))
head = (V[:, 2] > 1.40) & (np.abs(V[:, 0]) < 0.14)
E = set()
for f in F:
    if not all(head[i] for i in f): continue
    for i in range(len(f)):
        a, b = f[i], f[(i + 1) % len(f)]; E.add((min(a, b), max(a, b)))
E = np.array(sorted(E))
pe = H.plate_extents()
def section(z):
    a = V[E[:, 0]]; b = V[E[:, 1]]
    m = ((a[:, 2] - z) * (b[:, 2] - z) < 0)
    a = a[m]; b = b[m]
    t = (z - a[:, 2]) / (b[:, 2] - a[:, 2])
    p = a + (b - a) * t[:, None]
    return p
print('row   z      | plate front-y  mesh front-y  d(mm) | plate hw(mm)  mesh hw  d | plate back-y  mesh back-y d')
errs = []
for r in range(90, 262, 6):
    z = float(H.zrow(r)); p = section(z)
    if len(p) == 0: continue
    i = list(pe['rows']).index(r)
    yf_m = p[:, 1].min(); yb_m = p[:, 1].max()
    hw_m = np.abs(p[:, 0]).max() * 1000
    hw_p = pe['hw'][i] * 1000
    # exclude ear rows from width compare (ears are in the plate silhouette)
    ear = 160 <= r <= 212
    print(f"{r:3d} {z:.4f} | {pe['yf'][i]:+.4f} {yf_m:+.4f} {(yf_m - pe['yf'][i]) * 1000:+6.1f} | {hw_p:6.1f} {hw_m:6.1f} {hw_m - hw_p:+6.1f}{' (ears)' if ear else ''} | {pe['yb'][i]:+.4f} {yb_m:+.4f} {(yb_m - pe['yb'][i]) * 1000:+6.1f}")
