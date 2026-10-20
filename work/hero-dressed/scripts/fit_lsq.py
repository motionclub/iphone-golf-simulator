"""Skinning decomposition for the kit: fit the vertex weights to a collision-free, smoothed 'ideal cloth' motion over TRAINING poses (the 8 gate poses and their +-1 frames are held out).

  blender -b export/HeroBase_<Hero>_Dressed.blend --python fit_lsq.py -- <male|female> [piece ...]       env DR_LSQ_* knobs, DR_OUT_BLEND

For every training pose and every kit vertex k near the body (bind distance <= 40 mm) the ideal position is the OFFSET SURFACE of the deformed body (nearest bind body point moved with the body, plus the
bind gap along the body normal).  The displacement field of those ideal positions is Laplacian-smoothed over the kit mesh (cloth bridges the gap between arm and torso instead of tearing), the result is pushed
out of the deformed body (never closer than min(bind gap, 4 mm)), and the weights solve   min_w sum_poses |sum_c w_c (D_c,pose k0) - target|^2 + reg |w - w0|^2,  w >= 0, sum w = 1   per vertex
(accelerated projected gradient, batched).  Then limited to 4 influences and re-solved on those.  Linear blend skinning is linear in w, so this is an exact convex QP per vertex.
Writes the weights back and saves DR_OUT_BLEND.
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


def cfg_for(p):
    cls = {'Top': 'top', 'Bottom': 'bottom'}.get(p, 'rigid')
    return dict(smooth_iters=int(envf(f'DR_LSQ_SMOOTH_{cls.upper()}', {'top': 8, 'bottom': 8, 'rigid': 0}[cls])), smooth_factor=envf('DR_LSQ_SMOOTH_FACTOR', 0.5),
                gmin=envf('DR_LSQ_GMIN', 0.004), reg=envf('DR_LSQ_REG', 2.0), stride=int(envf('DR_LSQ_STRIDE', 6)), iters=int(envf('DR_LSQ_ITERS', 300)),
                push=int(envf('DR_LSQ_PUSH', 1)), outset=envf(f'DR_LSQ_OUTSET_{cls.upper()}', {'top': 0.0, 'bottom': 0.0, 'rigid': 0.0}[cls]))


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


def proj_simplex(V):
    n, m = V.shape
    U = -np.sort(-V, axis=1)
    css = np.cumsum(U, axis=1) - 1
    ar = np.arange(1, m + 1)
    cond = U - css / ar > 0
    rho = cond.sum(1) - 1
    theta = css[np.arange(n), rho] / (rho + 1)
    return np.maximum(V - theta[:, None], 0)


def smooth_field(F, edges, iters, factor, deg):
    for _ in range(iters):
        acc = np.zeros_like(F)
        np.add.at(acc, edges[:, 0], F[edges[:, 1]])
        np.add.at(acc, edges[:, 1], F[edges[:, 0]])
        F = (1 - factor) * F + factor * acc / deg[:, None]
    return F


def solve_qp(Hm, b, w0, mask, iters):
    """min 0.5 w'(2H)w - 2b'w  over the simplex (masked entries fixed at 0), batched FISTA"""
    n, m = w0.shape
    # Lipschitz bound per vertex: 2 * trace(H) is safe; use the max row sum (Gershgorin) which is tighter
    L = 2.0 * np.abs(Hm).sum(2).max(1)
    L = np.maximum(L, 1e-9)[:, None]
    w = w0.copy()
    y = w.copy()
    t = 1.0
    for _ in range(iters):
        g = 2.0 * (np.einsum('kcd,kd->kc', Hm, y) - b)
        wn = proj_simplex(np.where(mask > 0, y - g / L, -1e9)) * (mask > 0)
        tn = 0.5 * (1 + np.sqrt(1 + 4 * t * t))
        y = wn + ((t - 1) / tn) * (wn - w)
        w, t = wn, tn
    return w


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


t0 = time.time()
dg = set_pose(None, 0)
bco0 = evaluated_co(body, dg)
bn0 = vertex_normals(body)
btri = mesh_tris(body.data)
body_bvh0 = bvh_from(bco0, btri)
KT = {p: mesh_tris(kit[p].data) for p in PIECES}
K0 = {p: mesh_co(kit[p]) for p in PIECES}
W0 = {p: bone_weight_matrix(kit[p], bones) for p in PIECES}
EDGES, DEG = {}, {}
for p in PIECES:
    me = kit[p].data
    ed = np.empty(len(me.edges) * 2, np.int32)
    me.edges.foreach_get('vertices', ed)
    EDGES[p] = ed.reshape(-1, 2)
    deg = np.bincount(EDGES[p].ravel(), minlength=len(K0[p])).astype(np.float64)
    deg[deg == 0] = 1
    DEG[p] = deg

held = set()
for clip, kind in GATE_POSES:
    f = pose_frame(clip, kind, contacts)
    for d in (-1, 0, 1):
        held.add((clip, f + d))
stride = cfg_for('Top')['stride']
frames = []
for clip in CLIPS:
    n = int(round(lengths[clip] * FPS))
    for f in range(0, n + 1, stride):
        if (clip, f) not in held:
            frames.append((clip, f))
frames.append((None, 0))
print('training poses', len(frames), 'held out', len(held))

# per piece static data
PD = {}
for p in only:
    co0 = K0[p]
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
    cols = [j for j in range(len(bones)) if W0[p][:, j].max() > 0]
    nb = len(cols)
    PD[p] = dict(cfg=cfg_for(p), hug=(d_bind <= HUG), ntri=ntri, nbary=nbary, gap=gap, cols=cols, w0=W0[p][:, cols].copy(),
                 K0h=np.concatenate([co0, np.ones((len(co0), 1))], 1), Hm=np.zeros((len(co0), nb, nb)), b=np.zeros((len(co0), nb)), tri_corner=btri[ntri])
    print(p, 'hug', int(PD[p]['hug'].sum()), 'of', len(co0), 'bones', nb, round(time.time() - t0, 1), 's')

stats = {p: dict(pushed=0, total=0) for p in only}
for q, (clip, f) in enumerate(frames):
    dg = set_pose(clip, f)
    D = deform_matrices()
    bco = evaluated_co(body, dg)
    bn = evaluated_normals(body, dg)
    bvh = bvh_from(bco, btri)
    for p in only:
        d = PD[p]
        cfg = d['cfg']
        co0 = K0[p]
        T = d['tri_corner']
        Bp = (bco[T] * d['nbary'][:, :, None]).sum(1)
        Np_ = (bn[T] * d['nbary'][:, :, None]).sum(1)
        Np_ /= np.maximum(np.linalg.norm(Np_, axis=1, keepdims=True), 1e-12)
        Qraw = Bp + (d['gap'] + cfg['outset'])[:, None] * Np_
        # LBS under the starting weights is the target for vertices far from the body (they keep their behaviour)
        Dc = D[d['cols']]
        C = np.einsum('cij,kj->kci', Dc, d['K0h'])[..., :3]
        P0 = np.einsum('kc,kci->ki', d['w0'], C)
        Q = np.where(d['hug'][:, None], Qraw, P0)
        if cfg['smooth_iters'] > 0:
            disp = smooth_field(Q - co0, EDGES[p], cfg['smooth_iters'], cfg['smooth_factor'], DEG[p])
            Q = co0 + disp
        if cfg['push']:
            gmin = np.clip(np.minimum(d['gap'], cfg['gmin']), 0.0005, None)
            for k in np.nonzero(d['hug'])[0]:
                loc, nrm, idx, dist = bvh.find_nearest(tuple(map(float, Q[k])))
                n = np.array(nrm)
                s = float(np.dot(Q[k] - np.array(loc), n))
                if s < gmin[k]:
                    Q[k] = Q[k] + (gmin[k] - s) * n
                    stats[p]['pushed'] += 1
            stats[p]['total'] += int(d['hug'].sum())
        d['Hm'] += np.einsum('kci,kdi->kcd', C, C)
        d['b'] += np.einsum('kci,ki->kc', C, Q)
    if q % 20 == 0:
        print('pose', q, '/', len(frames), round(time.time() - t0, 1), 's', flush=True)

report = dict(tag=tag, pieces={})
for p in only:
    d = PD[p]
    cfg = d['cfg']
    nq = len(frames)
    Hm = d['Hm'] / nq
    b = d['b'] / nq
    # ridge toward the starting weights; scale relative to the mean diagonal
    scale = np.maximum(np.einsum('kcc->k', Hm) / Hm.shape[1], 1e-9)[:, None]
    reg = cfg['reg'] * 1e-3 * scale
    Hm = Hm + np.eye(Hm.shape[1])[None] * reg[:, :, None]
    b = b + reg * d['w0']
    mask = np.ones_like(d['w0'])
    W = solve_qp(Hm, b, d['w0'], mask, cfg['iters'])
    W[W < 1e-3] = 0
    order = np.argsort(-W, axis=1)
    keep = np.zeros_like(W, bool)
    keep[np.arange(len(W))[:, None], order[:, :4]] = True
    W4 = np.where(keep, W, 0.0)
    W4 /= np.maximum(W4.sum(1, keepdims=True), 1e-12)
    W4 = solve_qp(Hm, b, W4, keep.astype(float), cfg['iters'])
    W4[W4 < 1e-3] = 0
    W4 /= np.maximum(W4.sum(1, keepdims=True), 1e-12)
    full = np.zeros((len(K0[p]), len(bones)))
    full[:, d['cols']] = W4
    assert (full > 0).sum(1).max() <= 4
    write_weights(kit[p], full)
    ch = np.abs(W4 - d['w0']).sum(1)
    report['pieces'][p] = dict(cfg=cfg, l1_change_mean=float(ch.mean()), l1_change_p99=float(np.percentile(ch, 99)), pushed_fraction=stats[p]['pushed'] / max(stats[p]['total'], 1))
    print(p, 'weights changed: mean L1', round(float(ch.mean()), 3), 'p99', round(float(np.percentile(ch, 99)), 3), 'targets pushed out of the body', round(stats[p]['pushed'] / max(stats[p]['total'], 1), 3))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(report, open(f'{DATA}/fitlsq_{tag}.json', 'w'), indent=1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print('SAVED', OUT, round(time.time() - t0, 1), 's')
