"""Zone audit of the STAGED blend dump vs the start dump.  py.sh audit3.py <staged.npz> <out.json> [base.npz]"""
import sys, json, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
from hlib import *
from collections import Counter
st = np.load(sys.argv[1]); base = np.load(sys.argv[3] if len(sys.argv) > 3 else W / 'data/mesh_cur.npz')
V0 = base['V'].astype(np.float32); V1 = st['V'].astype(np.float32); N0 = len(V0)
out = {}
out['verts_start'] = int(N0); out['verts_staged'] = int(len(V1)); out['appended'] = int(len(V1) - N0)
moved = (V1[:N0] != V0).any(1)
shell = np.zeros(N0, bool); ring = np.zeros(N0, bool)
for s in (+1, -1): shell[np.load(W / f'data/shellv_{s}.npy')] = True; ring[np.load(W / f'data/ring_{s}.npy')] = True
out['moved_original_verts'] = int(moved.sum()); out['moved_in_hand_shell'] = int((moved & shell).sum()); out['shell_verts'] = int(shell.sum())
out['moved_outside_hand_shell'] = int((moved & ~shell).sum())
out['weld_ring_verts'] = int(ring.sum()); out['weld_ring_moved'] = int((moved & ring).sum())
zone_all = np.load(W / 'data/zone_R.npy') | np.load(W / 'data/zone_L.npy')
out['arm_zone_excluding_hand_shell_moved'] = int((moved & zone_all & ~shell).sum())
x = V0[:, 0]; z = V0[:, 2]
regions = {'head_neck(z>=1.40)': z >= 1.40, 'torso+pelvis(|x|<0.215,0.78<=z<1.40)': (np.abs(x) < 0.215) & (z >= 0.78) & (z < 1.40), 'legs_feet(z<0.78,|x|<0.40)': (z < 0.78) & (np.abs(x) < 0.40),
           'arm_shafts+deltoids(arm zone minus hand shell)': zone_all & ~shell}
out['bit_identical'] = {k: bool((~moved[m]).all()) for k, m in regions.items()}
# polygons: every start polygon that touches neither shell vertices nor was removed must still exist unchanged
def canon(p):
    p = list(p); k = p.index(min(p)); return tuple(p[k:] + p[:k])
def polys_of(D): return [tuple(int(i) for i in D['corner_verts'][s:s + t]) for s, t in zip(D['loop_start'], D['loop_total'])]
P0 = polys_of(base); P1 = polys_of(st)
keep0 = [p for p in P0 if not any(shell[v] for v in p)]
c1 = Counter(canon(p) for p in P1); c0 = Counter(canon(p) for p in keep0)
out['non_hand_polys_start'] = len(keep0); out['non_hand_polys_preserved'] = bool(all(c1[k] >= v for k, v in c0.items()))
out['polys_start'] = len(P0); out['polys_staged'] = len(P1)
out['tris_start'] = int(sum(len(p) - 2 for p in P0)); out['tris_staged'] = int(sum(len(p) - 2 for p in P1))
out['sharp_face_true'] = int(st['sharp_face'].sum()) if 'sharp_face' in st.files else 0
out['custom_normal_nonzero_start'] = int((base['custom_normal_i16'] != 0).any(1).sum()) if 'custom_normal_i16' in base.files else None
out['custom_normal_nonzero_staged'] = int((st['custom_normal_i16'] != 0).any(1).sum()) if 'custom_normal_i16' in st.files else None
out['vg_entries_equal'] = bool(len(base['vg_idx']) == len(st['vg_idx']) and np.array_equal(base['vg_idx'], st['vg_idx']) and np.array_equal(base['vg_gr'], st['vg_gr']) and np.allclose(base['vg_w'], st['vg_w']))
# max move of the shell vertices that existed before (informational) and appended extents
d = np.linalg.norm(V1[:N0] - V0, axis=1) * 1000
out['max_move_hand_shell_mm'] = float(d[shell].max()); out['mean_move_hand_shell_mm'] = float(d[shell].mean())
out['all_conditions_ok'] = bool(out['moved_outside_hand_shell'] == 0 and out['weld_ring_moved'] == 0 and all(out['bit_identical'].values()) and out['non_hand_polys_preserved'] and out['vg_entries_equal'])
json.dump(out, open(sys.argv[2], 'w'), indent=1); print(json.dumps(out, indent=1))
