"""Assemble a candidate Body_F mesh: start mesh (arms candidate 573ab443) with both hand shells replaced by fhand hands.

usage (./py.sh): python asm_f.py <tag> ['<json params>']
writes data/cand_<tag>.npz (V, corner_verts, loop_start, loop_total, meta) + prints a report.
Existing vertex indices never change meaning: the freed hand-shell vertex slots (654 / 672) are reused, extra vertices are appended.
Arm shafts, the wrist rings and every vertex outside the hand shells keep their exact start coordinates.
"""
import sys, json, time, os
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parent
sys.path.insert(0, str(W))
from femlib import *
import fhand

BASE_MESH = os.environ.get('BASE_MESH', 'data/mesh_start.npz')
M0 = Mesh.from_npz(W / BASE_MESH)
V0 = M0.V.astype(np.float64); POLYS0 = M0.polys; N0 = len(V0)

# --- frame / placement defaults (the +x hand; the -x hand is built in the x-mirrored frame)
POSE0 = dict(
    O=(0.2320, 0.0003, 0.8456),        # crease centre (= +x ring centre)
    out_deg=4.0, lean_deg=0.0,         # hand direction D: fingers tilt outward / forward from vertical
    psi_deg=0.0,                       # palm turn about D (positive = palm toward the back)
    shear_y=0.028, shear_L=0.100, shear_m0=0.157,   # forward (-y) shift of the hand relative to the wrist ring: cubic Hermite, start slope shear_m0 (= forearm lean), end slope 0 at w = shear_L
    shear_x=0.0,                       # outward (+x in the mirrored frame) shift ramp
    neck_dw=0.0075,                    # row spacing of the neck rows for a ring above the crease
)


def make_frame_for(pose):
    D = (np.tan(np.radians(pose['out_deg'])), -np.tan(np.radians(pose['lean_deg'])), -1.0)
    return Frame(pose['O'], D, pose['psi_deg'])


def side_data(side):
    return (np.load(W / f'data/start_hand_ring_{side}.npy'), np.load(W / f'data/start_hand_verts_{side}.npy'), np.load(W / f'data/start_hand_faces_{side}.npy'))


def apply_pose_shear(Lloc, pose):
    """displace local-frame positions (a,n,w) -> returns global-frame displacement vector additions are done after to_global; here we return per-vertex weights"""
    w = Lloc[:, 2]
    s = smooth01(w / pose['shear_L'])
    return s


def assemble(params=None, pose=None, verbose=True, base_V=None):
    t0 = time.time()
    pose_ = dict(POSE0); pose_.update(pose or {})
    FR = make_frame_for(pose_)
    V = (V0 if base_V is None else base_V).copy(); polys_new = []; extra = []; removed_all = np.zeros(len(POLYS0), bool)
    sides_info = {}
    for side in (+1, -1):
        ring, slots, rem_faces = side_data(side)
        L = FR.to_local(V0, side)
        rl = L[ring]
        w_weld = float(rl[:, 2].mean())
        neck = None
        if w_weld < -0.004:
            first = (params or {}).get('w_rows', fhand.P0['w_rows'])[0]
            n_neck = int(np.ceil((first - w_weld) / pose_['neck_dw'])) - 1
            neck = list(np.linspace(w_weld, first, n_neck + 2)[1:-1]) if n_neck > 0 else None
        ref_L = FR.to_local(V0, +1)[np.load(W / 'data/start_hand_ring_1.npy')] if side < 0 else None
        B, info = fhand.build_hand(ring.tolist(), rl, N0, params, w_weld_rows=neck, ref_ring_L=ref_L)
        used = sorted(set(v for f in B.faces for v in f if v >= N0))
        mapping = {}
        for k, vid in enumerate(used):
            if k < len(slots): mapping[vid] = int(slots[k])
            else:
                mapping[vid] = N0 + len(extra); extra.append(None)
        loc = np.array([B.pos[v - N0] for v in used])
        G = FR.to_global(loc, side)
        # --- placement shear (hand relative to the wrist ring): forward (-y) and optional outward ramp, zero value and slope at the ring
        t_ = np.clip(loc[:, 2] / pose_['shear_L'], 0, 1)
        s = pose_['shear_y'] * (3 * t_ ** 2 - 2 * t_ ** 3) + pose_['shear_m0'] * pose_['shear_L'] * (t_ ** 3 - 2 * t_ ** 2 + t_)
        s = np.where(loc[:, 2] > 0, s, 0.0)
        G[:, 1] += -s
        G[:, 0] += side * pose_['shear_x'] * smooth01(loc[:, 2] / pose_['shear_L'])
        for k, vid in enumerate(used):
            m = mapping[vid]
            if m < N0: V[m] = G[k]
            else: extra[m - N0] = G[k]
        assert len(used) >= len(slots), f'new hand has {len(used)} verts < {len(slots)} slots'
        mf = [tuple(mapping.get(v, v) for v in f) for f in B.faces]
        sides_info[side] = dict(B=B, info=info, mapping=mapping, faces=mf, n_new=len(used), n_slots=len(slots), used=used, w_weld=w_weld, neck=neck)
        removed_all[rem_faces] = True
        polys_new.append(mf)
    Vn = np.vstack([V, np.array(extra)]) if extra else V
    kept = [POLYS0[i] for i in range(len(POLYS0)) if not removed_all[i]]
    ring_all = set()
    for side in (+1, -1): ring_all |= set(int(i) for i in np.load(W / f'data/start_hand_ring_{side}.npy'))
    fixed = [p for p in kept if any(v in ring_all for v in p)]
    allnew = [f for mf in polys_new for f in mf]
    oriented, vis = orient_consistently(allnew, fixed)
    assert all(vis[len(fixed):]), 'unreached new faces during orientation'
    polys = kept + oriented
    if verbose:
        print('assembled: verts %d (+%d appended) polys %d (kept %d + new %d) tris %d in %.1fs' % (len(Vn), len(extra), len(polys), len(kept), len(oriented), tri_count(polys), time.time() - t0))
    return Vn, polys, sides_info, removed_all


def save(path, Vn, polys, removed, meta=None):
    M = Mesh(Vn.astype(np.float32), polys)
    cv, ls, lt = M.arrays()
    np.savez(path, V=M.V, corner_verts=cv, loop_start=ls, loop_total=lt, removed_faces=np.nonzero(removed)[0].astype(np.int32), **(meta or {}))


if __name__ == '__main__':
    tag = sys.argv[1]
    arg = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    pose = arg.pop('pose', None) if isinstance(arg, dict) else None
    Vn, polys, si, removed = assemble(arg, pose)
    mani = check_manifold(polys); mani0 = check_manifold(POLYS0)
    print('manifold new', mani, 'orig', mani0)
    for s in (+1, -1):
        print('side', s, 'new verts', si[s]['n_new'], 'slots', si[s]['n_slots'], 'w_weld %.4f' % si[s]['w_weld'], 'neck', None if si[s]['neck'] is None else np.round(si[s]['neck'], 4).tolist())
    save(W / f'data/cand_{tag}.npz', Vn, polys, removed)
    print('saved', tag)
