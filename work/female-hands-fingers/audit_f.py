"""Independent zone audit of a WRITTEN blend against the start dump.   ./py.sh audit_f.py <final_dump.npz> <out.json>
(final_dump = dump_mesh.py of the written blend.)"""
import sys, json
import numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent
S = np.load(W / 'data/mesh_start.npz'); F = np.load(sys.argv[1])
N0 = len(S['V'])
Vs = S['V']; Vf = F['V']
slots = set(); ring = set()
for sd in (1, -1):
    slots |= set(np.load(W / f'data/start_hand_verts_{sd}.npy').tolist()); ring |= set(np.load(W / f'data/start_hand_ring_{sd}.npy').tolist())
moved = np.nonzero(np.any(Vf[:N0] != Vs, axis=1))[0]
moved_set = set(moved.tolist())
out = dict(n_start=int(N0), n_final=int(len(Vf)), appended=int(len(Vf) - N0), slots=len(slots), slots_reused=len(moved_set & slots),
           moved_total=len(moved), moved_outside_shells=len(moved_set - slots), ring_moved=len(moved_set & ring),
           ring_max_mm=float(np.linalg.norm(Vf[sorted(ring)] - Vs[sorted(ring)], axis=1).max() * 1000))
disp = np.linalg.norm(Vf[:N0] - Vs, axis=1)
out['max_disp_outside_shells_mm'] = float(disp[[i for i in range(N0) if i not in slots]].max() * 1000)
# faces: every start polygon that does not touch a slot vertex must exist unchanged in the final mesh
def polys(D): 
    cv, ls, lt = D['corner_verts'], D['loop_start'], D['loop_total']
    return [tuple(int(x) for x in cv[s:s + t]) for s, t in zip(ls, lt)]
def canon(p):
    p = list(p); k = p.index(min(p)); return tuple(p[k:] + p[:k])
ps, pf = polys(S), polys(F)
fin = set(canon(p) for p in pf)
keep = [p for p in ps if not (set(p) & slots)]
missing = [p for p in keep if canon(p) not in fin]
out['faces_checked'] = len(keep); out['faces_missing'] = len(missing); out['faces_unchanged_ok'] = len(missing) == 0
out['faces_removed'] = len(ps) - len(keep)
# faces of the final that touch no slot / appended vertex must be start faces
newv = set(range(N0, len(Vf))) | slots
extra = [p for p in pf if not (set(p) & newv) and canon(p) not in set(canon(q) for q in ps)]
out['final_faces_untouching_shells_not_in_start'] = len(extra)
json.dump(out, open(sys.argv[2], 'w'), indent=1); print(json.dumps(out))
