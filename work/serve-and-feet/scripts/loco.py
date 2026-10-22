"""Locomotion + serve authoring on the match-anim-set rig (pure numpy; runs in Blender's python or in its bin/python3.13).

Read-only imports of work/match-anim-set/scripts/{kin,pose}.py (the rig kinematics and the pose solver of the 16 existing clips) - nothing there is edited.

  Hero(tag)            rig + solver + skinning of the foot vertices (linear blend skinning in numpy) + the READY floor
  PCurve               periodic monotone-cubic curve through (phase, value) keys
  Hermite              piecewise cubic Hermite with explicit slopes (stance is linear, swing is a Hermite)
  Gait                 channel generators: walk, run (forward / left / right)
  calibrate()          raises / lowers each foot so that its LOWEST SKINNED VERTEX follows a height target (planted = on the floor)
  solve_frames()       channel dicts -> bone quaternions + hips location + traces

Authoring frame: r = hero's right, f = forward, u = up.  World (Blender) = (-r, -f, u): the heroes face -Y and their right hand is -X."""
import json
import math
import os
import sys

import numpy as np

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
WORK = REPO + '/work/serve-and-feet'
MA = REPO + '/work/match-anim-set'
DATA = WORK + '/data'
sys.path.insert(0, MA + '/scripts')
import kin  # noqa: E402
import pose as PS  # noqa: E402
from kin import a2w, w2a, unit  # noqa: E402

FPS = 30


# --------------------------------------------------------------------------------------------------------------------- curves
def _pchip_slopes(ts, vs, periodic=False, period=1.0):
    """Fritsch-Carlson slopes (shape preserving).  ts increasing; periodic => ts are unique keys of one period."""
    vs = np.asarray(vs, float).reshape(len(ts), -1)
    n = len(ts)
    m = np.zeros_like(vs)
    if periodic:
        tt = np.concatenate([[ts[-1] - period], ts, [ts[0] + period]])
        vv = np.vstack([vs[-1:], vs, vs[:1]])
        h = np.diff(tt)
        d = np.diff(vv, axis=0) / h[:, None]
        for k in range(n):
            a, b = d[k], d[k + 1]
            w1, w2 = 2 * h[k + 1] + h[k], h[k + 1] + 2 * h[k]
            with np.errstate(divide='ignore', invalid='ignore'):
                mk = np.where(a * b > 0, (w1 + w2) / (w1 / a + w2 / b), 0.0)
            m[k] = np.nan_to_num(mk)
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
    m[0] = d[0]
    m[-1] = d[-1]
    return m


class PCurve:
    """periodic monotone cubic through keys [(phase, value)], phase in [0,1); value scalar or vector"""

    def __init__(self, keys, period=1.0, ease=None):
        ks = sorted(keys, key=lambda k: k[0])
        self.ts = np.array([k[0] for k in ks], float)
        self.vs = np.array([np.atleast_1d(np.asarray(k[1], float)) for k in ks])
        self.period = period
        m = _pchip_slopes(self.ts, self.vs, True, period)
        if ease is not None:
            e = np.asarray(ease, float).reshape(-1, 1)
            m = m * (1 - e)
        self.m = m
        self.scalar = np.ndim(ks[0][1]) == 0

    def __call__(self, u):
        T = self.period
        u = u % T
        ts, vs, m = self.ts, self.vs, self.m
        n = len(ts)
        k = int(np.searchsorted(ts, u, side='right') - 1)
        if k < 0:
            k = n - 1
            t0, t1 = ts[k] - T, ts[0]
            v0, v1, m0, m1 = vs[k], vs[0], m[k], m[0]
        elif k == n - 1:
            t0, t1 = ts[k], ts[0] + T
            v0, v1, m0, m1 = vs[k], vs[0], m[k], m[0]
        else:
            t0, t1 = ts[k], ts[k + 1]
            v0, v1, m0, m1 = vs[k], vs[k + 1], m[k], m[k + 1]
        h = t1 - t0
        s = (u - t0) / h if u >= t0 else (u + T - t0) / h
        h00, h10, h01, h11 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s, -2 * s ** 3 + 3 * s ** 2, s ** 3 - s ** 2
        r = h00 * v0 + h10 * h * m0 + h01 * v1 + h11 * h * m1
        return float(r[0]) if self.scalar else r


class Hermite:
    """open piecewise cubic Hermite through (t, value, slope) keys; slope None => shape-preserving estimate"""

    def __init__(self, keys):
        ks = sorted(keys, key=lambda k: k[0])
        self.ts = np.array([k[0] for k in ks], float)
        self.vs = np.array([np.atleast_1d(np.asarray(k[1], float)) for k in ks])
        est = _pchip_slopes(self.ts, self.vs, False)
        self.m = np.array([est[i] if ks[i][2] is None else np.atleast_1d(np.asarray(ks[i][2], float)) for i in range(len(ks))])
        self.scalar = np.ndim(ks[0][1]) == 0

    def __call__(self, t):
        ts, vs, m = self.ts, self.vs, self.m
        if t <= ts[0]:
            r = vs[0] + m[0] * (t - ts[0])
            return float(r[0]) if self.scalar else r
        if t >= ts[-1]:
            r = vs[-1] + m[-1] * (t - ts[-1])
            return float(r[0]) if self.scalar else r
        k = int(np.searchsorted(ts, t, side='right') - 1)
        h = ts[k + 1] - ts[k]
        s = (t - ts[k]) / h
        h00, h10, h01, h11 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s, -2 * s ** 3 + 3 * s ** 2, s ** 3 - s ** 2
        r = h00 * vs[k] + h10 * h * m[k] + h01 * vs[k + 1] + h11 * h * m[k + 1]
        return float(r[0]) if self.scalar else r


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


# --------------------------------------------------------------------------------------------------------------------- hero
class Hero:
    def __init__(self, tag):
        self.tag = tag
        rig = self.rig = kin.Rig(f'{MA}/data/rig_{tag}.json')
        racket = json.load(open(f'{MA}/data/racket_{tag}.json'))
        hands = json.load(open(f'{MA}/data/hands_{tag}.json'))
        self.S = PS.Solver(rig, racket, hands)
        sk = np.load(f'{DATA}/skin_{tag}.npz')
        ix = rig.idx
        dom = sk['dom']
        self.co, self.sk_idx, self.sk_w = sk['co'], sk['idx'], sk['w']
        self.foot_sel = {'L': np.where(np.isin(dom, [ix['LeftFoot'], ix['LeftToes']]))[0], 'R': np.where(np.isin(dom, [ix['RightFoot'], ix['RightToes']]))[0]}
        self.Minv = np.linalg.inv(rig.Mrest)
        self._sub = {}
        for sd, sel in self.foot_sel.items():
            self._sub[sd] = (np.hstack([self.co[sel], np.ones((len(sel), 1))]), self.sk_idx[sel], self.sk_w[sel])
        # bind foot geometry: direction ankle -> ball in the authoring frame (r, f)
        J = rig.J
        vb = w2a(J['ball_L'] - J['ankle_L'])
        self.bind_toe_deg = {'L': math.degrees(math.atan2(vb[0], vb[1])), 'R': -math.degrees(math.atan2(vb[0], vb[1]))}          # + = toes to the right
        self.ankle_rest, self.ball_rest = self.S.ankle_rest, self.S.ball_rest
        self.A = self.S.A_arm
        self.O = self.S.O
        self.ready = dict(self.S.ready)
        self.S.reset()
        b, h, info = self.S.solve(dict(self.ready))
        self.floor = min(self.foot_low(b, h)['L'], self.foot_low(b, h)['R'])        # lowest foot vertex in READY (both feet flat), world z
        self.ready_info = info
        self.hip_f = float(w2a(rig.fk(b, h)[1][rig.idx['LeftUpperLeg']] - self.O)[1])
        self.hip_z = float(rig.fk(b, h)[1][rig.idx['Hips']][2])
        # flat foot, toes straight ahead: how far the ball of the foot is in front of the ankle (authoring f) and how high the ankle is above the sole
        P = dict(self.ready)
        P['lf_yaw'] = self.toe_dir_to_yaw('L', 0.0)
        P['rf_yaw'] = self.toe_dir_to_yaw('R', 0.0)
        self.S.reset()
        b2, h2, i2 = self.S.solve(P)
        self.ankle_ball_f = float(w2a(i2['lf_ball'] - i2['lf_ankle'])[1])
        self.ankle_z = float(i2['lf_ankle'][2] - self.O[2])
        self.S.reset()

    # ---- skinning
    def skin_mats(self, basis, hips_loc):
        Q, P = self.rig.fk(basis, hips_loc)
        Mp = np.zeros((self.rig.n, 4, 4))
        Mp[:, :3, :3] = Q
        Mp[:, :3, 3] = P
        Mp[:, 3, 3] = 1.0
        return Mp @ self.Minv

    def foot_verts(self, side, S):
        vh, idx, w = self._sub[side]
        pos = np.zeros((len(vh), 3))
        for k in range(4):
            Sk = S[idx[:, k]]
            pos += w[:, k, None] * np.einsum('nij,nj->ni', Sk[:, :3, :], vh)
        return pos

    def foot_low(self, basis, hips_loc):
        S = self.skin_mats(basis, hips_loc)
        return {sd: float(self.foot_verts(sd, S)[:, 2].min()) for sd in 'LR'}

    def foot_h(self, basis, hips_loc):
        lo = self.foot_low(basis, hips_loc)
        return {sd: lo[sd] - self.floor for sd in 'LR'}

    # ---- channels
    def toe_dir_to_yaw(self, side, dir_deg):
        """foot yaw CHANNEL for a foot whose toes point `dir_deg` (+ = right of forward): the bind foot already has a toe-out of bind_toe_deg"""
        return dir_deg - self.bind_toe_deg[side]


# --------------------------------------------------------------------------------------------------------------------- solving
def solve_frames(hero, Ps, reset_each=True):
    """channel dicts -> (quats (N,n,4), hips (N,3), infos, bases)"""
    S = hero.S
    rig = hero.rig
    N = len(Ps)
    quats = np.zeros((N, rig.n, 4))
    hips = np.zeros((N, 3))
    infos, bases = [], []
    prev = None
    for k, P in enumerate(Ps):
        if reset_each:
            S.reset()
        basis, hl, info = S.solve(P)
        for i in range(rig.n):
            q = kin.mat_to_quat(basis[i])
            if prev is not None and np.dot(q, prev[i]) < 0:
                q = -q
            quats[k, i] = q
        prev = quats[k]
        hips[k] = hl
        infos.append(info)
        bases.append(basis)
    return quats, hips, infos, bases


def calibrate(hero, Ps, targets, iters=6, tol=0.0006, verbose=False, fixed=None):
    """Ps: list of channel dicts (modified in place: lf_lift / rf_lift).  targets: dict side -> array (N,) of desired foot height (lowest skinned vertex
    above the READY floor, metres).  Returns the final heights (N,2)."""
    N = len(Ps)
    for it in range(iters):
        worst = 0.0
        hs = np.zeros((N, 2))
        for k, P in enumerate(Ps):
            hero.S.reset()
            b, h, info = hero.S.solve(P)
            hh = hero.foot_h(b, h)
            hs[k] = (hh['L'], hh['R'])
            for j, sd in enumerate('LR'):
                err = hh[sd] - targets[sd][k]
                worst = max(worst, abs(err))
                P[f'{"lf" if sd == "L" else "rf"}_lift'] = float(P.get(f'{"lf" if sd == "L" else "rf"}_lift', 0.0) - err)
        if verbose:
            print('  calibrate iter', it, 'worst %.2f mm' % (worst * 1000))
        if worst < tol:
            break
    return hs
