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
T_STEP = F(59)
T_END = F(75)
LENGTH = T_END
# --- the new events inside the wind-up
T_FOLD = F(10)                                # deepest fold (0.333)
T_PUSH = F(13)                                # toes about to leave (0.433)
T_APEX = F(17)                                # top of the hop (0.567)
T_TD = F(21)                                  # toes touch the court again (= release)


def serve(S, hero):
    LREL = [float(x) for x in os.environ.get('LREL', '-22,68,1.14').split(',')]
    fem = getattr(hero, 'tag', 'male') == 'female'
    FR = float(os.environ.get('FEM_FR', 0.02)) if fem else 0.0           # the female's skort / legs are in a different place: the racket hangs a bit further out during the fold
    FAZ = float(os.environ.get('FEM_FAZ', 15)) if fem else 0.0
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

    # Ready-centered grounded feet; no authored toe pivot before the drive.
    xr, xl = R['rf_foot'][0], R['lf_foot'][0]
    pR, pL = tuple(R['rf_foot']), tuple(R['lf_foot'])
    FT('rf', [(0,pR,0,10,0),(T_S,pR,0,10,0),(T_R,pR,0,10,0),(T_T,pR,0,10,0),
              (F(47),pR,0,10,0),(F(48),pR,.020,10,10),(F(49),(xr-.02,f0-.03),.11,10,25),
              (F(50),(xr-.04,f0-.15),.25,12,45),(T_C,(xr-.07,f0-.32),.42,15,55),
              (F(53),(.16,f0-.40),.58,15,60),(F(55),(.14,f0-.35),.40,12,55),
              (F(57),(.15,f0+.10),.18,8,30),(F(58),(.16,f0+.29),0,5,0),
              (T_STEP,(.16,f0+.34),0,5,0),(T_END,(.16,f0+.34),0,5,0)], 'R3_GROUND_DRIVE_KICK_LAND')
    FT('lf', [(0,pL,0,-10,0),(T_S,pL,0,-10,0),(T_R,pL,0,-10,0),(T_T,pL,0,-10,0),
              (F(47),pL,0,-10,0),(F(48),pL,.025,-10,8),(F(49),(xl+.005,f0+.05),.09,-8,12),
              (F(50),(xl+.01,f0-.05),.16,-5,15),(T_C,(xl+.02,f0-.15),.10,0,8),
              (F(53),(xl+.03,f0-.13),.24,0,12),(F(55),(xl+.04,f0+.20),.13,-2,10),
              (F(56),(xl+.04,f0+.39),0,-2,0),(T_LAND,(xl+.04,f0+.39),0,-2,0),
              (T_END,(xl+.04,f0+.39),0,-2,0)], 'R3_FRONT_TOUCH_1p90')

    def body(t, pel, pyaw, ppitch, proll, cyaw, cpitch, croll, src, ease=None):
        keys.append(K(t, src, ease=ease, pel=[pel[1],pel[0],pel[2]],
                      pel_rot=[pyaw,ppitch,proll],chest_rot=[cyaw-pyaw,cpitch,croll]))
    body(0,(0,0,0),0,9,0,0,8,0,'STANCE',ease=1)
    body(T_S,(0,0,0),0,9,0,0,8,0,'READY_CENTER',ease=1)
    body(F(10),(-.025,0,-.012),31,9,0,44,5,0,'ROCK_BACK')
    body(F(14),(-.01,0,-.006),34,4,0,50,-6,0,'TOSS')
    body(F(17),(0,0,0),35,2,0,55,-10,0,'TOSS')
    body(T_R,(.01,0,0),36,2,0,58,-8,0,'RELEASE')
    body(F(27),(.02,0,-.035),40,3,1,66,-10,2,'LOAD')
    body(F(33),(.025,0,-.075),48,4,2,78,-12,4,'LOAD')
    body(F(38),(.025,0,-.14),56,4,4,88,-14,6,'SQUASH',ease=1)
    body(T_T,(.025,0,-.14),58,4,4,92,-14,6,'TROPHY',ease=1)
    body(F(42),(.02,0,-.108),54,4,5,88,-14,7,'COCK')
    body(T_D,(.01,0,-.095),36,4,6,62,-14,8,'COCK')
    body(F(47),(.00,0,-.065),22,6,4,32,-14,8,'DRIVE')
    body(F(49),(-.08,0,.025),10,6,0,10,-12,-2,'EXPLODE')
    body(F(50),(-.145,0,.09),6,5,-2,0,-10,-8,'STRETCH')
    body(T_C,(-.19,0,.15),4,2,-4,-6,-8,-14,'CONTACT')
    body(F(53),(-.10,0,.19),-8,4,-4,-24,-2,-10,'APEX',ease=1)
    body(F(55),(.10,0,.12),-12,8,0,-30,4,-4,'HANG')
    body(F(56),(.20,0,.04),-18,16,0,-40,12,0,'DESCEND')
    body(F(57),(.26,0,-.035),-24,24,0,-48,20,0,'LEFT_TOUCH')
    body(F(58),(.28,0,-.075),-14,22,0,-30,16,0,'LAND_SQUASH')
    body(F(59),(.29,0,-.035),-6,13,0,-12,10,0,'REBOUND')
    body(F(59),(.28,0,-.025),0,9,0,0,8,0,'SETTLE')
    body(T_END,(.28,0,-.025),0,9,0,0,8,0,'LOCK')

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
             K(T_T, 'S3.R3', l_hand=ls(0, 80, 1.14), l_palm=D(0, 0), l_fing=0.10, l_elbow=[-0.45, -0.7, 0.0]),
             # after the trophy the toss arm folds in and comes down along the LEFT side (in front of the left ribs): the forearm never reaches across the chest
             K(F(42), 'S3.R5', l_hand=ls(-16, 62, 0.90), l_fing=0.2, l_elbow=[-0.42, -0.65, -0.35]),
             K(T_D, 'S3.R5', l_hand=ls(-26, 34, 0.74), l_fing=0.2, l_elbow=[-0.45, -0.6, -0.7]),
             K(F(47), 'S3.R5', l_hand=ls(-32, 10, 0.60), l_fing=0.25),
             K(F(49), 'S3.R5', l_hand=ls(-34, -14, 0.52), l_fing=0.3),
             K(F(53), 'S3.R6', l_hand=ls(-36, -28, 0.50), l_fing=0.3),
             K(T_LAND, 'S3.R6', l_hand=ls(-34, -12, 0.82), l_fing=0.2),
             K(F(63), 'S3.R6', l_hand=ls(-30, -40, 0.70), l_fing=0.25),
             K(F(69), 'LOCK', l_hand=ls(-30, -50, 0.6), l_attach=0.0),
             K(T_END, 'LOCK', l_hand=ls(-30, -50, 0.6), l_attach=0.0)]

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
             RK(T_FOLD, 'FOLD', (0.24 + FR, 0.08 + FF, -0.38), elbow=(0.08, 0.0, -0.22), shaft=None, w=(0.02, 1.0), hw=0.8, ori_abs=((80 + FAZ, -58), (-72, 5)), r_tw=-10.0, r_tw_w=3.0),
             # pop: the arm swings forward and UP in front of the right shoulder (elbow low, forearm forward-up, racket rising from hanging to hoop-over-handle), then the elbow lifts out
             # to the side as the hand goes back to the head for the trophy
             RK(F(12), 'POP', (0.24 + FR, 0.23 + FF / 2, -0.28), elbow=(0.10, 0.02, -0.22), shaft=None, w=(0.0, 1.0), hw=0.8, ori_abs=((40 + FAZ / 2, -28), (-75, 5)), r_tw=-14.0, r_tw_w=3.0),
             RK(F(14), 'POP', (0.08, 0.28, -0.06), elbow=(0.12, 0.05, -0.20), shaft=None, w=(0.0, 1.0), hw=1.0, ori_abs=((26, 30), (-80, 5)), r_tw=-24.0, r_tw_w=3.0),
             RK(F(15), 'AIR', (0.09, 0.26, 0.05), elbow=(0.15, 0.04, -0.16), shaft=None, w=(0.0, 0.8), hw=1.0, ori_abs=((30, 52), (-85, 5)), r_tw=-30.0, r_tw_w=3.0),
             RK(F(16), 'AIR', (0.10, 0.22, 0.14), elbow=(0.17, 0.02, -0.12), shaft=None, w=(0.0, 0.7), hw=1.2, ori_abs=((36, 68), (-90, 0)), r_tw=-36.0, r_tw_w=3.0),
             RK(T_APEX, 'AIR', (0.11, 0.12, 0.25), elbow=(0.20, -0.02, -0.05), shaft=None, w=(0.0, 0.8), hw=1.5, ori_abs=((50, 76), (-100, 0)), r_tw=-44.0, r_tw_w=3.0),
             RK(F(19), 'AIR', (0.11, 0.00, 0.29), elbow=(0.22, -0.06, 0.0), shaft=None, w=(0.0, 1.0), hw=1.5, ori_abs=((80, 79), (-115, 0)), r_tw=-54.0, r_tw_w=3.0),
             RK(T_R, 'S3.R3', (0.11, -0.08, 0.30), elbow=(0.23, -0.08, 0.04), shaft=None, w=(0.05, 1.0), hw=1.5, ori_abs=((105, 80), (-130, 0)), r_tw=-62.0, r_tw_w=3.0),
             # trophy: elbow at shoulder height out to the right, forearm up, hoop up behind the head
             RK(F(30), 'S3.R3', (0.11, -0.14, 0.30), elbow=(0.23, -0.08, 0.07), shaft=(165, 74), face=(96, -8), w=(0.6, 1.0), hw=1.5),
             RK(T_T, 'S3.R3', (0.10, -0.15, 0.30), elbow=(0.23, -0.08, 0.07), shaft=(168, 72), face=(96, -10), w=(0.6, 1.0), hw=1.5),
             # drop: the forearm falls back about the elbow, which stays out and goes behind the shoulder line; the racket hangs behind the back
             RK(F(42), 'S3.R4', (0.12, -0.22, 0.20), elbow=(0.23, -0.10, 0.06), shaft=(172, 40), face=(95, -5), w=(0.3, 1.0), hw=1.5),
             RK(F(44), 'S3.R4', (0.11, -0.30, 0.12), elbow=(0.23, -0.12, 0.04), shaft=(178, -25), face=(92, 0), w=(0.3, 1.0), hw=1.5),
             RK(T_D, 'S3.R4', (0.10, -0.32, 0.15), elbow=(0.22, -0.14, 0.03), shaft=(180, -55), face=(90, 0), w=(0.3, 1.0), hw=1.5),
             # drive: the elbow leads up and forward, the forearm and racket follow from behind, on the right side
             RK(F(47), 'S3.R4', (0.12, -0.18, 0.30), elbow=(0.22, -0.04, 0.12), shaft=(170, -5), face=(75, 0), w=(0.3, 1.0), hw=1.5),
             RK(F(49), 'S3.R5', (0.10, 0.02, 0.44), elbow=(0.18, 0.08, 0.18), shaft=(120, 40), face=(40, 0), w=(0.3, 1.0), hw=1.0, rk_abs=0.0),
             K(F(50), 'R3_CONTACT_LEAD', rk_pos=rs(22, 72, 1.0), shaft=D(5, 56), face=D(0, 15), rk_sweet=[0.20, 0.55, zs], rk_abs=1.0, rk_w=[2.5, 0.5], r_hint=[0.0, 0.0, 0.0], r_hint_w=0.0),
             K(T_C, 'S3.C', rk_pos=rs(22, 72, 1.0), shaft=D(5, 56), face=D(0, 15), rk_sweet=[0.20, 0.55, zs], rk_abs=1.0, rk_w=[2.5, 0.5], r_hint=[0.0, 0.0, 0.0], r_hint_w=0.0),
             K(F(52), 'R3_CONTACT_HOLD', rk_pos=rs(22, 72, 1.0), shaft=D(5, 56), face=D(0, 15), rk_sweet=[0.20, 0.55, zs], rk_abs=1.0, rk_w=[2.5, 0.5], r_hint=[0.0, 0.0, 0.0], r_hint_w=0.0),
             # follow-through: the arm keeps going forward and down along the right side, the elbow stays outside the shoulder (no swivel flip), then across the belly to the left hip
             RK(F(53), 'S3.R7', (0.20, 0.32, 0.40), elbow=(0.21, 0.08, -0.07), shaft=(22, 8), face=(-45, 20), w=(0.2, 1.0), hw=1.5, rk_abs=0.0),
             RK(F(54), 'S3.R7', (0.10, 0.34, 0.27), elbow=(0.19, 0.08, -0.14), shaft=(20, -25), face=(-75, 10), w=(0.2, 1.0), hw=1.5),
             RK(F(56), 'S3.R7', (0.08 + (0.04 if fem else 0.0), 0.36 + (0.04 if fem else 0.0), 0.05 + (0.04 if fem else 0.0)), elbow=(0.16, 0.05, -0.18), shaft=(30, -30), face=(-75, 5), w=(0.2, 1.0), hw=1.2),
             RK(F(58), 'S3.R7', (0.16 + (0.05 if fem else 0.0), 0.20 + (0.05 if fem else 0.0), -0.12 + (0.05 if fem else 0.0)), elbow=(0.14, 0.03, -0.22), shaft=(20, -45), face=(-60, 10), w=(0.2, 1.0), hw=1.0),
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
                       'grounded toss and one cartoon drive jump requested by Adnan (2026-10-05)'],
             keys=keys)
    return d
