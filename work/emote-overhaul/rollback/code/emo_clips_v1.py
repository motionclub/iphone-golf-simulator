"""EMOTES: the six clip definitions (authored once per hero from the same keys; heroes differ only through their own proportions).

Every clip is a ClipDef: `length` (s), `solve(t)` -> dict(basis, hips, info, racket) where racket is None (the racket stays on Hand_Racket) or a dict(pos, R) = the racket's world frame
while it is off the hand.  Frames are sampled at 30 fps from t = 0 to `length` (both ends are the READY pose).

Authoring frame: r = hero's right, f = forward (towards the other player), u = up; chest-frame vectors are relative to the chest centre in the chest's own axes.  Metres, degrees."""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import emo_hero as EH
from emo_hero import Timeline, smooth, quats_of, rot_diff_deg, hand_frame
import kin
import pose as PS
from kin import a2w, w2a, unit

TAU = 2 * math.pi
REGISTRY = {}


def fingertip(H, info, name):
    i = H.rig.idx[name]
    return info['Pos'][i] + info['Q'][i] @ np.array([0.0, H.rig.length[i], 0.0])


def pad_point(H, info, side):
    """the pinching point: the middle of the index / middle finger tips"""
    S = 'Left' if side == 'L' else 'Right'
    return 0.5 * (fingertip(H, info, S + 'IndexDistal') + fingertip(H, info, S + 'MiddleDistal'))


def solve_contact(H, P, side, target, point_fn, iters=3, weight=1.0, tol=0.0015):
    """move the wrist target of `side` until point_fn(info) reaches `target` (world); returns basis, hips, info and the corrected P entries"""
    pre = 'l' if side == 'L' else 'r'
    basis = hips = info = None
    for it in range(iters + 1):
        basis, hips, info = H.solve(P)
        err = target - point_fn(info)
        if np.linalg.norm(err) < tol or it == iters:
            break
        frame = P.get(pre + '_frame', 'c')
        d = w2a(info['R_chest'].T @ err) if frame == 'c' else w2a(err)
        P[pre + '_wrist'] = np.asarray(P[pre + '_wrist'], float) + weight * d
    return basis, hips, info


def fit_face(H, P, pos, shaft, face0, step=10):
    """the racket face direction (a roll about the commanded shaft) that the right wrist can hold with the least clamp; face0 only breaks ties"""
    sh = unit(np.asarray(shaft, float))
    f0 = np.asarray(face0, float)
    f0 = unit(f0 - np.dot(f0, sh) * sh)
    g0 = np.cross(sh, f0)
    best = None
    for ang in range(0, 360, step):
        a = math.radians(ang)
        f = math.cos(a) * f0 + math.sin(a) * g0
        Pt = dict(P)
        Pt['r_rk_pos'], Pt['r_rk_shaft'], Pt['r_rk_face'] = np.asarray(pos, float), sh, f
        b, h, info = H.solve(Pt)
        d = min(ang, 360 - ang)
        score = info['R_wrist_clamp_deg'] + 400.0 * info['R_arm_short'] + 0.03 * d
        if best is None or score < best[0]:
            best = (score, f, info['R_wrist_clamp_deg'])
    return best[1], best[2]


def fit_palm(H, P, side, step=10):
    """the roll of the hand about its finger direction (palm vector turned) with the least wrist clamp, starting from the commanded one"""
    pre = 'l' if side == 'L' else 'r'
    fd = unit(np.asarray(P[pre + '_fdir'], float))
    p0 = np.asarray(P[pre + '_palm'], float)
    p0 = unit(p0 - np.dot(p0, fd) * fd)
    g0 = np.cross(fd, p0)
    best = None
    key = 'L_wrist_clamp_deg' if side == 'L' else 'R_wrist_clamp_deg'
    for ang in list(range(0, 181, step)) + [-a for a in range(step, 181, step)]:
        a = math.radians(ang)
        pm = math.cos(a) * p0 + math.sin(a) * g0
        Pt = dict(P)
        Pt[pre + '_palm'] = pm
        b, h, info = H.solve(Pt)
        score = info[key] + 0.15 * abs(ang)
        if best is None or score < best[0]:
            best = (score, pm, info[key])
    return best[1], best[2]


class ClipDef:
    def __init__(self, name, length, H):
        self.name, self.length, self.H = name, length, H
        self.R = H.ready_channels()
        self.T = Timeline()
        self.events = {}

    def refit(self, tprobe, times, right=False, left=False):
        """turn the racket about its shaft (right) / the hand about its fingers (left) to the least-clamp roll AT ONE PROBE TIME and write that roll into the keys at `times`"""
        H = self.H
        P = self.P(tprobe)
        if right and 'rk_face' in self.T.ch:
            f, c = fit_face(H, P, P['r_rk_pos'], P['r_rk_shaft'], P['r_rk_face'])
            for t in times:
                self.T.add(t, rk_face=f)
        if left and 'l_palm' in self.T.ch:
            pm, c = fit_palm(H, P, 'L')
            for t in times:
                self.T.add(t, l_palm=pm)
        self.T._c = {}

    def autofit(self, dt=0.05, thr=6.0, passes=2, left=True, right=True):
        """wherever a wrist is held beyond `thr` degrees of clamp, add a key that turns the hand about its finger axis (palm) / the racket about its shaft (face) to the
        least-clamp roll.  Only for clips whose P() takes l_palm / rk_face from the timeline."""
        H = self.H
        for ps in range(passes):
            n = 0
            for t in np.arange(0.0, self.length + 1e-9, dt):
                P = self.P(t)
                b, h, info = H.solve(P)
                if left and info['L_wrist_clamp_deg'] > thr and 'l_palm' in self.T.ch:
                    pm, c = fit_palm(H, P, 'L')
                    self.T.add(float(t), l_palm=pm)
                    n += 1
                if right and info['R_wrist_clamp_deg'] > thr and 'rk_face' in self.T.ch:
                    f, c = fit_face(H, P, P['r_rk_pos'], P['r_rk_shaft'], P['r_rk_face'])
                    self.T.add(float(t), rk_face=f)
                    n += 1
            self.T._c = {}
            if n == 0:
                break
        return n

    def P(self, t):
        P = dict(self.R)
        for k, v in self.T.pose(t).items():
            P[k] = v
            if k in ('rk_pos', 'rk_shaft', 'rk_face'):          # the racket-first right arm (solver channels r_rk_*)
                P['r_' + k] = v
        return P

    def solve(self, t):
        P = self.P(t)
        basis, hips, info = self.H.solve(P)
        return dict(basis=basis, hips=hips, info=info, racket=None, P=P)


# ------------------------------------------------------------------------------------------------------------------------------ Emote_Scuba
class Scuba(ClipDef):
    """Pinch the nose with one hand; the other hand (the racket hand) waves in front of the face; knees open and close twice; hold; READY.
    0.00-0.30 hands rise, 0.30-1.50 two knee cycles (period 0.6 s) with the wave, 1.50-1.68 hold, 1.68-2.00 back to READY."""

    def __init__(self, H):
        super().__init__('Emote_Scuba', 2.0, H)
        A = H.A
        k = A / 0.505
        R = self.R
        T = self.T
        t0, tA, tB, tC, tD = 0.0, 0.30, 1.50, 1.68, 2.0
        self.t = (t0, tA, tB, tC, tD)
        self.period = 0.60
        # ---- pinch hand (LEFT): the fingers' pad point goes to the nose; fingers up and inwards, palm to the nose
        self.l_fdir = np.array([0.30, 0.15, 0.95])
        self.l_palm = np.array([0.80, -0.55, -0.15])
        self.l_pinch_fing = H.finger_shape('L', 'pinch', 1.0)
        self.pinch_off = np.array([0.0, -0.012, -0.004])          # pad point relative to the nose tip (world offset): a hair in front of / below the tip
        # ---- wave hand (RIGHT, racket): grip centre beside the face, shaft up and out
        self.r_pos = np.array([0.15, 0.30, 0.29]) * np.array([k, k, k])
        self.r_shaft = np.array([0.35, 0.05, 0.93])
        self.r_face = np.array([-0.2, 0.95, 0.1])
        self.wave_hz = 2.4
        self.wave_amp_deg = 24.0
        self.knee_open, self.knee_closed = 40.0, 8.0
        # keys: READY at the ends; the pinch hand's wrist is calibrated at tA by a contact solve (below)
        P_hold = dict(R)
        P_hold.update(l_fdir=self.l_fdir, l_palm=self.l_palm, l_fing=self.l_pinch_fing, l_wrist=np.array([-0.10, 0.18, 0.15]) * k)
        self.nose_target = None
        T.add(t0, l_wrist=R['l_wrist'], l_fdir=R['l_fdir'], l_palm=R['l_palm'], l_fing=R['l_fing'], l_pole=R['l_pole'],
              r_wrist=R['r_wrist'], r_fdir=R['r_fdir'], r_palm=R['r_palm'], r_fing=R['r_fing'], r_pole=R['r_pole'], rk_w=0.0)
        T.add(tD, l_wrist=R['l_wrist'], l_fdir=R['l_fdir'], l_palm=R['l_palm'], l_fing=R['l_fing'], l_pole=R['l_pole'],
              r_wrist=R['r_wrist'], r_fdir=R['r_fdir'], r_palm=R['r_palm'], r_fing=R['r_fing'], r_pole=R['r_pole'], rk_w=0.0)
        self._calibrate(P_hold)
        for tt in (tA, tB, tC):
            T.add(tt, l_wrist=self.l_wrist_hold, l_fdir=self.l_fdir, l_palm=self.l_palm, l_fing=self.l_pinch_fing, l_pole=self.l_pole_hold, rk_w=1.0)
        T.add(tA, r_fing=H.finger_shape('R', 'grip', 1.0), r_pole=np.array([0.45, -0.55, -0.7]))
        T.add(tC, r_fing=H.finger_shape('R', 'grip', 1.0), r_pole=np.array([0.45, -0.55, -0.7]))
        T.add(tA, rk_pos=self.r_pos, rk_shaft=self.r_shaft, rk_face=self.r_face)
        T.add(tC, rk_pos=self.r_pos, rk_shaft=self.r_shaft, rk_face=self.r_face)
        # the right grip centre at READY in the chest frame, so the racket arm starts exactly where READY has it
        S, rig = H.S, H.rig
        b, h, info = H.solve(R)
        Rc = info['R_chest']
        C = info['chest_center']
        g0 = w2a(Rc.T @ (info['rk_origin'] - C))
        sh0 = w2a(Rc.T @ info['rk_R'][:, 1])
        fa0 = w2a(Rc.T @ info['rk_R'][:, 2])
        T.add(t0, rk_pos=g0, rk_shaft=sh0, rk_face=fa0)
        T.add(tD, rk_pos=g0, rk_shaft=sh0, rk_face=fa0)
        self.rk0 = (g0, sh0, fa0)
        self.refit(0.9, (tA, tB, tC), right=True)

    def _calibrate(self, P_hold):
        H = self.H
        P = dict(P_hold)
        P['l_pole'] = np.array([-0.35, -0.65, -0.65])           # elbow down and out to the left
        b, h, info = H.solve(self.R)
        nose = H.nose(b, h)
        tgt = nose + self.pinch_off
        b, h, info = solve_contact(H, P, 'L', tgt, lambda i: pad_point(H, i, 'L'), iters=6)
        self.l_wrist_hold = np.asarray(P['l_wrist'], float)
        self.l_pole_hold = P['l_pole']
        self.calib_err = float(np.linalg.norm(tgt - pad_point(H, info, 'L')))

    def knee_phase(self, t):
        """0 closed .. 1 open, 2 cycles in [tA, tB], eased in / out so the stance settles"""
        t0, tA, tB, tC, tD = self.t
        if t <= tA or t >= tB:
            return 0.0
        u = (t - tA) / self.period
        k = 0.5 - 0.5 * math.cos(TAU * u)
        return k

    def P(self, t):
        P = super().P(t)
        t0, tA, tB, tC, tD = self.t
        rise = smooth((t - t0) / (tA - t0)) * (1 - smooth((t - tC) / (tD - tC)))      # 0 at READY, 1 while the emote holds
        kn = self.knee_phase(t)
        P['pel'] = np.array([0.0, -0.02 * kn, -(0.03 * rise + 0.06 * kn)])
        P['lf_knee'] = 8.0 + (self.knee_closed - 8.0) * rise + (self.knee_open - self.knee_closed) * kn
        P['rf_knee'] = 8.0 + (self.knee_closed - 8.0) * rise + (self.knee_open - self.knee_closed) * kn
        # wave: the racket tilts side to side about the grip, the grip moves a few cm with it
        wv = 0.0
        if tA - 1e-9 <= t <= tC + 1e-9:
            env = smooth((t - tA) / 0.12) * (1 - smooth((t - (tC - 0.12)) / 0.12))
            wv = env * math.sin(TAU * self.wave_hz * (t - tA))
        th = math.radians(self.wave_amp_deg) * wv
        sh = np.array([math.sin(th) * 1.0 + self.r_shaft[0], self.r_shaft[1], math.cos(th) * self.r_shaft[2]])
        pos = np.asarray(P['rk_pos'], float) + np.array([0.05 * wv, 0.0, 0.0]) * rise
        w = float(P.get('rk_w', 0.0))
        P['r_rk_pos'] = pos
        P['r_rk_shaft'] = np.asarray(P['rk_shaft'], float) + np.array([math.sin(th) * 0.9, 0.0, -(1 - math.cos(th)) * 0.9]) * rise
        P['r_rk_face'] = np.asarray(P['rk_face'], float)
        # sway of the head and chest
        P['head_rot'] = np.array([0.0, -14.0, 0.0]) + np.array([2.0 * wv, 0.0, 4.0 * wv]) * rise
        P['chest_rot'] = np.asarray(R_chest_rot(self.R)) + np.array([0.0, 0.0, 2.5 * wv]) * rise
        return P

    def solve(self, t):
        P = self.P(t)
        H = self.H
        t0, tA, tB, tC, tD = self.t
        w_c = smooth((t - tA) / 0.10) * (1 - smooth((t - tC) / 0.10))              # pinch contact weight
        basis, hips, info = H.solve(P)
        if w_c > 1e-3:
            nose = H.nose(basis, hips) + self.pinch_off
            Pc = dict(P)
            for it in range(3):
                err = nose - pad_point(H, info, 'L')
                if np.linalg.norm(err) < 0.0015:
                    break
                Pc['l_wrist'] = np.asarray(Pc['l_wrist'], float) + w_c * w2a(info['R_chest'].T @ err)
                basis, hips, info = H.solve(Pc)
            P = Pc
        return dict(basis=basis, hips=hips, info=info, racket=None, P=P)


# ------------------------------------------------------------------------------------------------------------------------------ racket helpers
_RK_PTS = None


def racket_pts():
    global _RK_PTS
    if _RK_PTS is None:
        _RK_PTS = np.load(os.path.join(EH.DATA, 'racket_pts.npz'))['pts']
    return _RK_PTS


RK_SCALE = 1.3          # TennisRules.HeroRacketScale (the pre-registered Blender checks measure at this size)
RK_AUTHOR = 1.0         # the size the game really draws on the match heroes: measured in the Unity film trace (lossyScale 1.0 in every state: the clips' constant scale curves reset the driver's 1.3), so the floor contacts are authored for it


def racket_min_z(pos_w, R_w, scale=RK_AUTHOR):
    return float((pos_w[2] + (scale * racket_pts() @ R_w.T)[:, 2]).min())


def rot_slerp(A, B, u):
    return PS.slerp_mat(A, B, u)


class FreePath:
    """a racket flight: positions through (t, pos) keys (monotone cubic), orientations by eased slerp between (t, R) keys; world frame (Blender)"""

    def __init__(self, pos_keys, rot_keys):
        self.pos = EH.Curve(pos_keys)
        self.rk = sorted(rot_keys, key=lambda k: k[0])

    def __call__(self, t):
        p = self.pos(t)
        ks = self.rk
        if t <= ks[0][0]:
            R = ks[0][1]
        elif t >= ks[-1][0]:
            R = ks[-1][1]
        else:
            i = max(j for j in range(len(ks) - 1) if ks[j][0] <= t)
            u = (t - ks[i][0]) / (ks[i + 1][0] - ks[i][0])
            R = rot_slerp(ks[i][1], ks[i + 1][1], smooth(u))
        return p, R


# ------------------------------------------------------------------------------------------------------------------------------ Emote_Spike
class Spike(ClipDef):
    """One downward hit.  The racket leaves the hand, bounces once on the court and comes back to Hand_Racket; hands on hips; READY.  Both arms are keyed in the WORLD
    authoring frame (the trunk folds far forward).  0.00-0.28 racket cocked high behind the head (arched back) | 0.28-0.42 the arm whips down, the trunk folds, the racket
    leaves the hand at 0.42 | 0.56 it hits the court | 0.80 apex of the bounce | 1.05 it is back in the right hand | 1.05-1.30 both hands go to the hips, upright |
    head shake | 2.00 READY."""

    def __init__(self, H):
        super().__init__('Emote_Spike', 2.0, H)
        R, T = self.R, self.T
        W0 = H.ready_world()
        k = self.k = H.A / 0.505
        hz = H.rig.J['head_top'][2] / 1.705
        self.tW, self.tS, self.tR, self.tSW, self.tF, self.tA, self.tC, self.tH, self.tE, self.tD = 0.28, 0.34, 0.40, 0.50, 0.47, 0.80, 31 / 30, 1.26, 1.70, 2.0
        tW, tS, tR, tSW, tC, tH, tE, tD = self.tW, self.tS, self.tR, self.tSW, self.tC, self.tH, self.tE, self.tD
        v = lambda r, f, u: np.array([r * k, f * k, u * hz])
        rk = [(0.0, W0['rk_pos'], W0['rk_shaft'], W0['rk_face']),
              (0.10, v(0.34, 0.38, 1.14), unit(W0['rk_shaft'] + np.array([0.3, 0.2, 0.4])), np.array([-0.9, 0.0, 0.1])),
              (0.19, v(0.32, 0.20, 1.55), np.array([0.2, -0.3, 0.9]), np.array([-0.9, 0.0, 0.1])),
              (tW, v(0.14, -0.04, 1.86), np.array([0.10, -0.80, 0.55]), np.array([-0.9, 0.0, 0.1])),
              (tS, v(0.22, 0.42, 1.28), np.array([0.10, 0.65, 0.75]), np.array([-0.9, 0.3, 0.1])),
              (tR, v(0.26, 0.62, 0.80), np.array([0.10, 0.70, -0.70]), np.array([-0.9, 0.2, -0.1])),
              (tSW, v(0.28, 0.68, 0.36), np.array([0.10, 0.60, -0.80]), np.array([-0.9, 0.2, -0.1])),
              (0.78, v(0.30, 0.50, 0.55), np.array([0.10, 0.70, -0.70]), np.array([-0.9, 0.2, -0.1])),
              (tC - 0.12, v(0.30, 0.42, 0.70), np.array([0.05, 0.55, 0.10]), np.array([-0.9, 0.1, 0.2])),
              (tC, v(0.30, 0.42, 0.70), np.array([0.05, 0.55, 0.10]), np.array([-0.9, 0.1, 0.2])),
              (tC + 0.10, v(0.30, 0.42, 0.70), np.array([0.05, 0.55, 0.10]), np.array([-0.9, 0.1, 0.2])),
              (tH, v(0.22, 0.06, 0.78), np.array([0.15, -0.55, -0.80]), np.array([-0.95, 0.1, 0.1])),
              (tE, v(0.22, 0.06, 0.78), np.array([0.15, -0.55, -0.80]), np.array([-0.95, 0.1, 0.1])),
              (tE + 0.15, 0.5 * (v(0.22, 0.06, 0.78) + W0['rk_pos']), np.array([0.08, 0.90, 0.0]), W0['rk_face']),
              (tD, W0['rk_pos'], W0['rk_shaft'], W0['rk_face'])]
        for (t, pos, sh, fa) in rk:
            T.add(t, rk_pos=pos, rk_shaft=sh, rk_face=fa)
        for t, pole in ((0.0, W0['r_pole']), (tW, np.array([0.5, -0.3, -0.2])), (tS, np.array([0.4, -0.2, -0.5])), (tR, np.array([0.4, -0.6, -0.6])), (tC, np.array([0.5, -0.5, -0.6])),
                        (tH, np.array([0.7, -0.5, -0.35])), (tE, np.array([0.7, -0.5, -0.35])), (tE + 0.15, unit(np.array([0.7, -0.5, -0.35]) + W0['r_pole'])), (tD, W0['r_pole'])):
            T.add(t, r_pole=pole)
        grip, opn = H.finger_shape('R', 'grip', 1.0), H.finger_shape('R', 'open', 1.0)
        for t, vv in ((0.0, grip), (tR - 0.03, grip), (tR + 0.05, opn), (tC - 0.14, opn), (tC, grip), (tD, grip)):
            T.add(t, r_fing=vv)
        fdir_h, palm_h = np.array([0.20, 0.55, -0.80]), np.array([0.95, 0.0, 0.25])
        L = [(0.0, W0['l_wrist'], W0['l_fdir'], W0['l_palm'], W0['l_pole']),
             (tW, v(-0.30, 0.34, 1.55), np.array([-0.2, 0.7, 0.7]), np.array([0.8, -0.3, 0.5]), np.array([-0.5, -0.5, -0.5])),
             (tR, v(-0.28, 0.32, 0.58), np.array([0.0, 0.5, -0.8]), np.array([0.9, 0.0, 0.3]), np.array([-0.5, -0.6, -0.6])),
             (0.62, v(-0.30, 0.20, 0.62), np.array([0.1, 0.5, -0.8]), np.array([0.9, 0.0, 0.3]), np.array([-0.7, -0.5, -0.4])),
             (0.80, v(-0.30, 0.10, 0.88), fdir_h, palm_h, np.array([-0.8, -0.5, -0.3])),
             (tH, v(-0.27, 0.05, 0.96), fdir_h, palm_h, np.array([-0.85, -0.4, -0.2])),
             (tE, v(-0.27, 0.05, 0.96), fdir_h, palm_h, np.array([-0.85, -0.4, -0.2])),
             (tD, W0['l_wrist'], W0['l_fdir'], W0['l_palm'], W0['l_pole'])]
        for t, w, fd, pm, pl in L:
            T.add(t, l_wrist=w, l_fdir=fd, l_palm=pm, l_pole=pl)
        relax, fistL = H.finger_shape('L', 'relaxed', 1.0), H.finger_shape('L', 'fist', 1.0)
        for t, vv in ((0.0, R['l_fing']), (tW - 0.04, relax), (tS, fistL), (tR + 0.1, relax), (tE, relax), (tD, R['l_fing'])):
            T.add(t, l_fing=vv)
        for t, pel, pr, cr, hr in ((0.0, [0, 0, 0], 9.0, 8.0, -14.0),
                                   (tW, [0.0, -0.05, -0.04], 0.0, -26.0, -28.0),
                                   (tR, [0.0, -0.13, -0.20], 44.0, 30.0, -40.0),
                                   (0.62, [0.0, -0.14, -0.22], 48.0, 32.0, -38.0),
                                   (0.95, [0.0, -0.05, -0.08], 22.0, 12.0, -22.0),
                                   (tH, [0.0, 0.0, -0.03], 8.0, 8.0, -14.0),
                                   (tE, [0.0, 0.0, -0.03], 8.0, 8.0, -14.0),
                                   (tD, [0, 0, 0], 9.0, 8.0, -14.0)):
            T.add(t, pel=np.array(pel, float), pel_rot_p=pr, chest_rot_p=cr, head_rot_p=hr)
        for t, kn in ((0.0, 8.0), (tR, 38.0), (0.62, 40.0), (tH, 14.0), (tE, 14.0), (tD, 8.0)):
            T.add(t, knee=kn)
        self.limit_reach()
        self.roll_report = self.tune_roll([self.tH, self.tE, self.tE + 0.15], self.tC, self.tD)
        self.roll_report2 = self.tune_roll([self.tS, self.tR, self.tSW], self.tW - 0.04, self.tSW + 0.1)
        self._init_free_path()

    KEYS = ('rk_pos', 'rk_shaft', 'rk_face', 'pel_rot_p', 'chest_rot_p', 'head_rot_p', 'knee')

    def P(self, t):
        P = dict(self.R)
        pp = self.T.pose(t)
        P.update({kk: vv for kk, vv in pp.items() if kk not in self.KEYS})
        P['r_frame'] = 'w'
        P['l_frame'] = 'w'
        P['r_wlim'] = (math.radians(85.0), math.radians(178.0))
        P['pel_rot'] = np.array([0.0, pp['pel_rot_p'], 0.0])
        P['chest_rot'] = np.array([0.0, pp['chest_rot_p'], 0.0])
        sh = 0.0
        a0 = self.tH - 0.02
        if a0 <= t <= self.tE:
            sh = math.sin(TAU * (t - a0) / 0.40) * 20.0 * smooth((t - a0) / 0.10) * (1 - smooth((t - (self.tE - 0.10)) / 0.12))
        P['head_rot'] = np.array([sh, pp['head_rot_p'], 0.0])
        P['lf_knee'] = pp['knee']
        P['rf_knee'] = pp['knee']
        # the left foot stamps down as the arm comes down (lifted in the wind-up, planted at the release): in place, no travel
        lf = 0.0
        if self.tW - 0.10 <= t <= self.tR + 0.02:
            lf = math.sin(math.pi * min(1.0, (t - (self.tW - 0.10)) / (self.tR + 0.02 - (self.tW - 0.10)))) ** 1.5
            if t > self.tW + 0.04:
                lf = max(0.0, 1.0 - (t - (self.tW + 0.04)) / (self.tR + 0.02 - (self.tW + 0.04)))
        P['lf_lift'] = 0.07 * lf
        P['lf_heel'] = 25.0 * lf
        # shoulders heave while the hero fumes over the racket (0.45-1.15) and again, smaller, with the hands on the hips
        hv = smooth((t - 0.46) / 0.1) * (1 - smooth((t - 1.10) / 0.2)) + 0.5 * smooth((t - self.tH) / 0.1) * (1 - smooth((t - (self.tE - 0.1)) / 0.2))
        P['chest_rot'] = P['chest_rot'] + np.array([0.0, 3.0 * math.sin(TAU * 2.4 * t) * hv, 0.0])
        P['r_rk_pos'] = pp['rk_pos']
        P['r_rk_shaft'] = pp['rk_shaft']
        P['r_rk_face'] = pp['rk_face']
        return P

    def tune_roll(self, times, t0, t1, rolls=range(0, 360, 15)):
        """turn the racket about its shaft at the named keys until the arm moves smoothly (least max bone step + wrist clamp) over [t0, t1]"""
        H = self.H
        base = {t: np.asarray(dict(self.T.ch['rk_face'])[t], float) for t in times}
        shaft = {t: unit(np.asarray(dict(self.T.ch['rk_shaft'])[t], float)) for t in times}
        best = None
        for r in rolls:
            a = math.radians(r)
            for t in times:
                sh = shaft[t]
                f0 = base[t] - np.dot(base[t], sh) * sh
                f0 = unit(f0)
                f = math.cos(a) * f0 + math.sin(a) * np.cross(sh, f0)
                self.T.add(t, rk_face=f)
            self.T._c = {}
            prev = None
            mx, cl = 0.0, 0.0
            for fr in range(int(round(t0 * 30)), int(round(t1 * 30)) + 1):
                b, h, info = H.solve(self.P(fr / 30.0))
                q = quats_of(H.rig, b, prev)
                if prev is not None:
                    mx = max(mx, float(rot_diff_deg(q, prev).max()))
                prev = q
                cl = max(cl, info['R_wrist_clamp_deg'])
            score = mx + 1.5 * cl + 0.05 * min(r, 360 - r)
            if best is None or score < best[0]:
                best = (score, r, mx, cl)
        r = best[1]
        a = math.radians(r)
        for t in times:
            sh = shaft[t]
            f0 = unit(base[t] - np.dot(base[t], sh) * sh)
            self.T.add(t, rk_face=math.cos(a) * f0 + math.sin(a) * np.cross(sh, f0))
        self.T._c = {}
        return best

    def limit_reach(self):
        """pull a racket key towards the right shoulder by what the arm falls short, at the key time (two passes)"""
        for it in range(3):
            moved = 0.0
            for i, (t, pos) in enumerate(self.T.ch['rk_pos']):
                b, h, info = self.H.solve(self.P(t))
                sh = info['R_arm_short']
                if sh > 0.002:
                    d = unit(info['R_shoulder'] - info['rk_origin'])
                    self.T.ch['rk_pos'][i] = (t, np.asarray(pos, float) + w2a(d) * (sh + 0.006))
                    moved += sh
            for i, (t, pos) in enumerate(self.T.ch['l_wrist']):
                b, h, info = self.H.solve(self.P(t))
                sh = info['L_arm_short']
                if sh > 0.002:
                    d = unit(info['L_shoulder'] - info['L_wrist_target'])
                    self.T.ch['l_wrist'][i] = (t, np.asarray(pos, float) + w2a(d) * (sh + 0.006))
                    moved += sh
            self.T._c = {}
            if moved < 0.002:
                break
        self.reach_moved = moved

    # ---- the racket in flight
    def _init_free_path(self):
        H = self.H
        k = self.k
        O = H.O
        sock = {}
        for name, t in (('rel', self.tR), ('catch', self.tC)):
            b, h, info = H.solve(self.P(t))
            sock[name] = (info['rk_origin'].copy(), info['rk_R'].copy())
        self.sock = sock
        auth = lambda vv: O + a2w(np.asarray(vv, float))
        ax = lambda sh, fa: A2W_ @ PS.frame_from_axes(unit(np.asarray(sh, float)), np.asarray(fa, float))
        R_F = ax([0.10, 0.62, -0.78], [-0.95, 0.1, -0.1])
        zF = -racket_min_z(np.zeros(3), R_F)
        pF = auth([0.28 * k, 0.78, 0.0]).copy(); pF[2] = zF
        R_A = ax([0.10, 0.25, 0.95], [0.95, -0.2, 0.1])
        pA = auth([0.30 * k, 0.82, 0.0]).copy(); pA[2] = 0.98
        R_rel = sock['rel'][1]
        p_rel = sock['rel'][0]
        p_c, R_c = sock['catch']
        pM = 0.5 * (pA + p_c) + np.array([0.0, 0.0, 0.05])
        self.free = FreePath([(self.tR, p_rel), (self.tF, pF), (self.tA, pA), (0.5 * (self.tA + self.tC), pM), (self.tC, p_c), (self.tC + 0.1, p_c)],
                             [(self.tR, R_rel), (self.tF, R_F), (self.tA, R_A), (self.tC, R_c)])

    def racket_world(self, t, info):
        if t < self.tR - 1e-9 or t >= self.tC - 1e-9:
            return None
        p, R = self.free(t)
        return dict(pos=p, R=R)

    def solve(self, t):
        P = self.P(t)
        basis, hips, info = self.H.solve(P)
        return dict(basis=basis, hips=hips, info=info, racket=self.racket_world(t, info), P=P)


A2W_ = EH.A2W
REGISTRY['Emote_Spike'] = Spike


# ------------------------------------------------------------------------------------------------------------------------------ Intro_Wave
class Wave(ClipDef):
    """One hand waves twice, palm forward, from the wrist; the other (racket) hand holds the racket still; READY.
    0.00-0.40 the left hand leaves the throat and rises, the racket goes to the right side | 0.40-1.20 two waves (period 0.4 s) | 1.20-1.40 hold | 1.40-2.00 back to READY."""

    def __init__(self, H):
        super().__init__('Intro_Wave', 2.0, H)
        R, T = self.R, self.T
        k = self.k = H.A / 0.505
        b, h, info = H.solve(R)
        Rc, C = info['R_chest'], info['chest_center']
        g0 = (w2a(Rc.T @ (info['rk_origin'] - C)), w2a(Rc.T @ info['rk_R'][:, 1]), w2a(Rc.T @ info['rk_R'][:, 2]))
        self.t = (0.0, 0.14, 0.40, 1.20, 1.30, 1.55, 2.0)
        t0, t1, tA, tB, tC, tE, tD = self.t
        tH, tB2 = 1.70, 1.97                      # the racket hand holds its pose until 1.70 (the waving hand is long down by then) and is back on READY at 1.97
        tm, ts = 0.09, 0.20                       # the racket hand is on its side pose (and still) well before the hand above the shoulder starts waving
        # the racket hand: ready -> held low at the right side, still from 0.40 to 1.40
        side = (np.array([0.25, 0.10, -0.33]) * k, np.array([0.12, 0.40, 0.91]), np.array([-0.95, 0.1, 0.2]))
        mid = (0.5 * (g0[0] + side[0]), unit(g0[1] + side[1]), unit(g0[2] + side[2]))
        for t, v in ((t0, g0), (tm, mid), (ts, side), (tH, side), (tB2, g0), (tD, g0)):
            T.add(t, rk_pos=v[0], rk_shaft=v[1], rk_face=v[2])
        for t, pole in ((t0, R['r_pole']), (ts, np.array([0.6, -0.4, -0.7])), (tH, np.array([0.6, -0.4, -0.7])), (tD, R['r_pole'])):
            T.add(t, r_pole=pole)
        T.add(t0, r_fing=H.finger_shape('R', 'grip', 1.0))
        T.add(tD, r_fing=H.finger_shape('R', 'grip', 1.0))
        # the waving hand (left): the wrist beside the head, forearm up, fingers up, palm forward
        up = (np.array([-0.25, 0.14, 0.17]) * k, np.array([-0.25, 0.0, 0.97]), np.array([0.0, 0.97, 0.1]))
        way = (np.array([-0.20, 0.30, -0.06]) * k, np.array([-0.2, 0.6, 0.75]), np.array([0.5, 0.2, 0.8]))
        for t, v in ((t0, (R['l_wrist'], R['l_fdir'], R['l_palm'])), (t1 + 0.04, way), (tA, up), (tC, up), (tE, way), (tD, (R['l_wrist'], R['l_fdir'], R['l_palm']))):
            T.add(t, l_wrist=v[0], l_fdir=v[1], l_palm=v[2])
        for t, pl in ((t0, R['l_pole']), (tA, np.array([-0.7, -0.4, -0.5])), (tC, np.array([-0.7, -0.4, -0.5])), (tD, R['l_pole'])):
            T.add(t, l_pole=pl)
        for t, v in ((t0, R['l_fing']), (tA, H.finger_shape('L', 'open', 1.0)), (tC, H.finger_shape('L', 'open', 1.0)), (tD, R['l_fing'])):
            T.add(t, l_fing=v)
        self.up = up
        self.refit(0.8, (ts, tH), right=True)
        self.refit(0.8, (tA, tC), left=True)

    def P(self, t):
        P = super().P(t)
        t0, t1, tA, tB, tC, tE, tD = self.t
        ev = smooth((t - tA) / 0.06) * (1 - smooth((t - tB) / 0.06))
        wv = ev * math.sin(TAU * (t - tA) / 0.40) if tA <= t <= tB + 0.06 else 0.0
        a = math.radians(40.0) * wv
        # the hand swings about the wrist: the fingers tilt in the chest's r-u plane (a few degrees of palm roll with it), the wrist moves a little with it
        fd = np.asarray(P['l_fdir'], float)
        P['l_fdir'] = fd + ev * np.array([math.sin(a) * 0.9, 0.0, 0.0]) * 1.0 if ev > 0 else fd
        P['l_wrist'] = np.asarray(P['l_wrist'], float) + np.array([0.012 * wv, 0.0, 0.0]) * self.k
        P['head_rot'] = np.array([0.0, -14.0, 0.0]) + np.array([-3.0, 0.0, 3.0]) * ev
        return P


REGISTRY['Intro_Wave'] = Wave


# ------------------------------------------------------------------------------------------------------------------------------ Intro_BringIt
class BringIt(ClipDef):
    """The free (left) hand beckons: palm toward the body, fingers tucking in, three times.  The racket points at the other player.  Two steps in place.  READY.
    0.00-0.45 the racket comes out to point and the hand comes up | 0.45-2.40 beckon (period 0.55 s); left foot steps at 0.55-1.05, right foot at 1.30-1.80 | 2.40-3.00 back to READY."""

    def __init__(self, H):
        super().__init__('Intro_BringIt', 3.0, H)
        R, T = self.R, self.T
        k = self.k = H.A / 0.505
        b, h, info = H.solve(R)
        Rc, C = info['R_chest'], info['chest_center']
        g0 = (w2a(Rc.T @ (info['rk_origin'] - C)), w2a(Rc.T @ info['rk_R'][:, 1]), w2a(Rc.T @ info['rk_R'][:, 2]))
        self.t = (0.0, 0.65, 2.35, 3.0)
        t0, tA, tB, tD = self.t
        point = (np.array([0.20, 0.40, 0.00]) * k, np.array([0.04, 1.0, 0.12]), np.array([-1.0, 0.05, 0.0]))
        for t, v in ((t0, g0), (tA, point), (tB, point), (tD, g0)):
            T.add(t, rk_pos=v[0], rk_shaft=v[1], rk_face=v[2])
        for t, pole in ((t0, R['r_pole']), (tA, np.array([0.7, -0.3, -0.6])), (tB, np.array([0.7, -0.3, -0.6])), (tD, R['r_pole'])):
            T.add(t, r_pole=pole)
        T.add(t0, r_fing=H.finger_shape('R', 'grip', 1.0))
        T.add(tD, r_fing=H.finger_shape('R', 'grip', 1.0))
        # beckoning hand: forearm out in front, palm up and toward the body, fingers pointing forward-up
        bk = (np.array([-0.17, 0.36, -0.02]) * k, np.array([-0.15, 0.85, 0.45]), np.array([0.25, -0.35, 0.90]))
        for t, v in ((t0, (R['l_wrist'], R['l_fdir'], R['l_palm'])), (tA, bk), (tB, bk), (tD, (R['l_wrist'], R['l_fdir'], R['l_palm']))):
            T.add(t, l_wrist=v[0], l_fdir=v[1], l_palm=v[2])
        for t, pl in ((t0, R['l_pole']), (tA, np.array([-0.5, -0.5, -0.7])), (tB, np.array([-0.5, -0.5, -0.7])), (tD, R['l_pole'])):
            T.add(t, l_pole=pl)
        self.fing_open = H.finger_shape('L', 'open', 1.0)
        self.fing_tuck = H.finger_shape('L', 'tuck', 1.0)
        self.period = 0.55
        self.refit(1.0, (tA, tB), right=True, left=True)

    def tuck(self, t, finger_delay):
        """0 open .. 1 tucked for the beckon cycle (period 0.55 s, three cycles from 0.55 s), staggered per finger"""
        t0, tA, tB, tD = self.t
        u = (t - (self.t[1] + 0.10) - finger_delay) / self.period
        if u < 0 or t > tB - 0.1 + finger_delay:
            return 0.0
        ph = u % 1.0
        return (smooth(ph / 0.45) if ph < 0.45 else 1 - smooth((ph - 0.45) / 0.55))

    def P(self, t):
        P = super().P(t)
        H = self.H
        t0, tA, tB, tD = self.t
        names = H.finger_names('L')
        base = np.asarray(H.fing_vec('L'))
        vec = np.array(P['l_fing'], float) if 'l_fing' in P else np.array(self.R['l_fing'], float)
        rest = np.asarray(self.R['l_fing'], float)
        ev = smooth((t - 0.15) / 0.35) * (1 - smooth((t - (tB - 0.1)) / 0.3))
        out = (1 - ev) * rest + ev * self.fing_open
        for i, n in enumerate(names):
            d = {'Index': 0.0, 'Middle': 0.05, 'Ring': 0.10, 'Little': 0.15, 'Thumb': 0.0}[[f for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Little') if f in n][0]]
            c = self.tuck(t, d)
            out[i] = out[i] + c * (self.fing_tuck[i] - self.fing_open[i]) * ev
        P['l_fing'] = out
        # the wrist beckons a little with each tuck (the hand rocks up and back)
        c0 = self.tuck(t, 0.0)
        P['l_wrist'] = np.asarray(P['l_wrist'], float) + np.array([0.0, -0.025, 0.012]) * c0 * ev * self.k
        # two steps in place: left foot 0.55-1.05, right foot 1.30-1.80 (lift, no travel; the pelvis shifts over the standing foot)
        def lift(t, a, b):
            if t <= a or t >= b:
                return 0.0
            return math.sin(math.pi * (t - a) / (b - a)) ** 2
        ll, rl = lift(t, 0.85, 1.35), lift(t, 1.55, 2.05)
        P['lf_lift'] = 0.09 * ll
        P['rf_lift'] = 0.09 * rl
        P['lf_heel'] = 35.0 * ll
        P['rf_heel'] = 35.0 * rl
        P['pel'] = np.array([0.045 * ll - 0.045 * rl, 0.0, 0.0]) * 1.0
        P['chest_rot'] = np.asarray(self.R['chest_rot']) + np.array([0.0, -4.0 * ev, -3.0 * ll + 3.0 * rl])
        P['head_rot'] = np.array([0.0, -14.0, 0.0]) + np.array([0.0, 3.0 * ev, 5.0 * (rl - ll)])
        return P


REGISTRY['Intro_BringIt'] = BringIt


# ------------------------------------------------------------------------------------------------------------------------------ Intro_Pushups
def hand_from_racket(H, pos_a, shaft_a, face_a):
    """a racket frame in the world authoring frame -> the hand that holds it: (wrist, fingers dir, palm normal), all in the same frame"""
    S = H.S
    Rrk_w = A2W_ @ PS.frame_from_axes(unit(np.asarray(shaft_a, float)), np.asarray(face_a, float))
    Qh_w = Rrk_w @ S.R_rh.T
    org_w = A2W_ @ np.asarray(pos_a, float)                 # relative to the floor origin
    W_w = org_w - Qh_w @ S.t_rh
    return A2W_ @ W_w, A2W_ @ Qh_w[:, 1], A2W_ @ Qh_w[:, 2]


class Pushups(ClipDef):
    """Drop to the floor, two push-ups, stand, READY.  The racket is set down on the court at the right (leaves the hand at 0.50) and picked up again (back in the hand at 2.50).
    Everything is keyed in the WORLD authoring frame; the feet stay where they are (toes down in the plank), the hands walk out to the plank and back.
    0.00-0.50 squat and set the racket down | 0.50-1.00 hands to the floor, walk out to the plank | 1.00-2.05 two push-ups (period 0.5) | 2.05-2.50 walk back, pick the racket up |
    2.50-3.00 stand, READY."""


    def __init__(self, H):
        super().__init__('Intro_Pushups', 3.0, H)
        R, T = self.R, self.T
        W0 = H.ready_world()
        k = self.k = H.A / 0.505
        S = H.S
        self.W0 = W0
        # proportions of THIS hero: leg line (hip -> ankle, slightly bent), torso (hips -> chest centre)
        b0, h0, i0 = H.solve(R)
        self.LEG = 0.96 * (S.t_len + S.s_len)
        self.TORSO = float(np.linalg.norm(i0['chest_center'] - i0['Pos'][H.rig.idx['Hips']]))
        self.f_ball = float(R['rf_foot'][1])
        self.foot_r = float(R['rf_foot'][0])
        self.heel_plank = 66.0
        # the plank geometry from the solver: ankle height / forward position with the heel up
        P = dict(R); P['rf_heel'] = self.heel_plank; P['lf_heel'] = self.heel_plank
        P['l_frame'] = P['r_frame'] = 'w'
        for pre in 'lr':
            P[pre + '_wrist'] = np.array([0.2, 0.5, 0.5]); P[pre + '_fdir'] = np.array([0, 1, 0.0]); P[pre + '_palm'] = np.array([0, 0, -1.0])
        b, h, info = H.solve(P)
        self.ankle_pl = w2a(info['rf_ankle'] - H.O)                          # (r, f, u) of the right ankle in the plank
        self.t = dict(sq=0.30, rel=13 / 30, hand=0.56, plank=0.92, b1=1.15, t1=1.38, b2=1.61, t2=1.84, back=2.12, arrive=2.33, pick=73 / 30, up=2.72, end=3.0)
        # ---- the racket: set down flat on the court at the hero's right, grip at (0.50, 0.34)
        self.rk_floor_pos = np.array([0.60, 0.52, 0.0])
        sh, fa = np.array([0.0, -1.0, 0.0]), np.array([0.0, 0.0, 1.0])          # lying at the right of the hero, the head towards the heels: clear of the feet and of the plank
        zf = -racket_min_z(np.zeros(3), A2W_ @ PS.frame_from_axes(sh, fa))
        self.rk_floor_pos[2] = zf
        self.rk_floor = (self.rk_floor_pos.copy(), sh, fa)
        self.hover = 0.110
        hold = (self.rk_floor_pos + np.array([0.0, 0.0, self.hover]), sh, fa)
        self.rk_hold = hold
        wr, fd, pm = hand_from_racket(H, *hold)
        self.hand_on_rk = (wr, fd, pm)

    # ---- the prone body for hands at forward position fw and shoulder-over-floor height zs (the wrists are on the floor)
    def prone(self, fw, zs, heel):
        H = self.H
        O = H.O
        fa, za = float(self.ankle_pl[1]), float(self.ankle_pl[2])
        Lt = self.TORSO
        # shoulder joint target
        z_w = 0.062
        Sz = z_w + zs
        Sf = fa + math.sqrt(max((self.LEG * 0.998 + Lt) ** 2 - (Sz - za) ** 2, 0.0))        # the body is a straight line from the ankle to the shoulder
        # hip joint on the leg line (leg length LEG from the ankle) such that |hips - shoulder| = Lt: scan the hip height
        best = None
        for zh in np.linspace(za, za + self.LEG - 0.005, 400):
            fh = fa + math.sqrt(max(self.LEG ** 2 - (zh - za) ** 2, 0.0))
            d = math.hypot(Sf - fh, Sz - zh)
            e = abs(d - Lt)
            if best is None or e < best[0] - 1e-9 or (abs(e - best[0]) < 1e-9 and zh < best[1]):
                best = (e, zh, fh)
        e, zh, fh = best
        lean = math.degrees(math.atan2(Sf - fh, Sz - zh))                  # torso axis lean from vertical (+ forward)
        return dict(pel_abs=np.array([0.0, fh, zh]), lean=lean, S=(Sf, Sz), err=e)

    def solve_prone_frame(self, fw, zs, heel, P_base):
        """channel dict for the prone body: pelvis position / pitch iterated until the chest centre sits at the shoulder target"""
        H = self.H
        O = H.O
        pr = self.prone(fw, zs, heel)
        P = dict(P_base)
        pel = pr['pel_abs'].copy()
        pitch = pr['lean'] - 3.0
        chest = 3.0
        for it in range(4):
            P['pel_abs'] = pel
            P['pel_rot'] = np.array([0.0, pitch, 0.0])
            P['chest_rot'] = np.array([0.0, chest, 0.0])
            P['pel_auto'] = False
            b, h, info = H.solve(P)
            c = w2a(info['chest_center'] - O)
            err = np.array([0.0, pr['S'][0] - c[1], pr['S'][1] - c[2]])
            if np.linalg.norm(err) < 0.002:
                break
            pel = pel + err
        return P, pr


class PushupsFull(Pushups):
    """the shipped clip: see Pushups"""

    def __init__(self, H):
        super().__init__(H)
        self.name = 'Intro_Pushups'
        R, T, W0 = self.R, self.T, self.W0
        k = self.k
        tt = self.t
        A = H.A
        self._ankle_cache = {}
        self.zs_top, self.zs_bot = A + 0.006, 0.554 * A
        self.fw_pike = 0.82 * k
        an = self.ankle_for(self.heel_plank)
        Sz = 0.062 + self.zs_top
        self.fw_plank = float(an[1]) + math.sqrt(max((self.LEG * 0.998 + self.TORSO) ** 2 - (Sz - float(an[2])) ** 2, 0.0)) + 0.02
        self.pel_ready = np.array([0.0, float(w2a(H.solve(R)[2]['Pos'][H.rig.idx['Hips']] - H.O)[1]), float(w2a(H.solve(R)[2]['Pos'][H.rig.idx['Hips']] - H.O)[2])])
        self._ankle_cache = {}
        # ---- regime P parameters (hands on the floor): fw (hands' forward position), zs (shoulder height over the wrists), heel
        T.add(tt['hand'], fw=self.fw_pike, zs=self.zs_top - 0.01, heel=0.0)
        T.add(tt['plank'], fw=self.fw_plank, zs=self.zs_top, heel=self.heel_plank)
        for name, z in (('b1', self.zs_bot), ('t1', self.zs_top), ('b2', self.zs_bot), ('t2', self.zs_top)):
            T.add(tt[name], fw=self.fw_plank, zs=z, heel=self.heel_plank)
        T.add(tt['back'], fw=self.fw_pike, zs=self.zs_top - 0.01, heel=0.0)
        self.park()

    # the regime P pose at (fw, zs, heel): channel dict
    def ankle_for(self, heel):
        key = round(float(heel), 1)
        if key not in self._ankle_cache:
            P = dict(self.R); P['rf_heel'] = P['lf_heel'] = heel
            P['l_frame'] = P['r_frame'] = 'w'
            for pre in 'lr':
                P[pre + '_wrist'] = np.array([0.2, 0.5, 0.5]); P[pre + '_fdir'] = np.array([0, 1, 0.0]); P[pre + '_palm'] = np.array([0, 0, -1.0])
            b, h, info = self.H.solve(P)
            self._ankle_cache[key] = w2a(info['rf_ankle'] - self.H.O)
        return self._ankle_cache[key]

    def prone2(self, fw, zs, heel):
        """hips / shoulders for hands planted at fw.  The shoulders sit over the hands unless the straight body is too short to get there; the hips are where the leg line (length LEG from the
        ankle) and the torso (length TORSO from the shoulder) meet, on the side that piking up (never sagging)"""
        an = self.ankle_for(heel)
        A = np.array([float(an[1]), float(an[2])])
        Lt, Lg = self.TORSO, self.LEG * 0.998
        Sz = 0.062 + zs
        f_str = A[0] + math.sqrt(max((Lg + Lt) ** 2 - (Sz - A[1]) ** 2, 0.0))
        Sf = min(fw, f_str)
        Sv = np.array([Sf, Sz])
        d = float(np.linalg.norm(Sv - A))
        if d >= Lg + Lt - 1e-6:
            Hh = A + (Sv - A) * Lg / d
        else:
            a = (Lg * Lg - Lt * Lt + d * d) / (2 * d)
            h = math.sqrt(max(Lg * Lg - a * a, 0.0))
            u = (Sv - A) / d
            base = A + a * u
            perp = np.array([-u[1], u[0]])
            c1, c2 = base + h * perp, base - h * perp
            Hh = c1 if c1[1] >= c2[1] else c2
        fh, zh = float(Hh[0]), float(Hh[1])
        lean = math.degrees(math.atan2(Sf - fh, Sz - zh))
        return dict(pel_abs=np.array([0.0, fh, zh]), lean=lean, S=(Sf, Sz), err=0.0)

    def P_prone(self, t):
        H = self.H
        pp = self.T.pose(t)
        fw, zs, heel = float(pp['fw']), float(pp['zs']), float(pp['heel'])
        P = dict(self.R)
        P['l_frame'] = P['r_frame'] = 'w'
        P['lf_heel'] = heel; P['rf_heel'] = heel
        P['lf_knee'] = 4.0; P['rf_knee'] = 4.0
        P['pel_auto'] = False
        z_w = 0.062
        P['l_wrist'] = np.array([-0.23, fw, z_w]); P['r_wrist'] = np.array([0.23, fw, z_w])
        for pre, sg in (('l', -1), ('r', 1)):
            P[pre + '_fdir'] = np.array([0.0, 1.0, 0.0]); P[pre + '_palm'] = np.array([0.0, 0.0, -1.0])
            P[pre + '_pole'] = np.array([sg * 0.6, -0.7, 0.3])
            P[pre + '_wlim'] = (math.radians(105.0), math.radians(150.0))
        P['l_fing'] = H.finger_shape('L', 'open', 1.0); P['r_fing'] = H.finger_shape('R', 'open', 1.0)
        P['gaze'] = np.array([0.0, fw + 0.40, 0.05])
        pr = self.prone2(fw, zs, heel)
        pel = pr['pel_abs'].copy()
        pitch, chest = pr['lean'] - 3.0, 3.0
        for it in range(5):
            P['pel_abs'] = pel
            P['pel_rot'] = np.array([0.0, pitch, 0.0])
            P['chest_rot'] = np.array([0.0, chest, 0.0])
            b, h, info = H.solve(P)
            c = w2a(info['chest_center'] - H.O)
            err = np.array([0.0, pr['S'][0] - c[1], pr['S'][1] - c[2]])
            if np.linalg.norm(err) < 0.002:
                break
            pel = pel + err
        return P

    def fold_pose(self, hips, shoulders, chest=8.0, shift=0.0, roll=0.0):
        """a standing-fold pose (feet flat): the hips (f, z) and the chest centre (f, z) are given; returns pel_abs / pel_rot / chest_rot channel values"""
        H = self.H
        P = dict(self.R)
        P['pel_auto'] = False
        P['l_frame'] = P['r_frame'] = 'w'
        for pre in 'lr':
            P[pre + '_wrist'] = np.array([0.2, 0.5, 0.3]); P[pre + '_fdir'] = np.array([0, 1, 0.0]); P[pre + '_palm'] = np.array([0, 0, -1.0])
        pel = np.array([shift, hips[0], hips[1]])
        lean = math.degrees(math.atan2(shoulders[0] - hips[0], shoulders[1] - hips[1]))
        pitch = lean - 0.5 * chest
        for it in range(6):
            P['pel_abs'] = pel
            P['pel_rot'] = np.array([0.0, pitch, 0.0])
            P['chest_rot'] = np.array([0.0, chest, roll])
            b, h, info = H.solve(P)
            c = w2a(info['chest_center'] - H.O)
            err = np.array([shoulders[0] - c[1], shoulders[1] - c[2]])
            if np.linalg.norm(err) < 0.002:
                break
            # move the chest onto the target by tilting the pelvis (forward / back) first, then lifting it
            Hp = w2a(info['Pos'][H.rig.idx['Hips']] - H.O)
            lean_now = math.degrees(math.atan2(c[1] - Hp[1], c[2] - Hp[2]))
            pitch += 0.7 * (lean - lean_now)
            pel = pel + np.array([0.0, 0.0, 0.5 * err[1]])
        return dict(pel_abs=pel, pel_rot=np.array([0.0, pitch, 0.0]), chest_rot=np.array([0.0, chest, roll]))

    def park(self):
        """squat / stand keys (regime S): READY, the racket set down, regime P's first / last pose as keys, the pick-up, READY"""
        H, T, R, W0 = self.H, self.T, self.R, self.W0
        tt = self.t
        k = self.k
        wr, fd, pm = self.hand_on_rk
        grip, opn = H.finger_shape('R', 'grip', 1.0), H.finger_shape('R', 'open', 1.0)
        relax = H.finger_shape('L', 'relaxed', 1.0)
        floorL = (np.array([-0.23, 0.36, 0.075]), hand_frame(np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, -1.0])))
        pel_r = self.pel_ready
        ori = lambda f_, p_: hand_frame(f_, p_)
        S = {}
        S[0.0] = dict(pel_abs=pel_r, pel_rot=np.array([0.0, 9.0, 0.0]), chest_rot=np.array([0.0, 8.0, 0.0]), heel=0.0, knee=8.0,
                      l=(W0['l_wrist'], ori(W0['l_fdir'], W0['l_palm']), W0['l_pole'], R['l_fing']), r=(W0['r_wrist'], ori(W0['r_fdir'], W0['r_palm']), W0['r_pole'], grip))
        pole_r = np.array([0.7, -0.4, 0.2]); pole_l = np.array([-0.7, -0.4, 0.2])
        sq = self.fold_pose(hips=(0.0, 0.50), shoulders=(0.44 * k, 0.50 * k), shift=0.10, roll=16.0)
        sq.update(heel=0.0, knee=14.0)
        rO = ori(fd, pm)
        S[tt['sq']] = dict(sq, l=(floorL[0], floorL[1], pole_l, relax), r=(wr, rO, pole_r, grip))
        S[tt['rel']] = dict(sq, l=(floorL[0], floorL[1], pole_l, relax), r=(wr, rO, pole_r, opn))
        for key in (tt['hand'], tt['back']):
            P = self.P_prone(key)
            S[key] = dict(pel_abs=P['pel_abs'], pel_rot=P['pel_rot'], chest_rot=P['chest_rot'], heel=P['lf_heel'], knee=4.0,
                          l=(P['l_wrist'], ori(P['l_fdir'], P['l_palm']), P['l_pole'], P['l_fing']), r=(P['r_wrist'], ori(P['r_fdir'], P['r_palm']), P['r_pole'], P['r_fing']))
        S[tt['arrive']] = dict(sq, l=(floorL[0], floorL[1], pole_l, relax), r=(wr, rO, pole_r, opn))
        S[tt['pick']] = dict(sq, l=(floorL[0], floorL[1], pole_l, relax), r=(wr, rO, pole_r, grip))
        S[tt['up']] = dict(pel_abs=pel_r + np.array([0.0, 0.0, -0.05]), pel_rot=np.array([0.0, 14.0, 0.0]), chest_rot=np.array([0.0, 10.0, 0.0]), heel=0.0, knee=10.0,
                           l=(0.5 * (W0['l_wrist'] + np.array([-0.30, 0.30, 0.65])), ori(W0['l_fdir'], W0['l_palm']), W0['l_pole'], R['l_fing']),
                           r=(W0['r_wrist'] + np.array([0.05, 0.0, -0.1]), ori(W0['r_fdir'], W0['r_palm']), W0['r_pole'], grip))
        S[tt['end']] = dict(S[0.0])
        # the right hand lifts clear of the court and turns palm down on its way between the racket and the floor (and back): never with the fingers hanging down into the court
        flat = hand_frame(np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, -1.0]))
        def between(a, b, u, rwr):
            d = {kk: (1 - u) * np.asarray(S[a][kk], float) + u * np.asarray(S[b][kk], float) for kk in ('pel_abs', 'pel_rot', 'chest_rot')}
            d['heel'] = (1 - u) * S[a]['heel'] + u * S[b]['heel']
            d['knee'] = (1 - u) * S[a]['knee'] + u * S[b]['knee']
            d['l'] = ((1 - u) * S[a]['l'][0] + u * S[b]['l'][0], S[a]['l'][1] if u < 0.5 else S[b]['l'][1], S[a]['l'][2], S[a]['l'][3])
            d['r'] = (rwr, flat, S[a]['r'][2], opn)
            return d
        S[tt['rel'] + 0.09] = between(tt['rel'], tt['hand'], 0.6, np.array([0.40, 0.58, 0.24]))
        S[tt['back'] + 0.05] = between(tt['back'], tt['arrive'], 0.3, np.array([0.40, 0.58, 0.28]))
        mid_ori = PS.slerp_mat(flat, rO, 0.5)
        dm = between(tt['back'], tt['arrive'], 0.85, np.array([0.47, 0.57, 0.27]))
        dm['r'] = (dm['r'][0], mid_ori, dm['r'][2], opn)
        S[tt['arrive'] - 0.08] = dm
        self.S_keys = S
        for t, d in S.items():
            T.add(t, s_pel_abs=d['pel_abs'], s_pel_rot=d['pel_rot'], s_chest_rot=d['chest_rot'], s_heel=d['heel'], s_knee=d['knee'])
            for pre in 'lr':
                w, o, pl, fg = d[pre]
                T.add(t, **{f's_{pre}_wrist': w, f's_{pre}_ori': o, f's_{pre}_pole': pl, f's_{pre}_fing': fg})

    def P(self, t):
        H = self.H
        tt = self.t
        if tt['hand'] <= t <= tt['back']:
            return self.P_prone(t)
        pp = self.T.pose(t)
        P = dict(self.R)
        P['l_frame'] = P['r_frame'] = 'w'
        P['pel_auto'] = False
        P['pel_abs'] = pp['s_pel_abs']; P['pel_rot'] = pp['s_pel_rot']; P['chest_rot'] = pp['s_chest_rot']
        P['lf_heel'] = P['rf_heel'] = pp['s_heel']
        P['lf_knee'] = P['rf_knee'] = pp['s_knee']
        for pre in 'lr':
            Ro = pp[f's_{pre}_ori']
            P[pre + '_wrist'] = pp[f's_{pre}_wrist']; P[pre + '_fdir'] = Ro[:, 1]; P[pre + '_palm'] = Ro[:, 2]; P[pre + '_pole'] = pp[f's_{pre}_pole']
            P[pre + '_fing'] = pp[f's_{pre}_fing']
            P[pre + '_wlim'] = (math.radians(105.0), math.radians(160.0))
        return P

    # the racket is put down / picked up in a handful of whole frames (heights above its rest, in metres): it never lingers 2-5 cm above the court, so it is either
    # "lying" or "in the hand's reach" - and its origin does not drift while it lies
    FALL = ((13, 0.110), (14, 0.095), (15, 0.070), (16, 0.010), (17, 0.0))
    LIFT = ((68, 0.0), (69, 0.010), (70, 0.056), (71, 0.058), (72, 0.060), (73, 0.110))      # the last step (>= 4.1 cm) is a snap into the hand: no frame is 'nearly attached'

    def racket_world(self, t, info):
        tt = self.t
        f = t * 30.0
        if f < self.FALL[0][0] - 1e-6 or f >= self.LIFT[-1][0] - 1e-6:
            return None
        pos, sh, fa = self.rk_floor
        R = A2W_ @ PS.frame_from_axes(sh, fa)
        if f <= self.FALL[-1][0]:
            h = float(np.interp(f, [a for a, _ in self.FALL], [b for _, b in self.FALL]))
        elif f >= self.LIFT[0][0]:
            h = float(np.interp(f, [a for a, _ in self.LIFT], [b for _, b in self.LIFT]))
        else:
            h = 0.0
        p = np.array([pos[0], pos[1], pos[2] + h])
        return dict(pos=H_O(self.H) + A2W_ @ p, R=R)

    def solve(self, t):
        P = self.P(t)
        b, h, info = self.H.solve(P)
        return dict(basis=b, hips=h, info=info, racket=self.racket_world(t, info), P=P)


def H_O(H):
    return H.O


REGISTRY['Intro_Pushups'] = PushupsFull


def R_chest_rot(R):
    return R['chest_rot']


REGISTRY['Emote_Scuba'] = Scuba

# ------------------------------------------------------------------------------------------------------------------------------ Emote_Thrust
class Thrust(ClipDef):
    """Two big hip thrusts with both fists up.  0.00-0.25 sit back and bring the fists up, 0.25-1.25 two thrusts (period 0.5 s: hips drive forward, trunk leans back,
    knees straighten, fists punch forward and up), 1.25-1.40 hold, 1.40-2.00 settle to READY.  No hand goes near the pelvis."""

    def __init__(self, H):
        super().__init__('Emote_Thrust', 2.0, H)
        R, T = self.R, self.T
        k = H.A / 0.505
        self.k = k
        self.t = (0.0, 0.25, 1.25, 1.40, 2.0)
        self.period = 0.5
        # fists in the chest frame: g = 0 (hips back) and g = 1 (hips forward)
        self.fL0, self.fL1 = np.array([-0.21, 0.17, -0.03]) * k, np.array([-0.25, 0.28, -0.04]) * k
        self.fR0, self.fR1 = np.array([0.21, 0.19, 0.00]) * k, np.array([0.25, 0.29, 0.00]) * k
        self.r_shaft = np.array([0.15, 0.25, 0.95])
        self.r_face = np.array([-0.95, 0.1, 0.1])
        H_ = H
        b, h, info = H.solve(R)
        Rc, C = info['R_chest'], info['chest_center']
        self.g0 = (w2a(Rc.T @ (info['rk_origin'] - C)), w2a(Rc.T @ info['rk_R'][:, 1]), w2a(Rc.T @ info['rk_R'][:, 2]))
        self.fist_L = H.finger_shape('L', 'fist', 1.0)
        self.fist_R = H.finger_shape('R', 'grip', 1.0)
        for i, nm in enumerate(H.finger_names('R')):
            if 'Proximal' in nm and 'Thumb' not in nm:
                self.fist_R[i] += 6.0                      # the racket fist closes a few degrees tighter than the plain grip

    def g(self, t):
        """thrust phase: 0 hips back .. 1 hips forward; two bumps in [tA, tB], then held forward until tC, then eased back"""
        t0, tA, tB, tC, tD = self.t
        if t < tA:
            return 0.0
        if t <= tC:
            if t >= tB - self.period * 0.5:
                return 1.0
            return 0.5 - 0.5 * math.cos(TAU * (t - tA) / self.period)
        return 1.0 - smooth((t - tC) / 0.35)

    def P(self, t):
        H = self.H
        R = self.R
        t0, tA, tB, tC, tD = self.t
        P = dict(R)
        rise = smooth((t - t0) / (tA - t0)) * (1 - smooth((t - tC) / (tD - tC)))
        g = self.g(t)
        w = rise
        mix = lambda a, b, u: (1 - u) * np.asarray(a, float) + u * np.asarray(b, float)
        P['pel'] = np.array([0.0, w * mix(-0.05, 0.14, g), w * mix(-0.075, -0.015, g)])
        P['pel_rot'] = np.array([0.0, (1 - w) * 9.0 + w * mix(17.0, -13.0, g), 0.0])
        P['chest_rot'] = np.array([0.0, (1 - w) * 8.0 + w * mix(2.0, -13.0, g), 0.0])
        P['head_rot'] = np.array([0.0, -14.0 + w * mix(-3.0, 6.0, g), 0.0])
        P['lf_knee'] = 8.0 + w * mix(26.0, 14.0, g)
        P['rf_knee'] = 8.0 + w * mix(26.0, 14.0, g)
        # arms: ready -> fists up (during 0..tA), then pumping with the thrusts
        pump = mix(0.0, 1.0, g)
        fl = mix(self.fL0, self.fL1, g)
        fr = mix(self.fR0, self.fR1, g)
        P['l_wrist'] = (1 - w) * np.asarray(R['l_wrist'], float) + w * fl
        P['l_fdir'] = (1 - w) * np.asarray(R['l_fdir'], float) + w * np.array([0.0, 0.55, 0.83])
        P['l_palm'] = (1 - w) * np.asarray(R['l_palm'], float) + w * np.array([0.9, -0.2, 0.2])
        P['l_pole'] = (1 - w) * np.asarray(R['l_pole'], float) + w * np.array([-0.4, -0.5, -0.75])
        P['l_fing'] = (1 - w) * np.asarray(R['l_fing'], float) + w * self.fist_L
        P['r_rk_pos'] = (1 - w) * self.g0[0] + w * fr
        P['r_rk_shaft'] = (1 - w) * self.g0[1] + w * (self.r_shaft + np.array([0.0, 0.25 * pump, 0.0]))
        P['r_rk_face'] = (1 - w) * self.g0[2] + w * self.r_face
        P['r_pole'] = (1 - w) * np.asarray(R['r_pole'], float) + w * np.array([0.4, -0.5, -0.75])
        P['r_fing'] = self.fist_R
        return P


REGISTRY['Emote_Thrust'] = Thrust



def build(name, H):
    return REGISTRY[name](H)
