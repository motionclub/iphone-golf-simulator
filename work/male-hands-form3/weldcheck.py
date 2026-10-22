"""Crease check at the wrist weld on a mesh dump: max dihedral over edges adjacent to the weld ring (faces touching the ring or the first palm row), plus ring-to-first-row radial step.
py.sh weldcheck.py <dump.npz> [out.json]"""
import sys, json, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
from hlib import *
D = np.load(sys.argv[1]); M = Mesh.from_npz(sys.argv[1]); V = M.V.astype(np.float64); polys = M.polys
Fn = face_normals(V, polys); ef = edge_faces(polys)
out = {}
for side, nm in ((+1, 'R'), (-1, 'L')):
    ring = set(int(i) for i in np.load(W / f'data/ring_{side}.npy'))
    shell = set(int(i) for i in np.load(W / f'data/shellv_{side}.npy'))
    # faces touching the ring
    f_ring = set(fi for fi, p in enumerate(polys) if any(v in ring for v in p))
    # first-row vertices = shell vertices adjacent to ring faces
    row1 = set(v for fi in f_ring for v in polys[fi] if v in shell)
    f_band = f_ring | set(fi for fi, p in enumerate(polys) if any(v in row1 for v in p))
    mx = 0.0; n_gt45 = 0; n = 0
    for (a, b), fs in ef.items():
        if len(fs) == 2 and (fs[0] in f_band or fs[1] in f_band):
            ang = np.degrees(np.arccos(np.clip((Fn[fs[0]] * Fn[fs[1]]).sum(), -1, 1))); n += 1; mx = max(mx, ang); n_gt45 += int(ang > 45)
    out[nm] = dict(band_faces=len(f_band), edges=n, max_dihedral_deg=float(mx), gt45=n_gt45)
print(json.dumps(out)); 
if len(sys.argv) > 2: json.dump(out, open(sys.argv[2], 'w'), indent=1)
