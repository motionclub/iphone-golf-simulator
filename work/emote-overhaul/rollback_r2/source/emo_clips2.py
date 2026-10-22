"""EMOTE OVERHAUL (2026-10-05): Emote_Spike, Emote_Scuba, Emote_Thrust, rewritten on the same solver / pipeline as work/emotes (numpy; runs in Blender's python3.13).

The old classes in work/emotes/scripts/emo_clips.py stay untouched; importing this module REPLACES the three registry entries (Emote_Spike / Emote_Scuba / Emote_Thrust), so
`emo_clips.build(name, H)` returns the new clips.  Intros are not touched.

Decisions (Adnan, 2026-10-05): Scuba - the racket is dropped; Thrust - the racket stays in the right hand; Spike - one big slam plus one smaller, racket kept in hand, one arm;
clip lengths are not capped; crossed forearms for the thrust; the hero keeps facing the net.  Plan and references: work/emote-overhaul/REFERENCE_STUDY.md.

Authoring frame (as in the engine): r = hero's right, f = forward (towards the net), u = up, metres, origin on the floor under the Root bone."""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OLD = os.path.abspath(os.path.join(HERE, '..', '..', 'emotes', 'scripts'))
for p in (OLD, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import emo_hero as EH  # noqa: E402
from emo_hero import Timeline, smooth, quats_of, rot_diff_deg  # noqa: E402
import emo_clips as EC  # noqa: E402
from emo_clips import (ClipDef, REGISTRY, build, racket_pts, racket_min_z, FreePath, hand_from_racket, fit_face, fit_palm, solve_contact, pad_point, RK_AUTHOR, A2W_, TAU,
                       R_chest_rot, rot_slerp)  # noqa: E402,F401
import kin  # noqa: E402
import pose as PS  # noqa: E402
from kin import a2w, w2a, unit  # noqa: E402
import emo_clear  # noqa: E402

FPS = 30
_CLR = {}


def get_clear(H):
    """the body-clearance pass of this hero (CLEAR=0 in the environment switches it off, for A/B runs)"""
    if os.environ.get('CLEAR', '1') != '1':
        return None
    k = id(H)
    if k not in _CLR:
        _CLR[k] = emo_clear.Clearance(H)
    return _CLR[k]


# ------------------------------------------------------------------------------------------------------------------------------ small helpers
def ease_in(u, p=2.0):
    u = min(1.0, max(0.0, u))
    return u ** p


def ease_out(u, p=2.0):
    u = min(1.0, max(0.0, u))
    return 1.0 - (1.0 - u) ** p


def lerp(a, b, u):
    return (1.0 - u) * np.asarray(a, float) + u * np.asarray(b, float)


def vslerp(a, b, u):
    """blend two direction vectors (normalised nlerp)"""
    v = lerp(unit(np.asarray(a, float)), unit(np.asarray(b, float)), u)
    return unit(v) if np.linalg.norm(v) > 1e-6 else unit(np.asarray(b, float))


def sm(t, a, b):
    """smoothstep of t over [a, b]"""
    return smooth((t - a) / (b - a)) if b > a else float(t >= a)


class Clip2(ClipDef):
    """shared machinery: pre-solves of the body channels (to know where the shoulders / chest / pelvis are before the arms are placed), authoring-frame conversions"""

    def __init__(self, name, length, H):
        super().__init__(name, length, H)
        self.k = H.A / 0.505                                   # arm-length scale of this hero (male 1.0)
        self.hz = H.rig.J['head_top'][2] / 1.705               # height scale
        self.O = H.O
        b, h, info = H.solve(self.R)
        self.info_ready = info
        self.clr = get_clear(H)
        self._track = None

    # ---- frames of the body for a channel dict (the arms do not influence them)
    def body_info(self, P):
        b, h, info = self.H.solve(P)
        return info

    def A(self, w):
        """world (Blender) point -> authoring frame, origin on the floor"""
        return w2a(np.asarray(w, float) - self.O)

    def chest_to_auth(self, info, p_c):
        """a point given in the chest frame (authoring axes, from the chest centre) -> authoring frame (floor origin)"""
        Rc, C = info['R_chest'], info['chest_center']
        return self.A(C + Rc @ a2w(np.asarray(p_c, float)))

    def chest_dir_to_auth(self, info, d_c):
        return w2a(info['R_chest'] @ a2w(np.asarray(d_c, float)))

    def pelvis_to_auth(self, info, p_p):
        """a point in the pelvis frame (authoring axes: r right, f forward, u up when the pelvis is level) -> authoring frame"""
        H = self.H
        iH = H.rig.idx['Hips']
        Q, Pos = info['Q'], info['Pos']
        Rp = Q[iH] @ H.rig.Rrest[iH].T                         # pelvis orientation (the hip bone's rest orientation removed)
        return self.A(Pos[iH] + Rp @ a2w(np.asarray(p_p, float)))

    def pelvis_R(self, info):
        H = self.H
        iH = H.rig.idx['Hips']
        return info['Q'][iH] @ H.rig.Rrest[iH].T

    def shoulder(self, info, side):
        return self.A(info[f'{side}_shoulder'])

    def ready_grip_in_chest(self):
        """the READY right grip (centre, shaft, face) in the chest frame: the racket arm starts and ends exactly where READY has it"""
        info = self.info_ready
        Rc, C = info['R_chest'], info['chest_center']
        return (w2a(Rc.T @ (info['rk_origin'] - C)), w2a(Rc.T @ info['rk_R'][:, 1]), w2a(Rc.T @ info['rk_R'][:, 2]))

    def ignore_head(self, t):
        """sides whose hand is MEANT to touch the head at time t (they ignore the head in the body clearance)"""
        return ()

    def grip_exempt(self, t):
        """True while the two hands are still together on the racket (READY and the first / last moves): hand-hand and hand-racket contact is meant then"""
        return False

    def racket_attached(self, t):
        return self.racket_world(t, None) is None

    def no_clear(self, t):
        """times at which the clearance must not touch the channels at all"""
        return False

    def pinned(self, t):
        """sides whose hand is pinned to a contact (only the elbow may swing in the clearance), e.g. the pad on the nose"""
        return ()

    def arm_weight(self, t):
        """(left, right) factor on the clearance correction at time t - 0 where an arm must be exactly on its authored pose (e.g. the hand closing on the dropped racket)"""
        return 1.0, 1.0

    # ---- the clearance track: per frame the corrections (L, R) = [dw world (3), elbow swing (rad)], computed once, cached on disk
    def _track_key(self):
        import hashlib
        h = hashlib.sha256()
        for fn in ('emo_clips2.py', 'emo_clear.py'):
            h.update(open(os.path.join(HERE, fn), 'rb').read())
        h.update(self.name.encode() + self.H.tag.encode())
        h.update(repr(sorted((k, v) for k, v in os.environ.items() if k.startswith(('CROSS', 'L_CR', 'R_CR', 'L_ST', 'R_ST', 'FD_ST', 'SH_ST')))).encode())
        return h.hexdigest()[:12]

    def clearance_track(self):
        if self.clr is None:
            return None
        if getattr(self, '_track', None) is None:
            path = os.path.join(HERE, '..', 'data', f'track_{self.name}_{self.H.tag}_{self._track_key()}.npz')
            if os.path.exists(path) and not os.environ.get('NOCACHE'):
                self._track = np.load(path)['xs']
            else:
                self._track = self.compute_track()
                np.savez_compressed(path, xs=self._track)
        return self._track

    def compute_track(self):
        """per frame and arm a pool of candidate corrections (zero if clear, descents from several starts, the neighbours' corrections), then ONE path per arm through time by dynamic programming:
        unresolved penetration costs a lot, a jump between consecutive frames costs |dx|^2, a big move costs a little -> no pops between different local solutions"""
        clr = self.clr
        H = self.H
        nF = int(round(self.length * 30)) + 1
        Ps, infos = [], []
        for f in range(nF):
            P = self.P(f / 30.0)
            Ps.append(P)
            infos.append(H.solve(P)[2])
        pools = {'L': [None] * nF, 'R': [None] * nF}
        reps = [dict() for _ in range(nF)]

        def make_pool(f, extra):
            t = f / 30.0
            for side in 'LR':
                if self.no_clear(t):
                    pools[side][f] = [(np.zeros(4), 0.0)]
                    continue
                other = 'R' if side == 'L' else 'L'
                c, rep = clr.arm_candidates(Ps[f], infos[f], side, self.racket_attached(t), ignore_head=(side in self.ignore_head(t)), exempt=self.grip_exempt(t), extra_starts=extra.get(side, ()), swing_only=(side in self.pinned(t)))
                pools[side][f] = c
                reps[f][side] = rep
        for f in range(nF):                                   # pass 1: independent pools
            make_pool(f, {})
        for f in range(nF):                                   # pass 2: add what the neighbouring frames' corrections give here (keeps a branch alive through the frames where it is the only continuous one)
            extra = {}
            for side in 'LR':
                ex = []
                for g in (f - 1, f + 1):
                    if 0 <= g < nF:
                        ex += [c[0] for c in pools[side][g] if np.any(c[0])]
                extra[side] = ex[:6]
            if any(extra[s_] for s_ in 'LR') and not self.no_clear(f / 30.0):
                old = {s_: list(pools[s_][f]) for s_ in 'LR'}
                make_pool(f, extra)
                for s_ in 'LR':                               # keep the union
                    for c in old[s_]:
                        if all(np.linalg.norm(c[0] - d[0]) > 0.004 for d in pools[s_][f]):
                            pools[s_][f].append(c)
        xs = np.zeros((nF, 2, 4))
        self.track_reports = []
        for si, side in enumerate('LR'):
            pl = pools[side]

            def unit_cost(c):
                x, v = c
                return 6.0 * max(0.0, v - 0.003) / 0.01 + 0.4 * float(np.linalg.norm(x[:3])) + 0.1 * abs(float(x[3]))

            def jump(a, b):
                d = a[:3] - b[:3]
                return 40.0 * (float(d @ d) + (0.25 * (a[3] - b[3])) ** 2)
            INF = 1e18
            cost = [np.array([unit_cost(c) for c in pl[0]])]
            back = [None]
            for f in range(1, nF):
                cur = np.array([unit_cost(c) for c in pl[f]])
                prev = cost[-1]
                bp = np.zeros(len(pl[f]), int)
                tot = np.zeros(len(pl[f]))
                for j, c in enumerate(pl[f]):
                    cand = [prev[i] + jump(c[0], pl[f - 1][i][0]) for i in range(len(pl[f - 1]))]
                    i = int(np.argmin(cand))
                    bp[j] = i
                    tot[j] = cur[j] + cand[i]
                cost.append(tot)
                back.append(bp)
            j = int(np.argmin(cost[-1]))
            for f in range(nF - 1, -1, -1):
                xs[f, si] = pl[f][j][0]
                if back[f] is not None:
                    j = int(back[f][j])
        # ---- smooth the chosen path (7-tap triangle); frames where the smoothed correction leaves a violation keep their original value and the neighbours are smoothed around them
        kern = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 4.0, 3.0, 2.0, 1.0])
        kern /= kern.sum()

        def smooth_track(x):
            pad = np.pad(x, ((4, 4), (0, 0)), mode='edge')
            return np.stack([np.convolve(pad[:, j], kern, mode='valid') for j in range(4)], axis=1)
        fade = np.array([sm(f / FPS, 0.0, 0.20) * (1.0 - sm(f / FPS, self.length - 0.20, self.length)) for f in range(nF)])
        xs0 = xs.copy()
        for si, side in enumerate('LR'):
            # envelope first: every frame takes the largest correction of its +-3 frame neighbourhood (a correction starts BEFORE it is needed and ends after), then the 9-tap triangle smoothing
            mag = np.linalg.norm(xs0[:, si, :3], axis=1) + 0.25 * np.abs(xs0[:, si, 3])
            env = xs0[:, si].copy()
            for f in range(nF):
                g = max(range(max(0, f - 4), min(nF, f + 5)), key=lambda k: mag[k])
                if mag[g] > mag[f]:
                    env[f] = xs0[g, si]
            xsm = smooth_track(env)
            fixed = np.zeros(nF, bool)
            for it in range(4):
                bad = []
                for f in range(nF):
                    t = f / FPS
                    if fixed[f] or self.no_clear(t):
                        continue
                    if np.linalg.norm(xsm[f] * fade[f] - xs0[f, si] * fade[f]) < 0.003 and abs(xsm[f, 3] - xs0[f, si, 3]) < 0.01:
                        continue
                    v, n = clr.arm_violation(Ps[f], infos[f], side, xsm[f] * fade[f], self.racket_attached(t), ignore_head=(side in self.ignore_head(t)), exempt=self.grip_exempt(t))
                    if v > 0.003 and n >= clr.min_samples:
                        bad.append(f)
                if not bad:
                    break
                fixed[bad] = True
                xsm[bad] = xs0[bad, si]
                for _ in range(2):
                    xsm = smooth_track(xsm)
                    xsm[fixed] = xs0[fixed, si]
            for f in range(nF):                                   # a pinned hand (the pad on the nose) may swing its elbow, never translate: the smoothing must not leak translation into those frames
                if side in self.pinned(f / FPS):
                    xsm[f, :3] = 0.0
            xs[:, si] = xsm
        for f in range(nF):
            self.track_reports.append((f, [dict(reps[f].get(s_, {}), side=s_, sweep=0, iters=1, moved=float(np.linalg.norm(xs[f, 'LR'.index(s_), :3])), swing=float(np.degrees(xs[f, 'LR'.index(s_), 3])), viol1=0.0, starts=0, x=list(np.round(xs[f, 'LR'.index(s_)], 3))) for s_ in 'LR']))
        return xs

    def track_at(self, t):
        xs = self.clearance_track()
        if xs is None:
            return None
        f = min(max(t * 30.0, 0.0), len(xs) - 1.0)
        f0 = int(math.floor(f))
        f1 = min(f0 + 1, len(xs) - 1)
        a = f - f0
        x = (1 - a) * xs[f0] + a * xs[f1]
        w = sm(t, 0.0, 0.20) * (1.0 - sm(t, self.length - 0.20, self.length))      # READY at both ends stays exactly the READY pose
        wl, wr = self.arm_weight(t)
        return {'L': x[0] * w * wl, 'R': x[1] * w * wr}

    def base_solve(self, t):
        """channels -> body clearance (the precomputed track) -> solve.  -> (P, basis, hips, info, track corrections)"""
        P = self.P(t)
        xs = self.track_at(t) if self.clr is not None else None
        if xs is None or not any(np.any(v) for v in xs.values()):
            basis, hips, info = self.H.solve(P)
            return P, basis, hips, info, xs
        b, h, info_nom = self.H.solve(P)
        P2 = self.clr.apply_pair(P, info_nom, xs)
        basis, hips, info = self.H.solve(P2)
        return P2, basis, hips, info, xs

    def solve(self, t):
        P, basis, hips, info, xs = self.base_solve(t)
        return dict(basis=basis, hips=hips, info=info, racket=self.racket_world(t, info), P=P, clear=xs)

    def racket_world(self, t, info):
        return None


# ------------------------------------------------------------------------------------------------------------------------------ Emote_Spike
def curve(keys):
    """smooth monotone-cubic curve through (t, v) keys (v scalar or vector); flat outside"""
    return EH.Curve([(k[0], k[1]) for k in keys])


class Spike2(Clip2):
    """ONE-ARM racket slam.  The racket arm does everything; the free (left) arm only hangs and swings back a little.  The racket stays in the right hand.
    Procedural swing about the right shoulder: the grip centre is S + L (cos phi f + sin phi u) (+ a small outward offset), the shaft angle beta lags the arm (the racket whips).
    0.00-0.30 set (breath, head down) | 0.30-0.88 wind-up (racket over the head and dropped behind it, chest arched) | 0.90-1.18 strike (0.28 s) | 1.18 impact 1 (the racket
    head meets the court) | 1.18-1.45 rebound and hold low | 1.45-1.68 re-lift (smaller) | 1.70-1.94 second, smaller strike | 1.94 impact 2 | 1.94-2.2 rebound | 2.2-3.0 stand up,
    head shake, glare | 3.0-3.2 READY."""

    DUR = 3.2

    def grip_exempt(self, t):
        return t < 0.40 or t > 2.85

    TOP, IMP1, IMP2 = 27 / 30.0, 36 / 30.0, 59 / 30.0          # whole frames: the racket head meets the court ON a frame
    S1, S2 = 0.28, 8 / 30.0
    AZ = 24.0

    def __init__(self, H):
        super().__init__('Emote_Spike', self.DUR, H)
        R = self.R
        self.grip0 = self.ready_grip_in_chest()
        self.left_ready = dict(w=np.asarray(R['l_wrist'], float), fd=np.asarray(R['l_fdir'], float), pm=np.asarray(R['l_palm'], float), pl=np.asarray(R['l_pole'], float))
        self.grip_fing = H.finger_shape('R', 'grip', 1.0)
        g_tight = self.grip_fing.copy()
        for i, nm in enumerate(H.finger_names('R')):
            if 'Proximal' in nm and 'Thumb' not in nm:
                g_tight[i] += 8.0
        self.grip_tight = g_tight
        self.relax_L = H.finger_shape('L', 'relaxed', 1.0)
        self.fist_L = H.finger_shape('L', 'fist', 1.0)
        # ---- body: smooth keys for the slow parts, closed-form ramps for the two folds (see body())
        self.wind = curve([(0.00, [9.0, 8.0, -14.0, 8.0, 0.0, 0.0, 0.0, 0.0]),
                           (0.30, [11.0, 9.0, -8.0, 9.0, 0.0, 0.0, -0.012, 0.0]),
                           (0.60, [3.0, -8.0, -22.0, 12.0, -2.0, -0.030, -0.030, 0.0]),
                           (self.TOP, [0.0, -24.0, -30.0, 14.0, -5.0, -0.055, -0.045, 0.0])])
        # [pel pitch, chest pitch, head pitch, knee, chest roll, pel f, pel u, (spare)]
        self.hold1 = curve([(self.IMP1, [47.0, 38.0, -38.0, 22.0, 6.0, -0.135, -0.080, 0.0]),
                            (1.50, [45.0, 36.0, -36.0, 21.0, 3.0, -0.125, -0.072, 0.0]),
                            (1.70, [38.0, 27.0, -31.0, 17.0, 0.0, -0.105, -0.060, 0.0])])
        self.hold2 = curve([(self.IMP2, [45.0, 36.0, -36.0, 21.0, 4.0, -0.130, -0.076, 0.0]),
                            (2.20, [43.0, 33.0, -32.0, 20.0, 2.0, -0.115, -0.068, 0.0]),
                            (2.60, [24.0, 14.0, -24.0, 13.0, 0.0, -0.050, -0.032, 0.0]),
                            (3.00, [11.0, 9.0, -16.0, 9.0, 0.0, -0.005, -0.008, 0.0]),
                            (self.DUR, [9.0, 8.0, -14.0, 8.0, 0.0, 0.0, 0.0, 0.0])])
        # ---- swing: [phi, L, beta, roff, w, az]  (az = how far the swing plane is turned outward, deg: the racket comes down beside the right foot, in view from behind)
        self.sw_wind = curve([(0.30, [-54.0, 0.47, 46.0, -0.17, 0.0, 0.0]), (0.44, [15.0, 0.46, 72.0, -0.10, 1.0, 0.0]), (0.60, [95.0, 0.42, 128.0, -0.07, 1.0, 0.0]),
                              (0.76, [141.0, 0.38, 198.0, -0.07, 1.0, 0.0]), (self.TOP, [150.0, 0.37, 212.0, -0.07, 1.0, 0.0])])
        imp = [-72.0, 0.585, -52.0, 0.05, 1.0, self.AZ]
        self.sw_reb1 = curve([(self.IMP1, imp), (self.IMP1 + 0.09, [-60.0, 0.56, -24.0, 0.05, 1.0, self.AZ]), (self.IMP1 + 0.22, [-68.0, 0.58, -42.0, 0.05, 1.0, self.AZ]),
                              (1.50, [-68.0, 0.58, -44.0, 0.05, 1.0, self.AZ]), (1.60, [-32.0, 0.52, 4.0, 0.04, 1.0, 16.0]), (1.70, [4.0, 0.47, 40.0, 0.02, 1.0, 6.0]),
                              (1.72, [6.0, 0.47, 42.0, 0.02, 1.0, 6.0])])
        self.sw_reb2 = curve([(self.IMP2, imp), (self.IMP2 + 0.09, [-62.0, 0.56, -26.0, 0.05, 1.0, self.AZ]), (self.IMP2 + 0.20, [-68.0, 0.58, -42.0, 0.05, 1.0, self.AZ]),
                              (2.30, [-68.0, 0.57, -40.0, 0.04, 1.0, self.AZ]), (2.55, [-64.0, 0.52, -26.0, -0.02, 1.0, 14.0]), (2.90, [-66.0, 0.48, 6.0, -0.12, 0.7, 0.0]),
                              (3.06, [-58.0, 0.47, 30.0, -0.15, 0.25, 0.0]), (self.DUR, [-54.0, 0.47, 46.0, -0.17, 0.0, 0.0])])
        self.fold_d = [0.0, 0.0]
        self.fold_d = self.fit_fold()

    # ---- per-hero extra fold at each impact (so a shorter arm / lower shoulder still lands the racket head on the court)
    def fold_extra(self, t):
        d = 0.0
        for dl, imp_ in zip(self.fold_d, (self.IMP1, self.IMP2)):
            if dl <= 0.0:
                continue
            rise = sm(t, imp_ - 0.28, imp_)
            fall = 1.0 - sm(t, imp_ + 0.05, imp_ + 0.45)
            d += dl * rise * fall
        return d

    def fit_fold(self):
        """smallest extra trunk fold (deg, steps of 1) at each impact for which the right arm reaches the snapped racket target (shortfall < 3 mm)"""
        out = []
        for i, imp_ in enumerate((self.IMP1, self.IMP2)):
            best = 0.0
            for dl in range(0, 21):
                self.fold_d[i] = float(dl)
                P = self.P(imp_)
                b, h, info = self.H.solve(P)
                best = float(dl)
                if info['R_arm_short'] < 0.003:
                    break
            self.fold_d[i] = best
            out.append(best)
        return out

    # ---- closed-form folds
    @staticmethod
    def _ramp(t, t0, t1, a, b, p):
        u = min(1.0, max(0.0, (t - t0) / (t1 - t0)))
        return a + (b - a) * u ** p

    def body_vec(self, t):
        v = np.array(self._body_vec0(t), float)
        d = self.fold_extra(t)
        if d:
            v[0] += d
            v[1] += 0.8 * d
        return v

    def _body_vec0(self, t):
        """[pel pitch, chest pitch, head pitch, knee, chest roll, pel f, pel u]"""
        if t < self.TOP:
            return np.array(self.wind(t)[:7], float)
        if t < self.IMP1:                                       # strike 1: the trunk folds late (ease-in) while the arm comes over
            a = np.array(self.wind(self.TOP)[:7], float)
            b = np.array(self.hold1(self.IMP1)[:7], float)
            u = ((t - 0.94) / (self.IMP1 - 0.94)) if t > 0.94 else 0.0
            return a + (b - a) * min(1.0, max(0.0, u)) ** 1.7
        if t < 1.70:
            return np.array(self.hold1(t)[:7], float)
        if t < self.IMP2:                                       # strike 2
            a = np.array(self.hold1(1.70)[:7], float)
            b = np.array(self.hold2(self.IMP2)[:7], float)
            u = ((t - 1.76) / (self.IMP2 - 1.76)) if t > 1.76 else 0.0
            return a + (b - a) * min(1.0, max(0.0, u)) ** 1.7
        return np.array(self.hold2(t)[:7], float)

    def swing_vec(self, t):
        """[phi, L, beta, roff, w]"""
        if t < self.TOP:
            return np.array(self.sw_wind(t), float) if t > 0.30 else np.array([-54.0, 0.47, 46.0, -0.17, 0.0, 0.0])
        imp = np.array([-72.0, 0.585, -52.0, 0.05, 1.0, self.AZ])
        if t < self.IMP1:                                       # strike 1: constant angular acceleration (ease-in), the racket lags the arm and catches up at the court
            u = (t - self.TOP) / (self.IMP1 - self.TOP)
            top = np.array([150.0, 0.37, 212.0, -0.07, 1.0, 0.0])
            return self._strike(top, imp, u)
        if t < self.IMP2 - self.S2:
            return np.array(self.sw_reb1(t), float)
        if t < self.IMP2:                                       # strike 2 (smaller)
            u = (t - (self.IMP2 - self.S2)) / self.S2
            top = np.array(self.sw_reb1(self.IMP2 - self.S2), float)
            return self._strike(top, imp, u)
        return np.array(self.sw_reb2(t), float)

    @staticmethod
    def _strike(top, imp, u):
        ph = top[0] + (imp[0] - top[0]) * u ** 2
        be = top[2] + (imp[2] - top[2]) * u ** 2.15
        Lq = top[1] + (imp[1] - top[1]) * u ** 1.6
        ro = top[3] + (imp[3] - top[3]) * u
        az = top[5] + (imp[5] - top[5]) * u ** 1.8
        return np.array([ph, Lq, be, ro, 1.0, az])

    @staticmethod
    def swing_dir(phi_deg, az_deg=0.0):
        p, a = math.radians(phi_deg), math.radians(az_deg)
        return np.array([math.sin(a) * math.cos(p), math.cos(a) * math.cos(p), math.sin(p)])

    def body_P(self, t):
        bv = self.body_vec(t)
        P = dict(self.R)
        P['pel'] = np.array([0.0, bv[5], bv[6]])
        P['pel_rot'] = np.array([0.0, bv[0], 0.0])
        heave = 0.0
        if self.IMP1 <= t <= 2.9:
            heave = 2.2 * math.sin(TAU * 2.2 * (t - self.IMP1)) * sm(t, self.IMP1, 1.30) * (1 - sm(t, 2.55, 2.90))
        P['chest_rot'] = np.array([0.0, bv[1] + heave, bv[4]])
        sh = 0.0
        a0, a1 = 2.22, 2.86
        if a0 <= t <= a1:
            sh = 22.0 * math.sin(TAU * 2.4 * (t - a0)) * sm(t, a0, a0 + 0.10) * (1 - sm(t, a1 - 0.22, a1))
        P['head_rot'] = np.array([sh, bv[2], 0.0])
        P['lf_knee'] = bv[3]
        P['rf_knee'] = bv[3]
        return P

    def P(self, t):
        P = self.body_P(t)
        info = self.body_info(P)
        S_R = self.shoulder(info, 'R')
        S_L = self.shoulder(info, 'L')
        phi, L_, beta, roff, w, az = self.swing_vec(t)
        G_s = S_R + np.array([roff, 0.0, 0.0]) + (L_ * self.k) * self.swing_dir(phi, az)       # the reach follows the hero's arm length (male 1.0)
        b = math.radians(beta)
        sh_s = unit(np.array([0.10 + 0.9 * math.sin(math.radians(az)) * abs(math.cos(b)), math.cos(b), math.sin(b)]))
        fa_s = np.array([-1.0, 0.0, 0.0])
        g0, s0, f0 = self.grip0
        G_r = self.chest_to_auth(info, g0)
        sh_r = self.chest_dir_to_auth(info, s0)
        fa_r = self.chest_dir_to_auth(info, f0)
        G = (1 - w) * G_r + w * G_s
        sh = vslerp(sh_r, sh_s, w) if w > 0 else sh_r
        fa = vslerp(fa_r, fa_s, w) if w > 0 else fa_r
        fa = fa - np.dot(fa, sh) * sh
        fa = unit(fa) if np.linalg.norm(fa) > 1e-6 else fa_s
        Rw = A2W_ @ PS.frame_from_axes(sh, fa)
        mz = racket_min_z(np.array([0.0, 0.0, G[2]]), Rw)
        if mz < 0.0:                                            # the court stops the racket
            G = G + np.array([0.0, 0.0, -mz])
        elif mz > 0.0:                                          # the strikes END on the court: the grip is pulled down so the head touches it exactly on the impact frame
            tt = 0.0
            for imp_, dur_ in ((self.IMP1, self.S1), (self.IMP2, self.S2)):
                if imp_ - 0.07 <= t <= imp_:
                    tt = max(tt, ((t - (imp_ - 0.07)) / 0.07) ** 2)
            G = G + np.array([0.0, 0.0, -min(mz, 0.12) * tt])
        P['r_frame'] = 'w'
        P['r_rk_pos'] = G
        P['r_rk_shaft'] = sh
        P['r_rk_face'] = fa
        pole_rd = self.chest_dir_to_auth(info, self.R['r_pole'])                         # READY elbow direction while the arm is still in READY (w = 0)
        P['r_pole'] = unit((1 - w) * pole_rd + w * np.array([0.55, -0.35, -0.35]))
        P['r_wlim'] = (math.radians(85.0), math.radians(178.0))
        grip_amt = max(sm(t, self.IMP1 - 0.08, self.IMP1 - 0.02) * (1 - sm(t, 1.3, 1.45)), sm(t, self.IMP2 - 0.08, self.IMP2 - 0.02) * (1 - sm(t, 2.1, 2.25)))
        P['r_fing'] = lerp(self.grip_fing, self.grip_tight, grip_amt)
        # ---- the free (left) arm: READY (left hand on the racket throat) -> hangs from its shoulder, trails behind in the strikes, fist clenched
        wl = sm(t, 0.10, 0.34) * (1 - sm(t, 2.92, 3.18))
        sb1 = math.sin(math.pi * min(1.0, max(0.0, (t - 0.98) / (self.IMP1 - 0.98)))) if 0.98 <= t <= self.IMP1 else 0.0
        sb2 = math.sin(math.pi * min(1.0, max(0.0, (t - 1.76) / (self.IMP2 - 1.76)))) if 1.76 <= t <= self.IMP2 else 0.0
        hang = np.array([-0.13, -0.02 - 0.09 * sb1 - 0.06 * sb2, -0.46 * self.k])         # the free arm hangs a hand-width clear of the hip / thigh
        left_w = self.chest_to_auth(info, self.left_ready['w'])
        P['l_frame'] = 'w'
        arc = 4.0 * wl * (1.0 - wl)                                                    # bulge of the path READY <-> hang: out to the left, forward and a little up (clear of the hip / thigh)
        P['l_wrist'] = (1 - wl) * left_w + wl * (S_L + hang) + arc * np.array([-0.15, 0.13, 0.06]) * self.k
        fd_h, pm_h = np.array([0.05, 0.25, -0.97]), np.array([0.92, 0.0, 0.2])
        P['l_fdir'] = vslerp(self.chest_dir_to_auth(info, self.left_ready['fd']), fd_h, wl)
        P['l_palm'] = vslerp(self.chest_dir_to_auth(info, self.left_ready['pm']), pm_h, wl)
        P['l_pole'] = vslerp(self.chest_dir_to_auth(info, self.left_ready['pl']), np.array([-0.6, -0.3, -0.5]), wl)
        fist = sm(t, 0.80, 0.95) * (1 - sm(t, 2.3, 2.5))
        P['l_fing'] = lerp(lerp(self.R['l_fing'], self.relax_L, wl), self.fist_L, fist)
        return P


REGISTRY['Emote_Spike'] = Spike2


def a2w_inv(Rm, v_auth):
    """authoring-frame vector -> the frame whose world rotation (Blender) is Rm, in authoring axes"""
    return w2a(Rm.T @ a2w(np.asarray(v_auth, float)))


# ------------------------------------------------------------------------------------------------------------------------------ Emote_Thrust
class Thrust2(Clip2):
    """Pelvic-thrust taunt with a crossed-forearm chop.  The racket STAYS in the right hand.  ONE driver (th: 0 = hips back .. 1 = hips front) moves the pelvis, the trunk and both arms, so the
    forearms land on the pelvis on the very frame the hips arrive; between hits the hips go all the way back and the fists re-cock at the shoulders.  Feet stay on their READY spots (toes
    turned out), knees bent.  Three hits (each bigger), the last held with the head thrown back and the shoulders shaking; then a strut with the fists on the hips.
    0.00-0.50 settle (hips back, fists up) | hits at 0.60 / 1.1667 / 1.70 (rise 0.14 s, return 0.26 s, the last held 0.5 s) | 2.55-3.05 strut | 3.05-3.5 READY."""

    DUR = 3.5

    def grip_exempt(self, t):
        return t < 0.50 or t > 3.05

    HITS = ((18 / 30.0, 0.86, 0.06), (35 / 30.0, 0.95, 0.06), (51 / 30.0, 1.0, 0.50))      # time of the hit (whole frame), amplitude, hold
    RISE, FALL = 0.14, 0.26
    CROSS_SHAFT = tuple(float(x) for x in os.environ.get('CROSS_SHAFT', '-0.75,0.43,-0.50').split(','))
    L_CR = tuple(float(x) for x in os.environ.get('L_CR', '0.05,0.31,0.09').split(','))      # left wrist at the cross, pelvis frame (r, f, u) in metres for the male
    R_CR = tuple(float(x) for x in os.environ.get('R_CR', '-0.14,0.37,0.25').split(','))     # right grip centre at the cross
    L_CR_F = tuple(float(x) for x in os.environ.get('L_CR_F', '0.10,0.28,0.09').split(','))     # female hero (wider hips, skirt): the left wrist closer, the grip further out
    R_CR_F = tuple(float(x) for x in os.environ.get('R_CR_F', '-0.12,0.43,0.22').split(','))
    L_ST = tuple(float(x) for x in os.environ.get('L_ST', '-0.31,0.10,0.14').split(','))      # strut: left wrist (fist on the hip), pelvis frame
    R_ST = tuple(float(x) for x in os.environ.get('R_ST', '0.31,0.13,0.15').split(','))        # strut: right grip centre
    FD_ST = tuple(float(x) for x in os.environ.get('FD_ST', '0.05,0.93,-0.35').split(','))     # strut: finger direction of the left fist (pelvis frame)
    SH_ST = tuple(float(x) for x in os.environ.get('SH_ST', '0.15,0.55,0.82').split(','))       # strut: racket shaft direction (pelvis frame)

    def __init__(self, H):
        super().__init__('Emote_Thrust', self.DUR, H)
        R = self.R
        self.grip0 = self.ready_grip_in_chest()
        self.left_ready = dict(w=np.asarray(R['l_wrist'], float), fd=np.asarray(R['l_fdir'], float), pm=np.asarray(R['l_palm'], float), pl=np.asarray(R['l_pole'], float))
        self.fist_L = H.finger_shape('L', 'fist', 1.0)
        self.grip_fing = H.finger_shape('R', 'grip', 1.0)
        g_t = self.grip_fing.copy()
        for i, nm in enumerate(H.finger_names('R')):
            if 'Proximal' in nm and 'Thumb' not in nm:
                g_t[i] += 8.0
        self.grip_tight = g_t
        self.faces = None
        self.faces = self.scan_faces()

    def best_face(self, P, shaft, prefer, step=10):
        """the racket roll about `shaft` with the least wrist clamp (ties broken towards the preferred face direction)"""
        H = self.H
        sh = unit(np.asarray(shaft, float))
        g0 = unit(np.cross(sh, [0, 0, 1.0])) if abs(sh[2]) < 0.95 else np.array([1.0, 0.0, 0.0])
        g1 = unit(np.cross(sh, g0))
        pr = np.asarray(prefer, float)
        best = None
        for ang in range(0, 360, step):
            a = math.radians(ang)
            f = math.cos(a) * g0 + math.sin(a) * g1
            Pt = dict(P)
            Pt['r_rk_shaft'], Pt['r_rk_face'] = sh, f
            b, h, info = H.solve(Pt)
            sc = info['R_wrist_clamp_deg'] + 300.0 * info['R_arm_short'] + 4.0 * (1.0 - float(np.dot(f, unit(pr))))
            if best is None or sc < best[0]:
                best = (sc, f, info['R_wrist_clamp_deg'])
        return best

    def scan_faces(self):
        """face directions (pelvis frame for the cross and the strut, chest frame for the cock) found once from three representative instants"""
        out = {}
        for key, t, frame, prefer in (('cock', 0.45, 'c', [-1.0, 0.1, 0.0]), ('cross', 0.6, 'p', [0.2, 0.95, 0.0]), ('strut', 2.8, 'p', [-1.0, 0.1, 0.0])):
            P = self.P(t)
            info = self.body_info(P)
            if frame == 'c':
                Rm = info['R_chest']
            else:
                Rm = self.pelvis_R(info)
            pref_auth = w2a(Rm @ a2w(np.asarray(prefer, float)))
            sc, f, cl = self.best_face(P, P['r_rk_shaft'], pref_auth)
            out[key] = a2w_inv(Rm, f)
            self.scan_report = getattr(self, 'scan_report', {})
            self.scan_report[key] = (round(float(sc), 2), round(float(cl), 2))
        return out

    # ---- the driver
    def th(self, t):
        best, big = 0.0, self.HITS[0][1]
        for (p, a, hold) in self.HITS:
            if t < p - self.RISE or t > p + hold + self.FALL:
                continue
            if t < p:
                v = ((t - (p - self.RISE)) / self.RISE) ** 2
            elif t <= p + hold:
                v = 1.0
            else:
                v = 1.0 - smooth((t - p - hold) / self.FALL)
            if v > best:
                best, big = v, a
        return best, big

    def body_P(self, t, th, big, e, strut):
        P = dict(self.R)
        k = self.k
        f_back, f_front = -0.13, -0.13 + 0.42 * big
        u_back, u_front = -0.14, -0.045
        P['pel'] = np.array([0.0, e * lerp(f_back, f_front, th), e * lerp(u_back, u_front, th)])
        P['pel_rot'] = np.array([0.0, (1 - e) * 9.0 + e * lerp(16.0, -22.0 * big, th), 0.0])
        P['chest_rot'] = np.array([0.0, (1 - e) * 8.0 + e * lerp(12.0, 12.0 * big, th), 0.0])
        head_front = -10.0 if big < 0.95 else -22.0
        hp = (1 - e) * -14.0 + e * lerp(-33.0, head_front, th)
        cack = 1.0 if 1.95 <= t <= 2.5 else 0.0
        cack *= sm(t, 1.95, 2.05) * (1 - sm(t, 2.4, 2.5))
        hp += 5.0 * math.sin(TAU * 8.0 * t) * cack
        roll_head = 7.0 * strut
        P['head_rot'] = np.array([0.0, hp, roll_head])
        P['chest_rot'] = P['chest_rot'] + np.array([0.0, 0.0, 3.0 * math.sin(TAU * 7.0 * t) * cack])
        P['lf_yaw'] = lerp(-10.0, -32.0, e)
        P['rf_yaw'] = lerp(10.0, 32.0, e)
        kn = e * lerp(26.0, 18.0, th) + (1 - e) * 8.0
        P['lf_knee'] = kn
        P['rf_knee'] = kn
        return P

    def P(self, t):
        e = sm(t, 0.0, 0.50) * (1 - sm(t, 3.05, 3.50))
        th, big = self.th(t)
        strut = sm(t, 2.55, 2.80) * (1 - sm(t, 3.05, 3.40))
        P = self.body_P(t, th, big, e, strut)
        info = self.body_info(P)
        k = self.k
        # ---- weights: READY | cocked | crossed | strut
        w_rd, w_co, w_cr, w_st = 1 - e, e * (1 - strut) * (1 - th), e * (1 - strut) * th, e * strut
        # left arm (free): chest-frame cock, pelvis-frame cross and hip
        l_rd = self.chest_to_auth(info, self.left_ready['w'])
        l_co = self.chest_to_auth(info, np.array([-0.22, 0.16, 0.08]) * k)
        l_cr = self.pelvis_to_auth(info, np.array(self.L_CR_F if self.H.tag == 'female' else self.L_CR) * k)
        l_st = self.pelvis_to_auth(info, np.array(self.L_ST) * k)
        P['l_frame'] = 'w'
        P['l_wrist'] = w_rd * l_rd + w_co * l_co + w_cr * l_cr + w_st * l_st
        fd_rd = self.chest_dir_to_auth(info, self.left_ready['fd'])
        pm_rd = self.chest_dir_to_auth(info, self.left_ready['pm'])
        fd_co, pm_co = self.chest_dir_to_auth(info, np.array([0.0, 0.55, 0.83])), self.chest_dir_to_auth(info, np.array([0.9, -0.2, 0.2]))
        Rp = self.pelvis_R(info)
        fd_cr = w2a(Rp @ a2w(np.array([0.55, 0.25, -0.80]))); pm_cr = w2a(Rp @ a2w(np.array([-0.15, -0.95, 0.2])))
        fd_st = w2a(Rp @ a2w(unit(np.array(self.FD_ST)))); pm_st = w2a(Rp @ a2w(np.array([0.95, -0.1, 0.1])))
        P['l_fdir'] = unit(w_rd * fd_rd + w_co * fd_co + w_cr * fd_cr + w_st * fd_st)
        P['l_palm'] = unit(w_rd * pm_rd + w_co * pm_co + w_cr * pm_cr + w_st * pm_st)
        pl_rd = self.chest_dir_to_auth(info, self.left_ready['pl'])
        pl_co = self.chest_dir_to_auth(info, np.array([-0.4, -0.5, -0.75]))
        pl_cr = self.chest_dir_to_auth(info, np.array([-0.95, -0.25, -0.15]))
        pl_st = self.chest_dir_to_auth(info, np.array([-0.8, -0.5, -0.3]))
        P['l_pole'] = unit(w_rd * pl_rd + w_co * pl_co + w_cr * pl_cr + w_st * pl_st)
        P['l_fing'] = lerp(self.R['l_fing'], self.fist_L, e * (1 - strut * 0.6))
        # right arm (racket first)
        g0, s0, f0 = self.grip0
        r_rd, sh_rd, fa_rd = self.chest_to_auth(info, g0), self.chest_dir_to_auth(info, s0), self.chest_dir_to_auth(info, f0)
        r_co = self.chest_to_auth(info, np.array([0.22, 0.17, 0.10]) * k)
        sh_co = self.chest_dir_to_auth(info, np.array([0.12, 0.10, 0.99])); fa_co = self.chest_dir_to_auth(info, np.array([-1.0, 0.1, 0.0]))
        r_cr = self.pelvis_to_auth(info, np.array(self.R_CR_F if self.H.tag == 'female' else self.R_CR) * k)
        shc = unit(np.array(self.CROSS_SHAFT, float))              # pelvis frame: across the body to the left, forward and up: the racket extends the line of the right arm into a bold X
        sh_cr = w2a(Rp @ a2w(shc))
        fa_cr = w2a(Rp @ a2w(self.faces['cross'])) if self.faces else w2a(Rp @ a2w(np.array([0.2, 0.9, 0.0])))
        r_st = self.pelvis_to_auth(info, np.array(self.R_ST) * k)
        sh_st = w2a(Rp @ a2w(unit(np.array(self.SH_ST))))
        fa_st = w2a(Rp @ a2w(self.faces['strut'])) if self.faces else w2a(Rp @ a2w(np.array([-1.0, 0.1, 0.0])))
        if self.faces:
            fa_co = self.chest_dir_to_auth(info, self.faces['cock'])
        P['r_frame'] = 'w'
        arc = 4.0 * w_co * w_cr                                        # the racket swings AROUND the head on its way between the cross and the cock (out to the right and forward), not through it
        r_arc = self.chest_to_auth(info, np.array([0.12, 0.12, 0.05]) * k) - self.chest_to_auth(info, np.zeros(3))
        P['r_rk_pos'] = w_rd * r_rd + w_co * r_co + w_cr * r_cr + w_st * r_st + arc * r_arc
        sh = unit(w_rd * sh_rd + w_co * sh_co + w_cr * sh_cr + w_st * sh_st)
        fa = w_rd * fa_rd + w_co * fa_co + w_cr * fa_cr + w_st * fa_st
        fa = fa - np.dot(fa, sh) * sh
        P['r_rk_shaft'] = sh
        P['r_rk_face'] = unit(fa) if np.linalg.norm(fa) > 1e-6 else fa_co
        pr_rd = self.chest_dir_to_auth(info, self.R['r_pole'])
        P['r_pole'] = unit(w_rd * pr_rd + w_co * self.chest_dir_to_auth(info, np.array([0.7, -0.15, -0.35])) + w_cr * self.chest_dir_to_auth(info, np.array([0.95, -0.25, -0.15])) + w_st * self.chest_dir_to_auth(info, np.array([0.8, -0.4, -0.3])))
        P['r_wlim'] = (math.radians(85.0), math.radians(178.0))
        P['r_fing'] = lerp(self.grip_fing, self.grip_tight, e * th)
        return P


REGISTRY['Emote_Thrust'] = Thrust2


# ------------------------------------------------------------------------------------------------------------------------------ Emote_Scuba
class Scuba2(Clip2):
    """The Scuba dance (2025 TikTok): one hand holds the nose (the left, thumb and index pad on the nose tip), the other (right) arm is held out in front and its hand sweeps side to side
    like a fish; the knees open and close on the beat while the body leans in and the head peers down at the hand.  163 BPM: one sweep + one knee open / close = 2 beats = 22 frames
    (0.733 s), four of them.  The racket is DROPPED at the start (it falls beside the right foot and lies on the court) and picked up again at the end.
    0.00-0.20 READY, the right hand loosens | 0.20 the racket leaves the hand and falls (lands 0.60) | 0.20-0.55 into the dance | 0.533-3.467 four sweeps | 3.47-4.0 hands drop, the
    right hand goes down for the racket | 4.0-4.1 grasp (attached at 4.1) | 4.1-4.6 stand up with it, READY."""

    DUR = 4.7

    def grip_exempt(self, t):
        return t < 0.45 or t > 4.30

    def no_clear(self, t):
        return t <= self.F_REL / 30.0 + 1e-9                        # the racket is still in the hand until the release instant

    def racket_attached(self, t):
        return not (self.t_rel - 1e-9 <= t < self.t_att - 1e-9)

    F_REL, F_LAND, F_LOOP0, F_PERIOD, F_ATT = 6, 18, 16, 22, 123
    NLOOPS = 4

    def __init__(self, H):
        super().__init__('Emote_Scuba', self.DUR, H)
        R = self.R
        k, hz = self.k, self.hz
        self.t_rel, self.t_land = self.F_REL / 30.0, self.F_LAND / 30.0
        self.t_loop0, self.T = self.F_LOOP0 / 30.0, self.F_PERIOD / 30.0
        self.t_loop1 = self.t_loop0 + self.NLOOPS * self.T
        self.t_att = self.F_ATT / 30.0
        self.left_ready = dict(w=np.asarray(R['l_wrist'], float), fd=np.asarray(R['l_fdir'], float), pm=np.asarray(R['l_palm'], float), pl=np.asarray(R['l_pole'], float))
        self.right_ready = dict(w=np.asarray(R['r_wrist'], float), fd=np.asarray(R['r_fdir'], float), pm=np.asarray(R['r_palm'], float), pl=np.asarray(R['r_pole'], float))
        self.grip = H.finger_shape('R', 'grip', 1.0)
        self.open_R = H.finger_shape('R', 'open', 1.0)
        self.relax_R = H.finger_shape('R', 'relaxed', 1.0)
        self.flat_R = 0.35 * self.relax_R + 0.65 * self.open_R
        self.pinch_L = H.finger_shape('L', 'pinch', 1.0)
        self.relax_L = H.finger_shape('L', 'relaxed', 1.0)
        # ---- the pinch hand (as in the old clip: fingers up and inwards, palm to the nose; the wrist is calibrated by a contact solve)
        self.l_fdir = np.array([0.30, 0.15, 0.95])
        self.l_palm = np.array([0.80, -0.55, -0.15])
        self.pinch_off = np.array([0.0, -0.004, -0.002])
        P_hold = dict(R)
        P_hold.update(l_fdir=self.l_fdir, l_palm=self.l_palm, l_fing=self.pinch_L, l_wrist=np.array([-0.10, 0.18, 0.15]) * k)
        self._calibrate(P_hold)
        # ---- where the racket lands (lying flat, face up, the head pointing forward) and the grasp pose for the pick-up
        sh, fa = np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0])
        self.rk_land = np.array([0.40 * k, 0.50 * k, 0.0])
        zf = -racket_min_z(np.zeros(3), A2W_ @ PS.frame_from_axes(sh, fa))
        self.rk_land[2] = zf
        self.rk_shaft, self.rk_face = sh, fa
        self.hover = 0.075
        self.grasp = hand_from_racket(H, self.rk_land + np.array([0.0, 0.0, self.hover]), sh, fa)
        self.pk_body = self.fit_pickup()
        Pb = self.body_P(4.05)[0]                                                             # the squat body channels (pk = 1)
        self.S_grasp = self.shoulder(self.body_info(Pb), 'R')                                 # right shoulder of the BODY-ONLY solve, the same quantity P() uses
        # release pose of the racket (the socket pose at the release instant) is read from the solved READY-ish hand at t_rel (see racket_world)
        self._rel_cache = None

    def pickup_P(self, x):
        """body channels of the squat for the parameter vector x = [pel r, pel f, pel u, pel pitch, chest pitch, chest roll, chest yaw]; the right hand holds the grasp pose, the left hand is on the left knee"""
        P = dict(self.R)
        P['pel'] = np.array([x[0], x[1], x[2]])
        P['pel_rot'] = np.array([0.0, x[3], 0.0])
        P['chest_rot'] = np.array([x[6], x[4], x[5]])
        P['head_rot'] = np.array([0.0, -12.0, 0.0])
        P['lf_yaw'], P['rf_yaw'] = -28.0, 28.0
        P['lf_knee'] = P['rf_knee'] = 34.0
        w_g, fd_g, pm_g = self.grasp
        P['r_frame'] = 'w'
        P['r_wrist'], P['r_fdir'], P['r_palm'] = w_g, fd_g, pm_g
        P['r_pole'] = np.array([0.6, -0.5, 0.2])
        P['r_fing'] = self.open_R
        P['r_wlim'] = (math.radians(95.0), math.radians(170.0))
        return P

    def fit_pickup(self):
        """pattern search for the squat in which the right arm reaches the grasp pose (nearly) straight, the pelvis is not lower than needed and the spine is not folded more than needed"""
        H = self.H
        x = np.array([0.07, -0.09, -0.27, 38.0, 28.0, 12.0, 0.0])
        x0 = x.copy()
        step = np.array([0.03, 0.03, 0.03, 6.0, 6.0, 4.0, 4.0])
        scale = np.array([0.1, 0.1, 0.2, 30.0, 30.0, 15.0, 15.0])

        def cost(v):
            P = self.pickup_P(v)
            b, h, info = H.solve(P)
            reach = info['R_arm_short']
            c = 200.0 * reach + 0.6 * info['R_wrist_clamp_deg']
            c += 3.0 * float(np.sum(((v - x0) / scale) ** 2))
            c += 30.0 * max(0.0, 0.45 - float(w2a(info['Pos'][H.rig.idx['Hips']] - H.O)[2]))         # the pelvis stays above 0.45 m
            c += 40.0 * max(0.0, v[3] + v[4] - 100.0) / 100.0                                      # no more than ~100 degrees of spine fold
            return c
        best = cost(x)
        for it in range(14):
            improved = False
            for i in range(len(x)):
                for sg in (+1, -1):
                    y = x.copy()
                    y[i] += sg * step[i]
                    cy = cost(y)
                    if cy < best - 1e-9:
                        x, best, improved = y, cy, True
            if not improved:
                step *= 0.5
        self.pk_cost = best
        return x

    def _calibrate(self, P_hold):
        H = self.H
        P = dict(P_hold)
        P['l_pole'] = np.array([-0.6, -0.5, -0.2])                # elbow out to the left and back, level: clear of the chest (scan_pinch.py)
        b, h, info = H.solve(self.R)
        nose = H.nose(b, h)
        tgt = nose + self.pinch_off
        b, h, info = solve_contact(H, P, 'L', tgt, lambda i: pad_point(H, i, 'L'), iters=6)
        self.l_wrist_hold = np.asarray(P['l_wrist'], float)
        self.l_pole_hold = P['l_pole']
        self.calib_err = float(np.linalg.norm(tgt - pad_point(H, info, 'L')))

    # ---- timing helpers
    def dance_env(self, t):
        return sm(t, self.t_loop0 - 0.10, self.t_loop0 + 0.10) * (1 - sm(t, self.t_loop1 - 0.10, self.t_loop1 + 0.12))

    def phase(self, t):
        return TAU * (t - self.t_loop0) / self.T

    def body_P(self, t):
        P = dict(self.R)
        k = self.k
        e_in = sm(t, 0.12, 0.55)
        # dance posture (weights): in / out
        d = e_in * (1 - sm(t, 3.47, 3.80))
        env = self.dance_env(t)
        ph = self.phase(t)
        s, c = math.sin(ph) * env, math.cos(ph) * env
        kopen = (0.5 + 0.5 * math.sin(ph)) * env
        # pick-up posture weight
        pk = sm(t, 3.55, 4.00) * (1 - sm(t, 4.12, 4.58))
        x = self.pk_body
        P['pel'] = (1 - pk) * (np.array([0.012 * s, 0.0, 0.0]) + d * np.array([0.0, 0.0, -0.062 - 0.026 * kopen])) + pk * np.array([x[0], x[1], x[2]])
        P['pel_rot'] = (1 - pk) * (np.array([0.0, 9.0, 0.0]) + d * np.array([0.0, 10.0, 3.0 * c])) + pk * np.array([0.0, x[3], 0.0])
        P['chest_rot'] = (1 - pk) * (np.array([0.0, 8.0, 0.0]) + d * np.array([6.0 * s, 6.0, -3.0 * c])) + pk * np.array([x[6], x[4], x[5]])
        P['head_rot'] = (1 - pk) * (np.array([0.0, -14.0, 0.0]) + d * np.array([-4.0 * s, 6.0 + 3.0 * c, 5.0 * s])) + pk * np.array([0.0, -12.0, 0.0])
        P['lf_yaw'] = -10.0 - max(d, pk) * 18.0
        P['rf_yaw'] = 10.0 + max(d, pk) * 18.0
        kn = (1 - pk) * (8.0 + d * (8.0 + 30.0 * kopen)) + pk * 34.0
        P['lf_knee'] = kn
        P['rf_knee'] = kn
        return P, d, env, s, c, pk

    def P(self, t):
        P, d, env, s, c, pk = self.body_P(t)
        k = self.k
        info = self.body_info(P)
        ca, cd = self.chest_to_auth, self.chest_dir_to_auth
        # ---- left hand: READY (on the racket throat) -> nose (pinch) -> knee (pick-up squat, palm on the knee) -> READY.  World (authoring) frame; the three poses are mixed by weights, so the
        # hand goes from the nose straight to the knee (not via the belly)
        wp = sm(t, 0.22, 0.52) * (1 - sm(t, 3.47, 3.75))
        pkL = sm(t, 3.47, 3.95) * (1 - sm(t, 4.12, 4.58))
        w_r = max(0.0, 1.0 - wp - pkL)
        ix = self.H.rig.idx
        knee = self.A(info['Pos'][ix['LeftLowerLeg']])
        l_rd_w, l_pi_w = ca(info, self.left_ready['w']), ca(info, self.l_wrist_hold)
        l_kn_w = knee + np.array([-0.02, 0.03, 0.13]) * k                 # on top of the knee, a little to the outside
        P['l_frame'] = 'w'
        P['l_wrist'] = w_r * l_rd_w + wp * l_pi_w + pkL * l_kn_w
        P['l_fdir'] = unit(w_r * cd(info, self.left_ready['fd']) + wp * cd(info, self.l_fdir) + pkL * unit(np.array([0.10, 0.62, -0.78])))
        P['l_palm'] = unit(w_r * cd(info, self.left_ready['pm']) + wp * cd(info, self.l_palm) + pkL * unit(np.array([0.55, 0.0, -0.84])))             # palm down on the knee
        P['l_pole'] = unit(w_r * cd(info, self.left_ready['pl']) + wp * cd(info, self.l_pole_hold) + pkL * unit(np.array([-0.8, -0.2, 0.0])))          # elbow out to the left
        P['l_fing'] = w_r * self.R['l_fing'] + wp * self.pinch_L + pkL * self.relax_L
        # ---- right (swim) hand
        ps = sm(t, 0.20, 0.55) * (1 - sm(t, 3.40, 3.80))                       # swim weight
        ph = self.phase(t)
        env = self.dance_env(t)
        S_R = self.shoulder(info, 'R')
        dr = (-0.10 + 0.14 * math.sin(ph) * env) * k
        df = (0.40 - 0.02 * math.cos(ph) * env) * k
        du = (-0.13 + 0.03 * math.cos(ph + 0.6) * env) * k
        w_swim = S_R + np.array([dr, df, du])
        psi = math.radians(-35.0) * math.cos(ph) * env
        fd_sw = unit(np.array([math.sin(psi), math.cos(psi), -0.10]))
        pm_sw = np.array([0.05, 0.10, -1.0])
        pl_sw = np.array([0.45, -0.55, -0.55])
        w_rd = ca(info, self.right_ready['w'])
        fd_rd, pm_rd, pl_rd = cd(info, self.right_ready['fd']), cd(info, self.right_ready['pm']), cd(info, self.right_ready['pl'])
        # pick-up: toward the grasp pose (authoring floor frame) and back to READY
        w_g, fd_g, pm_g = self.grasp
        gk = sm(t, 3.47, 4.00) * (1 - sm(t, 4.12, 4.58))                      # reach for the racket / carry it up
        wr = (1 - ps) * w_rd + ps * w_swim
        fd = unit((1 - ps) * fd_rd + ps * fd_sw)
        pm = unit((1 - ps) * pm_rd + ps * pm_sw)
        pl = unit((1 - ps) * pl_rd + ps * pl_sw)
        # hand-over from swim/ready to the grasp pose: sequential blend (swim -> grasp during 3.47-4.0, grasp -> READY during 4.1-4.58).
        # The blend is done RELATIVE TO THE RIGHT SHOULDER (which moves with the squat): a convex mix of two reachable shoulder-relative vectors stays reachable.
        u1 = sm(t, 3.47, 4.00)
        u2 = sm(t, 4.12, 4.58)
        if t >= 3.47:
            S_now = S_R
            rel_sw = w_swim - S_now
            rel_g = w_g - self.S_grasp
            rel_rd = w_rd - S_now
            rel = (1 - u1) * rel_sw + u1 * rel_g if t < 4.12 else (1 - u2) * rel_g + u2 * rel_rd
            base_w = S_now + rel
            if t >= 4.12:                                              # carry-up arc: out to the right and forward while the hand rises past the knee
                base_w = base_w + 4.0 * u2 * (1 - u2) * np.array([0.08, 0.10, 0.03]) * k
            base_fd = vslerp(fd_sw, fd_g, u1) if t < 4.12 else vslerp(fd_g, fd_rd, u2)
            base_pm = vslerp(pm_sw, pm_g, u1) if t < 4.12 else vslerp(pm_g, pm_rd, u2)
            wr, fd, pm = base_w, base_fd, base_pm
            pl = vslerp(pl_sw, pl_sw, 1.0)
        P['r_frame'] = 'w'
        P['r_wrist'] = wr
        P['r_fdir'] = fd
        P['r_palm'] = pm
        P['r_pole'] = pl
        # fingers: grip -> open as the racket is let go, flat while swimming, open when reaching, closed on the handle, grip at READY
        f_open = sm(t, 0.12, 0.24)
        f = lerp(self.grip, self.open_R, f_open)
        f = lerp(f, self.flat_R, sm(t, 0.30, 0.55))
        f = lerp(f, self.open_R, sm(t, 3.55, 3.95))
        f = lerp(f, self.grip, sm(t, 3.98, 4.12))
        P['r_fing'] = f
        P['r_wlim'] = (math.radians(95.0), math.radians(170.0))
        # ---- contact solve INSIDE the channels (so the clearance sees what is played): the thumb / index pad sits on the nose tip, weighted by the pinch contact
        w_c = sm(t, 0.30, 0.50) * (1 - sm(t, 3.47, 3.70))
        if w_c > 1e-3:
            H = self.H
            basis, hips, info2 = H.solve(P)
            nose = H.nose(basis, hips) + self.pinch_off
            Pc = dict(P)
            for it in range(3):
                err = nose - pad_point(H, info2, 'L')
                if np.linalg.norm(err) < 0.0015:
                    break
                Pc['l_wrist'] = np.asarray(Pc['l_wrist'], float) + w_c * w2a(err)
                basis, hips, info2 = H.solve(Pc)
            P = Pc
        return P

    # ---- the racket: in the hand until t_rel, falls, lies, lifted by the hand at the pick-up, attached at t_att
    def release_pose(self):
        if self._rel_cache is None:
            P = self.P(self.t_rel)                       # no clearance correction before the release (no_clear), so the nominal hand pose is the hand pose
            b, h, info = self.H.solve(P)
            self._rel_cache = (info['rk_origin'].copy(), info['rk_R'].copy())
        return self._rel_cache

    def racket_world(self, t, info):
        if t < self.t_rel - 1e-9 or t >= self.t_att - 1e-9:
            return None
        H = self.H
        O = H.O
        p0, R0 = self.release_pose()
        pL = O + a2w(self.rk_land)
        RL = A2W_ @ PS.frame_from_axes(self.rk_shaft, self.rk_face)
        if t < self.t_land:
            tau = self.t_land - self.t_rel
            u = (t - self.t_rel) / tau
            g = 9.81
            vz = 0.6
            z0, zL = p0[2], pL[2]
            # time to fall in physics: z(tau) = z0 + vz tau - g tau^2 / 2 = zL  -> use the given tau and solve the vertical velocity instead
            vz = (zL - z0 + 0.5 * g * tau * tau) / tau
            dt = t - self.t_rel
            pos = p0 + (pL - p0) * np.array([u, u, 0.0])
            pos[2] = z0 + vz * dt - 0.5 * g * dt * dt
            Rr = rot_slerp(R0, RL, smooth(u))
            return dict(pos=pos, R=Rr)
        dt = t - self.t_land
        # a small bounce (apex +4 cm at +0.07 s), then rest
        hb = 0.0
        if dt < 0.14:
            hb = 0.04 * 4.0 * (dt / 0.14) * (1 - dt / 0.14)
        if t < self.t_att - 0.20:
            return dict(pos=pL + np.array([0.0, 0.0, hb]), R=RL)
        # pick-up: the racket is lifted to the grasp height by the closing hand over the last 6 frames, attached at t_att
        v = (t - (self.t_att - 0.20)) / 0.20
        lift = self.hover * smooth(v)
        return dict(pos=pL + np.array([0.0, 0.0, lift]), R=RL)

    def ignore_head(self, t):
        w_c = sm(t, 0.30, 0.50) * (1 - sm(t, 3.47, 3.70))
        return ('L',) if w_c > 0.02 else ()                     # the pinch hand is meant to touch the nose

    def pinned(self, t):
        w_c = sm(t, 0.30, 0.50) * (1 - sm(t, 3.47, 3.70))
        return ('L',) if w_c > 0.2 else ()                      # the pad stays on the nose, the elbow swings

    def arm_weight(self, t):
        g = sm(t, 3.85, 3.98) * (1 - sm(t, 4.12, 4.25))          # the right hand closes on the racket: exactly the grasp pose, no clearance move
        return 1.0, 1.0 - g


REGISTRY['Emote_Scuba'] = Scuba2
