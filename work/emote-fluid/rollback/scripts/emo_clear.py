"""BODY CLEARANCE for the free arms (numpy + Blender's mathutils BVH; run it with `blender -b --python ...`).

The IK of the arms knows nothing about the body.  This module keeps the forearms, the hands and the racket OUT of the torso, legs, head, the other arm and the clothes:

  * obstacle meshes = the skinned meshes of the dressed hero (shirt, shorts and the EXPOSED skin: head, neck, lower legs, feet, the other arm; work/emote-overhaul/data/proxy_<tag>.npz,
    written by extract_proxy.py), posed with the same linear blend skinning as the game (S = M_pose @ M_rest^-1) from the bone matrices of the solve (`info['Q']`, `info['Pos']`).
    One BVH per layer, because the shells are nested; the skin under the clothes is not an obstacle (the clothes are outside it).
  * sample points = vertices of the arm's own skin (every 4th, further than 7 cm from the elbow joint in the bind pose) and, for the racket arm, 960 points of the racket.  A sample
    VIOLATES a layer when its signed distance to the nearest surface point (along that face's normal) is below the layer's margin (positive violation = too close / inside).
  * the arm is moved out by a damped Gauss-Newton step on four parameters: the wrist (racket-grip) target, 3 numbers, and the swing of the elbow around the shoulder-wrist axis, 1 number,
    with a finite-difference Jacobian.  The hand orientation channels stay as the clip asked.  The arms are processed alternately (L, R, L, R) so two crossing forearms push each other apart.
  * contacts that are MEANT (two-handed grip at READY: the other hand holds the racket) are excluded from the obstacle layers; a clip can also let a hand ignore the head.

Frames that do not touch anything come out bit-identical to the unprocessed solve."""
import math
import os

import numpy as np

import kin
from kin import a2w, w2a, unit
import emo_hero as EH

try:
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
except Exception:                                                  # standalone python: no clearance
    BVHTree = None

HERE = os.path.dirname(os.path.abspath(__file__))
PROXY = os.path.abspath(os.path.join(HERE, '..', 'data'))
FOREARM_KEYS = ('LowerArm', 'Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Little')


def vertex_normals(co, tris):
    fn = np.cross(co[tris[:, 1]] - co[tris[:, 0]], co[tris[:, 2]] - co[tris[:, 0]])
    vn = np.zeros_like(co)
    for k in range(3):
        np.add.at(vn, tris[:, k], fn)
    ln = np.linalg.norm(vn, axis=1, keepdims=True)
    ln[ln < 1e-12] = 1.0
    return vn / ln


class SkinProxy:
    def __init__(self, co, idx, w, tris):
        self.co, self.idx, self.w, self.tris = co, idx.astype(np.int64), w, tris
        self.dom = self.idx[np.arange(len(co)), np.argmax(w, 1)]
        self.vh = np.hstack([co, np.ones((len(co), 1))])
        self.n0 = vertex_normals(co, tris)

    def pose_offset(self, S, Rd, off):
        """posed vertices pushed out along their posed normals by `off` (the clothes as an offset of the skin)"""
        pos = np.zeros((len(self.vh), 3))
        nrm = np.zeros((len(self.vh), 3))
        for k in range(4):
            wk = self.w[:, k, None]
            pos += wk * np.einsum('nij,nj->ni', S[self.idx[:, k]][:, :3, :], self.vh)
            nrm += wk * np.einsum('nij,nj->ni', Rd[self.idx[:, k]], self.n0)
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
        return pos + off[:, None] * nrm

    def pose(self, S):
        pos = np.zeros((len(self.vh), 3))
        for k in range(4):
            pos += self.w[:, k, None] * np.einsum('nij,nj->ni', S[self.idx[:, k]][:, :3, :], self.vh)
        return pos

    def pose_sel(self, S, sel):
        idx, w, vh = self.idx[sel], self.w[sel], self.vh[sel]
        pos = np.zeros((len(vh), 3))
        for k in range(4):
            pos += w[:, k, None] * np.einsum('nij,nj->ni', S[idx[:, k]][:, :3, :], vh)
        return pos


def rodrigues(axis, ang):
    a = unit(axis)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * (K @ K)


def make_bvh(pos, tris):
    return BVHTree.FromPolygons(pos.tolist(), tris.tolist(), all_triangles=True)


class Clearance:
    def __init__(self, H, margin_skin=-0.003, margin_cloth=-0.003, margin_racket=-0.002, elbow_skip=0.07, every=4):
        if BVHTree is None:
            raise RuntimeError('the body clearance needs Blender\'s mathutils: run the script with `blender -b --python` (bpyrun.sh), or set CLEAR=0 for a clearance-free run')
        self.H = H
        rig = H.rig
        self.rig = rig
        z = np.load(f'{PROXY}/proxy_{H.tag}.npz', allow_pickle=True)
        assert [str(n) for n in z['names']] == list(rig.names), 'proxy bone order differs from the rig'
        self.body = SkinProxy(z['body_co'], z['body_idx'], z['body_w'], z['body_tris'])
        self.layers = dict(skin=self.body)
        self.body_off = z['body_off']                       # clothes as an offset of the skin (build_offsets.py)
        self.margin = dict(skin=margin_cloth)
        self.margin_racket = margin_racket
        ix = rig.idx
        self.side_name = dict(L='Left', R='Right')
        self.fa_bones, self.hand_bones, self.ua_bone, self.elbow_i, self.wrist_i, self.sh_i = {}, {}, {}, {}, {}, {}
        for s, sn in self.side_name.items():
            self.fa_bones[s] = np.array([ix[n] for n in rig.names if n.startswith(sn) and any(k in n for k in FOREARM_KEYS)])
            self.hand_bones[s] = np.array([ix[n] for n in rig.names if n.startswith(sn) and any(k in n for k in FOREARM_KEYS[1:])])
            self.ua_bone[s] = ix[sn + 'UpperArm']
            self.elbow_i[s] = ix[sn + 'LowerArm']
            self.wrist_i[s] = ix[sn + 'Hand']
            self.sh_i[s] = ix[sn + 'UpperArm']
        # vertex masks (bind pose classification by the dominant bone)
        pr = self.body
        self.vm = dict(skin=dict(fa={s: np.isin(pr.dom, self.fa_bones[s]) for s in 'LR'}, hand={s: np.isin(pr.dom, self.hand_bones[s]) for s in 'LR'},
                                 head=np.isin(pr.dom, np.array([ix[n] for n in rig.names if n in ('Head', 'Neck')]))))
        self.arm_all = {s: np.isin(self.body.dom, np.concatenate([self.fa_bones[s], [self.ua_bone[s]]])) for s in 'LR'}
        self.sample_sel = {}
        for s in 'LR':                                    # a FIXED sample set: forearm / hand skin vertices (every `every`-th) further than `elbow_skip` from the elbow joint in the bind pose
            sel = np.where(self.vm['skin']['fa'][s])[0]
            far = np.linalg.norm(self.body.co[sel] - rig.hrest[self.elbow_i[s]], axis=1) > elbow_skip
            self.sample_sel[s] = sel[far][::every]
        from emo_clips import racket_pts
        self.rkp = racket_pts()[::6]                       # samples of the racket carried by the right arm
        self.rko = racket_pts()[::4]                       # the racket as an obstacle for the LEFT arm (points, radius `rk_rad`)
        self.rk_rad = 0.010
        self.stats = dict(frames=0, corrected=0)
        self.min_samples = 6

    # ---- posing
    def mats(self, info):
        Q, Pos = info['Q'], info['Pos']
        n = self.rig.n
        Mp = np.zeros((n, 4, 4))
        Mp[:, :3, :3] = Q
        Mp[:, :3, 3] = Pos
        Mp[:, 3, 3] = 1.0
        return Mp @ self.H.Minv

    def arm_samples(self, info, side, with_racket, S=None):
        S = self.mats(info) if S is None else S
        pos = self.body.pose_sel(S, self.sample_sel[side])
        kind = np.zeros(len(pos), np.int8)
        if with_racket:
            rp = info['rk_origin'] + (self.rkp @ info['rk_R'].T)
            pos = np.vstack([pos, rp])
            kind = np.concatenate([kind, np.ones(len(rp), np.int8)])
        return pos, kind

    def holding(self, info, other):
        """True when the `other` hand holds the racket (READY: the left hand on the throat) -> its mesh is not an obstacle for the racket arm"""
        W = info['Pos'][self.wrist_i[other]]
        o, ax = info['rk_origin'], info['rk_R'][:, 1]
        t = np.clip(np.dot(W - o, ax), 0.0, 0.40)
        return float(np.linalg.norm(W - (o + t * ax))) < 0.085

    def obstacles(self, info, side, ignore_head, racket_attached, exempt=False):
        """one BVH for `side`'s arm: the posed body skin pushed out by the cloth offset (torso, legs, head, the OTHER arm; not while the two hands are together on the racket)
        without this arm's forearm / hand, without the head when the clip lets this hand touch it"""
        S = self.mats(info)
        Rd = self.rdelta(info)
        other = 'L' if side == 'R' else 'R'
        grip = bool(racket_attached and self.holding(info, 'L')) or bool(exempt)
        pos = self.body.pose_offset(S, Rd, self.body_off)
        keep = ~self.arm_all[side]                          # the arm's own upper arm / forearm are no obstacle (a tight elbow overlaps by nature)
        if ignore_head:
            keep &= ~self.vm['skin']['head']
        if grip:
            keep &= ~self.arm_all[other]
        tris = self.body.tris[keep[self.body.tris].all(1)]
        return dict(skin=make_bvh(pos, tris))

    def rdelta(self, info):
        return info['Q'] @ np.transpose(self.rig.Rrest, (0, 2, 1))

    def violations(self, pts, kind, trees, reach=0.10, rk_obs=None):
        n = len(pts)
        viol = np.full(n, -1.0)
        nrm = np.zeros((n, 3))
        mar_r = self.margin_racket
        if rk_obs is not None:                              # the racket (points with a radius) as an obstacle for the arm's own samples
            for a in range(0, n, 128):
                q = pts[a:a + 128]
                d2 = ((q[:, None, :] - rk_obs[None, :, :]) ** 2).sum(-1)
                j = np.argmin(d2, axis=1)
                r = np.arange(len(q))
                d = np.sqrt(d2[r, j])
                v = (self.rk_rad + self.margin_racket) - d
                v = np.where(d < reach, v, -1.0)
                dirn = q - rk_obs[j]
                dirn /= np.maximum(np.linalg.norm(dirn, axis=1, keepdims=True), 1e-9)
                upd = v > viol[a:a + 128]
                viol[a:a + 128][upd] = v[upd]
                nrm[a:a + 128][upd] = dirn[upd]
        for name, tr in trees.items():
            mar = self.margin[name]
            for i in range(n):
                p = Vector(pts[i])
                loc, nor, idx, dist = tr.find_nearest(p, reach)
                if loc is None:
                    continue
                sd = (p - loc).dot(nor)
                if dist > 0.004 and abs(sd) < 0.8 * dist:          # the nearest point is on an edge / open border: the side cannot be trusted
                    continue
                v = (mar_r if kind[i] == 1 else mar) - sd
                if v > viol[i]:
                    viol[i] = v
                    nrm[i] = (nor[0], nor[1], nor[2])
        return viol, nrm

    # ---- the correction of one arm
    def chan(self, P, side):
        pre = 'l' if side == 'L' else 'r'
        key = f'{pre}_rk_pos' if (side == 'R' and 'r_rk_pos' in P) else f'{pre}_wrist'
        return pre, key

    def to_channel(self, P, info, side, dvec_world):
        """a world (Blender) displacement -> the same displacement in the channel frame of this arm ('w' = authoring axes, 'c' = chest frame)"""
        pre = 'l' if side == 'L' else 'r'
        if P.get(f'{pre}_frame', 'w') == 'c':
            return w2a(info['R_chest'].T @ dvec_world)
        return w2a(dvec_world)

    def apply(self, P, info, side, x, base):
        """P (copy) with the correction x = [dw_world(3), swing(rad)] added to the base channels"""
        pre, key = self.chan(P, side)
        Pn = dict(P)
        Pn[key] = np.asarray(base[key], float) + self.to_channel(P, info, side, x[:3])
        if abs(x[3]) > 1e-9:
            Sh, E, W = info['Pos'][self.sh_i[side]], info['Pos'][self.elbow_i[side]], info['Pos'][self.wrist_i[side]]
            u = unit(W - Sh)
            pole = (E - Sh) - np.dot(E - Sh, u) * u
            if np.linalg.norm(pole) > 1e-6:
                pw = rodrigues(u, float(x[3])) @ unit(pole)
                Pn[f'{pre}_pole'] = w2a(info['R_chest'].T @ pw) if P.get(f'{pre}_frame', 'w') == 'c' else w2a(pw)
        return Pn

    def gn(self, P, info, base, side, with_racket, trees, rk_obs, x0, iters, max_move, max_swing, swing_only=False):
        """damped Gauss-Newton from the start vector x0 -> (x, P', info', max violation)"""
        H = self.H
        x = np.array(x0, float)
        step = np.array([0.012, 0.012, 0.012, math.radians(7.0)])
        Pcur = self.apply(P, info, side, x, base) if np.any(x) else P
        icur = info if not np.any(x) else H.solve(Pcur)[2]
        J = None
        vmax = 9.0
        for it in range(iters):
            pts, kind = self.arm_samples(icur, side, with_racket)
            viol, nrm = self.violations(pts, kind, trees, rk_obs=rk_obs)
            vmax = float(viol.max())
            if vmax <= 0.0005 or int((viol > 0).sum()) < self.min_samples:             # clear, or only a few fingertip samples for an instant: accepted
                vmax = 0.0 if int((viol > 0).sum()) < self.min_samples else vmax
                break
            if J is None or it == 3:
                J = np.zeros((len(pts), 3, 4))
                for k in range(4):
                    xk = x.copy()
                    xk[k] += step[k]
                    Pk = self.apply(P, info, side, xk, base)
                    b_, h_, ik = H.solve(Pk)
                    ptk, _ = self.arm_samples(ik, side, with_racket)
                    J[:, :, k] = (ptk - pts) / step[k]
            act = viol > 0.0
            A = np.einsum('ij,ijk->ik', nrm, J)[act]
            b = (viol[act] + 0.0015)
            wgt = 1.0 + 4.0 * (viol[act] / max(vmax, 1e-6))          # the deepest points count most
            Aw = A * wgt[:, None]
            lam = 2e-3 * max(1.0, act.sum())
            Mx = Aw.T @ A + lam * np.diag([1.0, 1.0, 1.0, 0.5])
            if swing_only:                                   # the hand is pinned (e.g. the pad on the nose): only the elbow may swing around the shoulder-wrist axis
                dx = np.zeros(4)
                dx[3] = (Aw[:, 3] @ b) / max(Aw[:, 3] @ A[:, 3] + lam * 0.5, 1e-9) * 0.85
            else:
                dx = np.linalg.solve(Mx, Aw.T @ b) * 0.85
            mv = np.linalg.norm(dx[:3])
            if mv > 0.035:
                dx[:3] *= 0.035 / mv
            dx[3] = float(np.clip(dx[3], -math.radians(12.0), math.radians(12.0)))
            xn = x + dx
            if np.linalg.norm(xn[:3]) > max_move:
                xn[:3] *= max_move / np.linalg.norm(xn[:3])
            xn[3] = float(np.clip(xn[3], -max_swing, max_swing))
            x = xn
            Pcur = self.apply(P, info, side, x, base)
            b_, h_, icur = H.solve(Pcur)
        else:
            pts, kind = self.arm_samples(icur, side, with_racket)
            viol, nrm = self.violations(pts, kind, trees, rk_obs=rk_obs)
            vmax = float(viol.max())
            if int((viol > 0).sum()) < self.min_samples:
                vmax = 0.0
        return x, Pcur, icur, vmax, it + 1

    def arm_solution(self, P, info, side, racket_attached, ignore_head=False, exempt=False, x_prev=None, iters=7, max_move=0.14, max_swing=math.radians(45.0), tol=0.0005):
        """P: channels with THIS arm nominal (the other arm may already carry its correction); info = solve(P).  -> (x (4,), report)
        x = [dw_world(3), swing(rad)] added to this arm's wrist / grip target and elbow swing.  Candidates: nothing, the previous frame's x (continuity), a descent from 0, six restarts."""
        with_racket = bool(side == 'R' and racket_attached)
        base = {k: (np.array(v, float) if isinstance(v, np.ndarray) else v) for k, v in P.items()}
        trees = self.obstacles(info, side, ignore_head, racket_attached, exempt)
        rk_obs = None
        if side == 'L' and racket_attached and not exempt and not self.holding(info, 'L'):
            rk_obs = info['rk_origin'] + (self.rko @ info['rk_R'].T)
        pts0, kind = self.arm_samples(info, side, with_racket)
        viol, nrm = self.violations(pts0, kind, trees, rk_obs=rk_obs)
        v0 = float(viol.max())
        n0 = int((viol > 0).sum())
        rep = dict(side=side, viol0=round(v0, 4), n0=n0, iters=0, starts=0, moved=0.0, swing=0.0, viol1=round(v0, 4))
        if v0 <= tol or n0 < self.min_samples:                  # nothing, or only a few fingertip samples for an instant: not worth a visible move
            return np.zeros(4), rep
        xp = np.zeros(4) if x_prev is None else np.asarray(x_prev, float)
        cands = []
        if np.any(xp):                                         # continuity: first try to stay near the previous frame's correction
            cands.append(self.gn(P, info, base, side, with_racket, trees, rk_obs, 0.9 * xp, iters, max_move, max_swing))
        c0 = self.gn(P, info, base, side, with_racket, trees, rk_obs, np.zeros(4), iters, max_move, max_swing)
        cands.append(c0)
        starts = len(cands)
        if min(c[3] for c in cands) > 0.003:
            for d in ((0, 0, 1), (0, 0, -1), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)):     # six offsets of 6 cm in world axes
                cands.append(self.gn(P, info, base, side, with_racket, trees, rk_obs, np.concatenate([0.06 * np.array(d, float), [0.0]]), iters, max_move, max_swing))
                starts += 1
                if cands[-1][3] <= tol:
                    break
        # pick: resolved candidates first (violation <= 3 mm), then the one closest to the previous correction (continuity), then the smallest
        def key(c):
            resolved = c[3] <= 0.003
            return (0 if resolved else 1, round(c[3], 3) if not resolved else 0.0, float(np.linalg.norm(c[0][:3] - xp[:3])) + 0.05 * abs(c[0][3] - xp[3]))
        best = min(cands, key=key)
        x, Pcur, icur, vmax, nit = best
        rep.update(viol1=round(vmax, 4), moved=round(float(np.linalg.norm(x[:3])), 4), swing=round(math.degrees(x[3]), 1), iters=nit, starts=starts)
        return x, rep

    def arm_candidates(self, P, info, side, racket_attached, ignore_head=False, exempt=False, extra_starts=(), iters=7, max_move=0.14, max_swing=math.radians(70.0), tol=0.0005, resolved_tol=0.003, swing_only=False):
        """every distinct solution found for this arm (this arm nominal in P): -> list of (x, vmax) plus the report of the nominal state.
        x = 0 is a candidate whenever the nominal arm is clear; otherwise Gauss-Newton descents from 0, from `extra_starts` (neighbouring frames' corrections) and from six 6 cm offsets."""
        with_racket = bool(side == 'R' and racket_attached)
        base = {k: (np.array(v, float) if isinstance(v, np.ndarray) else v) for k, v in P.items()}
        trees = self.obstacles(info, side, ignore_head, racket_attached, exempt)
        rk_obs = None
        if side == 'L' and racket_attached and not exempt and not self.holding(info, 'L'):
            rk_obs = info['rk_origin'] + (self.rko @ info['rk_R'].T)
        pts0, kind = self.arm_samples(info, side, with_racket)
        viol, nrm = self.violations(pts0, kind, trees, rk_obs=rk_obs)
        v0 = float(viol.max())
        n0 = int((viol > 0).sum())
        rep = dict(side=side, viol0=round(v0, 4), n0=n0)
        zero_ok = (v0 <= tol) or (n0 < self.min_samples)
        cands = []
        if zero_ok:
            cands.append((np.zeros(4), 0.0))
        starts = [np.zeros(4)] + [np.asarray(x0, float) for x0 in extra_starts if np.any(x0)]
        if not zero_ok:
            if swing_only:
                for sw in (25.0, -25.0, 55.0, -55.0):
                    starts.append(np.array([0.0, 0.0, 0.0, math.radians(sw)]))
            else:
                for d in ((0, 0, 1), (0, 0, -1), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)):
                    starts.append(np.concatenate([0.06 * np.array(d, float), [0.0]]))
        else:
            starts = [x0 for x0 in starts if np.any(x0)]               # clear at zero: only the neighbours' corrections are worth trying (they may stay valid)
        for x0 in starts:
            if swing_only:
                x0 = np.array([0.0, 0.0, 0.0, x0[3]])
            x, Pc, ic, vmax, nit = self.gn(P, info, base, side, with_racket, trees, rk_obs, x0, iters, max_move, max_swing, swing_only=swing_only)
            if all(np.linalg.norm(x - c[0]) > 0.004 for c in cands):
                cands.append((x, vmax))
        rep['n_cands'] = len(cands)
        return cands, rep

    def arm_violation(self, P, info, side, x, racket_attached, ignore_head=False, exempt=False):
        """worst remaining violation and the number of violating samples of this arm when the correction x is applied (the other arm nominal)"""
        with_racket = bool(side == 'R' and racket_attached)
        base = {k: (np.array(v, float) if isinstance(v, np.ndarray) else v) for k, v in P.items()}
        trees = self.obstacles(info, side, ignore_head, racket_attached, exempt)
        rk_obs = None
        if side == 'L' and racket_attached and not exempt and not self.holding(info, 'L'):
            rk_obs = info['rk_origin'] + (self.rko @ info['rk_R'].T)
        Pn = self.apply(P, info, side, x, base) if np.any(x) else P
        icur = self.H.solve(Pn)[2] if np.any(x) else info
        pts, kind = self.arm_samples(icur, side, with_racket)
        viol, nrm = self.violations(pts, kind, trees, rk_obs=rk_obs)
        return float(viol.max()), int((viol > 0).sum())

    def apply_pair(self, P, info, xs):
        """channels with both corrections added (the pole swing uses the nominal elbow of `info`)"""
        Pn = dict(P)
        for side in 'LR':
            x = xs.get(side)
            if x is not None and np.any(x):
                Pn = self.apply(Pn, info, side, x, P)
        return Pn

    def solve_pair(self, Pnom, racket_attached, ignore_head=(), exempt=False, x_prev=None, sweeps=2):
        """both arms: alternate L, R (the other arm carries its latest correction while one is solved).  -> xs {'L','R'}, reports"""
        H = self.H
        xs = {'L': np.zeros(4), 'R': np.zeros(4)}
        xprev = x_prev or {'L': np.zeros(4), 'R': np.zeros(4)}
        b, h, info_nom = H.solve(Pnom)
        reps = []
        for sw in range(sweeps):
            moved = False
            for side in ('L', 'R'):
                other = 'R' if side == 'L' else 'L'
                Pside = self.apply(Pnom, info_nom, other, xs[other], Pnom) if np.any(xs[other]) else Pnom
                info_side = H.solve(Pside)[2] if Pside is not Pnom else info_nom
                x, rep = self.arm_solution(Pside, info_side, side, racket_attached, ignore_head=(side in ignore_head), exempt=exempt, x_prev=xprev[side])
                rep['sweep'] = sw
                reps.append(rep)
                if np.linalg.norm(x - xs[side]) > 1e-4:
                    moved = True
                xs[side] = x
            if not moved:
                break
        return xs, reps
