"""The new Serve (SERVE_AND_FEET), authored on the same engine as the 16 match clips (work/match-anim-set/scripts: clipkit / clips / pose, imported read-only).

Order of the movement is WATCH.md section 3 (JJEDwXeDjBc is NOT used here; this clip cites only rxo1uEdLouY t=178-181).  `src` of every key names the WATCH step:
  S3.F<n> = Feet list, S3.H<n> = Hips and shoulders (coil), S3.R<n> = Shoulders / arms / racket list, S3.C = contact, S3.B = the bounce line (not in frame: nothing keyed).

Clip time is NOT video time (slow motion): the three ritual phases the game paces are authored at the game's own durations so that they play at 1x:
  stance (ball in the left fist) held at T_S,  T_S -> T_R = TennisRules.ServeWindUp (0.5 s): the left hand lifts the ball and lets it go,
  T_R -> T_T = TennisRules.ServeApex (0.62 s): the toss rises, the knees bend, hips and shoulders coil to the trophy,
  T_T -> contact: racket drop + deepest bend + drive + take-off + contact (the driver re-times this part to the gameplay swing),
  after contact: landing on the left foot, the right leg kicks back, the right foot steps through.
"""
import math

import numpy as np

import clips as CL
from clipkit import K

D = CL.D
RS = CL.RS
FPS = 30


def g(t):
    return round(t * FPS) / FPS


# --- key times (seconds, on the 30 fps grid)
T_S = g(0.20)        # stance, ball held
T_R = g(0.70)        # ball released (T_S + 0.5)
T_T = g(1.32)        # trophy / apex of the toss (T_R + 0.62)
T_D = g(1.50)        # deepest knee bend, racket dropped, hips coiled to the maximum
T_OFF = g(1.60)      # both feet leave the court
T_C = g(1.70)        # CONTACT
T_LAND = g(1.90)     # left foot lands (toe first)
T_KICK = g(2.00)     # right leg at the top of its kick-back
T_STEP = g(2.20)     # right foot steps through and plants
T_END = g(2.50)
LENGTH = T_END


def serve(S, hero):
    R = S.ready
    f0 = R['rf_foot'][1]
    rs = lambda az, el, d: RS(S, az, el, d, 'R')
    ls = lambda az, el, d: RS(S, az, el, d, 'L')
    ye = lambda side, deg: hero.toe_dir_to_yaw(side, deg)            # effective foot direction (deg, + = toes to the right) -> solver channel
    sh_z = float(S.rig.J['shoulder_L'][2])
    zs = sh_z + 0.16 + (S.A_arm + 0.10 + 0.30) - 0.10                  # contact height of the old Serve formula (scaled to THIS hero); the reach limit pulls it in
    keys = []

    def FT(side, wps, src):
        for w in wps:
            t, pos, lift, yaw, heel = w
            ch = {f'{side}_foot': list(pos), f'{side}_lift': float(lift), f'{side}_heel': float(heel), f'{side}_yaw': float(ye('R' if side == 'rf' else 'L', yaw))}
            keys.append(K(t, src, ease=1.0 if lift <= 1e-6 else None, **ch))

    # ------------------------------------------------------------------------------------------------ feet (S3.F)
    # S3.F1 stance: feet about shoulder width, flat, side-on to the net (R foot back along the baseline, L foot toward the net); weight rocks a little.
    # S3.F2-3 knees start to bend at the trophy, keep bending to the deepest bend with both feet flat (S3.F3) and about shoulder width or slightly wider.
    # S3.F4 legs extend together (heels rise first); S3.F5 both feet leave the court together, toes pointing down; S3.F6 airborne through the contact.
    # S3.F7 R leg kicks back and up while the L leg reaches down; S3.F8 L foot lands first, toe first, R leg still high behind; S3.F9 the R leg swings forward and plants
    # (first step into the court); then back to the ready stance (in place: the clip must end where it began).
    xr, xl = 0.26, -0.18
    FT('rf', [(T_S, (xr, f0 - 0.08), 0.0, 75.0, 0.0), (T_D, (xr, f0 - 0.08), 0.0, 75.0, 0.0), (g(1.56), (xr - 0.01, f0 - 0.07), 0.0, 72.0, 22.0),
              (T_OFF, (xr - 0.02, f0 - 0.04), 0.010, 70.0, 48.0), (g(1.66), (xr - 0.05, f0 + 0.05), 0.07, 62.0, 62.0), (T_C, (xr - 0.07, f0 + 0.10), 0.12, 55.0, 62.0),
              (g(1.76), (xr - 0.09, f0 + 0.04), 0.17, 45.0, 64.0), (g(1.84), (0.12, f0 - 0.20), 0.36, 32.0, 70.0), (g(1.93), (0.10, f0 - 0.42), 0.58, 22.0, 70.0),
              (T_KICK, (0.10, f0 - 0.40), 0.58, 20.0, 66.0), (g(2.07), (0.11, f0 + 0.02), 0.34, 10.0, 50.0), (g(2.14), (0.13, f0 + 0.30), 0.08, 5.0, 24.0),
              (T_STEP, (0.15, f0 + 0.36), 0.0, 5.0, 0.0), (T_END, (0.15, f0 + 0.36), 0.0, 5.0, 0.0)], 'S3.F1/S3.F3/S3.F4/S3.F5/S3.F7/S3.F9')
    FT('lf', [(T_S, (xl, f0 + 0.14), 0.0, 38.0, 0.0), (T_D, (xl, f0 + 0.14), 0.0, 38.0, 0.0), (g(1.56), (xl, f0 + 0.14), 0.0, 38.0, 20.0),
              (T_OFF, (xl, f0 + 0.15), 0.010, 36.0, 45.0), (g(1.66), (xl + 0.01, f0 + 0.20), 0.07, 28.0, 62.0), (T_C, (xl + 0.02, f0 + 0.25), 0.12, 20.0, 62.0),
              (g(1.76), (xl + 0.03, f0 + 0.31), 0.13, 10.0, 56.0), (g(1.84), (xl + 0.04, f0 + 0.37), 0.04, 2.0, 42.0), (T_LAND, (xl + 0.04, f0 + 0.39), 0.0, -2.0, 30.0),
              (g(1.97), (xl + 0.04, f0 + 0.39), 0.0, -2.0, 4.0), (T_END, (xl + 0.04, f0 + 0.39), 0.0, -2.0, 0.0)], 'S3.F1/S3.F3/S3.F4/S3.F5/S3.F8/S3.F9')

    # ------------------------------------------------------------------------------------------------ hips and shoulders (S3.H): the coil
    # S3.H1 the pelvis is turned during the load (broad -> narrow in the picture) and turns back before the take-off; S3.H2 the shoulders turn further than the hips;
    # S3.H3 order of the uncoil: legs extend (T_D), hips turn toward the net, shoulders and arm follow; after the contact the trunk keeps turning and leans forward.
    # (pelvis yaw / chest yaw are absolute here, chest_rot is written relative to the pelvis)
    def body(t, pel, pyaw, ppitch, proll, cyaw, cpitch, croll, src):
        keys.append(K(t, src, pel=[pel[1], pel[0], pel[2]], pel_rot=[pyaw, ppitch, proll], chest_rot=[cyaw - pyaw, cpitch, croll]))      # pel is written (forward, right, up); the channel is [r, f, u]
    body(T_S, (0.0, 0.0, 0.0), 30, 9, 0, 42, 8, 0, 'S3.H1')
    body(g(0.45), (0.0, 0.0, 0.005), 33, 9, 0, 48, 8, 0, 'S3.H1')
    body(T_R, (0.01, 0.0, 0.01), 36, 8, 0, 56, 6, 0, 'S3.H1')
    body(g(1.00), (0.0, 0.0, -0.02), 46, 6, 2, 74, -2, 4, 'S3.H1/S3.F2')
    body(T_T, (-0.01, 0.0, -0.055), 58, 4, 4, 92, -10, 6, 'S3.H1/S3.H2')
    body(T_D, (-0.02, 0.0, -0.20), 70, 4, 6, 108, -14, 8, 'S3.H1/S3.F3')
    body(g(1.56), (0.00, 0.0, -0.14), 52, 6, 4, 90, -14, 8, 'S3.H3/S3.F4')
    body(g(1.63), (0.04, 0.0, -0.02), 28, 6, 0, 58, -12, -2, 'S3.H3/S3.F4')
    body(g(1.67), (0.09, 0.0, 0.08), 12, 5, -2, 26, -10, -8, 'S3.H3/S3.F5')
    body(T_C, (0.15, 0.0, 0.15), 4, 2, -4, -6, -8, -14, 'S3.C/S3.H3')
    body(g(1.76), (0.19, 0.0, 0.16), -8, 4, -4, -24, -2, -10, 'S3.H3/S3.F6')
    body(g(1.84), (0.22, 0.0, 0.08), -22, 14, 0, -44, 12, -4, 'S3.H3/S3.F7')
    body(T_LAND, (0.24, 0.0, -0.04), -26, 24, 0, -50, 20, 0, 'S3.F8')
    body(T_KICK, (0.26, 0.0, -0.10), -22, 28, 0, -46, 22, 0, 'S3.F8')
    body(g(2.10), (0.28, 0.0, -0.08), -14, 22, 0, -30, 16, 0, 'S3.F9')
    body(T_STEP, (0.29, 0.0, -0.05), -8, 16, 0, -16, 12, 0, 'S3.F9')
    body(T_END, (0.28, 0.0, 0.0), 0, 9, 0, 0, 8, 0, 'LOCK')

    # ------------------------------------------------------------------------------------------------ the tossing (left) arm holds the ball (S3.R)
    # S3.R1 left fist with the ball in front of the thigh / racket throat; S3.R2 the left hand lifts the ball in front of the body, arm nearly straight, ball released
    # (T_R); S3.R3 arm straight up pointing at the ball (trophy); stays up through the deepest bend and folds in from T_D + 0.05 (S3.R5); after the contact it swings out for balance.
    # frame 0 already holds the ball in the fist (the same pose as the stance key): the hand does not dip on its way to the stance (nothing like a bounce), and the game's cross-fade from ReadyIdle does the settling
    # SERVE_TOSS_ARM: the left hand rises WITH the ball.  The game moves the ball from the stance point to the release point by smoothstep over the wind-up (T_S -> T_R), so the hand is
    # keyed on that same path (p0 + (p1 - p0) * smoothstep) and the arm is straight, hand above the head, at the release; it then finishes the reach straight up (0.90 s) and holds.
    p0 = np.array([-0.15, 0.52, -0.66]); p1 = np.array(ls(-30, 36, 1.25))   # the shoulder girdle rises with the arm (clavicle), so a straight arm needs a target beyond 1.0 arm length; the solver clamps it to the straight arm
    sm = lambda u: u * u * (3 - 2 * u)
    on_path = lambda t: list(p0 + (p1 - p0) * sm((t - T_S) / (T_R - T_S)))
    keys += [K(0.0, 'S3.R1', l_attach=0.0, l_hand=[-0.15, 0.52, -0.66], l_palm=D(0, 70), l_fing=0.55, l_elbow=[-0.4, -0.6, -0.7]),
             K(T_S, 'S3.R1', l_attach=0.0, l_hand=[-0.15, 0.52, -0.66], l_palm=D(0, 70), l_fing=0.55, l_elbow=[-0.4, -0.6, -0.7]),
             K(g(0.325), 'S3.R2', l_hand=on_path(g(0.325)), l_palm=D(0, 66), l_fing=0.5, l_elbow=[-0.4, -0.6, -0.65]),
             K(g(0.45), 'S3.R2', l_hand=on_path(g(0.45)), l_palm=D(0, 60), l_fing=0.45, l_elbow=[-0.45, -0.6, -0.45]),
             K(g(0.575), 'S3.R2', l_hand=on_path(g(0.575)), l_palm=D(0, 52), l_fing=0.35, l_elbow=[-0.5, -0.65, -0.2]),
             K(T_R, 'S3.R2', l_hand=list(p1), l_palm=D(0, 45), l_fing=0.20, l_elbow=[-0.5, -0.7, 0.0]),
             K(g(0.90), 'S3.R3', l_hand=ls(0, 86, 1.25), l_palm=D(0, 20), l_fing=0.12, l_elbow=[-0.45, -0.7, 0.0]),
             K(g(1.17), 'S3.R3', l_hand=ls(0, 88, 1.25), l_palm=D(0, 5), l_fing=0.10, l_elbow=[-0.45, -0.7, 0.0]),
             K(g(1.23), 'S3.R3', l_hand=ls(1, 86, 1.13), l_palm=D(0, 3), l_fing=0.10, l_elbow=[-0.45, -0.7, 0.0]),
             K(T_T, 'S3.R3', l_hand=ls(2, 82, 1.04), l_palm=D(0, 0), l_fing=0.10, l_elbow=[-0.45, -0.7, 0.0]),
             # SERVE_ARMS: the toss arm leaves the ball at the trophy and comes down in front of the chest while the legs load (it used to stay straight up to 1.5 s)
             K(g(1.40), 'S3.R5', l_hand=ls(8, 62, 0.92), l_fing=0.2, l_elbow=[-0.42, -0.65, -0.35]),
             K(T_D, 'S3.R5', l_hand=ls(16, 32, 0.74), l_fing=0.2, l_elbow=[-0.4, -0.6, -0.7]),
             K(g(1.58), 'S3.R5', l_hand=ls(20, 8, 0.56), l_fing=0.25),
             K(g(1.65), 'S3.R5', l_hand=ls(18, -14, 0.46), l_fing=0.3),
             K(g(1.76), 'S3.R6', l_hand=ls(26, -30, 0.46), l_fing=0.3),
             K(T_LAND, 'S3.R6', l_hand=ls(-34, -12, 0.82), l_fing=0.2),
             K(g(2.10), 'S3.R6', l_hand=ls(-30, -40, 0.70), l_fing=0.25),
             K(g(2.30), 'LOCK', l_hand=ls(-30, -50, 0.6), l_attach=0.0),
             K(T_END, 'LOCK', l_attach=1.0, l_grip=0.0)]

    # ------------------------------------------------------------------------------------------------ racket arm (S3.R)
    # S3.R1 the racket hangs low in the right hand; S3.R2 it swings back and up as the toss arm rises; S3.R3 trophy: elbow at shoulder height, racket head up and behind;
    # S3.R4 the racket drops behind the back, torso arched; S3.R5 the arm swings up to full extension; S3.C contact at the top; S3.R7 the racket swings down across
    # the body to the left hip; S3.R8 it arrives at the hip as the left foot plants.
    # SERVE_TOSS_ARM: the racket turns as the toss arm rises: it dips behind the hip, swings up, and by the release (left arm straight up) the head is above the handle beside the right ear.
    keys += [K(T_S, 'S3.R1', rk_pos=[0.12, 0.50, -0.70], shaft=D(5, -35), face=D(-70, 0), rk_w=[0.2, 1.0]),
             K(g(0.27), 'S3.R1', rk_pos=[0.14, 0.50, -0.70], shaft=D(5, -35), face=D(-70, 0), rk_w=[0.2, 1.0]),    # 2 cm outward of the stance: the racket leaves the thigh (the stance touches it by 4-14 mm)
             # SERVE_TOSS_ARM (WATCH S3.R2: "racket vertical in front of the chest" at the release): the hand and the racket RISE in front of the body with the toss arm: the shaft turns from
             # forward-down through forward to vertical (head above the handle beside the right ear) by the release, then tilts back to the trophy while the left arm is straight up.
             # The face stays where the grip puts it until the head is vertical, then turns to the trophy face of the approved clip (about the near-vertical shaft: no visible motion).
             K(g(0.40), 'S3.R2', rk_pos=rs(60, -45, 0.58), shaft=D(8, 0), face=D(-75, 10), rk_w=[0.6, 1.0]),
             K(g(0.50), 'S3.R2', rk_pos=rs(62, -22, 0.56), shaft=D(15, 38), face=D(-75, 10), rk_w=[0.6, 1.0]),
             K(g(0.60), 'S3.R2', rk_pos=rs(70, -2, 0.54), shaft=D(25, 68), face=D(-80, 5), rk_w=[0.6, 1.0]),
             K(T_R, 'S3.R3', rk_pos=rs(85, 12, 0.52), shaft=D(40, 80), face=D(-100, 0), rk_w=[0.6, 1.0]),
             K(g(0.80), 'S3.R3', rk_pos=rs(110, 20, 0.50), shaft=D(100, 80), face=D(-140, -5), rk_w=[0.6, 1.0]),
             K(g(0.90), 'S3.R3', rk_pos=rs(125, 20, 0.50), shaft=D(150, 72), face=D(-175, -12), rk_w=[0.6, 1.0]),
             K(g(1.00), 'S3.R3', rk_pos=rs(135, 20, 0.50), shaft=D(165, 68), face=D(176, -20), rk_w=[0.6, 1.0]),
             K(T_T, 'S3.R3', rk_pos=rs(125, 42, 0.45), shaft=D(160, 74), face=D(-172, -15), rk_w=[0.6, 1.0]),
             # SERVE_ARMS: the racket drops behind the shoulder but the hand stays outside the ribs (az 105-120), then the arm drives up and FORWARD to full reach: contact in front of the head
             K(g(1.42), 'S3.R4', rk_pos=rs(118, 28, 0.52), shaft=D(165, 30), face=D(-70, 0), rk_w=[0.2, 1.0]),
             K(T_D, 'S3.R4', rk_pos=rs(108, 14, 0.58), shaft=D(172, -25), face=D(-80, -5), rk_w=[0.2, 1.0]),
             K(g(1.57), 'S3.R4', rk_pos=rs(85, 40, 0.72), shaft=D(130, 25), face=D(-50, 0), rk_w=[0.2, 1.0]),
             K(g(1.63), 'S3.R5', rk_pos=rs(50, 66, 0.88), shaft=D(70, 50), face=D(-15, 10), rk_w=[0.2, 1.0], rk_abs=0.0),
             K(T_C, 'S3.C', rk_pos=rs(22, 72, 1.0), shaft=D(5, 56), face=D(0, 15), rk_sweet=[0.20, 0.55, zs], rk_abs=1.0, rk_w=[2.5, 0.5]),
             K(g(1.80), 'S3.R7', rk_pos=rs(-10, 0, 0.80), shaft=D(-40, 20), face=D(-20, 20), rk_abs=0.0, rk_w=[0.2, 1.0]),
             K(g(1.95), 'S3.R7', rk_pos=rs(-5, -55, 0.65), shaft=D(-50, -10), face=D(-40, 10), rk_w=[0.2, 1.0]),
             K(g(2.15), 'S3.R8', rk_pos=rs(30, -60, 0.65), shaft=D(25, 20), face=D(-60, 0), rk_w=[0.2, 1.0]),
             K(T_END, 'LOCK', rk_pos=[0.08, 0.55, -0.52], shaft=D(15, 68), face=D(-60, 0), rk_w=[0.2, 1.0])]

    # ------------------------------------------------------------------------------------------------ head: follows the ball (S3.R3: head tilted back at the trophy)
    keys += [K(T_S, 'S3.H1', gaze=[0.2, 8.0, 1.25]), K(g(0.50), 'S3.H1', gaze=[0.2, 8.0, 1.25]),
             K(T_R, 'S3.R2', gaze=[-0.10, 0.40, 1.6]), K(g(1.00), 'S3.R3', gaze=[-0.10, 0.50, 2.7]), K(T_T, 'S3.R3', gaze=[-0.05, 0.55, 3.3]),
             K(T_D, 'S3.R4', gaze=[0.0, 0.60, 3.2]), K(T_C, 'S3.C', gaze=[0.15, 0.62, zs]), K(g(1.84), 'S3.R7', gaze=[0.3, 8.0, 1.3]),
             K(g(2.20), 'S3.R8', gaze=[0.2, 8.0, 1.2]), K(T_END, 'LOCK', gaze=[0.0, 8.0, 1.2])]

    d = dict(name='Serve', section=3, length=LENGTH, url='rxo1uEdLouY t=178-181', contact=T_C, loop=False, thin=True,
             thin_why=['bounce not in frame (ball hidden in the left fist until t=178.75): none keyed', 'ball on the strings not seen (contact time from the ball path: 180.175 +-0.01)',
                       'pelvis / shoulder angles not readable from this camera (order only)', 'slow-motion seconds are not real seconds'],
             keys=keys)
    return d
