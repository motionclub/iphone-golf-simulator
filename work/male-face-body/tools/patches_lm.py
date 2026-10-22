"""Landmark-anchored skin/lip/stubble patches: reference sheet 07 front vs a Unity MaleFaceReview front (1080 px, 0.3426 mm/px).
python3 tools/patches_lm.py <unity front.png> <eye_row> <nostril_row> <seam_row> [out.json]
Rows between landmarks are interpolated (eye -> nostril -> seam -> chin); x in mm from the midline."""
import sys, json, numpy as np
from PIL import Image
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import patches as PT
SHEET = '../../ArtDir/style/alive/male-reference-pack-2026-10-17/sheets/07-head-skin-neutral.png'
RS = 253.8 / 322; US = .370 / 1080 * 1000
ref_lm = dict(cx=359.5, eye=301, nose=367, seam=405, chin=472)
e, n, s = (float(v) for v in sys.argv[2:5]); our_lm = dict(cx=540, eye=e, nose=n, seam=s, chin=e + 134.0 / US)
# patch: (x mm, landmark a, landmark b, t in [0,1] between them (or offset rows in mm if a == b), half-size mm)
P = {'forehead': (0, 'eye', 'eye', 48, 10), 'cheek_L': (-40, 'eye', 'nose', .55, 5), 'cheek_R': (40, 'eye', 'nose', .55, 5),
     'upper_lip_stubble': (0, 'nose', 'seam', .55, 2.5), 'upper_lip': (0, 'seam', 'seam', 3.0, 1.2), 'lower_lip': (0, 'seam', 'seam', -5.0, 1.8),
     'chin_stubble': (0, 'seam', 'chin', .55, 5), 'jaw_stubble_L': (-46, 'seam', 'chin', .25, 4), 'jaw_stubble_R': (46, 'seam', 'chin', .25, 4),
     'neck': (0, 'chin', 'chin', -22, 7)}
def at(lm, sc, x, a, b, t, hs):
    row = lm[a] - t / sc if a == b else lm[a] + (lm[b] - lm[a]) * t
    c = lm['cx'] + x / sc; r = hs / sc; return (int(c - r), int(row - r), int(c + r), int(row + r))
ref = Image.open(SHEET).convert('RGB'); ours = Image.open(sys.argv[1]).convert('RGB'); rows = {}
for k, (x, a, b, t, hs) in P.items():
    r = PT.mean(ref, at(ref_lm, RS, x, a, b, t, hs)); o = PT.mean(ours, at(our_lm, US, x, a, b, t, hs)); lr, lo = PT.lab(r), PT.lab(o)
    rows[k] = dict(ref='#%02X%02X%02X' % tuple(r.astype(int)), ours='#%02X%02X%02X' % tuple(o.astype(int)), dE00=round(PT.de2000(lr, lo), 1),
                   dL=round(lo[0] - lr[0], 1), da=round(lo[1] - lr[1], 1), db=round(lo[2] - lr[2], 1))
    print(f"{k:18s} ref {rows[k]['ref']} ours {rows[k]['ours']} dE00 {rows[k]['dE00']:5.1f}  dL {rows[k]['dL']:6.1f} da {rows[k]['da']:6.1f} db {rows[k]['db']:6.1f}")
if len(sys.argv) > 5: json.dump(rows, open(sys.argv[5], 'w'), indent=1)
