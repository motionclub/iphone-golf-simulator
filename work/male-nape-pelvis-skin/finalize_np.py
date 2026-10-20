"""Apply the declared zone masks to a candidate, drop sub-0.02 mm noise, write data/V_<out>.npy and export/np_delta.npz (+ zone report).
python3.13 finalize_np.py <in_tag> <out_tag>"""
import sys, json, numpy as np
sys.path.insert(0, '.')
from common import *
tin, tout = sys.argv[1], sys.argv[2]
V = np.load(f'data/V_{tin}.npy'); X, Y, Z = V0[:, 0], V0[:, 1], V0[:, 2]; U = np.abs(X)
ZONES = dict(NAPE=dict(z=(1.30, 1.50), ax=0.18), PELVIS=dict(z=(0.725, 1.07), ax=0.22))
NAPE = (Z >= 1.30) & (Z <= 1.50) & (U <= 0.18); PELV = (Z >= 0.725) & (Z <= 1.07) & (U <= 0.22); IN = NAPE | PELV
D = (V - V0); d = np.linalg.norm(D, axis=1) * 1000
rep = dict(zones=ZONES, moved_before_mask=int((d > 1e-4).sum()), moved_outside_zone_before_mask=int(((d > 1e-4) & ~IN).sum()), max_outside_zone_mm_before_mask=float(d[~IN].max()) if (~IN).any() else 0.0)
V2 = V0.copy(); keep = IN & (d >= 0.02); V2[keep] = V[keep]
# float32 as stored in the blend
A0 = V0.astype(np.float32); A2 = V2.astype(np.float32); moved = np.any(A0 != A2, axis=1)
V2 = np.where(moved[:, None], A2.astype(np.float64), V0)
dd = np.linalg.norm(V2 - V0, axis=1) * 1000
rep.update(moved=int(moved.sum()), moved_in_NAPE=int((moved & NAPE).sum()), moved_in_PELVIS=int((moved & PELV).sum()), moved_outside_zones=int((moved & ~IN).sum()), max_move_mm=float(dd.max()), mean_move_mm=float(dd[moved].mean()),
           max_move_nape_mm=float(dd[moved & NAPE].max()), max_move_pelvis_mm=float(dd[moved & PELV].max()), max_move_pelvis_below_z0p77_mm=float(dd[moved & PELV & (Z < 0.77)].max()), moved_pelvis_below_z0p77=int((moved & PELV & (Z < 0.77)).sum()),
           moved_nape_above_z1p42=int((moved & NAPE & (Z > 1.42)).sum()), max_dx_mm=float(np.abs(V2[:, 0] - V0[:, 0]).max() * 1000), max_dy_mm=float(np.abs(V2[:, 1] - V0[:, 1]).max() * 1000), max_dz_mm=float(np.abs(V2[:, 2] - V0[:, 2]).max() * 1000))
# boundary step check: largest displacement among moved vertices within 3 mm of the zone edge
edge = ((np.abs(Z - 0.725) < 0.003) | (np.abs(Z - 1.07) < 0.003) | (np.abs(Z - 1.30) < 0.003) | (np.abs(Z - 1.50) < 0.003) | (np.abs(U - 0.22) < 0.003) | (np.abs(U - 0.18) < 0.003)) & IN
rep['max_move_at_zone_edge_band_mm'] = float(dd[edge].max()) if edge.any() else 0.0
np.save(f'data/V_{tout}.npy', V2); idx = np.where(moved)[0]
np.savez('export/np_delta.npz', indices=idx.astype(np.int64), base0=A0[idx], new=V2[idx].astype(np.float32))
json.dump(rep, open('export/np_zone_report.json', 'w'), indent=1); print(json.dumps(rep, indent=1))
