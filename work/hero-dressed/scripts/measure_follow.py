"""Gate 3 FOLLOWS_BODY (skin poke / float per piece in posed frames) and gate 8 SOLE_TRACK, measured on export/HeroBase_<Hero>_Dressed.blend.

  blender -b export/HeroBase_<Hero>_Dressed.blend --python measure_follow.py -- <male|female> <gate|sweep|sole> [out.json]

gate  : the 8 pre-registered poses (ReadyIdle frame 0 + contact frame of Forehand, Backhand, Serve, Overhead, ForehandWide, VolleyForehand, Return)
sweep : informational, every 6th frame of all 16 clips
sole  : gate 8 SOLE_TRACK over every frame of all 16 clips
Definitions: work/hero-dressed/GATE_DEFS_preregistered.md (gate 3, gate 8).  Metres inside, millimetres in the output.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

from dcommon import *
from follow_lib import *

a_ = args_after_dashes()
tag, mode = a_[0], a_[1]
H = HERO[tag]
sc = bpy.context.scene
rig = bpy.data.objects[H['rig']]
body = bpy.data.objects[H['body']]
kit = {p: bpy.data.objects[KIT_NAME[p]] for p in PIECES}
bones = [b.name for b in rig.data.bones if b.use_deform]
contacts, lengths = contact_seconds(H['label'])

# thresholds (pre-registered) ------------------------------------------------------------------------------------------------------------
POKE_MAX_MM, POKE_P99_MM = 15.0, 5.0
FLOAT = {'rigid': (12.0, 6.0), 'cloth': (40.0, 15.0)}          # (max, p99) mm
RIGID = {'Sock_L', 'Sock_R', 'Shoe_L', 'Shoe_R'}
SOLE_TOL_MM, PLANT_MM = 6.0, 5.0


def mt_first(o, d, V0, E1, E2, tmax, front=None):
    """exact Moller-Trumbore against all triangles; returns (t, dot(d, N)) of the nearest hit with 0 < t <= tmax (and front-facing if front=True) or None"""
    pvec = np.cross(d, E2)
    det = (E1 * pvec).sum(1)
    ok = np.abs(det) > 1e-14
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    tvec = o - V0
    u = (tvec * pvec).sum(1) * inv
    qv = np.cross(tvec, E1)
    v = (d * qv).sum(1) * inv
    t = (E2 * qv).sum(1) * inv
    e = 1e-9
    hit = ok & (u >= -e) & (v >= -e) & (u + v <= 1 + e) & (t > 1e-7) & (t <= tmax)
    if front:
        hit &= det * 1.0 > -1e300  # placeholder, facing filtered below
    if not hit.any():
        return None
    idx = np.nonzero(hit)[0]
    nrm = np.cross(E1[idx], E2[idx])
    face = nrm @ d
    k = int(np.argmin(t[idx]))
    if front:
        fr = np.nonzero(face < 0)[0]
        if len(fr) == 0:
            return None
        k = fr[int(np.argmin(t[idx][fr]))]
    return float(t[idx][k]), float(face[k] / max(np.linalg.norm(nrm[k]), 1e-18))



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


def snapshot(dg):
    return evaluated_co(body, dg), {p: evaluated_co(kit[p], dg) for p in PIECES}


# ---- bind pose ---------------------------------------------------------------------------------------------------------------------------
t0 = time.time()
dg = set_pose(None, 0)
bco0, kco0 = snapshot(dg)
assert np.abs(bco0 - mesh_co(body)).max() < 1e-5, 'rest evaluation must equal the raw body mesh'
btri = mesh_tris(body.data)
body_bvh0 = bvh_from(bco0, btri)
bn0 = vertex_normals(body)
Wb = bone_weight_matrix(body, bones)
KT = {p: mesh_tris(kit[p].data) for p in PIECES}
kit_bvh0 = {p: bvh_from(kco0[p], KT[p]) for p in PIECES}

info = {}
for p in PIECES:
    zone, ht, hb, it, ib = compute_zone(kco0[p], KT[p], bco0, bn0, body_bvh0, kit_bvh0[p])
    d_bind = np.array([body_bvh0.find_nearest(tuple(map(float, c)))[3] for c in kco0[p]])
    info[p] = dict(zone=zone, home_tri=ht, home_bary=hb, tris=KT[p], d_bind=d_bind, hug=np.nonzero(d_bind <= HUG)[0])
    print(f'{p}: covered zone {len(zone)} body vertices; kit vertices within {HUG*1000:.0f} mm of the body at bind: {len(info[p]["hug"])} of {len(d_bind)}')
print('bind setup', round(time.time() - t0, 1), 's')

# ---- gate 8: foot sets -------------------------------------------------------------------------------------------------------------------
foot_sets = {}
for side in ('Left', 'Right'):
    cols = [bones.index(side + n) for n in ('Foot', 'Toes')]
    foot_sets[side] = np.nonzero(Wb[:, cols].sum(1) > 0.5)[0]


def measure_pose(clip, frame, label):
    dg = set_pose(clip, frame)
    bco, kco = snapshot(dg)
    body_bvh = bvh_from(bco, btri)
    out = {'clip': clip, 'frame': int(frame), 'label': label, 'pieces': {}}
    for p in PIECES:
        co, tri = kco[p], info[p]['tris']
        zone, ht, hb = info[p]['zone'], info[p]['home_tri'], info[p]['home_bary']
        T = tri[ht]
        a, b, c = co[T[:, 0]], co[T[:, 1]], co[T[:, 2]]
        P = a * hb[:, 0:1] + b * hb[:, 1:2] + c * hb[:, 2:3]
        N = np.cross(b - a, c - a)
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-18)
        v = bco[zone]
        h = ((v - P) * N).sum(1)
        # informational (never gating, A7 stands): the same with the normal taken from the kit's smoothed VERTEX normals at the three corners (a stretched triangle can collapse and flip its own normal)
        kn = evaluated_normals(kit[p], dg)
        Nr = kn[T[:, 0]] * hb[:, 0:1] + kn[T[:, 1]] * hb[:, 1:2] + kn[T[:, 2]] * hb[:, 2:3]
        Nr /= np.maximum(np.linalg.norm(Nr, axis=1, keepdims=True), 1e-18)
        hr = ((v - P) * Nr).sum(1)
        near = np.linalg.norm(v - P, axis=1) <= HOME_NEAR
        depth = np.where(near, np.maximum(h, 0.0), 0.0)
        slid = int((~near).sum())
        hug = info[p]['hug']
        dbind = info[p]['d_bind'][hug]
        growth = np.zeros(len(hug))
        for k, j in enumerate(hug):
            growth[k] = max(0.0, body_bvh.find_nearest(tuple(map(float, co[j])))[3] - dbind[k])
        dump = os.environ.get('DR_DUMP', '')
        if dump and dump.split(':')[0] == str(clip) and int(dump.split(':')[1]) == int(frame) and p in dump.split(':')[2].split(','):
            np.savez(f'{DATA}/dump_{tag}_{p}_{clip}_{frame}.npz', zone=zone, depth=depth, near=near, h=h, bco0=bco0, bco=bco, kco0=kco0[p], kco=co, growth=growth, hug=hug)
        depth_r = np.where(near, np.maximum(hr, 0.0), 0.0)
        row = dict(poke_ring_max_mm=float(depth_r.max() * 1000) if len(depth_r) else 0.0, poke_ring_p99_mm=float(np.percentile(depth_r, 99) * 1000) if len(depth_r) else 0.0,
                   triangle_flips=int((np.einsum('ij,ij->i', N, Nr) < 0).sum()),
                   poke_max_mm=float(depth.max() * 1000) if len(depth) else 0.0, poke_p99_mm=float(np.percentile(depth, 99) * 1000) if len(depth) else 0.0,
                   poke_n=int((depth > 0).sum()), poke_n_over_5mm=int((depth > 0.005).sum()), slid_n=slid, zone_n=int(len(zone)),
                   float_max_mm=float(growth.max() * 1000) if len(growth) else 0.0, float_p99_mm=float(np.percentile(growth, 99)) * 1000 if len(growth) else 0.0, float_n=int(len(hug)))
        if len(depth):
            row['worst_body_vertex'] = int(zone[int(depth.argmax())])
        if p in RIGID:
            e = np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
            l0 = np.linalg.norm(kco0[p][e[:, 0]] - kco0[p][e[:, 1]], axis=1)
            l1 = np.linalg.norm(co[e[:, 0]] - co[e[:, 1]], axis=1)
            m = l0 > 4e-3        # edges shorter than 4 mm are skipped (relative strain of a sliver edge is meaningless)
            strain = np.abs(l1[m] / l0[m] - 1)
            row['edge_strain_max'] = float(strain.max())
            row['edge_strain_p99'] = float(np.percentile(strain, 99))
        out['pieces'][p] = row
    return out


def gate_frames():
    frames = []
    for clip, kind in GATE_POSES:
        frames.append((clip, pose_frame(clip, kind, contacts), f'{clip} {"frame 0" if kind == "start" else "contact"}'))
    return frames


outp = a_[2] if len(a_) > 2 else f'{DATA}/gate3_{tag}.json'
os.makedirs(os.path.dirname(outp), exist_ok=True)

if mode in ('gate', 'sweep'):
    if mode == 'gate':
        todo = gate_frames()
    else:
        todo = []
        for clip in CLIPS:
            n = int(round(lengths[clip] * FPS))
            for f in range(0, n + 1, 6):
                todo.append((clip, f, f'{clip} f{f}'))
    res = []
    for k, (clip, f, label) in enumerate(todo):
        t1 = time.time()
        r = measure_pose(clip, f, label)
        res.append(r)
        worst = max(r['pieces'].items(), key=lambda kv: kv[1]['poke_max_mm'])
        print(f'[{k + 1}/{len(todo)}] {label}: worst poke {worst[0]} {worst[1]["poke_max_mm"]:.1f} mm; slid ' + ' '.join(f'{q}:{v["slid_n"]}' for q, v in r['pieces'].items()) + f'  ({time.time() - t1:.1f} s)', flush=True)
    summary = {}
    for p in PIECES:
        pm = max(r['pieces'][p]['poke_max_mm'] for r in res)
        pp = max(r['pieces'][p]['poke_p99_mm'] for r in res)
        fm = max(r['pieces'][p]['float_max_mm'] for r in res)
        fp = max(r['pieces'][p]['float_p99_mm'] for r in res)
        cls = 'rigid' if p in RIGID else 'cloth'
        ok = pm <= POKE_MAX_MM and pp <= POKE_P99_MM and fm <= FLOAT[cls][0] and fp <= FLOAT[cls][1]
        wp = max(res, key=lambda r: r['pieces'][p]['poke_max_mm'])
        wf = max(res, key=lambda r: r['pieces'][p]['float_max_mm'])
        summary_extra = dict(poke_ring_max_mm=max(r['pieces'][p]['poke_ring_max_mm'] for r in res), poke_ring_p99_worst_mm=max(r['pieces'][p]['poke_ring_p99_mm'] for r in res), triangle_flips_max=max(r['pieces'][p]['triangle_flips'] for r in res))
        summary[p] = dict(**summary_extra, poke_max_mm=pm, poke_p99_worst_mm=pp, float_max_mm=fm, float_p99_worst_mm=fp, cls=cls, worst_poke_pose=wp['label'], worst_poke_clip=wp['clip'], worst_poke_frame=wp['frame'],
                          worst_float_pose=wf['label'], pass_=bool(ok), thresholds=dict(poke_max=POKE_MAX_MM, poke_p99=POKE_P99_MM, float_max=FLOAT[cls][0], float_p99=FLOAT[cls][1]))
        if p in RIGID:
            summary[p]['edge_strain_max'] = max(r['pieces'][p]['edge_strain_max'] for r in res)
    json.dump(dict(tag=tag, mode=mode, zone_n={p: int(len(info[p]['zone'])) for p in PIECES}, poses=res, summary=summary), open(outp, 'w'), indent=1)
    for p in PIECES:
        s = summary[p]
        print(f'{p:7s} poke max {s["poke_max_mm"]:6.2f} p99 {s["poke_p99_worst_mm"]:6.2f} | float max {s["float_max_mm"]:6.2f} p99 {s["float_p99_worst_mm"]:6.2f} | {"PASS" if s["pass_"] else "FAIL"}  worst poke at {s["worst_poke_pose"]}')
    print('GATE3', tag, mode, 'PASS' if all(s['pass_'] for s in summary.values()) else 'FAIL')

elif mode == 'sole':
    # bind sole offsets
    off0 = {}
    for side in ('Left', 'Right'):
        sh = 'Shoe_L' if side == 'Left' else 'Shoe_R'
        fmin = bco0[foot_sets[side], 2].min()
        smin = kco0[sh][:, 2].min()
        off0[side] = smin - fmin
    print('bind: foot min z', {s: float(bco0[foot_sets[s], 2].min()) for s in foot_sets}, 'shoe min z', {s: float(kco0['Shoe_' + s[0]][:, 2].min()) for s in foot_sets}, 'offset mm', {s: round(off0[s] * 1000, 2) for s in off0})
    # reference: ReadyIdle frame 0 foot min
    dg = set_pose('ReadyIdle', 0)
    bco, kco = snapshot(dg)
    ref = {s: float(bco[foot_sets[s], 2].min()) for s in foot_sets}
    ready0 = {s: dict(foot_min=ref[s], shoe_min=float(kco['Shoe_' + s[0]][:, 2].min())) for s in foot_sets}
    print('ReadyIdle f0:', ready0)
    rows = []
    worst = 0.0
    n_planted = 0
    for clip in CLIPS:
        nF = int(round(lengths[clip] * FPS)) + 1
        for f in range(nF):
            dg = set_pose(clip, f)
            bco, kco = snapshot(dg)
            for side in ('Left', 'Right'):
                fmin = float(bco[foot_sets[side], 2].min())
                smin = float(kco['Shoe_' + side[0]][:, 2].min())
                planted = (fmin - ref[side]) <= PLANT_MM / 1000
                err = (smin - fmin) - off0[side]
                rows.append((clip, f, side, fmin, smin, planted, err))
                if planted:
                    n_planted += 1
                    worst = max(worst, abs(err))
        print(clip, 'done', flush=True)
    arr_err = np.array([r[6] for r in rows if r[5]])
    allerr = np.array([r[6] for r in rows])
    res = dict(tag=tag, mode='sole', bind_offset_mm={s: off0[s] * 1000 for s in off0}, ready0=ready0, frames=len(rows) // 2, planted_samples=n_planted,
               worst_planted_err_mm=float(worst * 1000), p99_planted_err_mm=float(np.percentile(np.abs(arr_err), 99) * 1000), mean_planted_err_mm=float(arr_err.mean() * 1000),
               worst_any_err_mm=float(np.abs(allerr).max() * 1000), tolerance_mm=SOLE_TOL_MM, pass_=bool(worst * 1000 <= SOLE_TOL_MM),
               worst_rows=sorted([dict(clip=r[0], frame=r[1], side=r[2], err_mm=r[6] * 1000, planted=bool(r[5]), foot_min_mm=r[3] * 1000, shoe_min_mm=r[4] * 1000) for r in rows], key=lambda d: -abs(d['err_mm']))[:12],
               worst_planted_rows=sorted([dict(clip=r[0], frame=r[1], side=r[2], err_mm=r[6] * 1000, foot_min_mm=r[3] * 1000, shoe_min_mm=r[4] * 1000) for r in rows if r[5]], key=lambda d: -abs(d['err_mm']))[:12],
               by_clip_planted_worst={c: float(max([abs(r[6]) for r in rows if r[5] and r[0] == c] or [0]) * 1000) for c in CLIPS})
    json.dump(res, open(outp, 'w'), indent=1)
    print('SOLE_TRACK', tag, 'worst planted error', round(res['worst_planted_err_mm'], 2), 'mm p99', round(res['p99_planted_err_mm'], 2), 'PASS' if res['pass_'] else 'FAIL')
