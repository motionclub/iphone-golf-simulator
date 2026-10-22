"""jaw gate numbers on the delivered meshes.  python3 jaw_audit.py -> data/jaw_audit.json
 1. front-view jaw contour (mesh z-slices) vs the plate's smooth silhouette (cubic fit)       F2 vs F3
 2. normal quality in the jaw zone (w > 0.5): geometry vertex normals vs the analytic surface normals (what the shading used in F2), and F3's shading normals"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np
import fl, meshlib as ml, slices as sl, contour as ct, trial, make_f3
from analytic_normals import surf_normals
res = {}
D = fl.W / 'data/dump'
def load(tag):
    z = np.load(D / f'{tag}.npz'); V = z['Body_F_V']; F = [z['Body_F_F'][z['Body_F_Foff'][i]:z['Body_F_Foff'][i + 1]] for i in range(len(z['Body_F_Foff']) - 1)]
    return V, F
zs = np.arange(1.452, 1.4901, 0.002); tg = ct.target_hw(zs)
for tag in ('F1', 'F2', 'F3'):
    V, F = load(tag); T = ml.tri_fan(F); out = []
    for z in zs:
        polys = sl.slice_axis(V, T, 2, float(z)); pl = sl.chain(polys)
        xm = max((np.abs(p[:, 0]).max() for p in pl), default=np.nan); out.append(xm)
    out = np.array(out); e = out - tg
    res['contour_' + tag] = dict(rms_mm=float(np.sqrt(np.nanmean(e ** 2)) * 1000), max_abs_mm=float(np.nanmax(np.abs(e)) * 1000), mean_mm=float(np.nanmean(e) * 1000), per_z_mm={f'{z:.3f}': float(v * 1000) for z, v in zip(zs, e)})
    print('contour %s vs plate cubic (z 1.452..1.490): rms %.2f mm, max |err| %.2f mm, mean %+.2f mm' % (tag, res['contour_' + tag]['rms_mm'], res['contour_' + tag]['max_abs_mm'], res['contour_' + tag]['mean_mm']))
# normals
an = np.load(fl.W / 'data/anorm_f3.npz'); w = an['w']; zone = np.where(w > 0.5)[0]
for tag, kw in (('F2', dict()), ('F3', make_f3.KW)):
    H, P = trial.make_H(**kw)
    z = np.load(D / f'{tag}.npz'); V = z['Body_F_V'].astype(float)
    F = [z['Body_F_F'][z['Body_F_Foff'][i]:z['Body_F_Foff'][i + 1]] for i in range(len(z['Body_F_Foff']) - 1)]
    Nd, _, _ = ml.vertex_normals(V, F)
    Na = surf_normals(H, V[zone])
    ang = np.degrees(np.arccos(np.clip((Nd[zone] * Na).sum(1), -1, 1)))
    res['normals_geom_vs_analytic_' + tag] = dict(n=int(len(zone)), mean=float(ang.mean()), p90=float(np.percentile(ang, 90)), p99=float(np.percentile(ang, 99)), max=float(ang.max()))
    print('zone verts %d: geometry vertex normal vs analytic normal (%s): mean %.2f p90 %.2f p99 %.2f max %.1f deg' % (len(zone), tag, ang.mean(), np.percentile(ang, 90), np.percentile(ang, 99), ang.max()))
json.dump(res, open(fl.W / 'data/jaw_audit.json', 'w'), indent=1)
