"""Left-hand grips on the racket (HANDLE = two-hand backhand, THROAT = ready-stance support) and the finger-pose library.

  blender -b <stage.blend> --python leftgrip.py -- <male|female>

Method (reuses the dressed-look pieces: digit model, contact-stopping finger closing, racket cylinder model):
  * the left hand is the exact mirror of the right hand (the hand meshes are mirror copies); the right-hand grip is the dressed-look solution;
  * left hand frame in the racket frame = mirror of the right hand frame across the racket plane X=0, shifted by Delta along the shaft;
  * the hand is lifted along its palm normal until the (opened) hand clears the racket model by 0.4 mm;
  * every finger is closed until its segments touch the racket model (stop 0.3 mm short), neighbour difference <= 25 deg per joint;
  * candidates (Delta, roll about the shaft) are scored by how many fingers touch and by overlap with the right hand's posed vertices.
Writes data/hands_<hero>.json: finger poses OPEN / RELAX / RIGHT_GRIP / LEFT_HANDLE / LEFT_THROAT (degrees about each finger bone's X) and the
left-hand frame in the racket frame for both grips."""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'dressed-look', 'scripts'))
import numpy as np
import bpy
from common import *
import kin
import lm
from geom import Mesh
from handlib import adjacency
import handpose_np as HP

tag = args_after_dashes()[0]
H = HERO[tag]
rig_o = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
body = bpy.data.objects[H['body']]
R = kin.Rig(f'{DATA}/rig_{tag}.json')
rinfo = json.load(open(f'{DATA}/racket_{tag}.json'))
rep = json.load(open(f'{DATA}/build_rig_{tag}.json'))
d = np.load(f'{DATA}/{tag}_body_mesh.npz')
co = d['co']
mesh = Mesh(d['co'], d['tri'], d['ed'])
adj = adjacency(len(co), d['ed'])
hands = lm.hand_pipeline(mesh, adj, tag, print)
FINGERS = ['index', 'middle', 'ring', 'pinky']
FN = {'index': 'Index', 'middle': 'Middle', 'ring': 'Ring', 'pinky': 'Little', 'thumb': 'Thumb'}
SEG = ('Proximal', 'Intermediate', 'Distal')
MARGIN = 0.0003
LIMITS = dict(MCP=(-35.0, 95.0), PIP=(-8.0, 110.0), DIP=(-8.0, 80.0))
RELAXED = [70.0, 90.0, 55.0]
MAX_NEIGHBOUR_DIFF = 25.0


def bname(sd, nm, k):
    return f"{'Left' if sd == 'L' else 'Right'}{FN[nm]}{SEG[k]}"


def finger_bones(sd):
    return [bname(sd, nm, k) for nm in list(FN) for k in range(3)]


class HandLBS:
    """numpy linear-blend skinning of one hand's vertices through kin.Rig FK (finger flexion = rotation about the bone's local X)."""

    def __init__(self, rig, sd, hand_idx, X0):
        self.rig, self.sd = rig, sd
        self.X0 = np.asarray(X0, float)
        self.Xh = np.concatenate([self.X0, np.ones((len(self.X0), 1))], 1)
        self.bones = [b for b in rig.names if b.startswith('Left' if sd == 'L' else 'Right') and ('Hand' in b or any(f in b for f in FN.values()))]
        vg = {g.index: g.name for g in body.vertex_groups}
        pos = {int(v): k for k, v in enumerate(hand_idx)}
        W = np.zeros((len(hand_idx), len(self.bones)))
        bidx = {b: i for i, b in enumerate(self.bones)}
        for v in hand_idx:
            for g in body.data.vertices[int(v)].groups:
                nm = vg[g.group]
                if nm in bidx:
                    W[pos[int(v)], bidx[nm]] = g.weight
        # remaining weight (forearm bones) is treated as rigid-with-the-hand for this local study
        self.W = W
        self.rest_inv = {b: np.linalg.inv(rig.Mrest[rig.idx[b]]) for b in self.bones}

    def skin(self, ang, subset=None):
        rig = self.rig
        B = np.tile(np.eye(3), (rig.n, 1, 1))
        for nm, a in ang.items():
            if nm in rig.idx:
                B[rig.idx[nm]] = kin.rx(math.radians(a))
        Q, P = rig.fk(B)
        X = self.Xh if subset is None else self.Xh[subset]
        W = self.W if subset is None else self.W[subset]
        out = np.zeros((len(X), 3))
        wsum = W.sum(1)
        for j, b in enumerate(self.bones):
            w = W[:, j]
            if not w.any():
                continue
            i = rig.idx[b]
            M = np.eye(4)
            M[:3, :3] = Q[i]
            M[:3, 3] = P[i]
            S = M @ self.rest_inv[b]
            nz = w > 1e-9
            out[nz] += w[nz, None] * (X[nz] @ S.T)[:, :3]
        lack = 1.0 - wsum
        nz = lack > 1e-6
        out[nz] += lack[nz, None] * X[nz][:, :3]
        return out


def signed_bend(d_prev, d_next, p):
    pt = lm.unit(p - np.dot(p, d_prev) * d_prev)
    return math.degrees(math.atan2(np.dot(d_next, pt), np.dot(d_next, d_prev)))


def open_angles(sd, Hm):
    """straighten every finger into the palm plane (female: her relaxed hand is cupped).  male: zeros."""
    out = {b: 0.0 for b in finger_bones(sd)}
    if tag == 'male':
        return out
    wrist = R.J[f'wrist_{sd}']
    p = Hm['p']
    for nm in FINGERS:
        Jd = Hm['digits'][nm]['J']
        d1, d2, d3 = lm.unit(Jd[1] - Jd[0]), lm.unit(Jd[2] - Jd[1]), lm.unit(Jd[3] - Jd[2])
        meta = lm.unit(Jd[0] - wrist)
        out[bname(sd, nm, 0)] = float(np.clip(-signed_bend(meta, d1, p), LIMITS['MCP'][0], 0.0))
        out[bname(sd, nm, 1)] = float(np.clip(-signed_bend(d1, d2, p), LIMITS['PIP'][0], 0.0))
        out[bname(sd, nm, 2)] = float(np.clip(-signed_bend(d2, d3, p), LIMITS['DIP'][0], 0.0))
    return out


# --------------------------------------------------------------------------------------------------- setup both hands
lbs = {}
seg_masks = {}
for sd in ('L', 'R'):
    Hm = hands[sd]
    lbs[sd] = HandLBS(R, sd, Hm['hand'], co[Hm['hand']])
    seg_masks[sd] = {nm: [lbs[sd].W[:, lbs[sd].bones.index(bname(sd, nm, k))] > 0.55 for k in range(3)] for nm in FINGERS}
open_ang = {sd: open_angles(sd, hands[sd]) for sd in ('L', 'R')}
Mrest_hand = {sd: R.Mrest[R.idx['LeftHand' if sd == 'L' else 'RightHand']] for sd in ('L', 'R')}

# racket frame <-> right hand
T_rh = np.array(rinfo['T_hand_to_racket'])            # racket in the right-hand bone frame
T_hr = np.linalg.inv(T_rh)                            # right-hand bone frame in the racket frame
Mrk_bind = np.array(rinfo['racket_world_bind'])
F = np.diag([-1.0, 1.0, 1.0, 1.0])
Dm = np.diag([-1.0, 1.0, 1.0, 1.0])
T_hl_base = F @ T_hr @ Dm                             # left-hand bone frame in the racket frame (mirror image of the right hand)


def ry_m(a):
    M = np.eye(4)
    M[:3, :3] = kin.ry(a)
    return M


def shift_m(dy):
    M = np.eye(4)
    M[1, 3] = dy
    return M


def hand_in_racket(delta, roll_deg, lift):
    T = ry_m(math.radians(roll_deg)) @ shift_m(delta) @ T_hl_base
    T = T.copy()
    T[:3, 3] -= T[:3, 2] * lift                 # lift = away from the racket along -palm normal (hand local Z)
    return T


def racket_model_in_hand_rest(T_hl, sd='L'):
    """racket model placed in the hand's REST space (where HandLBS positions live) for a hand pose T_hl (hand frame in the racket frame)."""
    return Mrest_hand[sd] @ np.linalg.inv(T_hl)


def close_digit_args(sd, ang, nm):
    names = [bname(sd, nm, k) for k in range(3)]
    return names


def close_all(sd, T_hl):
    rk = HP.RacketModel(racket_model_in_hand_rest(T_hl, sd))
    ang = dict(open_ang[sd])
    res = {}
    for nm in FINGERS:
        names = [bname(sd, nm, k) for k in range(3)]
        cur, frozen, trace = HP.close_digit_np(lbs[sd], rk, ang, names, seg_masks[sd][nm], list(RELAXED), margin=MARGIN)
        for k in range(3):
            ang[names[k]] = cur[k]
        res[nm] = (cur, trace)
    for _ in range(4):
        for a_, b_ in zip(FINGERS[:-1], FINGERS[1:]):
            for k in range(3):
                na, nb = bname(sd, a_, k), bname(sd, b_, k)
                if ang[nb] - ang[na] > MAX_NEIGHBOUR_DIFF:
                    ang[nb] = ang[na] + MAX_NEIGHBOUR_DIFF
                elif ang[na] - ang[nb] > MAX_NEIGHBOUR_DIFF:
                    ang[na] = ang[nb] + MAX_NEIGHBOUR_DIFF
    X = lbs[sd].skin(ang)
    d_f = {nm: float(min(rk.dist(X[seg_masks[sd][nm][k]]).min() for k in range(3) if seg_masks[sd][nm][k].any())) for nm in FINGERS}
    pen = float(rk.dist(X).min())
    return ang, d_f, pen, rk


def solve_lift(sd, delta, roll_deg):
    lo, hi = -0.03, 0.12
    for _ in range(36):
        mid = 0.5 * (lo + hi)
        T = hand_in_racket(delta, roll_deg, mid)
        rk = HP.RacketModel(racket_model_in_hand_rest(T, sd))
        if rk.dist(lbs[sd].skin(open_ang[sd])).min() >= 0.0004:
            hi = mid
        else:
            lo = mid
    return hi


def right_hand_world_pts(ang_R):
    """right hand vertices in the racket frame, posed with the right-grip angles (via the same LBS twin)."""
    X = lbs['R'].skin(ang_R)                                # armature space, hand bone unposed
    Mh = Mrest_hand['R']
    Xw = X @ np.linalg.inv(Mh)[:3, :3].T + np.linalg.inv(Mh)[:3, 3]      # hand local
    Xr = Xw @ T_hr[:3, :3].T + T_hr[:3, 3]                              # racket frame
    return Xr


ang_R = dict(open_ang['R'])
ang_R.update(rep['right_grip_angles_deg'])
# the dressed-look angles were relative to the bind pose for the male and relative to the straightened pose for the female (they include the open angles)
Xr_right = right_hand_world_pts(ang_R)
rk_check = HP.RacketModel(np.eye(4))
print('right hand vs racket model (min dist, mm):', round(float(rk_check.dist(Xr_right).min()) * 1000, 2))


def left_pts_in_racket(sd_ang, T_hl):
    X = lbs['L'].skin(sd_ang)
    Mh = Mrest_hand['L']
    Xl = X @ np.linalg.inv(Mh)[:3, :3].T + np.linalg.inv(Mh)[:3, 3]
    return Xl @ T_hl[:3, :3].T + T_hl[:3, 3]


def score(ang, d_f, pen, T_hl):
    sc = 0.0
    for nm in FINGERS:
        tot = sum(ang[bname('L', nm, k)] - open_ang['L'][bname('L', nm, k)] for k in range(3))
        if d_f[nm] <= 0.0008:
            sc += 1.0 + 0.5 * min(1.0, tot / 150.0)
    if pen < -0.0004:
        sc -= 5.0
    # overlap with the right hand (vertex-in-hand proxy: distance between the two vertex clouds)
    XL = left_pts_in_racket(ang, T_hl)
    from scipy_free_nn import min_dist_cloud
    dmin = min_dist_cloud(XL, Xr_right)
    if dmin < 0.003:
        sc -= 3.0 * (0.003 - dmin) / 0.003
    return sc, dmin


# tiny nearest-neighbour helper (numpy, chunked) - written here so no scipy is needed
import types
_snn = types.ModuleType('scipy_free_nn')


def _min_dist_cloud(A, B, chunk=400):
    best = 1e9
    for i in range(0, len(A), chunk):
        a = A[i:i + chunk]
        d2 = ((a[:, None, :] - B[None, :, :]) ** 2).sum(-1)
        best = min(best, float(d2.min()))
    return math.sqrt(best)


_snn.min_dist_cloud = _min_dist_cloud
sys.modules['scipy_free_nn'] = _snn

results = {}
for mode, deltas in (('HANDLE', [0.050, 0.060, 0.070, 0.080, 0.090, 0.100]), ('THROAT', [0.130, 0.145, 0.160, 0.175])):
    table = []
    for delta in deltas:
        for roll in (-45.0, -30.0, -15.0, 0.0, 15.0, 30.0, 45.0):
            lift = solve_lift('L', delta, roll)
            T = hand_in_racket(delta, roll, lift)
            ang, d_f, pen, rk = close_all('L', T)
            sc, dmin = score(ang, d_f, pen, T)
            table.append((sc, delta, roll, lift, ang, d_f, pen, dmin, T))
    table.sort(key=lambda r: (-round(r[0], 3), abs(r[2])))          # best score; ties -> roll closest to 0
    best = table[0]
    # refine: lift the hand until the CLOSED hand also clears the racket model by >= 0.2 mm (re-close at every lift)
    sc0, delta0, roll0, lift0, ang0, d_f0, pen0, dmin0, T0 = best
    lift_r = lift0
    for _ in range(8):
        T_r = hand_in_racket(delta0, roll0, lift_r)
        ang_r, d_f_r, pen_r, rk_r = close_all('L', T_r)
        if pen_r >= 0.0002:
            break
        lift_r += (0.0004 - pen_r)
    sc_r, dmin_r = score(ang_r, d_f_r, pen_r, T_r)
    best = (sc_r, delta0, roll0, lift_r, ang_r, d_f_r, pen_r, dmin_r, T_r)
    print(mode, 'best score %.2f delta %.3f roll %.0f lift %.4f  finger gaps(mm) %s  hand-hand min %.1f mm' % (
        best[0], best[1], best[2], best[3], {k: round(v * 1000, 1) for k, v in best[5].items()}, best[7] * 1000))
    results[mode] = dict(score=best[0], delta=best[1], roll_deg=best[2], lift=best[3], angles=best[4], finger_gap_mm={k: v * 1000 for k, v in best[5].items()},
                         hand_to_racket_mm=best[6] * 1000, hand_to_right_hand_mm=best[7] * 1000, T_hand_in_racket=best[8].tolist(),
                         top5=[dict(score=r[0], delta=r[1], roll=r[2]) for r in table[:5]])

out = dict(tag=tag, open_L=open_ang['L'], open_R=open_ang['R'], right_grip=ang_R, left_handle=results['HANDLE'], left_throat=results['THROAT'],
           T_hand_R_in_racket=T_hr.tolist(), T_hand_L_mirror_base=T_hl_base.tolist())
json.dump(out, open(f'{DATA}/hands_{tag}.json', 'w'), indent=1)
print('LEFTGRIP_DONE', tag)
