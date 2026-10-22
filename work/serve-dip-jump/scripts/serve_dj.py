"""SERVE_DIP_JUMP: the Serve keyed again from the stance to the follow-through (engine = work/match-anim-set kin / pose / clipkit / clips, imported read-only).

What the request asked for (the order of events, from the ball in the left hand):
  1. before the ball leaves the hand the hips FOLD (trunk bows forward over bent knees, big and bouncy like the run), then pop up into the toss;
  2. both feet leave the court as the toss arm goes up, hips well above the ready stance, then land - in place (the contact hop at the end is the old one, untouched);
  3. the toss arm climbs with the ball (elbow opening), the racket is hoop-over-handle by the time the ball is at the head;
  4. the racket elbow goes out to the right and BEHIND the back, the racket drops behind the back and comes up from the side; the forearm never crosses the chest.

Times are the game's (prefab: stance 0.2 / release 0.7 / trophy 1.3333 / contact 1.7): they are NOT changed, only what happens in between.
The toss arm is not keyed in chest coordinates between the stance and the trophy: the game moves the ball on a straight line (smoothstep) from the stance palm to the release palm and
the toss arm follows it (HeroTennisDriver.TossArm), so run_dj.py puts the clip's own left palm on that same line in hero space (the chest moves, the palm does not care).
"""
import math
import os

import numpy as np

import clips as CL
from clipkit import K

D = CL.D
RS = CL.RS
FPS = 30


def F(n):
    return n / FPS


# --- ritual times (frames at 30 fps): fixed by the prefab, the table and the game
T_S, T_R, T_T = F(6), F(21), F(40)            # stance 0.2 / release 0.7 / trophy 1.3333
T_D = F(45)                                   # deepest bend before the drive (1.5)
T_OFF = F(48)                                 # both feet leave the court for the serve jump (1.6)
T_C = F(51)                                   # CONTACT 1.7
T_LAND = F(57)
T_KICK = F(60)
T_STEP = F(66)
T_END = F(75)
LENGTH = T_END
# --- the new events inside the wind-up
T_FOLD = F(10)                                # deepest fold (0.333)
T_PUSH = F(13)                                # toes about to leave (0.433)
T_APEX = F(17)                                # top of the hop (0.567)
T_TD = F(21)                                  # toes touch the court again (= release)


def serve(S, hero):
    LREL = [float(x) for x in os.environ.get('LREL', '-22,68,0.93').split(',')]
    fem = getattr(hero, 'tag', 'male') == 'female'
    FR = float(os.environ.get('FEM_FR', 0.02)) if fem else 0.0           # the female's skort / legs are in a different place: the racket hangs a bit further out during the fold
    FAZ = float(os.environ.get('FEM_FAZ', 45)) if fem else 0.0
    FF = float(os.environ.get('FEM_FF', -0.05)) if fem else 0.0
    LSTANCE = [float(x) for x in os.environ.get('LSTANCE', '-0.15,0.52,-0.66').split(',')]
    R = S.ready
    f0 = R['rf_foot'][1]
    rs = lambda az, el, d: RS(S, az, el, d, 'R')
    ls = lambda az, el, d: RS(S, az, el, d, 'L')
    ye = lambda side, deg: hero.toe_dir_to_yaw(side, deg)
    sh_z = float(S.rig.J['shoulder_L'][2])
    zs = sh_z + 0.16 + (S.A_arm + 0.10 + 0.30) - 0.10                  # contact height of the old Serve formula (scaled to THIS hero); the reach limit pulls it in
    keys = []

    def FT(side, wps, src):
        for w in wps:
            t, pos, lift, yaw, heel = w
            ch = {f'{side}_foot': list(pos), f'{side}_lift': float(lift), f'{side}_heel': float(heel), f'{side}_yaw': float(ye('R' if side == 'rf' else 'L', yaw))}
            keys.append(K(t, src, ease=1.0 if lift <= 1e-6 and heel <= 1e-6 else None, **ch))

    # ------------------------------------------------------------------------------------------------ feet
    # stance, planted through the fold (heels stay down), push off through the balls of the feet, both feet airborne from frame 14 to 20, toes touch first, then planted again
    # (the same spots: the hop is in place).  From the deepest bend before the drive (T_D) on, the old keys of the contact jump and the landing.
    xr, xl = 0.26, -0.18
    pR, pL = (xr, f0 - 0.08), (xl, f0 + 0.14)
    FT('rf', [(T_S, pR, 0.0, 75.0, 0.0), (F(8), pR, 0.0, 75.0, 0.0), (T_FOLD, pR, 0.0, 75.0, 0.0), (F(12), pR, 0.0, 75.0, 8.0), (T_PUSH, pR, 0.0, 74.0, 28.0),
              (F(14), (xr, f0 - 0.08), 0.075, 73.0, 55.0), (F(15), pR, 0.115, 72.0, 63.0), (F(16), pR, 0.14, 72.0, 66.0), (T_APEX, pR, 0.15, 72.0, 66.0), (F(18), pR, 0.14, 72.0, 63.0),
              (F(19), pR, 0.105, 73.0, 52.0), (F(20), pR, 0.045, 74.0, 30.0), (T_TD, pR, 0.0, 75.0, 12.0), (F(22), pR, 0.0, 75.0, 3.0), (F(24), pR, 0.0, 75.0, 0.0),
              (T_D, pR, 0.0, 75.0, 0.0), (F(47), (xr - 0.01, f0 - 0.07), 0.0, 72.0, 22.0),
              (T_OFF, (xr - 0.02, f0 - 0.04), 0.010, 70.0, 48.0), (F(50), (xr - 0.05, f0 + 0.05), 0.07, 62.0, 62.0), (T_C, (xr - 0.07, f0 + 0.10), 0.12, 55.0, 62.0),
              (F(53), (xr - 0.09, f0 + 0.04), 0.17, 45.0, 64.0), (F(55), (0.12, f0 - 0.20), 0.36, 32.0, 70.0), (F(58), (0.10, f0 - 0.42), 0.58, 22.0, 70.0),
              (T_KICK, (0.10, f0 - 0.40), 0.58, 20.0, 66.0), (F(62), (0.11, f0 + 0.02), 0.34, 10.0, 50.0), (F(64), (0.13, f0 + 0.30), 0.08, 5.0, 24.0),
              (T_STEP, (0.15, f0 + 0.36), 0.0, 5.0, 0.0), (T_END, (0.15, f0 + 0.36), 0.0, 5.0, 0.0)], 'S3.F1/S3.F3/S3.F4/S3.F5/S3.F7/S3.F9')
    FT('lf', [(T_S, pL, 0.0, 38.0, 0.0), (F(8), pL, 0.0, 38.0, 0.0), (T_FOLD, pL, 0.0, 38.0, 0.0), (F(12), pL, 0.0, 38.0, 8.0), (T_PUSH, pL, 0.0, 38.0, 28.0),
              (F(14), pL, 0.075, 37.0, 55.0), (F(15), pL, 0.115, 37.0, 63.0), (F(16), pL, 0.14, 36.0, 66.0), (T_APEX, pL, 0.15, 36.0, 66.0), (F(18), pL, 0.14, 36.0, 63.0),
              (F(19), pL, 0.105, 37.0, 52.0), (F(20), pL, 0.045, 38.0, 30.0), (T_TD, pL, 0.0, 38.0, 12.0), (F(22), pL, 0.0, 38.0, 3.0), (F(24), pL, 0.0, 38.0, 0.0),
              (T_D, pL, 0.0, 38.0, 0.0), (F(47), pL, 0.0, 38.0, 20.0),
              (T_OFF, (xl, f0 + 0.15), 0.010, 36.0, 45.0), (F(50), (xl + 0.01, f0 + 0.20), 0.07, 28.0, 62.0), (T_C, (xl + 0.02, f0 + 0.25), 0.12, 20.0, 62.0),
              (F(53), (xl + 0.03, f0 + 0.31), 0.13, 10.0, 56.0), (F(55), (xl + 0.04, f0 + 0.37), 0.04, 2.0, 42.0), (T_LAND, (xl + 0.04, f0 + 0.39), 0.0, -2.0, 30.0),
              (F(59), (xl + 0.04, f0 + 0.39), 0.0, -2.0, 4.0), (T_END, (xl + 0.04, f0 + 0.39), 0.0, -2.0, 0.0)], 'S3.F1/S3.F3/S3.F4/S3.F5/S3.F8/S3.F9')

    # ------------------------------------------------------------------------------------------------ hips and trunk
    # body(t, (forward, right, up) pelvis offset, pelvis yaw / pitch / roll, chest yaw (absolute) / pitch (relative to the pelvis) / roll)
    # FOLD: the pelvis sits back and down, the trunk bows over the bent knees (pelvis pitch 9 -> 42 deg, the chest rounds 8 -> 16 deg more), then everything extends at once: the hips go up
    # and a little forward, the trunk comes up and arches back for the reach, the legs leave the court.  The yaw (side-on turn) keeps growing monotonically.
    def body(t, pel, pyaw, ppitch, proll, cyaw, cpitch, croll, src, ease=None):
        keys.append(K(t, src, ease=ease, pel=[pel[1], pel[0], pel[2]], pel_rot=[pyaw, ppitch, proll], chest_rot=[cyaw - pyaw, cpitch, croll]))
    body(T_S, (0.0, 0.0, 0.0), 30, 9, 0, 42, 8, 0, 'S3.H1')
    fp_, ff_, fz_, fc_ = [float(x) for x in os.environ.get('FOLD', '32,-0.30,-0.17,8').split(',')]
    body(F(7), (0.30 * ff_, 0.0, 0.16 * fz_), 30, 9 + 0.156 * (fp_ - 9), 0, 42.5, 8, 0, 'FOLD')
    body(F(8), (0.5 * ff_, 0.0, 0.5 * fz_), 30, 9 + 0.5 * (fp_ - 9), 0, 43, 8 + 0.5 * (fc_ - 8), 0, 'FOLD')
    body(F(9), (0.84 * ff_, 0.0, 0.84 * fz_), 30.5, 9 + 0.844 * (fp_ - 9), 0, 43.5, 8 + 0.844 * (fc_ - 8), 0, 'FOLD')
    body(T_FOLD, (ff_, 0.0, fz_), 31, fp_, 0, 44, fc_, 0, 'FOLD')
    body(F(12), (-0.06, 0.0, -0.055), 32, 12, 0, 46, 3, 0, 'POP')
    body(T_PUSH, (0.01, 0.0, 0.0), 33, 4, 0, 48, 2, 0, 'POP')
    body(F(14), (0.03, 0.0, 0.09), 34, -3, 0, 50, -6, 0, 'POP')
    body(F(15), (0.04, 0.0, 0.16), 34, -7, 0, 52, -10, 0, 'AIR')
    body(F(16), (0.04, 0.0, 0.21), 35, -9, 0, 54, -13, 0, 'AIR')
    body(T_APEX, (0.04, 0.0, 0.225), 35, -9, 0, 55, -14, 0, 'AIR')
    body(F(18), (0.04, 0.0, 0.21), 36, -8, 0, 56, -14, 0, 'AIR')
    body(F(19), (0.03, 0.0, 0.16), 36, -5, 0, 57, -12, 0, 'AIR')
    body(F(20), (0.02, 0.0, 0.09), 36, 0, 0, 58, -9, 0, 'AIR')
    body(T_TD, (0.0, 0.0, 0.0), 36, 6, 0, 58, -5, 0, 'LAND')
    body(F(22), (-0.02, 0.0, -0.05), 37, 12, 0, 59, 0, 0, 'LAND')
    body(F(23), (-0.03, 0.0, -0.085), 37, 14, 0, 60, 2, 0, 'LAND')
    body(F(26), (-0.02, 0.0, -0.045), 40, 9, 1, 66, -1, 2, 'S3.H1/S3.F2')
    body(F(30), (0.0, 0.0, -0.02), 46, 6, 2, 74, -2, 4, 'S3.H1/S3.F2')
    body(T_T, (-0.01, 0.0, -0.055), 58, 4, 4, 92, -10, 6, 'S3.H1/S3.H2')
    body(T_D, (-0.02, 0.0, -0.20), 70, 4, 6, 108, -14, 8, 'S3.H1/S3.F3')
    body(F(47), (0.00, 0.0, -0.14), 52, 6, 4, 90, -14, 8, 'S3.H3/S3.F4')
    body(F(49), (0.04, 0.0, -0.02), 28, 6, 0, 58, -12, -2, 'S3.H3/S3.F4')
    body(F(50), (0.09, 0.0, 0.08), 12, 5, -2, 26, -10, -8, 'S3.H3/S3.F5')
    body(T_C, (0.15, 0.0, 0.15), 4, 2, -4, -6, -8, -14, 'S3.C/S3.H3')
    body(F(53), (0.19, 0.0, 0.16), -8, 4, -4, -24, -2, -10, 'S3.H3/S3.F6')
    body(F(55), (0.22, 0.0, 0.08), -22, 14, 0, -44, 12, -4, 'S3.H3/S3.F7')
    body(T_LAND, (0.24, 0.0, -0.04), -26, 24, 0, -50, 20, 0, 'S3.F8')
    body(T_KICK, (0.26, 0.0, -0.10), -22, 28, 0, -46, 22, 0, 'S3.F8')
    body(F(63), (0.28, 0.0, -0.08), -14, 22, 0, -30, 16, 0, 'S3.F9')
    body(T_STEP, (0.29, 0.0, -0.05), -8, 16, 0, -16, 12, 0, 'S3.F9')
    body(T_END, (0.28, 0.0, 0.0), 0, 9, 0, 0, 8, 0, 'LOCK')

    # ------------------------------------------------------------------------------------------------ the tossing (left) arm
    # keys at the three ritual instants (stance / release / trophy) in chest coordinates; BETWEEN them the palm is put on the game's own path by run_dj.py:
    #   stance -> release: straight line, smoothstep; release -> trophy hand: smoothstep over 0.2 s, then fixed in hero space (TossPalm).
    keys += [K(0.0, 'S3.R1', l_attach=0.0, l_hand=LSTANCE, l_palm=D(0, 70), l_fing=0.55, l_elbow=[-0.4, -0.6, -0.7]),
             K(T_S, 'S3.R1', l_attach=0.0, l_hand=LSTANCE, l_palm=D(0, 70), l_fing=0.55, l_elbow=[-0.4, -0.6, -0.7]),
             K(F(10), 'S3.R2', l_palm=D(0, 66), l_fing=0.5, l_elbow=[-0.4, -0.6, -0.65]),
             K(F(14), 'S3.R2', l_palm=D(0, 60), l_fing=0.45, l_elbow=[-0.45, -0.6, -0.45]),
             K(F(18), 'S3.R2', l_palm=D(0, 52), l_fing=0.35, l_elbow=[-0.5, -0.65, -0.2]),
             K(T_R, 'S3.R2', l_hand=ls(LREL[0], LREL[1], LREL[2]), l_palm=D(0, 45), l_fing=0.20, l_elbow=[-0.5, -0.7, 0.0]),
             K(F(27), 'S3.R3', l_palm=D(0, 20), l_fing=0.12, l_elbow=[-0.45, -0.7, 0.0]),
             K(F(35), 'S3.R3', l_palm=D(0, 5), l_fing=0.10, l_elbow=[-0.45, -0.7, 0.0]),
             K(T_T, 'S3.R3', l_hand=ls(0, 80, 0.97), l_palm=D(0, 0), l_fing=0.10, l_elbow=[-0.45, -0.7, 0.0]),
             # after the trophy the toss arm folds in and comes down along the LEFT side (in front of the left ribs): the forearm never reaches across the chest
             K(F(42), 'S3.R5', l_hand=ls(-16, 62, 0.90), l_fing=0.2, l_elbow=[-0.42, -0.65, -0.35]),
             K(T_D, 'S3.R5', l_hand=ls(-26, 34, 0.74), l_fing=0.2, l_elbow=[-0.45, -0.6, -0.7]),
             K(F(47), 'S3.R5', l_hand=ls(-32, 10, 0.60), l_fing=0.25),
             K(F(49), 'S3.R5', l_hand=ls(-34, -14, 0.52), l_fing=0.3),
             K(F(53), 'S3.R6', l_hand=ls(-36, -28, 0.50), l_fing=0.3),
             K(T_LAND, 'S3.R6', l_hand=ls(-34, -12, 0.82), l_fing=0.2),
             K(F(63), 'S3.R6', l_hand=ls(-30, -40, 0.70), l_fing=0.25),
             K(F(69), 'LOCK', l_hand=ls(-30, -50, 0.6), l_attach=0.0),
             K(T_END, 'LOCK', l_attach=1.0, l_grip=0.0)]

    # ------------------------------------------------------------------------------------------------ racket arm
    # Designed in the CHEST frame (r right, f forward, u up; metres from the right shoulder joint; the shaft / face as (azimuth, elevation) from the chest's forward):
    #   * the racket rises on the RIGHT side of the body, hoop over the handle, the elbow stays outside the ribs;
    #   * trophy: elbow out at shoulder height, forearm up, hoop up behind the head;
    #   * drop: the elbow stays out and goes BEHIND the shoulder line, the forearm falls behind the back and the racket hangs down behind it;
    #   * drive: the elbow leads up and forward, the forearm and racket follow from behind and come up from the side to the contact.
    # The elbow direction (hint) steers the tracker's swivel; the chest-frame shaft / face are turned into the stance frame by run_dj.py (chest yaw / pitch of that instant).
    A_ = S.A_arm
    half = S.shoulder_w / 2.0 / A_

    CYAW = {F(8): 43, T_FOLD: 44, F(12): 46, F(14): 50, F(16): 54, T_APEX: 55, F(19): 57, T_R: 58, F(30): 74, T_T: 92}

    def RK(t, src, grip, elbow=None, shaft=None, face=None, w=(0.4, 1.0), hw=0.0, face_abs=None, ori_abs=None, **extra):
        ch = dict(rk_pos=[half + grip[0] / A_, grip[1] / A_, grip[2] / A_], rk_w=list(w))
        if elbow is not None:
            ch['r_hint'] = list(elbow)
            ch['r_hint_w'] = float(hw)
        ch.update(extra)
        k = K(t, src, **ch)
        if ori_abs is not None:
            k['ori'] = (D(*ori_abs[0]), D(*ori_abs[1]))
        if shaft is not None:
            if face_abs is not None:                                     # face given in the stance frame (continuity with the stance face): turned into the chest frame here
                face = (face_abs[0] - CYAW[t], face_abs[1])
            k['ori_c'] = (D(shaft[0], shaft[1]), D(face[0], face[1]))
        return k

    keys += [K(T_S, 'S3.R1', rk_pos=[0.20, 0.46, -0.70], shaft=D(35, -35), face=D(-70, 0), rk_w=[0.2, 1.0]),
             # fold: the arm hangs from the shoulder while the trunk bows, the racket hangs down by the right thigh (no big back-swing: a 170 deg shaft flip in two frames made the wrist twist jump);
             # the face keeps the stance's roll (it is left almost free, so the wrist twist stays continuous)
             RK(F(7), 'FOLD', (-0.01 + FR / 2, 0.17 + FF / 2, -0.38), elbow=(0.05, -0.02, -0.22), shaft=None, w=(0.02, 1.0), hw=0.5, ori_abs=((50 + FAZ / 2, -46), (-70, 0)), r_tw=-8.0, r_tw_w=3.0),
             RK(F(8), 'FOLD', (0.06 + FR, 0.10 + FF, -0.40), elbow=(0.06, 0.0, -0.22), shaft=None, w=(0.02, 1.0), hw=0.8, ori_abs=((70 + FAZ, -52), (-70, 0)), r_tw=-8.0, r_tw_w=3.0),
             RK(T_FOLD, 'FOLD', (0.10 + FR, 0.06 + FF, -0.42), elbow=(0.08, 0.0, -0.22), shaft=None, w=(0.02, 1.0), hw=0.8, ori_abs=((80 + FAZ, -58), (-72, 5)), r_tw=-10.0, r_tw_w=3.0),
             # pop: the arm swings forward and UP in front of the right shoulder (elbow low, forearm forward-up, racket rising from hanging to hoop-over-handle), then the elbow lifts out
             # to the side as the hand goes back to the head for the trophy
             RK(F(12), 'POP', (0.10 + FR, 0.20 + FF / 2, -0.32), elbow=(0.10, 0.02, -0.22), shaft=None, w=(0.0, 1.0), hw=0.8, ori_abs=((40 + FAZ / 2, -28), (-75, 5)), r_tw=-14.0, r_tw_w=3.0),
             RK(F(14), 'POP', (0.08, 0.28, -0.10), elbow=(0.12, 0.05, -0.20), shaft=None, w=(0.0, 1.0), hw=1.0, ori_abs=((26, 30), (-80, 5)), r_tw=-24.0, r_tw_w=3.0),
             RK(F(15), 'AIR', (0.09, 0.26, 0.05), elbow=(0.15, 0.04, -0.16), shaft=None, w=(0.0, 0.8), hw=1.0, ori_abs=((30, 52), (-85, 5)), r_tw=-30.0, r_tw_w=3.0),
             RK(F(16), 'AIR', (0.10, 0.22, 0.18), elbow=(0.17, 0.02, -0.12), shaft=None, w=(0.0, 0.7), hw=1.2, ori_abs=((36, 68), (-90, 0)), r_tw=-36.0, r_tw_w=3.0),
             RK(T_APEX, 'AIR', (0.11, 0.12, 0.25), elbow=(0.20, -0.02, -0.05), shaft=None, w=(0.0, 0.8), hw=1.5, ori_abs=((50, 76), (-100, 0)), r_tw=-44.0, r_tw_w=3.0),
             RK(F(19), 'AIR', (0.11, 0.00, 0.29), elbow=(0.22, -0.06, 0.0), shaft=None, w=(0.0, 1.0), hw=1.5, ori_abs=((80, 79), (-115, 0)), r_tw=-54.0, r_tw_w=3.0),
             RK(T_R, 'S3.R3', (0.11, -0.08, 0.30), elbow=(0.23, -0.08, 0.04), shaft=None, w=(0.05, 1.0), hw=1.5, ori_abs=((105, 80), (-130, 0)), r_tw=-62.0, r_tw_w=3.0),
             # trophy: elbow at shoulder height out to the right, forearm up, hoop up behind the head
             RK(F(30), 'S3.R3', (0.11, -0.14, 0.30), elbow=(0.23, -0.08, 0.07), shaft=(165, 74), face=(96, -8), w=(0.6, 1.0), hw=1.5),
             RK(T_T, 'S3.R3', (0.10, -0.15, 0.30), elbow=(0.23, -0.08, 0.07), shaft=(168, 72), face=(96, -10), w=(0.6, 1.0), hw=1.5),
             # drop: the forearm falls back about the elbow, which stays out and goes behind the shoulder line; the racket hangs behind the back
             RK(F(42), 'S3.R4', (0.12, -0.22, 0.20), elbow=(0.23, -0.10, 0.06), shaft=(172, 40), face=(95, -5), w=(0.3, 1.0), hw=1.5),
             RK(F(44), 'S3.R4', (0.11, -0.30, 0.02), elbow=(0.23, -0.12, 0.04), shaft=(178, -25), face=(92, 0), w=(0.3, 1.0), hw=1.5),
             RK(T_D, 'S3.R4', (0.10, -0.32, -0.10), elbow=(0.22, -0.14, 0.03), shaft=(180, -55), face=(90, 0), w=(0.3, 1.0), hw=1.5),
             # drive: the elbow leads up and forward, the forearm and racket follow from behind, on the right side
             RK(F(47), 'S3.R4', (0.12, -0.18, 0.08), elbow=(0.22, -0.04, 0.12), shaft=(170, -5), face=(75, 0), w=(0.3, 1.0), hw=1.5),
             RK(F(49), 'S3.R5', (0.10, 0.02, 0.28), elbow=(0.18, 0.08, 0.18), shaft=(120, 40), face=(40, 0), w=(0.3, 1.0), hw=1.0, rk_abs=0.0),
             K(T_C, 'S3.C', rk_pos=rs(22, 72, 1.0), shaft=D(5, 56), face=D(0, 15), rk_sweet=[0.20, 0.55, zs], rk_abs=1.0, rk_w=[2.5, 0.5], r_hint=[0.0, 0.0, 0.0], r_hint_w=0.0),
             # follow-through: the arm keeps going forward and down along the right side, the elbow stays outside the shoulder (no swivel flip), then across the belly to the left hip
             RK(F(52), 'S3.R7', (0.26, 0.20, 0.10), elbow=(0.22, 0.06, 0.02), shaft=(18, 38), face=(-15, 35), w=(0.2, 1.0), hw=1.5, rk_abs=0.0),
             RK(F(53), 'S3.R7', (0.20, 0.32, -0.08), elbow=(0.21, 0.08, -0.07), shaft=(22, 8), face=(-45, 20), w=(0.2, 1.0), hw=1.5),
             RK(F(54), 'S3.R7', (0.10, 0.34, -0.24), elbow=(0.19, 0.08, -0.14), shaft=(20, -25), face=(-75, 10), w=(0.2, 1.0), hw=1.5),
             RK(F(56), 'S3.R7', (0.08 + (0.04 if fem else 0.0), 0.36 + (0.04 if fem else 0.0), -0.30 + (0.04 if fem else 0.0)), elbow=(0.16, 0.05, -0.18), shaft=(30, -30), face=(-75, 5), w=(0.2, 1.0), hw=1.2),
             RK(F(58), 'S3.R7', (0.04 + (0.05 if fem else 0.0), 0.30 + (0.05 if fem else 0.0), -0.37 + (0.05 if fem else 0.0)), elbow=(0.14, 0.03, -0.22), shaft=(20, -45), face=(-60, 10), w=(0.2, 1.0), hw=1.0),
             K(F(64), 'S3.R8', rk_pos=rs(30, -60, 0.65), shaft=D(25, 20), face=D(-60, 0), rk_w=[0.2, 1.0]),
             K(T_END, 'LOCK', rk_pos=[0.08, 0.55, -0.52], shaft=D(15, 68), face=D(-60, 0), rk_w=[0.2, 1.0])]

    # ------------------------------------------------------------------------------------------------ head: keeps looking at the court through the fold, then follows the ball up
    keys += [K(T_S, 'S3.H1', gaze=[0.2, 8.0, 1.25]), K(T_FOLD, 'S3.H1', gaze=[0.2, 8.0, 1.25]), K(T_PUSH, 'S3.H1', gaze=[0.1, 5.0, 1.45]),
             K(F(16), 'S3.R2', gaze=[-0.05, 0.9, 2.2]), K(T_R, 'S3.R2', gaze=[-0.10, 0.50, 2.2]), K(F(30), 'S3.R3', gaze=[-0.10, 0.50, 2.7]), K(T_T, 'S3.R3', gaze=[-0.05, 0.55, 3.3]),
             K(T_D, 'S3.R4', gaze=[0.0, 0.60, 3.2]), K(T_C, 'S3.C', gaze=[0.15, 0.62, zs]), K(F(55), 'S3.R7', gaze=[0.3, 8.0, 1.3]),
             K(F(66), 'S3.R8', gaze=[0.2, 8.0, 1.2]), K(T_END, 'LOCK', gaze=[0.0, 8.0, 1.2])]

    d = dict(name='Serve', section=3, length=LENGTH, url='rxo1uEdLouY t=178-181', contact=T_C, loop=False, thin=True,
             thin_why=['bounce not in frame (ball hidden in the left fist until t=178.75): none keyed', 'ball on the strings not seen in any serve; contact time from the ball path: 180.175 +-0.01',
                       'pelvis / shoulder angles not readable from this camera (order only)', 'slow-motion seconds are not real seconds',
                       'the pre-toss fold and hop are requested by Adnan (2026-10-03), not read from the video'],
             keys=keys)
    return d
