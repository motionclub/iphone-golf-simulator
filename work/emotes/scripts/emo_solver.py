"""EMOTES: a pose solver with two FREE arms (numpy only; runs in Blender's python3.13).

The match-anim-set engine (work/match-anim-set/scripts/pose.py, imported read-only) solves the right arm as a racket tracker: it can not put a hand flat on the floor or
pinch a nose.  EmoSolver subclasses its Solver, keeps everything that is shared (the fitted rig, the leg / arm two-bone IK, the clavicle rule, the wrist limit, the
spine / head distribution, the foot-ground table) and replaces `solve` by `solve_emote`, in which BOTH arms are driven by a wrist target + a hand orientation + an
elbow pole + a finger pose.  The racket stays rigid on the right hand (Hand_Racket), so its pose is a by-product (`rk_origin`, `rk_R` in the result).

Authoring frame (as in the engine): r = hero's right, f = forward (towards the net / the other player), u = up, metres, origin on the floor under the Root bone.
World (Blender) = (-r, -f, u).  Channels (all optional; a missing one takes the READY value; arrays are numpy):

  pel [r,f,u] offset from the READY pelvis      pel_abs [r,f,u] absolute pelvis (Hips joint)     pel_rot [yaw,pitch,roll] deg      chest_rot, head_rot, gaze as the engine's
  lf_/rf_  foot [r,f]  yaw  lift  heel  knee    (engine meaning; heel > 0 = heel up)
  pel_auto  True / False  automatic pelvis drop so that the planted legs can reach (engine default True)
  for each arm (prefix l / r):
     {p}_frame   'c' = vectors are in the CHEST frame (default), 'w' = in the authoring frame
     {p}_wrist   [r,f,u] metres   wrist joint (chest frame: from the chest centre; world frame: from the floor origin)
     {p}_fdir    [r,f,u]          direction the fingers point
     {p}_palm    [r,f,u]          direction the palm normal faces (made orthogonal to fdir)
     {p}_pole    [r,f,u] or None  elbow apex direction (None = the engine's natural pole)
     {p}_fing    dict bone name -> angle (deg about the finger bone's local X), or None = relaxed
     {p}_twist_share  fraction of the forearm twist that the forearm bone takes (default the engine's ROLL_FRAC)

Hand bone convention (measured): local Y = along the fingers, local Z = palm normal (out of the palm), local X = Y x Z; both hands, both heroes.
A positive finger angle tucks the finger towards the palm."""
import math
import os
import sys

import numpy as np

MA = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set'
sys.path.insert(0, MA + '/scripts')
import kin  # noqa: E402
import pose as PS  # noqa: E402
from kin import a2w, w2a, unit, rx, ry, rz, axis_angle  # noqa: E402

A2W = np.diag([-1.0, -1.0, 1.0])            # authoring -> world (a proper rotation: 180 degrees about z)


def hand_frame(fdir, palm):
    """3x3 with columns (X, Y, Z) = (Y x Z, fingers, palm normal) in whatever frame fdir / palm are given in."""
    y = unit(np.asarray(fdir, float))
    z = np.asarray(palm, float)
    z = z - np.dot(z, y) * y
    if np.linalg.norm(z) < 1e-6:
        z = np.cross(y, [0.0, 0.0, 1.0] if abs(y[2]) < 0.9 else [1.0, 0.0, 0.0])
    z = unit(z)
    return np.stack([np.cross(y, z), y, z], 1)


class EmoSolver(PS.Solver):
    # ------------------------------------------------------------------------------------------------ setup
    def __init__(self, rig, racket, hands):
        super().__init__(rig, racket, hands)
        ix = rig.idx
        self.finger_bones = [n for n in rig.names if any(k in n for k in ('Thumb', 'Index', 'Middle', 'Ring', 'Little'))]
        self.open = {'L': dict(hands['open_L']), 'R': dict(hands['open_R'])}
        self.R0 = {s: rig.Rrest[ix[('Left' if s == 'L' else 'Right') + 'LowerArm']].T @ rig.Rrest[ix[('Left' if s == 'L' else 'Right') + 'Hand']] for s in 'LR'}
        self.min_wrist_r = 0.30 * self.A_arm                # a free hand may come close to the shoulder (nose pinch): elbow flexion up to ~150 degrees
        self.reset()

    def rest_fingers(self, side):
        return {n: float(a) for n, a in self.open[side].items()}

    # ------------------------------------------------------------------------------------------------ main solve
    def solve_emote(self, Pin):
        rig = self.rig
        ix = rig.idx
        n = rig.n
        P = dict(self.ready)
        for k, v in Pin.items():
            P[k] = v
        Q = np.zeros((n, 3, 3))
        Pos = np.zeros((n, 3))
        basis = np.tile(np.eye(3), (n, 1, 1))
        diag = {}
        O = self.O

        def put(i, Qi):
            p = rig.parent[i]
            if p < 0:
                basis[i] = rig.rel_rot[i].T @ Qi
                Q[i] = Qi
                Pos[i] = rig.rel_off[i]
            else:
                basis[i] = rig.rel_rot[i].T @ Q[p].T @ Qi
                Q[i] = Qi
                Pos[i] = Pos[p] + Q[p] @ rig.rel_off[i]

        put(ix['Root'], rig.Rrest[ix['Root']])
        # ---- feet
        feet = {}
        for s, key in (('L', 'lf'), ('R', 'rf')):
            br = np.array(P[f'{key}_foot'], float)
            yaw = float(P[f'{key}_yaw'])
            lift = float(P[f'{key}_lift'])
            heel = float(P[f'{key}_heel'])
            if self.foot_dip is not None and heel > 0.0:
                lift += float(np.interp(heel, self.foot_dip[0], self.foot_dip[1]))
            ball = O + a2w([br[0], br[1], 0.0]) + np.array([0.0, 0.0, self.ball_rest[s][2] + lift])
            Ry_ = PS.R_yaw(yaw)
            Rh_ = rx(math.radians(heel))
            Rfoot = Ry_ @ Rh_
            ankle = ball + Rfoot @ (self.ankle_rest[s] - self.ball_rest[s])
            feet[s] = dict(ball=ball, ankle=ankle, Rfoot=Rfoot, Ry=Ry_, heel=heel, yaw=yaw)
        # ---- pelvis
        hips_rest = rig.hrest[ix['Hips']]
        hip_off = {s: rig.J[f'hip_{s}'] - hips_rest for s in 'LR'}
        R_pel = PS.R_ypr(P['pel_rot'])
        if P.get('pel_abs') is not None:
            pel_pos = O + a2w(np.asarray(P['pel_abs'], float))
        else:
            ready_ank_y = self._ready_ankle_y()
            pel_pos = np.array([O[0], ready_ank_y, self._ready_height()]) + a2w(np.array(P['pel'], float))
        iH = ix['Hips']
        Q_h = R_pel @ rig.Rrest[iH]
        Hjoint = {s: pel_pos + R_pel @ hip_off[s] for s in 'LR'}
        max_reach = math.sqrt(self.t_len ** 2 + self.s_len ** 2 + 2 * self.t_len * self.s_len * math.cos(math.radians(9.0)))
        need = 0.0
        for s in 'LR':
            dxy = np.linalg.norm((feet[s]['ankle'] - Hjoint[s])[:2])
            dz = Hjoint[s][2] - feet[s]['ankle'][2]
            if math.sqrt(dxy ** 2 + dz ** 2) > max_reach:
                z_allowed = feet[s]['ankle'][2] + math.sqrt(max(max_reach ** 2 - dxy ** 2, 0.0))
                need = max(need, Hjoint[s][2] - z_allowed)
        if need > 0 and P.get('pel_auto', True):
            pel_pos = pel_pos - np.array([0, 0, need])
            diag['pelvis_auto_drop'] = need
        iP = rig.parent[iH]
        loc = rig.rel_rot[iH].T @ (Q[iP].T @ (pel_pos - Pos[iP]) - rig.rel_off[iH])
        basis[iH] = rig.rel_rot[iH].T @ Q[iP].T @ Q_h
        Q[iH] = Q_h
        Pos[iH] = Pos[iP] + Q[iP] @ (rig.rel_off[iH] + rig.rel_rot[iH] @ loc)
        hips_loc = loc
        # ---- spine
        cr = P['chest_rot']
        Rc = np.eye(3)
        for nm, w in zip(('Spine', 'Chest', 'UpperChest'), PS.SPINE_W):
            Rc = Rc @ PS.R_ypr(cr, w)
            put(ix[nm], R_pel @ Rc @ rig.Rrest[ix[nm]])
        R_chest = R_pel @ PS.R_ypr(cr, 1.0)
        iNeck, iHead = ix['Neck'], ix['Head']
        if P.get('gaze') is not None:
            put(iNeck, R_chest @ rig.Rrest[iNeck])
            put(iHead, R_chest @ rig.Rrest[iHead])
            hp = Pos[iHead].copy()
            g = O + a2w(np.array(P['gaze'], float))
            dvec = unit(g - (hp + np.array([0, 0, 0.07])))
            c_ = w2a(R_chest.T @ dvec)
            yaw = max(-75.0, min(75.0, math.degrees(math.atan2(c_[0], c_[1]))))
            pitch = max(-40.0, min(50.0, math.degrees(math.atan2(-c_[2], math.hypot(c_[0], c_[1])))))
            hr = [yaw + float(P.get('head_yaw_add', 0.0)), pitch, float(P['head_rot'][2])]
        else:
            hr = list(P['head_rot'])
        put(iNeck, R_chest @ PS.R_ypr(hr, 0.4) @ rig.Rrest[iNeck])
        put(iHead, R_chest @ PS.R_ypr(hr, 1.0) @ rig.Rrest[iHead])
        # ---- legs
        for s in 'LR':
            key = 'lf' if s == 'L' else 'rf'
            Sd = 'Left' if s == 'L' else 'Right'
            ft = feet[s]
            iU, iLo, iFo, iTo = ix[f'{Sd}UpperLeg'], ix[f'{Sd}LowerLeg'], ix[f'{Sd}Foot'], ix[f'{Sd}Toes']
            hip = Pos[iH] + Q[iH] @ rig.rel_off[iU]
            out = float(P[f'{key}_knee'])
            sign = 1.0 if s == 'R' else -1.0
            fwd_foot = PS.R_yaw(ft['yaw'] + sign * out) @ PS.F_W
            if P.get(f'{key}_pole_w') is not None:
                fwd_foot = np.asarray(P[f'{key}_pole_w'], float)
            knee, ankle, u_, pp, short = self._leg_ik(hip, ft['ankle'], fwd_foot, self.t_len, self.s_len)
            N = unit(np.cross(u_, pp))
            t_dir = unit(knee - hip)
            s_dir = unit(ankle - knee)
            put(iU, np.stack([N, t_dir, np.cross(N, t_dir)], 1))
            put(iLo, np.stack([N, s_dir, np.cross(N, s_dir)], 1))
            put(iFo, ft['Rfoot'] @ rig.Rrest[iFo])
            put(iTo, ft['Ry'] @ rig.Rrest[iTo])
            diag[f'{key}_short'] = short
            diag[f'{key}_knee_flex_deg'] = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(t_dir, s_dir))))))
            diag[f'{key}_ankle'] = ankle
            diag[f'{key}_ball'] = ft['ball']
            diag[f'{key}_knee'] = knee
        # ---- arms
        self._arms(P, Q, Pos, put, basis, diag, R_chest)
        # ---- fingers
        for side in 'LR':
            pre = 'l' if side == 'L' else 'r'
            ang = P.get(f'{pre}_fing')
            base = self.open[side]
            for nm in self.finger_bones:
                if not nm.startswith('Left' if side == 'L' else 'Right'):
                    continue
                a = base.get(nm, 0.0) if ang is None else ang.get(nm, base.get(nm, 0.0))
                basis[ix[nm]] = rx(math.radians(a))
        # ---- racket (rigid on the right hand)
        iHR = ix['RightHand']
        diag['rk_origin'] = Pos[iHR] + Q[iHR] @ self.t_rh
        diag['rk_R'] = Q[iHR] @ self.R_rh
        diag['Q_hand_R'] = Q[iHR].copy()
        diag['Q_hand_L'] = Q[ix['LeftHand']].copy()
        diag['R_chest'] = R_chest
        Qf, Pf = rig.fk(basis, hips_loc)            # full FK including the finger bones
        diag['Q'] = Qf
        diag['Pos'] = Pf
        return basis, hips_loc, diag

    # ------------------------------------------------------------------------------------------------ arms
    def _arms(self, P, Q, Pos, put, basis, diag, R_chest):
        rig = self.rig
        ix = rig.idx
        O = self.O
        iUC = ix['UpperChest']
        ucr = rig.Rrest[iUC]
        c_off = ucr.T @ (0.5 * (rig.J['shoulder_L'] + rig.J['shoulder_R']) - rig.hrest[iUC])
        C_ctr = Pos[iUC] + Q[iUC] @ c_off
        diag['chest_center'] = C_ctr
        sh_half = float(np.linalg.norm(rig.J['shoulder_L'] - rig.J['shoulder_R'])) / 2.0
        for s in 'LR':
            pre = 'l' if s == 'L' else 'r'
            Sd = 'Left' if s == 'L' else 'Right'
            frame = P.get(f'{pre}_frame', 'c')
            if frame == 'c':
                M = R_chest @ A2W
                origin = C_ctr
            else:
                M = A2W
                origin = O
            rk_cmd = None
            if s == 'R' and P.get('r_rk_pos') is not None:
                # racket-first right arm: the grip centre + the shaft / face directions are given, the hand follows (hand = racket frame * R_rh^T)
                Rrk = M @ PS.frame_from_axes(unit(np.asarray(P['r_rk_shaft'], float)), np.asarray(P['r_rk_face'], float))
                Qh_cmd = Rrk @ self.R_rh.T
                W_t = origin + M @ np.asarray(P['r_rk_pos'], float) - Qh_cmd @ self.t_rh
                rk_cmd = Qh_cmd
            else:
                W_t = origin + M @ np.asarray(P[f'{pre}_wrist'], float)
            # clavicle (engine rule): from the direction of the hand target as seen from the chest
            iC, iU, iLo, iHd = ix[f'{Sd}Shoulder'], ix[f'{Sd}UpperArm'], ix[f'{Sd}LowerArm'], ix[f'{Sd}Hand']
            sh0 = C_ctr + R_chest @ a2w([(1.0 if s == 'R' else -1.0) * sh_half, 0.0, 0.0])
            cr = w2a(R_chest.T @ unit(W_t - sh0))
            L = float(np.linalg.norm(W_t - sh0))
            elev = math.degrees(math.acos(max(-1.0, min(1.0, -cr[2]))))
            e = min(24.0, 0.42 * max(0.0, elev - 55.0)) * float(P.get('clav_gain', 1.0))
            q = 11.0 * max(-0.6, min(1.0, cr[1])) * min(1.0, L / self.A_arm) + (3.0 if elev > 100 else 0.0)
            sg_e = 1.0 if s == 'L' else -1.0
            sg_q = -1.0 if s == 'L' else 1.0
            Rcl = R_chest @ (rz(math.radians(sg_q * q)) @ axis_angle(PS.F_W, math.radians(sg_e * e))) @ R_chest.T
            put(iC, Rcl @ (Q[iUC] @ rig.rel_rot[iC]))
            S = Pos[iC] + Q[iC] @ rig.rel_off[iU]
            pole = P.get(f'{pre}_pole')
            u_t = unit(W_t - S)
            pv = self._auto_pole(s, u_t) if pole is None else unit(M @ np.asarray(pole, float))
            ik = self._arm_ik(s, S, W_t, pv)
            Rh = rk_cmd if rk_cmd is not None else M @ hand_frame(P[f'{pre}_fdir'], P[f'{pre}_palm'])
            put(iU, ik['Qu'])
            lim = P.get(f'{pre}_wlim')
            Qh, clamp = self._limit_wrist(ik['Ql'], Rh, rig.Rrest[iLo].T @ rig.Rrest[iHd], lim=lim)
            sg, tw = self._wrist_dev(ik['Ql'], Qh, self.R0[s])
            a_tw = abs(tw)
            fade = 1.0 if a_tw <= math.radians(120.0) else (0.0 if a_tw >= math.pi else 0.5 * (1.0 + math.cos(math.pi * (a_tw - math.radians(120.0)) / math.radians(60.0))))
            share = float(P.get(f'{pre}_twist_share', self.ROLL_FRAC))
            roll = float(np.clip(share * tw * fade, -math.radians(self.ROLL_MAX), math.radians(self.ROLL_MAX)))
            put(iLo, ik['Ql'] @ ry(roll))
            put(iHd, Qh)
            diag[f'{s}_wrist_target'] = W_t
            diag[f'{s}_wrist'] = Pos[iHd].copy()
            diag[f'{s}_shoulder'] = S.copy()
            diag[f'{s}_elbow'] = ik['E'].copy()
            diag[f'{s}_arm_short'] = ik['short']
            diag[f'{s}_arm_near'] = ik['near']
            diag[f'{s}_wrist_clamp_deg'] = clamp
            diag[f'{s}_wrist_swing_deg'] = math.degrees(sg)
            diag[f'{s}_wrist_twist_deg'] = math.degrees(tw)
            diag[f'{s}_elbow_flex_deg'] = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(ik['u_dir'], ik['f_dir']))))))
