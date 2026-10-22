"""Where does the planted foot of a BLEND of two run clips go?  (SERVE_AND_FEET, the diagonal runs.)

Unity blends the bone rotations of the clips that carry weight (weighted, normalised quaternions) and the Hips location linearly; the planted foot of the blend does not move at
V along the weighted direction: the legs swing in different planes, so a 50/50 blend of RunForward and RunRight moves its foot by about 0.6 V, not 0.707 V, and not exactly 45 deg.
This script poses the hero from the blended arrays (data/gen_*.npz = what the clips were baked from), reads the Toes bones in the stance windows of the clips (L frames 9-15, R 0-6)
and writes, for every blend weight, the hero velocity that leaves the planted foot standing still on the court (u = -foot velocity): its angle from forward and its speed per unit clip rate.
  blender -b export/HeroBase_<Hero>_MatchAnims.blend --python scripts/run_blend_model.py -- <male|female>        -> data/run_blend_model_<tag>.json"""
import json
import sys

import numpy as np
import bpy

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
WORK = REPO + '/work/serve-and-feet'
sys.path.insert(0, WORK + '/scripts')
import loco

tag = sys.argv[sys.argv.index('--') + 1]
rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
names = [b['name'] for b in json.load(open(f'{loco.MA}/data/rig_{tag}.json'))['bones']]
sc = bpy.context.scene
G = {c: np.load(f'{loco.DATA}/gen_{g}_{tag}.npz', allow_pickle=True) for c, g in (('F', 'runf'), ('R', 'runr'), ('L', 'runl'))}
Q = {c: G[c]['quats'] for c in G}          # (frames, bones, 4)
H = {c: G[c]['hips'] for c in G}           # (frames, 3)
N = 17                                      # frames per cycle (the loop closes on frame 17 == frame 0)
tab = json.load(open(f'{WORK}/data/clip_table_new.json'))
V = tab['runSpeed']
PIVOT = tab['runReversePivot'] * 30.0       # frames

rig.animation_data_create()
rig.animation_data.action = None
rig.rotation_mode = 'XYZ'
for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'
HIPS = names.index('Hips')


def sample(c, t):
    """clip c at fractional frame t (loop of N frames): linear keys, as baked"""
    t = t % N
    i = int(np.floor(t)); f = t - i
    j = (i + 1) % N
    q = Q[c][i] * (1 - f) + Q[c][j] * f
    h = H[c][i] * (1 - f) + H[c][j] * f
    return q, h


def blend(parts):
    """parts = [(clip, frame, weight)] -> blended quats (bones, 4), hips"""
    q0 = None
    acc = np.zeros_like(Q['F'][0]); hh = np.zeros(3)
    for c, t, w in parts:
        if w <= 0:
            continue
        q, h = sample(c, t)
        if q0 is None:
            q0 = q
        sign = np.where((q * q0).sum(axis=1, keepdims=True) < 0, -1.0, 1.0)     # shortest path
        acc += w * sign * q
        hh += w * h
    n = np.linalg.norm(acc, axis=1, keepdims=True)
    return acc / np.maximum(n, 1e-9), hh


def toes(q, h):
    for i, nm in enumerate(names):
        if nm == 'Root':
            continue
        rig.pose.bones[nm].rotation_quaternion = q[i]
    rig.pose.bones['Hips'].location = h
    bpy.context.view_layer.update()
    out = []
    for side in ('Left', 'Right'):
        p = rig.matrix_world @ rig.pose.bones[f'{side}Toes'].head
        out.append([p.x, p.y, p.z])
    return np.array(out)


WIN = {0: range(9, 16), 1: range(0, 7)}     # stance windows (frames) of the left / right foot
res = {}
W = np.linspace(0, 1, 21)
for name, fwd_clip_rev, lat, lat_rev in (('F+R', False, 'R', False), ('F+L', False, 'L', False), ('B+R', True, 'R', False), ('B+L', True, 'L', False), ('B+Rrev', True, 'R', True), ('B+Lrev', True, 'L', True)):
    rows = []
    for w in W:
        vel = []
        resid = []
        for side in (0, 1):
            fr = list(WIN[side])
            P = []
            for k in fr:
                tf = (PIVOT - k) if fwd_clip_rev else k
                tl = (PIVOT - k) if lat_rev else k
                q, h = blend([('F', tf, 1 - w), (lat, tl, w)])
                P.append(toes(q, h)[side])
            P = np.array(P)
            t = np.array(fr, float) / 30.0
            A = np.vstack([t, np.ones_like(t)]).T
            sx = np.linalg.lstsq(A, P[:, 0], rcond=None)[0]; sy = np.linalg.lstsq(A, P[:, 1], rcond=None)[0]
            v = np.array([sx[0], sy[0]])                    # foot velocity in the rig frame (Blender axes: right = -x, forward = -y)
            vel.append(v)
            resid.append(float(np.sqrt(np.mean((P[:, 0] - (sx[0] * t + sx[1])) ** 2 + (P[:, 1] - (sy[0] * t + sy[1])) ** 2))))
        v = np.mean(vel, axis=0)
        right, fwd = v[0], v[1]                             # u = -v_foot expressed (right, forward) = (-(-vx)... : u_right = +vx, u_fwd = +vy  because right = -x, forward = -y and u = -v
        rows.append(dict(w=float(w), right=float(right), fwd=float(fwd), speed=float(np.hypot(right, fwd)), angle_deg=float(np.degrees(np.arctan2(right, fwd))), per_foot_speed=[float(np.hypot(*x)) for x in vel],
                         per_foot_angle=[float(np.degrees(np.arctan2(x[0], x[1]))) for x in vel], resid_mm=[round(r * 1000, 2) for r in resid]))
    res[name] = rows
    print(name)
    for r in rows[::2]:
        print('  w=%.2f  angle %6.1f deg  speed %.3f V  (feet %.3f / %.3f V; angles %.0f / %.0f; resid mm %s)' % (r['w'], r['angle_deg'], r['speed'] / V, r['per_foot_speed'][0] / V, r['per_foot_speed'][1] / V, r['per_foot_angle'][0], r['per_foot_angle'][1], r['resid_mm']))
json.dump(dict(V=V, pivot_frames=PIVOT, combos=res), open(f'{WORK}/data/run_blend_model_{tag}.json', 'w'), indent=1)
