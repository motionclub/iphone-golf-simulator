"""Pose solver for the fitted hero rigs (pure numpy).

Input: a dict of channel values `P` (authoring frame: r = hero's right, f = forward (towards the net), u = up; metres / degrees /
arm-length units where stated).  Output: one 3x3 basis rotation per bone + the Hips location, plus diagnostics.

Channels (all optional - missing ones take the READY value):
  pel        [r,f,u] m     pelvis centre offset from the READY pelvis position
  pel_rot    [yaw,pitch,roll] deg   pelvis orientation (yaw + = turn right, pitch + = lean forward, roll + = tilt right)
  chest_rot  [yaw,pitch,roll] deg   upper body relative to the pelvis (spread over Spine / Chest / UpperChest)
  head_rot   [yaw,pitch,roll] deg   head relative to the chest (Neck 40 %, Head 60 %);  gaze [r,f,u] m (point relative to the Root) overrides yaw/pitch
  {lf,rf}_foot  [r,f] m    ball-of-foot ground point        {lf,rf}_yaw deg (toes to the right +)   {lf,rf}_lift m (ball above floor)
  {lf,rf}_heel  deg (heel up +)    {lf,rf}_knee deg (knee pole rotated outwards +)
  rk_pos     [r,f,u] arm-length units   racket GRIP CENTRE relative to the right shoulder joint
  rk_shaft   [r,f,u]  racket Y axis (towards the head)      rk_face [r,f,u]  racket Z axis (face normal; made orthogonal to the shaft)
  r_elbow    [r,f,u]  right elbow apex direction (default: down/back/out)      l_elbow likewise
  l_attach   0..1 left hand follows the racket        l_grip  0 = throat, 1 = handle
  l_hand     [r,f,u] arm-length units  left WRIST relative to the left shoulder when free      l_palm [r,f,u] direction the left palm faces (free)
  r_fing, l_fing  0..1  finger closure  (right: 1 = racket grip;  left free hand: 0 relaxed .. 1 fist)
"""
import json
import math
import os

import numpy as np

import kin
from kin import a2w, w2a, unit, axis_angle, rx, ry, rz

F_W = np.array([0.0, -1.0, 0.0])            # forward in world
UP = np.array([0.0, 0.0, 1.0])
SPINE_W = (0.30, 0.34, 0.36)
KNEE_MIN_FLEX = math.radians(4.0)


def R_yaw(a_deg):                              # + = turn right (clockwise seen from above)
    return rz(-math.radians(a_deg))


def R_pitch(a_deg):                            # + = lean forward
    return rx(math.radians(a_deg))


def R_roll(a_deg):                             # + = tilt right
    return axis_angle(F_W, math.radians(a_deg))


def R_ypr(v, w=1.0):
    return R_yaw(w * v[0]) @ R_pitch(w * v[1]) @ R_roll(w * v[2])


def frame_from_axes(y, z_hint):
    """racket / generic frame: columns X,Y,Z with Y = y, Z = z_hint made orthogonal to Y, X = Y x Z."""
    y = unit(y)
    z = np.asarray(z_hint, float) - np.dot(z_hint, y) * y
    z = unit(z)
    x = np.cross(y, z)
    return np.stack([x, y, z], 1)


def slerp_mat(A, B, t):
    return A @ kin.mat_pow(A.T @ B, t)


class Solver:
    def __init__(self, rig, racket, hands):
        self.rig = rig
        R = rig
        self.racket = racket
        self.hands = hands
        self.T_rh = np.array(racket['T_hand_to_racket'])                    # racket frame in the right-hand bone frame
        self.R_rh = self.T_rh[:3, :3]
        self.t_rh = self.T_rh[:3, 3]
        self.head_center = np.array(racket['head_center'])                 # sweet spot in the racket frame
        self.O = R.root_origin.copy()
        J = R.J
        self.A_arm = float(np.linalg.norm(J['wrist_L'] - J['shoulder_L']))
        self.a_u = float(np.linalg.norm(J['elbow_L'] - J['shoulder_L']))
        self.a_f = float(np.linalg.norm(J['wrist_L'] - J['elbow_L']))
        self.t_len = float(np.linalg.norm(J['knee_L'] - J['hip_L']))
        self.s_len = float(np.linalg.norm(J['ankle_L'] - J['knee_L']))
        self.ankle_rest = {s: J[f'ankle_{s}'] for s in 'LR'}
        self.ball_rest = {s: J[f'ball_{s}'] for s in 'LR'}
        self.shoulder_w = float(np.linalg.norm(J['shoulder_L'] - J['shoulder_R']))
        self.min_wrist_r = 0.50 * self.A_arm
        # hands: T of the left hand in the racket frame for the two grips (hands_<hero>.json)
        self.T_hl_handle = np.array(hands['left_handle']['T_hand_in_racket'])
        self.T_hl_throat = np.array(hands['left_throat']['T_hand_in_racket'])
        # finger pose library (degrees about each finger bone's local X)
        self.fing_names = sorted(set(list(hands['right_grip'].keys()) + list(hands['left_handle']['angles'].keys())))
        self.open = {'L': hands['open_L'], 'R': hands['open_R']}
        self.grip_R = hands['right_grip']
        self.grip_Lh = hands['left_handle']['angles']
        self.grip_Lt = hands['left_throat']['angles']
        # foot grounding table (scripts/foot_ground.py): the extra lift that keeps the lowest toe vertex at its standing height when the heel is raised
        self.foot_dip = None
        try:
            _fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', f'foot_ground_{rig.tag}.json')
            if os.path.exists(_fp):
                _fd = json.load(open(_fp))
                self.foot_dip = (np.array(_fd['heel_deg'], float), np.array(_fd['lift_m'], float))
        except Exception:
            self.foot_dip = None
        self.ready = self._ready_params()
        self.ready['sh_half_A'] = 0.5 * self.shoulder_w / self.A_arm          # shoulder joint offset from the chest centre, in arm lengths (authoring r axis)
        self.reset()
        # torso ellipse (half widths, metres) used to keep elbows out of the body
        self.torso_a = 0.5 * float(np.linalg.norm(rig.J['shoulder_L'] - rig.J['shoulder_R'])) * 0.95
        self.torso_b = 0.13

    def reset(self):
        self.state = dict(R=dict(phi=0.0, wr=None, pole=None, tw=None, axis=None), L=dict(phi=0.0, pole=None, tau=None, tw=None, axis=None))

    # ------------------------------------------------------------------------------------------ ready pose
    def _ready_params(self):
        SWref = 0.40
        W = 1.55 * SWref * 1.06                                  # feet centre to centre
        f0 = float(-(self.ball_rest['L'][1] - self.O[1]))       # ball forward of the root in the bind pose
        ready = dict(
            pel=[0.0, 0.0, 0.0], pel_rot=[0.0, 9.0, 0.0], chest_rot=[0.0, 8.0, 0.0], head_rot=[0.0, -14.0, 0.0],
            lf_foot=[-W / 2, f0 + 0.02], rf_foot=[W / 2, f0 + 0.02], lf_yaw=-10.0, rf_yaw=10.0,
            lf_lift=0.0, rf_lift=0.0, lf_heel=0.0, rf_heel=0.0, lf_knee=8.0, rf_knee=8.0,
            rk_pos=[0.06, 0.56, -0.56], rk_shaft=[0.10, 0.45, 0.89], rk_face=[-1.0, 0.1, 0.0], rk_abs=0.0, rk_sweet=None, rk_fit=1.0, rk_w=[0.4, 1.0],
            r_elbow=None, l_elbow=None, l_attach=1.0, l_grip=0.0, l_hand=[-0.2, 0.5, -0.7], l_palm=[1.0, 0.0, 0.0],
            r_fing=1.0, l_fing=0.3,
        )
        return ready

    # ------------------------------------------------------------------------------------------ helpers
    def _aw(self, v):
        return a2w(v)

    def _leg_ik(self, hip, ankle, pole, a, b):
        """returns knee position (world) and the bone frames' hinge normal for a leg (apex direction = pole).  Clamps the reach."""
        d = ankle - hip
        L = np.linalg.norm(d)
        max_reach = math.sqrt(a * a + b * b + 2 * a * b * math.cos(KNEE_MIN_FLEX))
        short = 0.0
        if L > max_reach:
            short = L - max_reach
            L = max_reach
            ankle = hip + unit(d) * L
            d = ankle - hip
        min_reach = abs(a - b) + 1e-3
        if L < min_reach:
            L = min_reach
            d = unit(d) * L
        u_ = d / L
        pp = np.asarray(pole, float) - np.dot(pole, u_) * u_
        if np.linalg.norm(pp) < 1e-4:
            pp = unit(np.cross(u_, [1.0, 0.0, 0.0]))
        pp = unit(pp)
        cosA = (a * a + L * L - b * b) / (2 * a * L)
        A_ = math.acos(max(-1.0, min(1.0, cosA)))
        knee = hip + a * (u_ * math.cos(A_) + pp * math.sin(A_))
        return knee, ankle, u_, pp, short

    # ------------------------------------------------------------------------------------------ main solve
    def solve(self, Pin):
        rig = self.rig
        names = rig.names
        ix = rig.idx
        n = rig.n
        P = dict(self.ready)
        for k, v in Pin.items():
            if v is not None or k not in P:
                P[k] = v
            elif v is None and k in ('r_elbow', 'l_elbow'):
                P[k] = None
        Q = np.zeros((n, 3, 3))
        Pos = np.zeros((n, 3))
        basis = np.tile(np.eye(3), (n, 1, 1))
        diag = {}
        O = self.O

        def put(i, Qi, loc=None):
            """set bone i's world orientation (parent already solved) and update FK arrays."""
            p = rig.parent[i]
            if p < 0:
                basis[i] = rig.rel_rot[i].T @ Qi
                Q[i] = Qi
                Pos[i] = rig.rel_off[i]
            else:
                basis[i] = rig.rel_rot[i].T @ Q[p].T @ Qi
                Q[i] = Qi
                Pos[i] = Pos[p] + Q[p] @ rig.rel_off[i]

        # Root (identity)
        iR = ix['Root']
        put(iR, rig.Rrest[iR])
        # ---- feet targets (needed first: the ready pelvis height depends on them)
        feet = {}
        for s, key in (('L', 'lf'), ('R', 'rf')):
            br = np.array(P[f'{key}_foot'], float)
            yaw = float(P[f'{key}_yaw'])
            lift = float(P[f'{key}_lift'])
            heel = float(P[f'{key}_heel'])
            if self.foot_dip is not None and heel > 0.0:
                lift += float(np.interp(heel, self.foot_dip[0], self.foot_dip[1]))
            ball = O + a2w([br[0], br[1], 0.0]) + np.array([0.0, 0.0, self.ball_rest[s][2] + lift])
            Ry_ = R_yaw(yaw)
            Rh_ = rx(math.radians(heel))                                       # heel up: +Y (back) rotates towards +Z
            # the player's left foot (L) is at -r: its yaw sign follows the "toes to the right +" convention for both feet
            Rfoot = Ry_ @ Rh_
            ankle = ball + Rfoot @ (self.ankle_rest[s] - self.ball_rest[s])
            feet[s] = dict(ball=ball, ankle=ankle, Rfoot=Rfoot, Ry=Ry_, heel=heel, yaw=yaw)
        # ---- pelvis position: READY height from the knee flexion target, then offsets
        hips_rest = rig.hrest[ix['Hips']]
        hip_off = {s: rig.J[f'hip_{s}'] - hips_rest for s in 'LR'}          # hip joints relative to the Hips head (bind)
        mid_ank = 0.5 * (feet['L']['ankle'] + feet['R']['ankle'])
        z_ready = self._ready_height()
        pel_off = np.array(P['pel'], float)
        # base pelvis position: over the ankles' midpoint (xy) at the ready height; then the authoring offset
        # ready pelvis centre = (x 0, y = ankle y of the READY stance, z_ready); the authoring offset moves it from there
        ready_ank_y = self._ready_ankle_y()
        pel_pos = np.array([O[0], ready_ank_y, z_ready]) + a2w(pel_off)
        R_pel = R_ypr(P['pel_rot'])
        iH = ix['Hips']
        # hips orientation
        Q_h = R_pel @ rig.Rrest[iH]
        # --- automatic pelvis drop so both planted legs can reach
        Hjoint = {s: pel_pos + R_pel @ hip_off[s] for s in 'LR'}
        max_reach = math.sqrt(self.t_len ** 2 + self.s_len ** 2 + 2 * self.t_len * self.s_len * math.cos(math.radians(9.0)))
        need = 0.0
        for s in 'LR':
            dxy = np.linalg.norm((feet[s]['ankle'] - Hjoint[s])[:2])
            dz = Hjoint[s][2] - feet[s]['ankle'][2]
            full = math.sqrt(dxy ** 2 + dz ** 2)
            if full > max_reach:
                z_allowed = feet[s]['ankle'][2] + math.sqrt(max(max_reach ** 2 - dxy ** 2, 0.0))
                need = max(need, Hjoint[s][2] - z_allowed)
        if need > 0 and P.get('pel_auto', True):
            pel_pos = pel_pos - np.array([0, 0, need])
            diag['pelvis_auto_drop'] = need
        # Hips: location so that its head lands on pel_pos
        iP = rig.parent[iH]
        loc = rig.rel_rot[iH].T @ (Q[iP].T @ (pel_pos - Pos[iP]) - rig.rel_off[iH])
        basis[iH] = rig.rel_rot[iH].T @ Q[iP].T @ Q_h
        Q[iH] = Q_h
        Pos[iH] = Pos[iP] + Q[iP] @ (rig.rel_off[iH] + rig.rel_rot[iH] @ loc)
        hips_loc = loc
        # ---- spine
        cr = P['chest_rot']
        Rc = np.eye(3)
        Rs_tot = R_pel
        for nm, w in zip(('Spine', 'Chest', 'UpperChest'), SPINE_W):
            Rc = Rc @ R_ypr(cr, w)
            i = ix[nm]
            put(i, R_pel @ Rc @ rig.Rrest[i])
        R_chest = R_pel @ R_ypr(cr, 1.0)            # chest frame (no rest-bone orientation)
        iNeck, iHead = ix['Neck'], ix['Head']
        # head: yaw / pitch relative to chest
        if P.get('gaze') is not None:
            # first place neck with zero relative rotation to find the head position
            put(iNeck, R_chest @ rig.Rrest[iNeck])
            put(iHead, R_chest @ rig.Rrest[iHead])
            hp = Pos[iHead].copy()
            g = O + a2w(np.array(P['gaze'], float))
            dvec = unit(g - (hp + np.array([0, 0, 0.07])))
            c_ = w2a(R_chest.T @ dvec)
            yaw = math.degrees(math.atan2(c_[0], c_[1]))
            pitch = math.degrees(math.atan2(-c_[2], math.hypot(c_[0], c_[1])))
            yaw = max(-75.0, min(75.0, yaw))
            pitch = max(-40.0, min(50.0, pitch))
            hr = [yaw, pitch, float(P['head_rot'][2])]
        else:
            hr = list(P['head_rot'])
        R_neck = R_chest @ R_ypr(hr, 0.4)
        put(iNeck, R_neck @ rig.Rrest[iNeck])
        R_head = R_chest @ R_ypr(hr, 1.0)
        put(iHead, R_head @ rig.Rrest[iHead])
        # ---- legs
        for s in 'LR':
            key = 'lf' if s == 'L' else 'rf'
            Sd = 'Left' if s == 'L' else 'Right'
            ft = feet[s]
            iU, iLo, iFo, iTo = ix[f'{Sd}UpperLeg'], ix[f'{Sd}LowerLeg'], ix[f'{Sd}Foot'], ix[f'{Sd}Toes']
            hip = Pos[iH] + Q[iH] @ rig.rel_off[iU]
            # knee pole: foot forward direction rotated outwards by `knee` degrees
            out = float(P[f'{key}_knee'])
            sign = 1.0 if s == 'R' else -1.0                  # outwards: right knee towards the right
            fwd_foot = R_yaw(ft['yaw'] + sign * out) @ F_W
            knee, ankle, u_, pp, short = self._leg_ik(hip, ft['ankle'], fwd_foot, self.t_len, self.s_len)
            N = unit(np.cross(u_, pp))                        # hinge axis (legs: +)
            t_dir = unit(knee - hip)
            s_dir = unit(ankle - knee)
            Qu = np.stack([N, t_dir, np.cross(N, t_dir)], 1)
            Ql = np.stack([N, s_dir, np.cross(N, s_dir)], 1)
            put(iU, Qu)
            put(iLo, Ql)
            put(iFo, ft['Rfoot'] @ rig.Rrest[iFo])
            put(iTo, ft['Ry'] @ rig.Rrest[iTo])
            diag[f'{key}_short'] = short
            diag[f'{key}_knee_flex_deg'] = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(t_dir, s_dir))))))
            diag[f'{key}_ankle'] = ankle
            diag[f'{key}_ball'] = ft['ball']
        # ---- arms: racket first (right arm drives it), clavicles from the targets
        racket = self._solve_arms(P, Q, Pos, put, basis, diag, R_chest)
        # ---- fingers
        self._fingers(P, basis, diag)
        info = dict(diag)
        info.update(racket)
        return basis, hips_loc, info

    # ------------------------------------------------------------------------------------------ arms + clavicles + racket
    def _arm_ik(self, s, S, W, pole_v):
        """two-bone arm IK: returns dict(E, Qu, Ql, short, W, flex)."""
        a, b = self.a_u, self.a_f
        d = W - S
        L = np.linalg.norm(d)
        max_r = (a + b) * 0.9985
        short = 0.0
        if L > max_r:
            short = L - max_r
            d = unit(d) * max_r
            L = max_r
            W = S + d
        min_r = max(abs(a - b) + 0.01, self.min_wrist_r)          # a hand cannot fold into the shoulder: the elbow stops at ~125 degrees of flexion
        near = 0.0
        if L < min_r:
            near = min_r - L
            d = unit(d) * min_r if L > 1e-4 else np.array([0.0, -1.0, -0.4]) / math.sqrt(1.16) * min_r
            L = min_r
            W = S + d
        u_ = d / L
        pp = self._pole_perp(s, pole_v, u_)
        cosA = (a * a + L * L - b * b) / (2 * a * L)
        A_ = math.acos(max(-1.0, min(1.0, cosA)))
        E = S + a * (u_ * math.cos(A_) + pp * math.sin(A_))
        N = -unit(np.cross(u_, pp))                        # arms: hinge axis sign (-)
        u_dir = unit(E - S)
        f_dir = unit(W - E)
        Qu = np.stack([N, u_dir, np.cross(N, u_dir)], 1)
        Ql = np.stack([N, f_dir, np.cross(N, f_dir)], 1)
        return dict(E=E, Qu=Qu, Ql=Ql, short=short, near=near, W=W, u_dir=u_dir, f_dir=f_dir, u_=u_)

    def _arm_ik_batch(self, S, W, pole):
        """vectorised two-bone arm IK over leading axes: S (3,), W (..., 3), pole (..., 3) -> Ql (..., 3, 3), E, short, near (same maths as _arm_ik)."""
        a, b = self.a_u, self.a_f
        d = W - S
        L = np.linalg.norm(d, axis=-1)
        max_r = (a + b) * 0.9985
        min_r = max(abs(a - b) + 0.01, self.min_wrist_r)
        short = np.maximum(L - max_r, 0.0)
        near = np.maximum(min_r - L, 0.0)
        Lc = np.clip(L, min_r, max_r)
        u = d / np.maximum(L, 1e-9)[..., None]
        Wc = S + u * Lc[..., None]
        pp = pole - np.sum(pole * u, axis=-1, keepdims=True) * u
        pp = pp / np.maximum(np.linalg.norm(pp, axis=-1, keepdims=True), 1e-9)
        cosA = (a * a + Lc * Lc - b * b) / (2 * a * Lc)
        A_ = np.arccos(np.clip(cosA, -1.0, 1.0))
        E = S + a * (u * np.cos(A_)[..., None] + pp * np.sin(A_)[..., None])
        N = -np.cross(u, pp)
        N = N / np.maximum(np.linalg.norm(N, axis=-1, keepdims=True), 1e-9)
        f = Wc - E
        f = f / np.maximum(np.linalg.norm(f, axis=-1, keepdims=True), 1e-9)
        Ql = np.stack([N, f, np.cross(N, f)], axis=-1)
        return Ql, E, short, near

    def _wrist_dev(self, Ql, Qh, R0):
        """(swing, twist) in radians of the hand relative to the bind relation with the forearm."""
        D = (Ql.T @ Qh) @ R0.T
        q = kin.mat_to_quat(D)
        if q[0] < 0:
            q = -q
        w, x, y, z = q
        tw = np.array([w, 0.0, y, 0.0])
        n = np.linalg.norm(tw)
        tw = tw / n if n > 1e-12 else np.array([1.0, 0, 0, 0])
        sw = kin.qmul(q, kin.qconj(tw))
        return 2.0 * math.atan2(np.linalg.norm(sw[1:]), sw[0]), 2.0 * math.atan2(tw[2], tw[0])

    def _solve_arms(self, P, Q, Pos, put, basis, diag, R_chest):
        rig = self.rig
        ix = rig.idx
        O = self.O
        iUC = ix['UpperChest']
        out = {}

        # all arm channels are written in the CHEST frame (r, f, u of the upper body, whatever its yaw / lean): cw() maps them to world
        def cw(v):
            return R_chest @ a2w(np.asarray(v, float))
        # racket orientation is written in the STANCE frame (what the camera sees); hand / racket positions are chest-relative
        shaft = unit(a2w(np.asarray(P['rk_shaft'], float)))
        face = a2w(np.asarray(P['rk_face'], float))
        R_rk0 = frame_from_axes(shaft, face)
        face_n = R_rk0[:, 2]
        R0 = {s: rig.Rrest[ix[('Left' if s == 'L' else 'Right') + 'LowerArm']].T @ rig.Rrest[ix[('Left' if s == 'L' else 'Right') + 'Hand']] for s in 'LR'}

        def clavicle_and_shoulder(s, target_dir_chest, L):
            """set the clavicle bone for side s from the direction of the hand target (chest frame, authoring axes); returns the shoulder joint."""
            Sd = 'Left' if s == 'L' else 'Right'
            iC, iU = ix[f'{Sd}Shoulder'], ix[f'{Sd}UpperArm']
            cr = target_dir_chest
            elev = math.degrees(math.acos(max(-1.0, min(1.0, -cr[2]))))
            e = min(24.0, 0.42 * max(0.0, elev - 55.0))
            q = 11.0 * max(-0.6, min(1.0, cr[1])) * min(1.0, L / self.A_arm) + (3.0 if elev > 100 else 0.0)
            sg_e = 1.0 if s == 'L' else -1.0
            sg_q = -1.0 if s == 'L' else 1.0
            Rcl = R_chest @ (rz(math.radians(sg_q * q)) @ axis_angle(F_W, math.radians(sg_e * e))) @ R_chest.T
            put(iC, Rcl @ (Q[iUC] @ rig.rel_rot[iC]))
            return Pos[iC] + Q[iC] @ rig.rel_off[iU], (e, q)

        # chest centre (midpoint of the two shoulder joints carried by the upper chest)
        ucr = rig.Rrest[iUC]
        c_off = ucr.T @ (0.5 * (rig.J['shoulder_L'] + rig.J['shoulder_R']) - rig.hrest[iUC])
        C_ctr = Pos[iUC] + Q[iUC] @ c_off
        out['chest_center'] = C_ctr
        shoulder_half = float(np.linalg.norm(rig.J['shoulder_L'] - rig.J['shoulder_R'])) / 2.0
        att = float(P['l_attach'])
        att0 = att
        g = float(P['l_grip'])
        T_att = self._lerp_T(self.T_hl_throat, self.T_hl_handle, g)
        # arm targets are CHEST-CENTRE relative (A units); the right-shoulder / left-shoulder offsets are applied here
        l_rel_c = np.array(P['l_hand'], float) * self.A_arm
        palm = unit(cw(P['l_palm']))
        rk_rel_c = np.array(P['rk_pos'], float) * self.A_arm
        w_abs = float(P.get('rk_abs', 0.0))
        sweet_abs = P.get('rk_sweet')

        def pole_vec(pole, s, u_):
            return self._auto_pole(s, u_) if pole is None else unit(cw(pole))

        def right_origin(R_rk):
            if P.get('r_wrist_world') is not None:
                return np.asarray(P['r_wrist_world'],float) + (R_rk @ self.R_rh.T) @ self.t_rh
            o = C_ctr + cw(rk_rel_c)
            if sweet_abs is not None and w_abs > 0.0:
                grip_abs = O + a2w(np.asarray(sweet_abs, float)) - R_rk @ self.head_center
                o = (1.0 - w_abs) * o + w_abs * grip_abs
            return o

        # ---- pass 0: clavicles from the nominal targets
        clav = {}
        S_ = {}
        for s in 'LR':
            if s == 'R':
                Wt = right_origin(R_rk0) - (R_rk0 @ self.R_rh.T) @ self.t_rh
            else:
                Wt = C_ctr + cw(l_rel_c)
            sh0 = C_ctr + cw([(1.0 if s == 'R' else -1.0) * shoulder_half, 0.0, 0.0])
            S_[s], clav[s] = clavicle_and_shoulder(s, w2a(R_chest.T @ unit(Wt - sh0)), float(np.linalg.norm(Wt - sh0)))
        # ---- right arm.  rk_mode 'fit': search the elbow swivel + the three wrist angles for the feasible racket orientation nearest to the commanded one
        # (used at the keys that carry a racket intent); 'fixed': use the interpolated rk_swivel / rk_wrist (every other frame).
        wfw = P.get('rk_w', [0.4, 1.0])
        wf, ws = float(wfw[0]), float(wfw[1])
        mode = P.get('rk_mode', 'fit')
        R_rk = R_rk0
        S_R = S_['R']
        st = self.state['R']

        def transported(prev, u_, s, u_prev=None):
            """elbow reference direction perpendicular to the arm axis u_: the previous frame's one carried over (parallel transport, so it never jumps),
            the automatic pole at the start of a sequence."""
            if prev is None:
                return self._auto_pole(s, u_)
            pp = prev - np.dot(prev, u_) * u_
            n = float(np.linalg.norm(pp))
            if n < 0.2:
                return self._auto_pole(s, u_)
            # leak: a small pull toward the natural direction (its weight vanishes smoothly where that direction is parallel to the arm axis, and while the
            # arm axis does not move), so the carried-over reference cannot wind up but a held pose stays still
            vn = self._natural_vec(s)
            pn = vn - np.dot(vn, u_) * u_
            moved = 1.0 if u_prev is None else min(1.0, math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(u_prev, u_)))))) / 15.0)
            q = pp / n + 0.35 * moved * pn
            nq = float(np.linalg.norm(q))
            return q / nq if nq > 1e-6 else pp / n

        def rbase(u_):
            if P.get('r_pole_w') is not None:
                return unit(np.asarray(P['r_pole_w'], float))
            if P['r_elbow'] is not None:
                return pole_vec(P['r_elbow'], 'R', u_)
            return transported(st.get('pole'), u_, 'R', st.get('axis'))

        def rot_pole(p0, u_, phi_deg):
            pp = self._pole_perp('R', p0, u_)
            a = math.radians(phi_deg)
            return math.cos(a) * pp + math.sin(a) * np.cross(u_, pp)

        def torso_pen(E):
            c_ = w2a(R_chest.T @ (E - C_ctr))
            if abs(c_[2]) > 0.40:
                return 0.0
            q = (c_[0] / self.torso_a) ** 2 + (c_[1] / self.torso_b) ** 2
            return 0.0 if q >= 1.25 ** 2 else ((1.25 ** 2 - q) * 6.0) ** 2

        w_pr = float(P.get('prior_w', 0.08)) if st['wr'] is not None else 0.0

        def eval_phi(phi, wr_fixed=None, coarse=False):
            Rk = R_rk0
            cst = 0.0
            for it in range(3 if wr_fixed is None else 4):
                Qh = Rk @ self.R_rh.T
                o = right_origin(Rk)
                W = o - Qh @ self.t_rh
                u0 = unit(W - S_R)
                p0 = rbase(u0)
                ik = self._arm_ik('R', S_R, W, rot_pole(p0, u0, phi))
                if wr_fixed is None:
                    D, ang_, errs, cst = self._fit_wrist(ik['Ql'], R0['R'], R_rk0, wf, ws, prev=st['wr'], w_prev=w_pr, refine=not coarse, box=P.get('rk_wbox'))
                else:
                    ang_ = np.asarray(wr_fixed, float)
                    D = self._wrist_D(*ang_)
                    errs = None
                Rk = (ik['Ql'] @ D @ R0['R']) @ self.R_rh
            if wr_fixed is None:
                cst += 0.30 * (phi / 50.0) ** 2 + torso_pen(ik['E']) + (ik['short'] * 40.0) ** 2 + w_pr * ((phi - st['phi']) / 25.0) ** 2
            return cst, Rk, ang_, errs, ik

        if mode == 'fixed' and P.get('rk_swivel') is not None:
            phi_b = float(P['rk_swivel'])
            Qh0 = R_rk0 @ self.R_rh.T
            o0 = right_origin(R_rk0)
            W0 = o0 - Qh0 @ self.t_rh
            u00 = unit(W0 - S_R)
            ik_b = self._arm_ik('R', S_R, W0, rot_pole(rbase(u00), u00, phi_b))
            Rk_b = R_rk0
            ang_b = [0.0, 0.0, 0.0]
        elif mode == 'fit' and P.get('rk_phi_fixed') is not None:
            phi_b = float(P['rk_phi_fixed'])
            c_b, Rk_b, ang_b, errs_b, ik_b = eval_phi(phi_b)
        elif mode == 'anchor':
            # pinned-sweet-spot (contact) frame: the racket position and orientation are coupled through the 40 cm lever, so the search is done over the
            # RACKET ORIENTATION itself (sampled around the commanded one) and the swivel; everything else follows explicitly (sweet spot -> grip ->
            # wrist joint -> arm IK -> the wrist angles that orientation needs), the wrist box enters as a penalty.  No fixed-point iteration.
            pole0 = unit(np.asarray(P['r_pole_w'], float))
            o_nom = C_ctr + cw(rk_rel_c)
            sweet_w = None if sweet_abs is None else O + a2w(np.asarray(sweet_abs, float))
            _W0 = right_origin(R_rk0) - (R_rk0 @ self.R_rh.T) @ self.t_rh
            _u0 = unit(_W0 - S_R)
            nat_off = self._nat_offset('R', pole0, _u0)
            lo_b = np.array([self.W_FLEX[0], self.W_DEV[0], self.W_TWIST[0]])
            hi_b = np.array([self.W_FLEX[1], self.W_DEV[1], self.W_TWIST[1]])

            def pose_of(R, phi):
                """explicit pose for a racket orientation R (3,3) and swivel phi: returns (ik, wrist angles deg)."""
                Qh_ = R @ self.R_rh.T
                if sweet_w is not None and w_abs > 0.0:
                    o_ = (1.0 - w_abs) * o_nom + w_abs * (sweet_w - R @ self.head_center)
                else:
                    o_ = o_nom
                W_ = o_ - Qh_ @ self.t_rh
                u_ = unit(W_ - S_R)
                ik_ = self._arm_ik('R', S_R, W_, rot_pole(pole0, u_, phi))
                Dp = (ik_['Ql'].T @ Qh_) @ R0['R'].T
                f_ = math.degrees(math.asin(max(-1.0, min(1.0, -Dp[1, 2]))))
                d_ = math.degrees(math.atan2(Dp[1, 0], Dp[1, 1]))
                t_ = math.degrees(math.atan2(Dp[0, 2], Dp[2, 2]))
                return ik_, np.array([f_, d_, t_])

            def cost_of(R, phi):
                ik_, w_ = pose_of(R, phi)
                e_s = math.degrees(math.acos(max(-1.0, min(1.0, float(R[:, 1] @ R_rk0[:, 1])))))
                e_f = math.degrees(math.acos(max(-1.0, min(1.0, float(R[:, 2] @ R_rk0[:, 2])))))
                exc = np.maximum(w_ - hi_b, 0.0) + np.maximum(lo_b - w_, 0.0)
                cst_ = (ws * (e_s / 25.0) ** 2 + wf * (e_f / 25.0) ** 2 + 0.00035 * float(np.sum(w_ ** 2)) + 0.30 * ((phi + nat_off) / 50.0) ** 2 + 0.4 * ((phi + nat_off) / 100.0) ** 4
                        + torso_pen(ik_['E']) + (ik_['short'] * 40.0) ** 2 + (ik_['near'] * 40.0) ** 2 + float(np.sum((exc / 6.0) ** 2)))
                return cst_, e_s, e_f, ik_, w_

            # coarse stage: rotation vectors on a grid (|v| <= 80 deg) x swivel grid, explicit and vectorised
            gv = np.arange(-80.0, 80.1, 16.0)
            VV = np.array([(a_, b_, c_) for a_ in gv for b_ in gv for c_ in gv if a_ * a_ + b_ * b_ + c_ * c_ <= 82.0 ** 2])
            Rs = np.array([axis_angle(unit(v), math.radians(float(np.linalg.norm(v)))) if np.linalg.norm(v) > 1e-9 else np.eye(3) for v in VV]) @ R_rk0
            if P.get('anchor_phi') is not None:
                _c0, _w0 = float(P['anchor_phi']), float(P.get('anchor_phi_win', 40.0))
                PHa = np.arange(_c0 - _w0, _c0 + _w0 + 0.1, 10.0)
            else:
                PHa = np.arange(-180.0, 180.1, 20.0)
            best_list = []
            Qh_s = Rs @ self.R_rh.T
            if sweet_w is not None and w_abs > 0.0:
                o_s = (1.0 - w_abs) * o_nom + w_abs * (sweet_w - Rs @ self.head_center)
            else:
                o_s = np.broadcast_to(o_nom, (len(Rs), 3))
            W_s = o_s - np.einsum('nab,b->na', Qh_s, self.t_rh)
            u_s = W_s - S_R
            u_s = u_s / np.maximum(np.linalg.norm(u_s, axis=-1, keepdims=True), 1e-9)
            pp_s = pole0 - np.sum(pole0 * u_s, axis=-1, keepdims=True) * u_s
            pp_s = pp_s / np.maximum(np.linalg.norm(pp_s, axis=-1, keepdims=True), 1e-9)
            ash = np.degrees(np.arccos(np.clip(Rs[:, :, 1] @ R_rk0[:, 1], -1.0, 1.0)))
            afc = np.degrees(np.arccos(np.clip(Rs[:, :, 2] @ R_rk0[:, 2], -1.0, 1.0)))
            cost_all = np.zeros((len(PHa), len(Rs)))
            for jj, ph in enumerate(PHa):
                pole_j = math.cos(math.radians(ph)) * pp_s + math.sin(math.radians(ph)) * np.cross(u_s, pp_s)
                Ql_b, E_b, sh_b, nr_b = self._arm_ik_batch(S_R, W_s, pole_j)
                Dp = np.swapaxes(Ql_b, -1, -2) @ Qh_s @ R0['R'].T
                f_ = np.degrees(np.arcsin(np.clip(-Dp[:, 1, 2], -1.0, 1.0)))
                d_ = np.degrees(np.arctan2(Dp[:, 1, 0], Dp[:, 1, 1]))
                t_ = np.degrees(np.arctan2(Dp[:, 0, 2], Dp[:, 2, 2]))
                w_ = np.stack([f_, d_, t_], axis=-1)
                exc = np.maximum(w_ - hi_b, 0.0) + np.maximum(lo_b - w_, 0.0)
                cq0 = (E_b - C_ctr) @ R_chest
                cq = np.stack([-cq0[:, 0], -cq0[:, 1], cq0[:, 2]], axis=-1)
                qq = (cq[:, 0] / self.torso_a) ** 2 + (cq[:, 1] / self.torso_b) ** 2
                tpen = np.where((np.abs(cq[:, 2]) > 0.40) | (qq >= 1.25 ** 2), 0.0, ((1.25 ** 2 - qq) * 6.0) ** 2)
                cost_all[jj] = (ws * (ash / 25.0) ** 2 + wf * (afc / 25.0) ** 2 + 0.00035 * np.sum(w_ ** 2, axis=-1) + 0.30 * ((ph + nat_off) / 50.0) ** 2 + 0.4 * ((ph + nat_off) / 100.0) ** 4
                                + tpen + (sh_b * 40.0) ** 2 + (nr_b * 40.0) ** 2 + np.sum((exc / 6.0) ** 2, axis=-1))
            order = np.argsort(cost_all, axis=None)[:10]
            best = None
            for flat in order:
                jj, ni = np.unravel_index(int(flat), cost_all.shape)
                v = VV[ni].copy()
                phi_c = float(PHa[jj])
                Rc = Rs[ni].copy()
                cb, e_s, e_f, ik_c, w_c = cost_of(Rc, phi_c)
                for step in (8.0, 4.0, 2.0, 1.0):
                    improved = True
                    n_it = 0
                    while improved and n_it < 10:
                        improved = False
                        n_it += 1
                        for k_ in range(4):
                            for sgn in (-1.0, 1.0):
                                v2, ph2 = v.copy(), phi_c
                                if k_ < 3:
                                    v2[k_] += sgn * step
                                else:
                                    ph2 += sgn * step
                                nv = float(np.linalg.norm(v2))
                                R2 = (axis_angle(v2 / nv, math.radians(nv)) if nv > 1e-9 else np.eye(3)) @ R_rk0
                                c2, es2, ef2, ik2, w2 = cost_of(R2, ph2)
                                if c2 < cb - 1e-9:
                                    cb, v, phi_c, Rc, e_s, e_f, ik_c, w_c = c2, v2, ph2, R2, es2, ef2, ik2, w2
                                    improved = True
                if best is None or cb < best[0]:
                    best = (cb, phi_c, w_c.copy(), Rc.copy(), e_s, e_f, ik_c['short'])
            diag['anchor'] = dict(phi=float(best[1]), wrist=best[2], cost=float(best[0]), shaft_err=float(best[4]), face_err=float(best[5]), short=float(best[6]),
                                  resid=0.0, shaft=w2a(best[3][:, 1]), face=w2a(best[3][:, 2]))
            phi_b = float(best[1])
            c_b, Rk_b, ang_b, errs_b, ik_b = eval_phi(phi_b, coarse=True)
        elif mode == 'cands2':
            # arm frames of every swivel candidate for the wrist-grid Viterbi tracker (clipkit.Clip.track): the wrist joint W is placed for the GUESS
            # orientation (the commanded one on the first pass, the achieved one on the second), the tracker scores every (swivel, wrist) cell itself.
            gs, gf = P.get('rk_guess_shaft'), P.get('rk_guess_face')
            Rg = R_rk0 if gs is None else frame_from_axes(unit(a2w(np.asarray(gs, float))), a2w(np.asarray(gf, float)))
            Wg = right_origin(Rg) - (Rg @ self.R_rh.T) @ self.t_rh
            u0g = unit(Wg - S_R)
            p0g = rbase(u0g)
            PH = np.asarray(P.get('cands_phis', np.arange(-180.0, 180.1, 10.0)), float)
            Qls, shs, trs = [], [], []
            for phi in PH:
                ik_ = self._arm_ik('R', S_R, Wg, rot_pole(p0g, u0g, float(phi)))
                Qls.append(ik_['Ql'])
                shs.append(ik_['short'])
                trs.append(torso_pen(ik_['E']))
            diag['cands2'] = dict(phis=PH, Ql=np.array(Qls), short=np.array(shs), torso=np.array(trs), R0=R0['R'].copy(), Rk_cmd=R_rk0.copy(), wf=wf, ws=ws,
                                  pole=self._pole_perp('R', p0g, u0g), axis=u0g, nat_offset=self._nat_offset('R', p0g, u0g))
            phi_b = 0.0
            c_b, Rk_b, ang_b, errs_b, ik_b = eval_phi(phi_b, coarse=True)
        elif mode == 'cands':
            cands = []
            for phi in np.arange(-80.0, 80.1, 10.0):
                c1, Rk1, ang1, errs1, ik1 = eval_phi(float(phi), coarse=True)
                cands.append(dict(phi=float(phi), cost=float(c1), shaft=w2a(Rk1[:, 1]), face=w2a(Rk1[:, 2]), wrist=np.array(ang1, float), short=float(ik1['short'])))
            diag['cands'] = cands
            kbest = int(np.argmin([c_['cost'] for c_ in cands]))
            phi_b = cands[kbest]['phi']
            c_b, Rk_b, ang_b, errs_b, ik_b = eval_phi(phi_b)
        else:
            rng_ = float(P.get('phi_range', 100.0))
            res = [(eval_phi(phi), phi) for phi in np.arange(-rng_, rng_ + 0.1, 20.0)]
            (c_b, Rk_b, ang_b, errs_b, ik_b), phi_b = min(res, key=lambda x: x[0][0])
            for step in (8.0, 3.0, 1.0):
                for sgn in (-1.0, 1.0):
                    for _ in range(4):
                        r2 = eval_phi(phi_b + sgn * step)
                        if r2[0] < c_b - 1e-9:
                            (c_b, Rk_b, ang_b, errs_b, ik_b) = r2
                            phi_b += sgn * step
                        else:
                            break
        R_rk = Rk_b
        diag['rk_fit_flex_dev_twist'] = [float(x) for x in ang_b]
        diag['rk_swivel_deg'] = float(phi_b)
        st['phi'], st['wr'] = phi_b, np.array(ang_b, float)
        fit = 0.0 if mode == 'fixed' else 1.0
        u_fin = unit(ik_b['W'] - S_R)
        p0_fin = rbase(u_fin)
        diag['r_pole_w'] = self._pole_perp('R', p0_fin, u_fin)
        diag['r_axis_w'] = u_fin
        st['pole'] = diag['r_pole_w']
        st['axis'] = u_fin
        swivel_pole_R = (lambda u_, p0=p0_fin, ph=phi_b: rot_pole(p0, u_, ph))
        Q_hand_R = R_rk @ self.R_rh.T

        tw_rec = {}

        def solve_side(s, W_target, Qh_target, pole, limit_wrist=True):
            Sd = 'Left' if s == 'L' else 'Right'
            iC, iU, iLo, iH_ = ix[f'{Sd}Shoulder'], ix[f'{Sd}UpperArm'], ix[f'{Sd}LowerArm'], ix[f'{Sd}Hand']
            S, clv = clavicle_and_shoulder(s, w2a(R_chest.T @ unit(W_target - C_ctr)), float(np.linalg.norm(W_target - C_ctr)))
            u_t = unit(W_target - S)
            pv = pole(u_t) if callable(pole) else pole_vec(pole, s, u_t)
            ik = self._arm_ik(s, S, W_target, pv)
            Qh = Qh_target(ik) if callable(Qh_target) else Qh_target
            Qh_target = Qh
            put(iU, ik['Qu'])
            if limit_wrist:
                Qh, clamp_deg = self._limit_wrist(ik['Ql'], Qh, rig.Rrest[iLo].T @ rig.Rrest[iH_], lim=(limit_wrist if isinstance(limit_wrist, tuple) else None))
            else:
                clamp_deg = 0.0
            sg, tw = self._wrist_dev(ik['Ql'], Qh, R0[s])
            # forearm pronation / supination is shared between the forearm bone (rolls about its own axis; the wrist joint lies on that axis, so nothing
            # moves) and the hand: the racket arm can then turn the face further than a hand alone could, without a candy-wrapper wrist.  The share fades
            # to zero towards +-180 degrees so that it is continuous where the principal twist angle wraps.
            a_tw = abs(tw)
            fade = 1.0 if a_tw <= math.radians(120.0) else (0.0 if a_tw >= math.pi else 0.5 * (1.0 + math.cos(math.pi * (a_tw - math.radians(120.0)) / math.radians(60.0))))
            roll = float(np.clip(self.ROLL_FRAC * tw * fade, -math.radians(self.ROLL_MAX), math.radians(self.ROLL_MAX)))
            put(iLo, ik['Ql'] @ ry(roll))
            put(iH_, Qh)
            diag[f'{s}_forearm_roll_deg'] = math.degrees(roll)
            diag[f'{s}_arm_short'] = ik['short']
            diag[f'{s}_arm_near'] = ik['near']
            diag[f'{s}_elbow_flex_deg'] = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(ik['u_dir'], ik['f_dir']))))))
            diag[f'{s}_wrist_swing_deg'] = math.degrees(sg)
            diag[f'{s}_wrist_twist_deg'] = math.degrees(tw)
            diag[f'{s}_wrist_clamp_deg'] = clamp_deg
            diag[f'{s}_wrist_swing_pre_deg'] = math.degrees(self._wrist_dev(ik['Ql'], Qh_target, R0[s])[0])
            diag[f'{s}_clav'] = clv
            diag[f'{s}_shoulder'] = S.copy()
            diag[f'{s}_elbow'] = ik['E'].copy()
            return S

        # ---- right arm drives the racket; the left hand follows it when attached.  If the two-hand hold is out of reach the racket is shifted
        # towards the left shoulder by the shortfall (reported in `racket_shift`; authored keys should not need it).
        shift = np.zeros(3)
        for it in range(5):
            o = right_origin(R_rk) + shift
            W_R = o - Q_hand_R @ self.t_rh
            solve_side('R', W_R, Q_hand_R, swivel_pole_R if swivel_pole_R is not None else P['r_elbow'], limit_wrist=((math.radians(112.0), math.radians(155.0)) if (mode == 'fixed' and not P.get('rk_nolim')) else False))
            iHR = ix['RightHand']
            rk_origin = Pos[iHR] + Q[iHR] @ self.t_rh
            Rrk_world = Q[iHR] @ self.R_rh
            M_rk = np.eye(4)
            M_rk[:3, :3] = Rrk_world
            M_rk[:3, 3] = rk_origin
            M_att = M_rk @ T_att
            W_free = C_ctr + cw(l_rel_c)
            # a hand that is letting go (or taking hold) only follows the racket as far as its arm reaches: the attach fraction is limited to what the left
            # arm can hold, instead of dragging the racket back towards the body (that shows as a one-frame jump of the racket)
            att = att0
            if 0.02 < att0 < 0.999:
                max_rL = (self.a_u + self.a_f) * 0.9985
                a_try = att0
                for _k in range(21):
                    pt = self._sph_blend(S_['L'], W_free, M_att[:3, 3], a_try)
                    if np.linalg.norm(pt - S_['L']) <= max_rL - 0.004:
                        break
                    a_try -= 0.05
                    if a_try <= 0.02:
                        a_try = 0.0
                        break
                att = max(a_try, 0.0)
            W_L = self._sph_blend(S_['L'], W_free, M_att[:3, 3], att)
            Rrest_lh = rig.Rrest[ix['LeftHand']]
            tau_rec = {}

            def free_hand(ik_):
                """relaxed free left hand: neutral wrist, the forearm pronates / supinates until the palm faces `palm` as well as a twist allows, the
                remaining misalignment is closed by at most 35 degrees of wrist flexion (continuous: no 180 degree ambiguity of a shortest-arc turn)."""
                Ql_ = ik_['Ql']
                v_loc = R0['L'] @ np.array([0.0, 0.0, 1.0])               # palm normal in the forearm frame at neutral wrist
                p_loc = Ql_.T @ palm
                if (p_loc[0] ** 2 + p_loc[2] ** 2) > 1e-4:
                    tau = math.atan2(p_loc[0], p_loc[2]) - math.atan2(v_loc[0], v_loc[2])
                    prev_tau = self.state['L'].get('tau')
                    if prev_tau is None:
                        tau = (tau + math.pi) % (2 * math.pi) - math.pi
                    else:                                                  # unwrap against the previous frame: no 360 degree flip when the palm turns past 180
                        tau = tau + 2 * math.pi * round((prev_tau - tau) / (2 * math.pi))
                    tau_rec['v'] = tau
                else:
                    tau = self.state['L'].get('tau') or 0.0
                    tau_rec['v'] = tau
                tau = max(-math.radians(125.0), min(math.radians(125.0), tau))
                Dt = ry(tau)
                a_ = Dt @ v_loc
                cs = float(np.dot(a_, p_loc))
                res = math.acos(max(-1.0, min(1.0, cs)))
                if res > 1e-4:
                    ax = np.cross(a_, p_loc)
                    nax = float(np.linalg.norm(ax))
                    Dr = axis_angle(ax / nax, min(res, math.radians(35.0))) if nax > 1e-6 else np.eye(3)
                else:
                    Dr = np.eye(3)
                return Ql_ @ (Dr @ Dt) @ R0['L']

            def hand_L(ik_):
                if att >= 0.999:
                    return M_att[:3, :3]
                Qf = free_hand(ik_)
                if att <= 0:
                    return Qf
                # blend the two wrist poses as (swing vector, forearm twist) pairs: a plain slerp between two orientations that are nearly opposite
                # (free hand vs grip) has no stable axis and flips the hand
                Ql_ = ik_['Ql']
                rv_f, tw_f = self._swing_twist((Ql_.T @ Qf) @ R0['L'].T)
                rv_g, tw_g = self._swing_twist((Ql_.T @ M_att[:3, :3]) @ R0['L'].T)
                tw_f = tw_g + ((tw_f - tw_g + math.pi) % (2 * math.pi) - math.pi)         # the twist blend takes the short way round
                return Ql_ @ self._from_swing_twist((1 - att) * rv_f + att * rv_g, (1 - att) * tw_f + att * tw_g) @ R0['L']

            def lbase(u_):
                if P['l_elbow'] is not None:
                    return pole_vec(P['l_elbow'], 'L', u_)
                return transported(self.state['L'].get('pole'), u_, 'L', self.state['L'].get('axis'))

            pole_L = lbase
            if att > 0.02:
                # left swivel: choose the elbow position that keeps the left wrist closest to neutral while it holds the racket; as the hand lets go the
                # swivel is faded out (g) so that the arm settles on the authored pole without a jump
                S_Lg = S_['L']
                u0 = unit(W_L - S_Lg)
                p0L = lbase(u0)
                stL = self.state['L']

                def rotL(p0, u_, phi_deg):
                    pp = self._pole_perp('L', p0, u_)
                    a_ = math.radians(phi_deg)
                    return math.cos(a_) * pp + math.sin(a_) * np.cross(u_, pp)

                def torso_penL(E):
                    c_ = w2a(R_chest.T @ (E - C_ctr))
                    if abs(c_[2]) > 0.40:
                        return 0.0
                    q = (c_[0] / self.torso_a) ** 2 + (c_[1] / self.torso_b) ** 2
                    return 0.0 if q >= 1.25 ** 2 else ((1.25 ** 2 - q) * 6.0) ** 2

                nat_offL = self._nat_offset('L', p0L, u0)

                def evalL_pure(phi):
                    ikl = self._arm_ik('L', S_Lg, W_L, rotL(p0L, unit(W_L - S_Lg), phi))
                    sg_, tw_ = self._wrist_dev(ikl['Ql'], hand_L(ikl), R0['L'])
                    return ((math.degrees(sg_) / 55.0) ** 2 + (math.degrees(tw_) / 80.0) ** 2 + 0.25 * ((phi + nat_offL) / 50.0) ** 2 + torso_penL(ikl['E']))

                def evalL(phi):
                    return evalL_pure(phi) + 0.6 * ((phi - stL['phi']) / 25.0) ** 2
                if P.get('l_swivel_fixed') is not None:              # chosen by the clip tracker (Viterbi over the whole clip)
                    phL = float(P['l_swivel_fixed'])
                elif P.get('l_mode') == 'cands':
                    phis_L = np.arange(-100.0, 100.1, 5.0)
                    costs_L = np.array([evalL_pure(float(ph)) for ph in phis_L])
                    diag['candsL'] = dict(phis=phis_L, costs=costs_L, nat_off=nat_offL)
                    phL = float(phis_L[int(np.argmin(costs_L))])
                else:
                    resL = [(evalL(ph), ph) for ph in np.arange(-100.0, 100.1, 20.0)]
                    cL, phL = min(resL)
                    for step in (8.0, 3.0, 1.0):
                        for sgn in (-1.0, 1.0):
                            for _ in range(4):
                                c2 = evalL(phL + sgn * step)
                                if c2 < cL - 1e-9:
                                    cL, phL = c2, phL + sgn * step
                                else:
                                    break
                stL['phi'] = phL
                gfade = min(1.0, att / 0.5)
                gfade = gfade * gfade * (3.0 - 2.0 * gfade)
                phL_eff = phL * gfade
                diag['L_swivel_deg'] = float(phL_eff)
                pole_L = (lambda u_, p0=p0L, ph=phL_eff: rotL(p0, u_, ph))
            # left wrist limit: free hand clamped to the anatomical box; it relaxes continuously while the hand takes the racket (grip pose is exact from att 0.5)
            if att >= 0.5:
                lim_L = False
            else:
                ga = att / 0.5
                ga = ga * ga * (3.0 - 2.0 * ga)
                lim_L = (self.WRIST_SWING + math.radians(95.0) * ga, self.WRIST_TWIST + math.radians(95.0) * ga)
            S_Lf = solve_side('L', W_L, hand_L, pole_L, limit_wrist=lim_L)
            uLf = unit(W_L - S_Lf)
            pole_L_commit = self._pole_perp('L', lbase(uLf), uLf)
            if att > 0.5 and diag.get('L_arm_short', 0.0) > 1.5e-3 and P.get('rk_auto', True):
                shift = shift + unit(S_Lf - M_att[:3, 3]) * diag['L_arm_short'] * 1.02
            elif att > 0.5 and diag.get('L_arm_near', 0.0) > 1.5e-3 and P.get('rk_auto', True):
                shift = shift - unit(S_Lf - M_att[:3, 3]) * diag['L_arm_near'] * 1.02
            else:
                break
        self.state['L']['pole'] = pole_L_commit
        self.state['L']['axis'] = uLf
        if tau_rec.get('v') is not None:
            self.state['L']['tau'] = tau_rec['v']
        P['l_attach'] = att                                   # the fingers follow the effective attach fraction
        out['rk_origin'] = rk_origin
        out['rk_R'] = Rrk_world
        out['sweet'] = rk_origin + Rrk_world @ self.head_center
        out['sweet_a'] = w2a(out['sweet'] - O)
        out['grip_a'] = w2a(rk_origin - O)
        out['shaft_a'] = w2a(Rrk_world[:, 1])
        out['face_a'] = w2a(Rrk_world[:, 2])
        out['shaft_err_deg'] = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(Rrk_world[:, 1], R_rk0[:, 1]))))))
        out['face_err_deg'] = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(Rrk_world[:, 2], R_rk0[:, 2]))))))
        out['shaft_cmd_a'] = w2a(R_rk0[:, 1])
        out['face_cmd_a'] = w2a(R_rk0[:, 2])
        # world-aligned (stance-frame) racket axes for reading the achieved orientation
        out['sweet_height'] = float(out['sweet'][2])
        out['racket_shift'] = float(np.linalg.norm(shift))
        out['rk_L_attached'] = att
        return out

    _WGRID = None
    W_FLEX = (-85.0, 85.0)
    W_DEV = (-50.0, 35.0)
    W_TWIST = (-150.0, 150.0)          # total pronation / supination: forearm roll (ROLL_FRAC of it) + hand twist
    ROLL_FRAC = 0.35
    ROLL_MAX = 52.0

    @classmethod
    def _wrist_grid(cls):
        if cls._WGRID is None:
            fl = np.arange(cls.W_FLEX[0], cls.W_FLEX[1] + 0.1, 5.0)
            dv = np.arange(cls.W_DEV[0], cls.W_DEV[1] + 0.1, 5.0)
            tw = np.arange(cls.W_TWIST[0], cls.W_TWIST[1] + 0.1, 10.0)
            F, Dv, T = np.meshgrid(fl, dv, tw, indexing='ij')
            ang = np.stack([F.ravel(), Dv.ravel(), T.ravel()], 1)
            cls._WGRID = (ang, np.array([cls._wrist_D(*a) for a in ang]))
        return cls._WGRID

    @staticmethod
    def _wrist_D(flex, dev, twist):
        """hand rotation relative to its neutral hold, in the forearm frame: twist (pronation) about Y, then flexion about X, deviation about Z."""
        return ry(math.radians(twist)) @ rx(math.radians(flex)) @ rz(math.radians(dev))

    def _fit_wrist(self, Ql, R0, Rk_cmd, wf, ws, reg=0.00035, prev=None, w_prev=0.0, refine=True, box=None):
        """nearest feasible racket orientation: best (flex, dev, twist) in the anatomical box; returns (D, angles, (shaft err, face err), cost).
        `box` (half widths in degrees around `prev`) keeps the search on the branch the tracker chose."""
        ang, Dg = self._wrist_grid()
        Qh_c = np.einsum('ij,njk->nik', Ql, Dg) @ R0
        Rk_c = Qh_c @ self.R_rh
        ash = np.degrees(np.arccos(np.clip(Rk_c[:, :, 1] @ Rk_cmd[:, 1], -1, 1)))
        afc = np.degrees(np.arccos(np.clip(Rk_c[:, :, 2] @ Rk_cmd[:, 2], -1, 1)))
        cost = ws * (ash / 25.0) ** 2 + wf * (afc / 25.0) ** 2 + reg * (ang ** 2).sum(1)
        if prev is not None and w_prev > 0:
            cost = cost + w_prev * (((ang - prev) / np.array([25.0, 15.0, 35.0])) ** 2).sum(1)
        if box is not None and prev is not None:
            cost = np.where((np.abs(ang - np.asarray(prev, float)) > np.asarray(box, float)).any(1), 1e9, cost)
        k = int(np.argmin(cost))
        best = ang[k].copy()
        pv = None if prev is None else np.asarray(prev, float)

        def c_of(a):
            D = self._wrist_D(*a)
            Rk = (Ql @ D @ R0) @ self.R_rh
            e_s = math.degrees(math.acos(max(-1.0, min(1.0, float(Rk[:, 1] @ Rk_cmd[:, 1])))))
            e_f = math.degrees(math.acos(max(-1.0, min(1.0, float(Rk[:, 2] @ Rk_cmd[:, 2])))))
            c = ws * (e_s / 25.0) ** 2 + wf * (e_f / 25.0) ** 2 + reg * float((a ** 2).sum())
            if pv is not None and w_prev > 0:
                c += w_prev * float((((a - pv) / np.array([25.0, 15.0, 35.0])) ** 2).sum())
            return c, e_s, e_f
        cb, es, ef = c_of(best)
        if not refine:
            return self._wrist_D(*best), best, (es, ef), cb
        lo = np.array([self.W_FLEX[0], self.W_DEV[0], self.W_TWIST[0]])
        hi = np.array([self.W_FLEX[1], self.W_DEV[1], self.W_TWIST[1]])
        if box is not None and prev is not None:
            lo = np.maximum(lo, np.asarray(prev, float) - np.asarray(box, float))
            hi = np.minimum(hi, np.asarray(prev, float) + np.asarray(box, float))
        for step in (2.0, 1.0, 0.5):
            improved = True
            n_it = 0
            while improved and n_it < 12:
                improved = False
                n_it += 1
                for j in range(3):
                    for sgn in (-1.0, 1.0):
                        a2 = best.copy()
                        a2[j] = min(hi[j], max(lo[j], a2[j] + sgn * step))
                        c2, e2s, e2f = c_of(a2)
                        if c2 < cb - 1e-9:
                            best, cb, es, ef = a2, c2, e2s, e2f
                            improved = True
        return self._wrist_D(*best), best, (es, ef), cb

    WRIST_SWING = math.radians(85.0)
    WRIST_TWIST = math.radians(150.0)

    @staticmethod
    def _swing_twist(D):
        """D = swing * twist(about the forearm axis Y): returns (swing rotation vector, twist angle)."""
        q = kin.mat_to_quat(D)
        if q[0] < 0:
            q = -q
        w, x, y, z = q
        tw = np.array([w, 0.0, y, 0.0])
        n = np.linalg.norm(tw)
        tw = tw / n if n > 1e-12 else np.array([1.0, 0, 0, 0])
        sw = kin.qmul(q, kin.qconj(tw))
        if sw[0] < 0:
            sw = -sw
        vec = sw[1:]
        vn = float(np.linalg.norm(vec))
        sig = 2.0 * math.atan2(vn, sw[0])
        rv = vec / vn * sig if vn > 1e-12 else np.zeros(3)
        return rv, 2.0 * math.atan2(tw[2], tw[0])

    @staticmethod
    def _from_swing_twist(rv, tau):
        ang = float(np.linalg.norm(rv))
        qs = np.concatenate([[math.cos(ang / 2)], rv / ang * math.sin(ang / 2)]) if ang > 1e-12 else np.array([1.0, 0, 0, 0])
        qt = np.array([math.cos(tau / 2), 0.0, math.sin(tau / 2), 0.0])
        return kin.quat_to_mat(kin.qmul(qs, qt))

    def _limit_wrist(self, Ql, Qh, R0, lim=None):
        lim_sw, lim_tw = lim if lim is not None else (self.WRIST_SWING, self.WRIST_TWIST)
        D = (Ql.T @ Qh) @ R0.T                       # deviation of the hand from its bind relation to the forearm, in the forearm frame
        q = kin.mat_to_quat(D)
        if q[0] < 0:
            q = -q
        w, x, y, z = q
        tw = np.array([w, 0.0, y, 0.0])
        n = np.linalg.norm(tw)
        tw = tw / n if n > 1e-12 else np.array([1.0, 0, 0, 0])
        sw = kin.qmul(q, kin.qconj(tw))
        tau = 2.0 * math.atan2(tw[2], tw[0])
        vec = sw[1:]
        vn = np.linalg.norm(vec)
        sigma = 2.0 * math.atan2(vn, sw[0])
        tau_c = max(-lim_tw, min(lim_tw, tau))
        sig_c = min(sigma, lim_sw)
        if abs(tau_c - tau) < 1e-9 and abs(sig_c - sigma) < 1e-9:
            return Qh, 0.0
        sw_c = np.concatenate([[math.cos(sig_c / 2)], (vec / vn if vn > 1e-12 else np.zeros(3)) * math.sin(sig_c / 2)])
        tw_c = np.array([math.cos(tau_c / 2), 0.0, math.sin(tau_c / 2), 0.0])
        D2 = kin.quat_to_mat(kin.qmul(sw_c, tw_c))
        Qh2 = Ql @ D2 @ R0
        ang = math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(D.T @ D2) - 1) / 2))))
        return Qh2, ang

    def _rot_to(self, a, b):
        a, b = unit(a), unit(b)
        c = float(np.dot(a, b))
        if c > 0.999999:
            return np.eye(3)
        if c < -0.999999:
            ax = unit(np.cross(a, [1, 0, 0]) if abs(a[0]) < 0.9 else np.cross(a, [0, 1, 0]))
            return axis_angle(ax, math.pi)
        ax = unit(np.cross(a, b))
        return axis_angle(ax, math.acos(c))

    def _lerp_T(self, A, B, t):
        M = np.eye(4)
        M[:3, :3] = slerp_mat(A[:3, :3], B[:3, :3], t)
        M[:3, 3] = (1 - t) * A[:3, 3] + t * B[:3, 3]
        return M

    @staticmethod
    def _sph_blend(S, A_, B_, t):
        """point between A_ (t=0) and B_ (t=1) that swings around the shoulder S (direction slerp, radius lerp) instead of cutting through the shoulder."""
        if t <= 0.0:
            return np.asarray(A_, float)
        if t >= 1.0:
            return np.asarray(B_, float)
        a, b = np.asarray(A_, float) - S, np.asarray(B_, float) - S
        ra, rb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
        if ra < 1e-6 or rb < 1e-6:
            return (1 - t) * np.asarray(A_, float) + t * np.asarray(B_, float)
        ua, ub = a / ra, b / rb
        ang = math.acos(max(-1.0, min(1.0, float(np.dot(ua, ub)))))
        if ang < 1e-4:
            u = ua
        elif ang > math.pi - 1e-3:
            u = unit((1 - t) * ua + t * ub + 1e-3 * np.cross(ua, [0.0, 0.0, 1.0]))
        else:
            u = (math.sin((1 - t) * ang) * ua + math.sin(t * ang) * ub) / math.sin(ang)
        return S + u * ((1 - t) * ra + t * rb)

    def _nat_offset(self, s, p0, u_):
        """angle (deg) of the base pole p0 (carried over from frame to frame) from the natural elbow direction about the arm axis u_: a swivel phi puts
        the elbow at phi + offset degrees from natural, which is what the 'stay near natural' preference must be measured on."""
        pp = self._pole_perp(s, p0, u_)
        a = self._auto_pole(s, u_)
        return math.degrees(math.atan2(float(np.dot(u_, np.cross(a, pp))), float(np.dot(a, pp))))

    def _pole_perp(self, s, p0, u_):
        """unit vector perpendicular to the arm axis u_ that is nearest to the pole p0; it blends smoothly into the automatic pole when p0 is nearly
        parallel to the axis (a hard switch there flips the whole arm between two frames)."""
        p0 = np.asarray(p0, float)
        pp = p0 - np.dot(p0, u_) * u_
        n = float(np.linalg.norm(pp))
        if n >= 0.35:
            return pp / n
        ap = self._auto_pole(s, u_)
        ap = unit(ap - np.dot(ap, u_) * u_)
        if n < 1e-6:
            return ap
        w = n / 0.35
        w = w * w * (3.0 - 2.0 * w)
        v = w * (pp / n) + (1.0 - w) * ap
        nv = float(np.linalg.norm(v))
        return v / nv if nv > 1e-6 else ap

    def ready_fit(self):
        """swivel + wrist angles + racket axes of the READY pose (cached): the forced first / last state of every tracked clip."""
        if getattr(self, '_ready_fit', None) is None:
            st = self.state
            self.reset()
            P = dict(self.ready)
            P['rk_mode'] = 'fit'
            b, h, info = self.solve(P)
            self._ready_fit = dict(phi=float(info['rk_swivel_deg']), wr=np.array(info['rk_fit_flex_dev_twist'], float),
                                   shaft=np.array(info['shaft_a'], float), face=np.array(info['face_a'], float),
                                   pole=np.array(info['r_pole_w'], float), axis=np.array(info['r_axis_w'], float))
            self.reset()
            P2 = dict(self.ready)
            P2['rk_mode'] = 'fit'
            P2['l_mode'] = 'cands'
            b, h, info2 = self.solve(P2)
            cd = info2['candsL']
            self._ready_fit['phiL'] = float(cd['phis'][int(np.argmin(cd['costs']))])
            self._ready_fit['natL'] = float(cd['nat_off'])
            self.state = st
        return self._ready_fit

    @staticmethod
    def _natural_vec(s):
        out = np.array([-1.0, 0.0, 0.0]) if s == 'R' else np.array([1.0, 0.0, 0.0])
        return np.array([0.0, 0.0, -1.0]) + 0.30 * out + 0.25 * np.array([0.0, 1.0, 0.0])

    def _auto_pole(self, s, u_):
        """elbow apex direction when not given: down, a little back and out."""
        out = np.array([-1.0, 0.0, 0.0]) if s == 'R' else np.array([1.0, 0.0, 0.0])
        p = np.array([0.0, 0.0, -1.0]) + 0.30 * out + 0.25 * np.array([0.0, 1.0, 0.0])
        p = p - np.dot(p, u_) * u_
        if np.linalg.norm(p) < 0.2:
            p = np.array([0.0, 1.0, 0.0]) + 0.5 * out
            p = p - np.dot(p, u_) * u_
        return unit(p)

    # ------------------------------------------------------------------------------------------ ready geometry
    def _ready_ankle_y(self):
        f0 = float(-(self.ball_rest['L'][1] - self.O[1]))
        ready = self.ready
        # ankle y when the heel is down: ball y + (ankle - ball) rotated by the ready yaw  (the two feet are symmetric)
        ball = self.O + a2w([0, ready['rf_foot'][1], 0])
        v = self.ankle_rest['R'] - self.ball_rest['R']
        ank = ball + R_yaw(ready['rf_yaw']) @ v
        return float(ank[1])

    _h_cache = None

    def _ready_height(self):
        if self._h_cache is not None:
            return self._h_cache
        # pelvis z such that both knees flex by ~24 degrees in the READY stance (ankles at ground level)
        ready = self.ready
        t, s = self.t_len, self.s_len
        th = math.radians(24.0)
        L = math.sqrt(t * t + s * s + 2 * t * s * math.cos(th))
        ball = self.O + a2w([ready['rf_foot'][0], ready['rf_foot'][1], 0.0])
        v = self.ankle_rest['R'] - self.ball_rest['R']
        ank = ball + R_yaw(ready['rf_yaw']) @ v + np.array([0, 0, self.ball_rest['R'][2]])
        # hip joint position relative to the pelvis (bind)
        hipoff = self.rig.J['hip_R'] - self.rig.hrest[self.rig.idx['Hips']]
        R_pel = R_ypr(ready['pel_rot'])
        hip_rel = R_pel @ hipoff
        ready_y = self._ready_ankle_y()
        hx = ready['rf_foot'][0] * (-1)            # world x of the right foot is -r
        hip_xy = np.array([self.O[0], ready_y]) + hip_rel[:2]
        dxy = np.linalg.norm(ank[:2] - hip_xy)
        dz = math.sqrt(max(L * L - dxy * dxy, 1e-6))
        hip_z = ank[2] + dz
        self._h_cache = float(hip_z - hip_rel[2])
        return self._h_cache


    # ------------------------------------------------------------------------------------------ fingers
    def _fingers(self, P, basis, diag):
        rig = self.rig
        ix = rig.idx
        # right hand: closure of the racket grip
        cr = float(P['r_fing'])
        for nm in self.fing_names:
            if nm.startswith('Right'):
                a = self.open['R'].get(nm, 0.0) + cr * (self.grip_R.get(nm, 0.0) - self.open['R'].get(nm, 0.0))
                basis[ix[nm]] = rx(math.radians(a))
        # left hand: free relaxed .. fist, or the racket grip (throat <-> handle)
        att = float(P['l_attach'])
        g = float(P['l_grip'])
        cf = float(P['l_fing'])
        for nm in self.fing_names:
            if nm.startswith('Left'):
                op = self.open['L'].get(nm, 0.0)
                fist = self.grip_Lh.get(nm, 0.0)
                free = op + (0.30 + 0.70 * cf) * (fist - op)
                gr = (1 - g) * self.grip_Lt.get(nm, 0.0) + g * self.grip_Lh.get(nm, 0.0)
                a = (1 - att) * free + att * gr
                basis[ix[nm]] = rx(math.radians(a))
