"""See-through slot measurement from 4x silhouette renders (rig 'sil' look): widths (mm) at z levels + apex z, front and back.
python3 slotw.py tag1 tag2 ...   (renders r/sil4_<tag>/ via rv.sh if missing)"""
import sys, json, os, subprocess, numpy as np
from PIL import Image
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
CAM = {c['name']: c for c in json.load(open(R + '/work/male-silhouette/reference-cameras.json'))['views']}
ZS = (0.70, 0.71, 0.72, 0.73, 0.735, 0.74, 0.745, 0.75, 0.755, 0.76, 0.765, 0.77)
def measure(tag):
    out = {}
    d = f'r/sil4_{tag}'
    if not os.path.exists(d + '/back@4.png'): subprocess.run(['./rv.sh', tag, f'sil4_{tag}', 'front@4,back@4', 'sil'], check=False)
    for view in ('front', 'back'):
        a = np.asarray(Image.open(f'{d}/{view}@4.png'))[..., 3] > 127; c = CAM['bald_' + view]; mpp = c['metres_per_pixel']; cx = c['centre_x'] * 4; sy = c['sole_y']; k = 4
        row = {}
        for z in ZS:
            r = int(round((sy - z / mpp) * k)); line = a[r]; ic = int(round(cx))
            if line[ic]: row[z] = 0.0; continue
            l = ic
            while l > 0 and not line[l]: l -= 1
            rr = ic
            while rr < len(line) - 1 and not line[rr]: rr += 1
            row[z] = (rr - l) * mpp / k * 1000
        apex = None
        for z in np.arange(0.84, 0.60, -0.0005):
            r = int(round((sy - z / mpp) * k)); cc = int(round(cx))
            if (not a[r, cc - 1:cc + 2].any()) and all(not a[int(round((sy - (z - dz) / mpp) * k)), cc - 1:cc + 2].any() for dz in (0.01, 0.03, 0.05)): apex = float(z); break
        out[view] = dict(widths_mm={f'{z:.3f}': round(v, 1) for z, v in row.items()}, apex_z=apex)
    return out
if __name__ == '__main__':
    for t in sys.argv[1:]:
        m = measure(t); print(t)
        for v in ('front', 'back'):
            w = m[v]['widths_mm']; print(f'  {v:5s} apex {m[v]["apex_z"]}  widths @ z .72/.735/.745/.755/.765: ' + ' / '.join(f'{w[k]:.0f}' for k in ('0.720', '0.735', '0.745', '0.755', '0.765')))
