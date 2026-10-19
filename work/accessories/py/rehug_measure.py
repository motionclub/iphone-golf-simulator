"""10-17 male cap re-hug: measure caps (N-frame *_final.npz) against a head dump.
blender -b --factory-startup --python rehug_measure.py -- <out.json> <label=cap_dir> ...   (env ACC_DUMP = head dump to measure against)
Per cap: lining clearance (min / mean / p95), band clearance by azimuth sector (front, temple, side, back), front rim height,
lowest brim edge vs the brow line, and (for pairs named X_before / X_after) per-vertex brim displacement."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import acc_common as A, acc_fit as F, cap as CAP

args = A.args_after_dashes()
out_json = args[0]
caps = dict(a.split('=', 1) for a in args[1:])
hd = A.HeroData('Male')
hp, ht = F.region(hd, hd.rest_pos['Head'][2] - 0.07)
clear = F.Clearance(hp, ht)
# brow line: highest brow-ridge skin point in front of the eyes (N frame: hero faces -Y)
yc = .5 * (hp[:, 1].min() + hp[:, 1].max())
res = dict(dump=os.environ.get('ACC_DUMP', 'default'), head_top_z=float(hp[:, 2].max()),
           head_width_at_temple=None)
m = (np.abs(hp[:, 2] - 1.64) < .004) & (hp[:, 1] < yc)
res['head_width_at_temple'] = float(hp[m, 0].max() - hp[m, 0].min()) if m.any() else None
pos_by = {}
for label, d in caps.items():
    z = np.load(os.path.join(d, 'Kit_Cap_final.npz'))
    P, T, k, zo = z['pos'], z['tri'], z['kind'], z['zone']
    pos_by[label] = P
    lin = np.unique(T[((k == CAP.K_CROWN) & (zo == 2)) | ((k == CAP.K_BAND) & (zo == 0))])
    band = np.unique(T[(k == CAP.K_BAND) & (zo == 0)])
    brim = np.unique(T[k == CAP.K_BRIM])
    cl = clear(P[lin]); cb = clear(P[band])
    az = np.degrees(np.arctan2(np.abs(P[band, 0]), -(P[band, 1] - yc)))     # 0 = front, 90 = side, 180 = back
    sect = {}
    for name, lo, hi in (('front', 0, 35), ('temple', 35, 75), ('side', 75, 115), ('back', 115, 181)):
        s = (az >= lo) & (az < hi)
        if s.any(): sect[name] = dict(n=int(s.sum()), mean_mm=round(float(cb[s].mean() * 1e3), 2), max_mm=round(float(cb[s].max() * 1e3), 2), min_mm=round(float(cb[s].min() * 1e3), 2))
    front = brim[np.abs(P[brim, 0]) < .01]
    res[label] = dict(lining_min_mm=round(float(cl.min() * 1e3), 2), lining_mean_mm=round(float(cl.mean() * 1e3), 2), lining_p95_mm=round(float(np.percentile(cl, 95) * 1e3), 2),
                      lining_inside=int((cl < 0).sum()), band_sectors=sect,
                      brim_front_lowest_z=round(float(P[front, 2].min()), 4), brim_front_y=round(float(P[front, 1].min()), 4), cap_top_z=round(float(P[:, 2].max()), 4),
                      width_at_band_mm=round(float((P[band, 0].max() - P[band, 0].min()) * 1e3), 1))
for label in list(pos_by):
    if label.endswith('_before') and label[:-7] + '_after' in pos_by:
        a, b = pos_by[label], pos_by[label[:-7] + '_after']
        z = np.load(os.path.join(caps[label], 'Kit_Cap_final.npz')); T, k = z['tri'], z['kind']
        brim = np.unique(T[k == CAP.K_BRIM]); fr = brim[np.abs(a[brim, 0]) < .03]
        dv = np.linalg.norm(b - a, axis=1)
        res[label[:-7] + '_delta'] = dict(brim_max_mm=round(float(dv[brim].max() * 1e3), 2), brim_front_max_mm=round(float(dv[fr].max() * 1e3), 2),
                                          brim_mean_mm=round(float(dv[brim].mean() * 1e3), 2), all_max_mm=round(float(dv.max() * 1e3), 2))
json.dump(res, open(out_json, 'w'), indent=1)
print(json.dumps(res, indent=1))
