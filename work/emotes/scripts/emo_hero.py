"""EMOTES: hero container (rig + EmoSolver + skinned mesh + landmarks), the READY pose in channel form, and the keyframe timeline.  numpy only (Blender's python3.13)."""
import json
import math
import os
import sys

import numpy as np

R_ = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
W = R_ + '/work/emotes'
MA = R_ + '/work/match-anim-set'
DATA = W + '/data'
sys.path.insert(0, W + '/scripts')
sys.path.insert(0, MA + '/scripts')
import kin  # noqa: E402
import pose as PS  # noqa: E402
from kin import a2w, w2a, unit  # noqa: E402
from emo_solver import EmoSolver, A2W, hand_frame  # noqa: E402

FPS = 30


# ----------------------------------------------------------------------------------------------------------------------------- curves
def pchip_slopes(ts, vs):
    ts = np.asarray(ts, float)
    vs = np.asarray(vs, float).reshape(len(ts), -1)
    n = len(ts)
    m = np.zeros_like(vs)
    if n == 1:
        return m
    h = np.diff(ts)
    d = np.diff(vs, axis=0) / h[:, None]
    if n == 2:
        m[:] = d[0]
        return m
    for k in range(1, n - 1):
        a, b = d[k - 1], d[k]
        w1, w2 = 2 * h[k] + h[k - 1], h[k] + 2 * h[k - 1]
        with np.errstate(divide='ignore', invalid='ignore'):
            mk = np.where(a * b > 0, (w1 + w2) / (w1 / a + w2 / b), 0.0)
        m[k] = np.nan_to_num(mk)
    m[0] = d[0] * 0.0 if np.allclose(vs[0], vs[1]) else d[0]
    m[-1] = d[-1] * 0.0 if np.allclose(vs[-1], vs[-2]) else d[-1]
    return m


class Curve:
    """monotone cubic Hermite through (t, value) keys; clamps outside"""

    def __init__(self, keys):
        ks = sorted(keys, key=lambda k: k[0])
        self.ts = np.array([k[0] for k in ks], float)
        self.vs = np.array([np.atleast_1d(np.asarray(k[1], float)) for k in ks]).reshape(len(ks), -1)
        self.m = pchip_slopes(self.ts, self.vs)
        self.scalar = np.ndim(ks[0][1]) == 0
        self.shape = np.shape(ks[0][1])

    def __call__(self, t):
        ts, vs, m = self.ts, self.vs, self.m
        if t <= ts[0]:
            r = vs[0]
        elif t >= ts[-1]:
            r = vs[-1]
        else:
            k = int(np.searchsorted(ts, t, side='right') - 1)
            h = ts[k + 1] - ts[k]
            s = (t - ts[k]) / h
            r = (2 * s ** 3 - 3 * s ** 2 + 1) * vs[k] + (s ** 3 - 2 * s ** 2 + s) * h * m[k] + (-2 * s ** 3 + 3 * s ** 2) * vs[k + 1] + (s ** 3 - s ** 2) * h * m[k + 1]
        return float(r[0]) if self.scalar else r.reshape(self.shape)


class RotCurve:
    """3x3 rotation keys (t, R): eased slerp between neighbours (a repeated key is a hold)"""

    def __init__(self, keys):
        self.ks = sorted(keys, key=lambda k: k[0])

    def __call__(self, t):
        ks = self.ks
        if t <= ks[0][0]:
            return np.asarray(ks[0][1], float)
        if t >= ks[-1][0]:
            return np.asarray(ks[-1][1], float)
        i = max(j for j in range(len(ks) - 1) if ks[j][0] <= t)
        u = (t - ks[i][0]) / (ks[i + 1][0] - ks[i][0])
        return PS.slerp_mat(np.asarray(ks[i][1], float), np.asarray(ks[i + 1][1], float), smooth(u))


class Timeline:
    """Per-channel keys: add(t, ch=value, ...) ; pose(t) -> dict of channel values (only channels that have keys).  A channel is interpolated through the keys
    that name it (monotone cubic, so a repeated value is a hold with zero velocity)."""

    def __init__(self):
        self.ch = {}

    def add(self, t, **kw):
        for k, v in kw.items():
            lst = self.ch.setdefault(k, [])
            t = float(t)
            for i, (tt, _) in enumerate(lst):
                if abs(tt - t) < 1e-9:
                    lst[i] = (t, v)
                    break
            else:
                lst.append((t, v))
        return self

    def hold(self, t0, t1, **kw):
        self.add(t0, **kw)
        self.add(t1, **kw)
        return self

    def pose(self, t):
        out = {}
        for k, ks in self.ch.items():
            if not hasattr(self, '_c'):
                self._c = {}
            c = self._c.get(k)
            if c is None or c[0] != len(ks):
                c = (len(ks), RotCurve(ks) if k.endswith('_ori') else Curve(ks))
                self._c[k] = c
            out[k] = c[1](t)
        return out


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


# ----------------------------------------------------------------------------------------------------------------------------- hero
class EmoHero:
    def __init__(self, tag):
        self.tag = tag
        rig = self.rig = kin.Rig(f'{MA}/data/rig_{tag}.json')
        racket = json.load(open(f'{MA}/data/racket_{tag}.json'))
        hands = self.hands = json.load(open(f'{MA}/data/hands_{tag}.json'))
        self.S = EmoSolver(rig, racket, hands)
        self.A = self.S.A_arm
        self.O = self.S.O
        sk = np.load(f'{DATA}/skin_{tag}.npz')
        self.co, self.sk_idx, self.sk_w = sk['co'], sk['idx'], sk['w']
        self.dom = sk['dom']
        self.Minv = np.linalg.inv(rig.Mrest)
        self.vh = np.hstack([self.co, np.ones((len(self.co), 1))])
        ix = rig.idx
        # landmarks in the bind pose (world), then in the head bone's frame
        co = self.co
        J = rig.J
        m = (co[:, 2] > J['head'][2] - 0.02) & (co[:, 2] < J['head_top'][2] - 0.04) & (abs(co[:, 0]) < 0.04)
        sub = co[m]
        self.nose_bind = sub[np.argmin(sub[:, 1])].copy()
        self.nose_local = rig.Rrest[ix['Head']].T @ (self.nose_bind - rig.hrest[ix['Head']])
        self.head_top_bind = J['head_top'].copy()
        self.ftip = {}
        for s in ('Left', 'Right'):
            for fn in ('Thumb', 'Index', 'Middle'):
                self.ftip[s + fn] = None
        self._ready = None
        self._ready_P = None

    # ---- skinned mesh
    def mesh(self, basis, hips_loc):
        Q, P = self.rig.fk(basis, hips_loc)
        n = self.rig.n
        Mp = np.zeros((n, 4, 4))
        Mp[:, :3, :3] = Q
        Mp[:, :3, 3] = P
        Mp[:, 3, 3] = 1.0
        S = Mp @ self.Minv
        pos = np.zeros((len(self.vh), 3))
        for k in range(4):
            Sk = S[self.sk_idx[:, k]]
            pos += self.sk_w[:, k, None] * np.einsum('nij,nj->ni', Sk[:, :3, :], self.vh)
        return pos

    def region_mask(self, *names):
        ix = self.rig.idx
        ids = [ix[n] for n in names]
        return np.isin(self.dom, ids)

    def hand_mask(self, side):
        pre = 'Left' if side == 'L' else 'Right'
        return self.region_mask(*([pre + 'Hand'] + [n for n in self.rig.names if n.startswith(pre) and any(f in n for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Little'))]))

    def foot_mask(self, side):
        pre = 'Left' if side == 'L' else 'Right'
        return self.region_mask(pre + 'Foot', pre + 'Toes')

    def mesh_M(self, Mw):
        """skinned body vertices from (n, 4, 4) world bone matrices (e.g. read back from an FBX)"""
        S = Mw @ self.Minv
        pos = np.zeros((len(self.vh), 3))
        for k in range(4):
            Sk = S[self.sk_idx[:, k]]
            pos += self.sk_w[:, k, None] * np.einsum('nij,nj->ni', Sk[:, :3, :], self.vh)
        return pos

    def nose(self, basis, hips_loc):
        Q, P = self.rig.fk(basis, hips_loc)
        i = self.rig.idx['Head']
        return P[i] + Q[i] @ self.nose_local

    # ---- finger poses
    def fing_vec(self, side, spec=None):
        """vector of the 15 finger angles of a hand (order of S.finger_bones filtered by side); spec: None = relaxed open, dict name->deg overrides"""
        pref = 'Left' if side == 'L' else 'Right'
        names = [n for n in self.S.finger_bones if n.startswith(pref)]
        base = self.S.open[side]
        v = np.array([base.get(n, 0.0) for n in names], float)
        if spec:
            for i, n in enumerate(names):
                if n in spec:
                    v[i] = spec[n]
        return v

    def finger_names(self, side):
        pref = 'Left' if side == 'L' else 'Right'
        return [n for n in self.S.finger_bones if n.startswith(pref)]

    def finger_shape(self, side, kind, amount=1.0):
        """named hand shapes as ABSOLUTE angle vectors.  kind: open, relaxed, fist, tuck (fingers only), pinch, grip (racket, the engine's right grip / left throat)"""
        pref = 'Left' if side == 'L' else 'Right'
        base = self.S.open[side]
        names = self.finger_names(side)
        out = {}
        for n in names:
            b = base.get(n, 0.0)
            seg = 'Proximal' if 'Proximal' in n else 'Intermediate' if 'Intermediate' in n else 'Distal'
            fing = 'Thumb' if 'Thumb' in n else 'Index' if 'Index' in n else 'Middle' if 'Middle' in n else 'Ring' if 'Ring' in n else 'Little'
            d = 0.0
            if kind == 'open':
                d = 0.0
            elif kind == 'relaxed':
                d = {'Proximal': 12, 'Intermediate': 16, 'Distal': 10}[seg] * (0.0 if fing == 'Thumb' else 1.0)
            elif kind == 'fist':
                d = {'Proximal': 88, 'Intermediate': 100, 'Distal': 62}[seg] * (0.0 if fing == 'Thumb' else 1.0) + (0.0)
            elif kind == 'tuck':      # fingers only, a beckon tuck: knuckles lead, tips follow
                d = {'Proximal': 70, 'Intermediate': 95, 'Distal': 55}[seg] * (0.0 if fing == 'Thumb' else 1.0)
            elif kind == 'pinch':     # index / middle half closed, ring / little relaxed closed
                f = {'Index': 1.0, 'Middle': 0.9, 'Ring': 0.55, 'Little': 0.5}.get(fing, 0.0)
                d = {'Proximal': 45, 'Intermediate': 60, 'Distal': 30}[seg] * f
            out[n] = b + amount * d
        if kind == 'grip':
            g = self.hands['right_grip'] if side == 'R' else self.hands['left_throat']['angles']
            for n in names:
                out[n] = (1 - amount) * base.get(n, 0.0) + amount * g.get(n, 0.0)
        return np.array([out[n] for n in names], float)

    def fing_dict(self, side, vec):
        return {n: float(a) for n, a in zip(self.finger_names(side), vec)}

    # ---- READY in channel form
    def ready_channels(self):
        """the engine's READY pose (racket in the right hand, left hand on the throat) expressed in the free-arm channels + the engine's own bone rotations"""
        if self._ready_P is not None:
            return self._ready_P
        S, rig = self.S, self.rig
        ix = rig.idx
        S.reset()
        P0 = dict(S.ready)
        P0['rk_mode'] = 'fit'
        b, h, info = PS.Solver.solve(S, P0)
        S.reset()
        # the READY the clips must start and end on is the ReadyIdle CLIP's frame 0 (its tracked left-elbow swivel differs from the engine's default solve by up to 14 deg on the male)
        z0 = np.load(f'{MA}/data/anim_{self.tag}.npz', allow_pickle=True)
        q0, hips0 = z0['ReadyIdle/quats'][0], z0['ReadyIdle/hips'][0]
        b0 = np.array([kin.quat_to_mat(q) for q in q0])
        Q, Pos = rig.fk(b0, hips0)
        R_chest = Q[ix['UpperChest']] @ rig.Rrest[ix['UpperChest']].T
        c_off = rig.Rrest[ix['UpperChest']].T @ (0.5 * (rig.J['shoulder_L'] + rig.J['shoulder_R']) - rig.hrest[ix['UpperChest']])
        C = Pos[ix['UpperChest']] + Q[ix['UpperChest']] @ c_off
        P = {k: v for k, v in S.ready.items() if not k.startswith('rk_') and k not in ('l_attach', 'l_grip', 'l_hand', 'l_palm', 'l_elbow', 'r_elbow', 'r_fing', 'l_fing')}
        for s in 'LR':
            pre = 'l' if s == 'L' else 'r'
            Sd = 'Left' if s == 'L' else 'Right'
            Wp = Pos[ix[Sd + 'Hand']]
            Sh = Pos[ix[Sd + 'UpperArm']]
            E = Pos[ix[Sd + 'LowerArm']]
            Qh = Q[ix[Sd + 'Hand']]
            u = unit(Wp - Sh)
            pole = (E - Sh) - np.dot(E - Sh, u) * u
            P[f'{pre}_frame'] = 'c'
            P[f'{pre}_wrist'] = w2a(R_chest.T @ (Wp - C))
            P[f'{pre}_fdir'] = w2a(R_chest.T @ Qh[:, 1])
            P[f'{pre}_palm'] = w2a(R_chest.T @ Qh[:, 2])
            P[f'{pre}_pole'] = w2a(R_chest.T @ unit(pole))
            P[f'{pre}_fing'] = self.finger_shape(s, 'grip', 1.0)
        self._ready = dict(basis=b, hips=h, info=info)
        self._ready_P = P
        return P

    def ready_world(self):
        """READY arm channels in the WORLD authoring frame (r, f, u from the floor origin): wrist / fdir / palm / pole per hand + the racket grip / shaft / face"""
        if getattr(self, '_ready_W', None) is not None:
            return self._ready_W
        S, rig = self.S, self.rig
        ix = rig.idx
        P = self.ready_channels()
        b, h, info = self.solve(P)
        Q, Pos = info['Q'], info['Pos']
        O = self.O
        out = {}
        for s_ in 'LR':
            pre = 'l' if s_ == 'L' else 'r'
            Sd = 'Left' if s_ == 'L' else 'Right'
            Wp, Sh, E, Qh = Pos[ix[Sd + 'Hand']], Pos[ix[Sd + 'UpperArm']], Pos[ix[Sd + 'LowerArm']], Q[ix[Sd + 'Hand']]
            u = unit(Wp - Sh)
            pole = (E - Sh) - np.dot(E - Sh, u) * u
            out[f'{pre}_wrist'] = w2a(Wp - O)
            out[f'{pre}_fdir'] = w2a(Qh[:, 1])
            out[f'{pre}_palm'] = w2a(Qh[:, 2])
            out[f'{pre}_pole'] = w2a(unit(pole))
        out['rk_pos'] = w2a(info['rk_origin'] - O)
        out['rk_shaft'] = w2a(info['rk_R'][:, 1])
        out['rk_face'] = w2a(info['rk_R'][:, 2])
        self._ready_W = out
        return out

    def solve(self, P):
        """channel dict (arrays) -> basis, hips, info.  Finger vectors are turned into dicts here."""
        Pc = dict(P)
        for s in 'LR':
            pre = 'l' if s == 'L' else 'r'
            v = Pc.get(f'{pre}_fing')
            if v is not None and not isinstance(v, dict):
                Pc[f'{pre}_fing'] = self.fing_dict(s, v)
        return self.S.solve_emote(Pc)


def quats_of(rig, basis, prev=None):
    q = np.zeros((rig.n, 4))
    for i in range(rig.n):
        qi = kin.mat_to_quat(basis[i])
        if prev is not None and np.dot(qi, prev[i]) < 0:
            qi = -qi
        q[i] = qi
    return q


def rot_diff_deg(qa, qb):
    d = np.abs(np.sum(qa * qb, axis=-1))
    return np.degrees(2 * np.arccos(np.clip(d, 0, 1)))
