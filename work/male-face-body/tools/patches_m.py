"""Male skin/lip/stubble patches, mm in the finished-face frame (x right, y up from the eye line), reference sheet 07 front vs a Unity
front render (MaleFaceReview 1080 px, 0.3426 mm/px).  python3 tools/patches_m.py <unity front.png> [eye_row] [out.json]"""
import sys, json, numpy as np
from PIL import Image
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import patches as PT
SHEET = '../../ArtDir/style/alive/male-reference-pack-2026-10-17/sheets/07-head-skin-neutral.png'
RS = 253.8 / (472 - 150); REYE = (359.5, 301)               # ref mm/px, eye line centre
US = .370 / 1080 * 1000; UEYE = (540, float(sys.argv[2]) if len(sys.argv) > 2 else 540)
P = {'forehead': (0, 48, 12, 7), 'cheek_L': (-40, -32, 6, 5), 'cheek_R': (40, -32, 6, 5), 'upper_lip_stubble': (0, -61, 6, 2.5),
     'chin_stubble': (0, -112, 8, 5), 'jaw_stubble_L': (-48, -92, 5, 5), 'jaw_stubble_R': (48, -92, 5, 5), 'lower_lip': (0, -88, 7, 2),
     'upper_lip': (0, -79, 6, 1.5), 'neck': (0, -158, 10, 6)}
def box(c, s, x, y, w, h): return (int(c[0] + (x - w) / s), int(c[1] - (y + h) / s), int(c[0] + (x + w) / s), int(c[1] - (y - h) / s))
ref = Image.open(SHEET).convert('RGB'); ours = Image.open(sys.argv[1]).convert('RGB'); rows = {}
for k, (x, y, w, h) in P.items():
    r = PT.mean(ref, box(REYE, RS, x, y, w, h)); o = PT.mean(ours, box(UEYE, US, x, y, w, h)); lr, lo = PT.lab(r), PT.lab(o)
    rows[k] = dict(ref='#%02X%02X%02X' % tuple(r.astype(int)), ours='#%02X%02X%02X' % tuple(o.astype(int)), dE00=round(PT.de2000(lr, lo), 1),
                   dL=round(lo[0] - lr[0], 1), da=round(lo[1] - lr[1], 1), db=round(lo[2] - lr[2], 1), refLab=np.round(lr, 1).tolist())
    print(f"{k:18s} ref {rows[k]['ref']} ours {rows[k]['ours']} dE00 {rows[k]['dE00']:5.1f}  dL {rows[k]['dL']:6.1f} da {rows[k]['da']:6.1f} db {rows[k]['db']:6.1f}   refLab {rows[k]['refLab']}")
if len(sys.argv) > 3: json.dump(rows, open(sys.argv[3], 'w'), indent=1)
