"""Assemble the Micro1f body: Micro1e lock everywhere, new hand coordinates (same faces).

python (Blender's python) assemble2.py reproduce      -> proves the pipeline regenerates the lock bit-exactly
python assemble2.py build <tag> [json overrides]       -> writes final/<tag>_verts.npy and reports the diff vs the lock
"""
import sys, json, pickle
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parent
E1 = W.parent / 'male-micro1e'
for p in (str(W), str(E1)):
    if p not in sys.path:
        sys.path.insert(0, p)
import hand_build as HB0, hand_assemble as HA, hand_build2 as HB2

LOCK_VERTS = np.load(E1 / 'final_verts.npy')
LOCK_FACES = pickle.load(open(E1 / 'final_faces.pkl', 'rb'))
BASE = np.load(E1 / 'baseline/mesh.npz')['co'].astype(float)
F0 = np.load(E1 / 'faces.npy')
HEAD = np.load(E1 / 'r/head_s5.npy')

# parameters used for the Micro1e lock (hand_build.P file defaults + the 'k2' overrides of the live session)
LOCK_PARAMS = dict(curl=0.005, r_a=0.0130, r_n=0.0186, f_tip=[0.160, 0.173, 0.164, 0.142], thumb_r=(0.0195, 0.0195, 0.0175, 0.0155))

# Micro1f hand parameters (positions only)
M1F_PARAMS = dict(
    r_a=0.0128, r_n=0.0178, gap=0.0030,
    taper=0.10, taper2=0.07, tip_bulb=0.10,
    f_tip=[0.158, 0.171, 0.162, 0.140],
    splay_deg=[6.0, 2.0, -2.0, -6.0],
    pad_mcp=0.22, pad_pip=0.26, pad_dip=0.18,
    hinge_pip=0.030, hinge_dip=0.030, curl=0.0, curl2=0.0,
    ridge=0.0035, palm_thick=0.0020,
    thenar=0.0090, thenar_sig=0.70, hypo=0.0035,
    thumb_pts=[(0.040, -0.004, 0.036), (0.055, 0.012, 0.047), (0.062, 0.028, 0.072), (0.060, 0.042, 0.098)],
    thumb_r=(0.0235, 0.0220, 0.0190, 0.0158), thumb_flat=0.90,
)


def assemble(params, module):
    """run hand_assemble.assemble with `module` as the hand generator"""
    HA.HB = module
    module.P.update(params)
    verts, faces, info = HA.assemble(BASE.copy(), F0, smooth_iters=(10 if module is HB0 else 0))
    if module is not HB0:
        # weighted Taubin: full at the weld, half on the palm, light on the fingers/thumb so pads and bends survive
        import hand_sdf as H
        w = np.zeros(len(verts))
        for sign in (+1, -1):
            L = H.to_local(verts, sign)
            hand = (sign * verts[:, 0] > 0.30) & (verts[:, 2] < 1.10) & (L[:, 2] > -0.08)
            ww = L[:, 2]
            wt = np.where(ww < 0.0, 1.0, np.where(ww < 0.058, 0.55, SMOOTH_FINGER))
            w[hand] = wt[hand]
        # only the rebuilt hand shell (freed slots + appended vertices) may move: forearm + weld ring stay bit-identical
        import hand_topo as T
        shell = np.zeros(len(verts), bool)
        for sign in (+1, -1):
            shell[:len(BASE)] |= T.extract_cut(BASE, F0, sign, -0.055)['Hmask']
        shell[len(BASE):] = True
        w[~shell] = 0.0
        verts = HA.taubin_new(verts, faces, w, SMOOTH_ITERS)
    verts[:len(BASE)] += (HEAD - BASE)
    return verts, faces, info


SMOOTH_FINGER = 0.18
SMOOTH_ITERS = 10


def report(verts, faces):
    same_faces = (len(faces) == len(LOCK_FACES)) and all(tuple(a) == tuple(b) for a, b in zip(faces, LOCK_FACES))
    d = np.linalg.norm(verts - LOCK_VERTS, axis=1)
    moved = d > 1e-9
    z = LOCK_VERTS[:, 2]; x = LOCK_VERTS[:, 0]
    hand = (np.abs(x) > 0.44) & (z < 1.06)
    out = dict(same_faces=bool(same_faces), n_verts=len(verts), moved=int(moved.sum()), moved_outside_hand_zone=int((moved & ~hand).sum()),
               max_disp_mm=float(d.max() * 1000), max_disp_outside_hand_mm=float(d[~hand].max() * 1000) if (~hand).any() else 0.0)
    return out


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'reproduce':
        import importlib
        importlib.reload(HB0)
        v, f, info = assemble(LOCK_PARAMS, HB0)
        r = report(v, f)
        r['bit_identical'] = bool(np.array_equal(v.astype(np.float32), LOCK_VERTS.astype(np.float32)))
        print(json.dumps(r))
    elif mode == 'build':
        tag = sys.argv[2]
        over = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        params = dict(M1F_PARAMS); params.update(over)
        v, f, info = assemble(params, HB2)
        r = report(v, f)
        (W / 'final').mkdir(exist_ok=True)
        np.save(W / f'final/{tag}_verts.npy', v)
        pickle.dump(f, open(W / f'final/{tag}_faces.pkl', 'wb'))
        json.dump(dict(params=params, report=r, info=info), open(W / f'final/{tag}_build.json', 'w'), indent=1, default=str)
        print(json.dumps(r))
