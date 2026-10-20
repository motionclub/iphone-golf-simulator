"""Fit the kit skin weights so the kit follows the body: projected-gradient minimisation over TRAINING poses (the 8 gate poses and their +-1 frames are held out).

  blender -b export/HeroBase_<Hero>_Dressed.blend --python fit_weights.py -- <male|female> [piece ...]      env: DR_FIT_* knobs, DR_OUT_BLEND

Start = the weights already on the kit (transfer + whitelist + smoothing).  Objective per piece (all in mm):
   L = sum_poses [ lam_poke * sum_zone relu(h + margin)^2          h = (v - H) . N : the body vertex v relative to its HOME outer-wall point (barycentric on its home triangle) and normal
                 + lam_follow * sum_hug |P_k - Q_k|^2              Q_k = nearest-body-point motion plus the bind gap along the body normal (the kit as an offset surface of the body)
                 ] + lam_smooth * sum_edges |w_k - w_j|^2 + lam_reg * |w - w0|^2
subject to w >= 0, sum w = 1 on the piece's whitelisted bones; afterwards pruned to 4 influences and refined on those.  Linear blend skinning is linear in w, so the gradient is exact for
fixed normals.  Writes the weights back into the vertex groups and saves DR_OUT_BLEND (default: overwrite the opened file's path under export/).
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np

from dcommon import *
from follow_lib import *

a_ = args_after_dashes()
tag = a_[0]
only = a_[1:] or PIECES
H = HERO[tag]
sc = bpy.context.scene
rig = bpy.data.objects[H['rig']]
body = bpy.data.objects[H['body']]
kit = {p: bpy.data.objects[KIT_NAME[p]] for p in PIECES}
bones = [b.name for b in rig.data.bones if b.use_deform]
contacts, lengths = contact_seconds(H['label'])


def envf(k, d):
    return float(os.environ.get(k, d))


CFG = dict(iters=int(envf('DR_FIT_ITERS', 120)), refine=int(envf('DR_FIT_REFINE', 40)), lr=envf('DR_FIT_LR', 1e-6), stride=int(envf('DR_FIT_STRIDE', 6)),
           lam_poke=envf('DR_FIT_POKE', 1.0), margin_mm=envf('DR_FIT_MARGIN', 3.0), lam_follow=envf('DR_FIT_FOLLOW', 0.02), lam_smooth=envf('DR_FIT_SMOOTH', 0.5), lam_reg=envf('DR_FIT_REG', 0.2))
OUT = os.environ.get('DR_OUT_BLEND', H['dressed'])


def set_pose(clip, frame):
    if clip is None:
        rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.location = (0, 0, 0)
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.rotation_euler = (0, 0, 0)
            pb.scale = (1, 1, 1)
    else:
        activate_clip(rig, clip)
    sc.frame_set(int(frame))
    bpy.context.view_layer.update()
    return bpy.context.evaluated_depsgraph_get()


rest_inv = {b.name: np.array(b.matrix_local.inverted(), np.float64) for b in rig.data.bones}


def deform_matrices():
    return np.stack([np.array(rig.pose.bones[n].matrix, np.float64) @ rest_inv[n] for n in bones])


# ---- bind -----------------------------------------------------------------------------------------------------------------------------------
dg = set_pose(None, 0)
bco0 = evaluated_co(body, dg)
bn0 = vertex_normals(body)
btri = mesh_tris(body.data)
body_bvh0 = bvh_from(bco0, btri)
Wb = bone_weight_matrix(body, bones)
KT = {p: mesh_tris(kit[p].data) for p in PIECES}
K0 = {p: mesh_co(kit[p]) for p in PIECES}
W0 = {p: bone_weight_matrix(kit[p], bones) for p in PIECES}
EDGES = {}
for p in PIECES:
    me = kit[p].data
    ed = np.empty(len(me.edges) * 2, np.int32)
    me.edges.foreach_get('vertices', ed)
    EDGES[p] = ed.reshape(-1, 2)

# ---- training frames --------------------------------------------------------------------------------------------------------------------------
held = set()
for clip, kind in GATE_POSES:
    f = pose_frame(clip, kind, contacts)
    for d in (-1, 0, 1):
        held.add((clip, f + d))
frames = []
for clip in CLIPS:
    n = int(round(lengths[clip] * FPS))
    for f in range(0, n + 1, CFG['stride']):
        if (clip, f) not in held:
            frames.append((clip, f))
frames.append((None, 0))        # the bind pose itself
print('training poses', len(frames), 'held out', len(held))

# ---- per piece static data ----------------------------------------------------------------------------------------------------------------------
PD = {}
t0 = time.time()
for p in only:
    co0 = K0[p]
    kbv = bvh_from(co0, KT[p])
    zone, ht, hb, it, ib = compute_zone(co0, KT[p], bco0, bn0, body_bvh0, kbv)
    d_bind = np.empty(len(co0))
    ntri = np.empty(len(co0), np.int64)
    nbary = np.empty((len(co0), 3))
    gap = np.empty(len(co0))
    for k in range(len(co0)):
        loc, nrm, idx, d = body_bvh0.find_nearest(tuple(map(float, co0[k])))
        t = btri[idx]
        b = bary_of(np.array(loc), bco0[t[0]], bco0[t[1]], bco0[t[2]])
        n0 = (bn0[t] * b[:, None]).sum(0)
        n0 /= np.linalg.norm(n0)
        ntri[k], nbary[k], gap[k], d_bind[k] = idx, b, float(np.dot(co0[k] - np.array(loc), n0)), d
    hug = np.nonzero(d_bind <= HUG)[0]
    cols = [j for j in range(len(bones)) if W0[p][:, j].max() > 0]
    PD[p] = dict(zone=zone, ht=ht, hb=hb, hug=hug, ntri=ntri[hug], nbary=nbary[hug], gap=gap[hug], cols=cols, w0=W0[p][:, cols].copy())
    print(p, 'zone', len(zone), 'hug', len(hug), 'bones', len(cols), round(time.time() - t0, 1), 's')

# ---- sample the poses -----------------------------------------------------------------------------------------------------------------------------
POSES = []
for (clip, f) in frames:
    dg = set_pose(clip, f)
    D = deform_matrices()
    bco = evaluated_co(body, dg).astype(np.float32)
    bn = evaluated_normals(body, dg).astype(np.float32)
    POSES.append((D, bco, bn))
print('sampled', len(POSES), 'poses', round(time.time() - t0, 1), 's')

for p in only:
    d = PD[p]
    zone, hug = d['zone'], d['hug']
    T = btri[d['ntri']]                    # (nh,3) body corner vertices of the nearest triangle
    d['Dp'] = np.stack([P[0][d['cols']] for P in POSES]).astype(np.float32)               # (np, nb_p, 4, 4)
    d['Vz'] = np.stack([P[1][zone] for P in POSES]).astype(np.float32)                    # (np, nz, 3)
    Qs = []
    for (D, bco, bn) in POSES:
        Bp = (bco[T] * d['nbary'][:, :, None]).sum(1)
        Np_ = (bn[T] * d['nbary'][:, :, None]).sum(1)
        Np_ /= np.maximum(np.linalg.norm(Np_, axis=1, keepdims=True), 1e-12)
        Qs.append(Bp + d['gap'][:, None] * Np_)
    d['Q'] = np.stack(Qs).astype(np.float32)                                              # (np, nh, 3)
    d['K0h'] = np.concatenate([K0[p], np.ones((len(K0[p]), 1))], 1).astype(np.float32)
    # C[pose, k, c, :] is not stored (memory); recomputed per iteration
del POSES


def proj_simplex(V):
    """row-wise Euclidean projection onto {w >= 0, sum w = 1}"""
    n, m = V.shape
    U = -np.sort(-V, axis=1)
    css = np.cumsum(U, axis=1) - 1
    ar = np.arange(1, m + 1)
    cond = U - css / ar > 0
    rho = cond.sum(1) - 1
    theta = css[np.arange(n), rho] / (rho + 1)
    return np.maximum(V - theta[:, None], 0)


def loss_grad(p, W, grad=True):
    d = PD[p]
    nk = len(K0[p])
    tri = KT[p]
    zone, ht, hb = d['zone'], d['ht'], d['hb']
    corner = tri[ht]                                   # (nz, 3) kit vertices of the home triangles
    hug = d['hug']
    marg = CFG['margin_mm'] / 1000.0
    ed = EDGES[p]
    npz = len(d['Dp'])
    gW = np.zeros_like(W)
    Lpoke = Lfol = 0.0
    npoke = 0
    for q in range(npz):
        Dq = d['Dp'][q]                                           # (nb,4,4)
        Cq = np.einsum('cij,kj->kci', Dq, d['K0h'])[..., :3]      # (nk, nb, 3)
        P = np.einsum('kc,kci->ki', W, Cq)
        gP = np.zeros((nk, 3))
        a, b, c = P[corner[:, 0]], P[corner[:, 1]], P[corner[:, 2]]
        Hq = a * hb[:, 0:1] + b * hb[:, 1:2] + c * hb[:, 2:3]
        N = np.cross(b - a, c - a)
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        h = ((d['Vz'][q] - Hq) * N).sum(1)
        r = np.maximum(h + marg, 0.0) * 1000.0                    # mm
        act = r > 0
        npoke += int(act.sum())
        Lpoke += float((r ** 2).sum())
        res = (P[hug] - d['Q'][q]) * 1000.0
        Lfol += float((res ** 2).sum())
        if grad:
            if act.any():
                coef = (-2.0 * CFG['lam_poke'] * r[act] * 1000.0)[:, None] * N[act]
                for ci in range(3):
                    np.add.at(gP, corner[act, ci], hb[act, ci:ci + 1] * coef)
            gP[hug] += 2.0 * CFG['lam_follow'] * res * 1000.0
            gW += np.einsum('ki,kci->kc', gP, Cq)
    diff = W[ed[:, 0]] - W[ed[:, 1]]
    Ls = float((diff ** 2).sum())
    Lr = float(((W - d['w0']) ** 2).sum())
    tot = (CFG['lam_poke'] * Lpoke + CFG['lam_follow'] * Lfol) / npz + CFG['lam_smooth'] * Ls + CFG['lam_reg'] * Lr
    if grad:
        gW /= npz
        sm = np.zeros_like(W)
        np.add.at(sm, ed[:, 0], diff)
        np.add.at(sm, ed[:, 1], -diff)
        gW += 2.0 * CFG['lam_smooth'] * sm + 2.0 * CFG['lam_reg'] * (W - d['w0'])
    return tot, gW, dict(poke=Lpoke / npz, follow=Lfol / npz, active=npoke / npz, smooth=Ls, reg=Lr)


def fit_piece(p, W, mask, iters, lr):
    """projected gradient descent with Armijo backtracking (plain, no momentum: the problem is a sum of convex quadratics/hinges in w)"""
    step = lr
    tot, gW, parts = loss_grad(p, W)
    for it in range(iters):
        g = gW * mask
        ok = False
        for _ in range(12):
            Wn = proj_simplex(np.where(mask > 0, W - step * g, -1e9)) * (mask > 0)
            tn, _, _ = loss_grad(p, Wn, grad=False)
            dec = float((g * (W - Wn)).sum())
            if tn <= tot - 1e-4 * dec:
                ok = True
                break
            step *= 0.5
        if not ok:
            print(f'  {p} it {it}: no decrease, stopping')
            break
        W = Wn
        tot, gW, parts = loss_grad(p, W)
        step *= 1.6
        if it % 10 == 0 or it == iters - 1:
            print(f'  {p} it {it:3d} L {tot:12.1f}  poke/pose {parts["poke"]:10.1f} ({parts["active"]:6.1f} active) follow/pose {parts["follow"]:10.1f} smooth {parts["smooth"]:8.2f} reg {parts["reg"]:8.2f} step {step:.2e}', flush=True)
    return W


if os.environ.get('DR_GRADCHECK'):
    p = only[0]
    W = PD[p]['w0'].copy()
    tot, g, parts = loss_grad(p, W)
    rng = np.random.default_rng(0)
    for _ in range(8):
        k = int(rng.integers(len(W)))
        c = int(rng.integers(W.shape[1]))
        e = 1e-4
        W2 = W.copy(); W2[k, c] += e
        W3 = W.copy(); W3[k, c] -= e
        num = (loss_grad(p, W2, grad=False)[0] - loss_grad(p, W3, grad=False)[0]) / (2 * e)
        print(f'gradcheck k {k} c {c}: analytic {g[k, c]:.4f} numeric {num:.4f}')
    sys.exit(0)


def write_weights(obj, Wfull):
    for vg in list(obj.vertex_groups):
        obj.vertex_groups.remove(vg)
    groups = {}
    for j in range(Wfull.shape[1]):
        if Wfull[:, j].max() > 0:
            groups[j] = obj.vertex_groups.new(name=bones[j])
    for i in range(len(Wfull)):
        for j in np.nonzero(Wfull[i])[0]:
            groups[int(j)].add([i], float(Wfull[i, j]), 'REPLACE')


report = dict(tag=tag, cfg=CFG, pieces={})
for p in only:
    d = PD[p]
    print('fitting', p)
    W = d['w0'].copy()
    W = fit_piece(p, W, np.ones_like(W), CFG['iters'], CFG['lr'])
    # prune to 4 influences, refine on the survivors
    W4 = W.copy()
    W4[W4 < 1e-3] = 0
    order = np.argsort(-W4, axis=1)
    keep = np.zeros_like(W4, bool)
    keep[np.arange(len(W4))[:, None], order[:, :4]] = True
    W4[~keep] = 0
    W4 /= np.maximum(W4.sum(1, keepdims=True), 1e-12)
    if CFG['refine'] > 0:
        W4 = fit_piece(p, W4, keep.astype(float), CFG['refine'], CFG['lr'] * 0.5)
    W4[W4 < 1e-3] = 0
    W4 /= np.maximum(W4.sum(1, keepdims=True), 1e-12)
    full = np.zeros((len(K0[p]), len(bones)))
    full[:, d['cols']] = W4
    assert (full > 0).sum(1).max() <= 4
    write_weights(kit[p], full)
    moved = np.abs(W4 - d['w0']).sum(1)
    report['pieces'][p] = dict(l1_change_mean=float(moved.mean()), l1_change_p99=float(np.percentile(moved, 99)), influences_max=int((full > 0).sum(1).max()))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(report, open(f'{DATA}/fit_{tag}.json', 'w'), indent=1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print('SAVED', OUT, round(time.time() - t0, 1), 's')
