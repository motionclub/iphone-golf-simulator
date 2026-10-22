"""Finalize: apply the declared zone masks to a candidate, drop sub-0.02 mm noise, float32 as stored, write data/V_<out>.npy, export/f3_delta.npz and the zone report.
python3 finalize_f3.py <in_tag> <out_tag>"""
import sys, json, numpy as np
sys.path.insert(0, '.')
from common import *
tin, tout = sys.argv[1], sys.argv[2]
V = np.load(f'data/V_{tin}.npy'); X, Y, Z = V0[:, 0], V0[:, 1], V0[:, 2]; U = np.abs(X)
PEL = (Z >= 0.77) & (Z <= 1.07) & (U <= 0.22); LEG = (Z >= 0.705) & (Z < 0.77) & (U <= 0.22); IN = PEL | LEG
D = V - V0; d = np.linalg.norm(D, axis=1) * 1000
rep = dict(zones=dict(PELVIS='z in [0.77,1.07], |x|<=0.22', LEG_TOP='z in [0.705,0.77), |x|<=0.22'), moved_before_mask=int((d > 1e-4).sum()), moved_outside_zone_before_mask=int(((d > 1e-4) & ~IN).sum()))
V2 = V0.copy(); keep = IN & (d >= 0.02); V2[keep] = V[keep]
A0 = V0.astype(np.float32); A2 = V2.astype(np.float32); moved = np.any(A0 != A2, axis=1); V2 = np.where(moved[:, None], A2.astype(np.float64), V0)
dd = np.linalg.norm(V2 - V0, axis=1) * 1000
rep.update(moved=int(moved.sum()), moved_in_PELVIS=int((moved & PEL).sum()), moved_in_LEG_TOP=int((moved & LEG).sum()), moved_outside_zones=int((moved & ~IN).sum()), max_move_mm=float(dd.max()), mean_move_mm=float(dd[moved].mean()),
           max_move_PELVIS_mm=float(dd[moved & PEL].max()), max_move_LEG_TOP_mm=float(dd[moved & LEG].max()), moved_below_z0p735=int((moved & (Z < 0.735)).sum()), max_move_below_z0p735_mm=float(dd[moved & (Z < 0.735)].max()) if (moved & (Z < 0.735)).any() else 0.0,
           max_dx_mm=float(np.abs(V2[:, 0] - V0[:, 0]).max() * 1000), max_dy_mm=float(np.abs(V2[:, 1] - V0[:, 1]).max() * 1000), max_dz_mm=float(np.abs(V2[:, 2] - V0[:, 2]).max() * 1000))
edge = ((np.abs(Z - 0.705) < 0.003) | (np.abs(Z - 1.07) < 0.003) | (np.abs(U - 0.22) < 0.003)) & IN; rep['max_move_at_zone_edge_band_mm'] = float(dd[edge].max()) if edge.any() else 0.0
np.save(f'data/V_{tout}.npy', V2); idx = np.where(moved)[0]
np.savez('export/f3_delta.npz', indices=idx.astype(np.int64), base0=A0[idx], new=V2[idx].astype(np.float32))
json.dump(rep, open('export/f3_zone_report.json', 'w'), indent=1); print(json.dumps(rep, indent=1))
