"""The 16 match clips, authored from work/match-anim-set/WATCH.md only.  `build(name, solver)` returns the clip dict.

Authoring frame: r = hero's right, f = forward (towards the net), u = up.  Hand / racket positions are in ARM-LENGTH units relative to the
shoulder (so the same numbers scale to both heroes); feet / pelvis offsets are metres.  `src` names the WATCH.md step each key comes from:
S<section>.<F|R|C>.<n> = section, F = Feet list, R = Shoulders-and-racket list, C = contact line.  READY = anchor pose.  LOCK = a brief lock."""
import math

import numpy as np

from clipkit import K

URL = {
    1: 'HI0bvG0pw4w t=21.5-22.9', 2: 'DGIkkdxMrWc t=1015.90-1016.40', 3: 'DGIkkdxMrWc t=10.19-12.16', 4: 'HI0bvG0pw4w t=150.0-156.5',
    5: 'DGIkkdxMrWc t=7.60-9.90', 6: 'yAM1j_B6yQs t=0.00-1.37', 7: 'HI0bvG0pw4w t=145.5-150.0', 9: '-Eu80hGbgVA t=164.0-176.0',
    10: '0a_DL1I4q38 t=17.40-22.10', 12: 'rxo1uEdLouY t=178.0-181.2', 13: 'DGIkkdxMrWc t=635.48-637.98', 14: 'DGIkkdxMrWc t=835.28-839.09',
    15: 'DGIkkdxMrWc t=865.30-866.60', 16: 'bvVXmtHt0DM t=447.60-449.90', 17: 'ebS3Lf25hZ0 t=3.40-18.70', 18: 'WBfw9nFojHc t=64.50-68.00',
}
SECTION = dict(ReadyIdle=1, SplitToForehand=2, SplitToBackhand=3, RecoverCenter=4, Forehand=5, ForehandOpen=6, ForehandWide=7, ForehandShort=18,
               Backhand=9, BackhandWide=10, SliceApproach=17, Serve=12, Return=13, VolleyForehand=14, VolleyBackhand=15, Overhead=16)
LENGTH = dict(ReadyIdle=2.2, SplitToForehand=0.6, SplitToBackhand=0.6, RecoverCenter=0.8, Forehand=1.2, ForehandOpen=1.0, ForehandWide=1.3,
              ForehandShort=1.0, Backhand=1.2, BackhandWide=1.3, SliceApproach=1.2, Serve=1.6, Return=0.9, VolleyForehand=0.7, VolleyBackhand=0.7,
              Overhead=1.2)
THIN = dict(ForehandOpen=['take-back / unit turn not in the clip (S6 says use the S5 whole-swing shape)', 'L-foot landing not seen'],
            ForehandWide=['exact order of the last two steps could not be read'],
            ForehandShort=['take-back hidden', 'strides before the cut at t=64.50 not in frame'],
            SliceApproach=['contact not in frame (ball hidden behind the body)', 'strings / racket face / cut under the ball not seen', 'speed-ramped video seconds'],
            Serve=['ball on the strings not seen in any serve; contact time inferred from the racket apex'],
            Return=['strings-contact frame not seen (ball tiny)', 'two hands assumed from the swing shape'],
            VolleyForehand=['foot order in the last 0.3 s before contact not seen'],
            VolleyBackhand=['foot-by-foot order not seen'],
            Overhead=['ball hidden behind the arm at the contact frame'])


def base(name, **kw):
    d = dict(name=name, section=SECTION[name], length=LENGTH[name], url=URL[SECTION[name]], contact=None, loop=False, thin=name in THIN,
             thin_why=THIN.get(name, []), keys=[])
    d.update(kw)
    return d


def sw(v):
    """feet / pelvis metres are written for a 0.40 m shoulder-width reference"""
    return v


# ---------------------------------------------------------------------------------------------------------------- 1. ReadyIdle
def ReadyIdle(S):
    R = S.ready
    L = LENGTH['ReadyIdle']
    keys = []
    # S1: both feet flat, only weight sway of a few centimetres; hands together at the belly, racket in front (no cyclic bob).
    # Four keys per loop: sway to the right foot, settle, sway to the left, settle.  Last key == first key (loop).
    def k(t, dx, dz, pit, rk_dr, rk_du):
        return K(t, 'S1.F3/S1.F4/S1.R3', ease=0.0,
                 pel=[dx, 0.0, dz], chest_rot=[0.6 * dx * 40, 8.0 + pit, 0.0],
                 rk_pos=[R['rk_pos'][0] + rk_dr, R['rk_pos'][1], R['rk_pos'][2] + rk_du])
    keys = [k(0.0, 0.0, 0.0, 0.0, 0.0, 0.0), k(0.55, 0.018, -0.004, 0.6, 0.006, -0.004), k(1.10, 0.0, 0.0, 0.0, 0.0, 0.0),
            k(1.65, -0.018, -0.004, 0.6, -0.006, -0.004), k(2.2, 0.0, 0.0, 0.0, 0.0, 0.0)]
    return base('ReadyIdle', loop=True, keys=keys)


# helpers -------------------------------------------------------------------------------------------------------------------
def D(az, el):
    """unit direction in the authoring frame: az 0 = forward, +90 = right, 180 = back, -90 = left; el = elevation above horizontal (deg)"""
    a, e = math.radians(az), math.radians(el)
    return [math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)]


def PP(az, el, d):
    return [d * x for x in D(az, el)]


def RS(S, az, el, d, side='R'):
    """chest-centre-relative target (arm-length units) for a point at (az, el, distance d in arm lengths) from the hero's own RIGHT (or LEFT) shoulder joint"""
    half = S.shoulder_w / 2.0 / S.A_arm
    v = PP(az, el, d)
    v[0] += half if side == 'R' else -half
    return v


# ---------------------------------------------------------------------------------------------------------------- forehand swing generator
def fh_swing(S, tm, src, sweet, yaw_load=(55, 52), yaw_c=(-14, 10), yaw_fin=(-60, -48), lean=(10, 8), sweet_post=None, fin_hand=None, l_chin=None, l_load=None, fin_shaft=None, c_shaft=None, wrap_el=(30, 20)):
    """torso + racket + off-hand keys of a right-handed forehand (WATCH S5 order).  tm: times of 'turn','vert','load','drop','fwd','c','post','wrap','peak','back'.
    Positions chest-relative; racket orientation in the stance frame (az 0 = net, +90 = right sideline, 180 = back fence)."""
    rs = lambda az, el, d: RS(S, az, el, d, 'R')
    ls = lambda az, el, d: RS(S, az, el, d, 'L')
    p0, c0 = lean
    keys = [
        K(tm['turn'], src['turn'], pel_rot=[25, p0 - 1, 0], chest_rot=[20, c0, 0]),
        K(tm['vert'], src['vert'], pel_rot=[45, p0, 0], chest_rot=[45, c0, 0]),
        K(tm['load'], src['load'], pel_rot=[yaw_load[0], p0, 0], chest_rot=[yaw_load[1], c0, 0]),
        K(tm['drop'], src['drop'], pel_rot=[yaw_load[0] - 5, p0, 0], chest_rot=[yaw_load[1] - 2, c0, 0]),
        K(tm['fwd'], src['fwd'], pel_rot=[8, p0 + 2, 0], chest_rot=[32, c0 - 2, 0]),
        K(tm['c'], src['c'], pel_rot=[yaw_c[0], p0 + 2, 0], chest_rot=[yaw_c[1], c0 - 2, -3]),
        K(tm['wrap'], src['wrap'], pel_rot=[-45, p0 - 2, 0], chest_rot=[-38, c0 - 4, 0]),
        K(tm['peak'], src['peak'], pel_rot=[yaw_fin[0], p0 - 4, 0], chest_rot=[yaw_fin[1], c0 - 4, 0]),
        # racket
        K(tm['turn'], src['turn'], rk_pos=[0.08, 0.55, -0.52], shaft=D(15, 68), face=D(-60, 0), rk_w=[0.2, 1.0]),
        K(tm['vert'], src['vert'], rk_pos=[0.22, 0.48, -0.30], shaft=D(45, 80), face=D(0, 0), rk_w=[0.2, 1.0]),
        K(tm['load'], src['load'], rk_pos=rs(118, 22, 0.55), shaft=D(120, 70), face=D(15, 5), rk_w=[0.2, 1.0], l_attach=0.0),
        K(tm['drop'], src['drop'], rk_pos=rs(118, -50, 0.62), shaft=D(150, -30), face=D(-20, -10), rk_w=[0.2, 1.0]),
        K(tm['fwd'], src['fwd'], rk_pos=rs(88, -55, 0.70), shaft=D(125, -30), face=D(-10, -20), rk_w=[0.2, 1.0], rk_abs=0.0),
        K(tm['c'], src['c'], rk_pos=rs(45, -40, 0.85), shaft=c_shaft or D(80, 28), face=D(0, 0), rk_sweet=sweet, rk_abs=1.0, rk_w=[2.5, 0.5]),
        K(tm['post'], src['c'], rk_sweet=sweet_post or [sweet[0] - 0.02, sweet[1] + 0.09, sweet[2] + 0.02], rk_abs=0.6),
        K(tm['wrap'], src['wrap'], rk_pos=rs(-30, wrap_el[0], 0.70), shaft=D(-100, wrap_el[1]), face=D(-150, 10), rk_abs=0.0, rk_w=[0.2, 1.0]),
        K(tm['peak'], src['peak'], rk_pos=fin_hand or rs(-25, 40, 0.50), shaft=fin_shaft or D(-120, 35), face=D(-160, 20), rk_w=[0.2, 1.0]),
        K(tm['back'], 'LOCK', l_attach=1.0),
        # left arm: takes the throat (vert); lets go and extends toward the ball (load); folds in (fwd)
        K(tm['vert'] + 0.03, src['vert'], l_attach=1.0),
        K(tm['load'] + 0.02, src['load'], l_attach=0.0, l_hand=l_load or ls(-80, 8, 0.95), l_palm=D(-30, -60)),
        K(tm['drop'], src['drop'], l_attach=0.0, l_hand=l_load or ls(-80, 8, 0.95)),
        K(tm['fwd'], src['fwd'], l_attach=0.0, l_hand=l_chin or ls(-30, -25, 0.60)),
        K(tm['wrap'] + 0.04, src['wrap'], l_attach=0.0, l_hand=l_chin or ls(-20, -35, 0.55)),
    ]
    return keys


# ---------------------------------------------------------------------------------------------------------------- 5. Forehand
def Forehand(S):
    R = S.ready
    L = LENGTH['Forehand']
    W = 0.66
    f0 = R['rf_foot'][1]

    def T(video):                                   # video seconds (DGIkk) -> clip seconds: 7.59 .. 9.79 (2.2 s) onto 1.2 s
        return round((video - 7.59) / 2.2 * L * 30) / 30
    tm = dict(turn=T(7.74), vert=T(8.04), load=T(8.38), drop=T(8.69), fwd=T(8.84), c=T(8.99), post=T(9.04), wrap=T(9.19), peak=T(9.45), back=T(9.79))
    src = dict(turn='S5.R2', vert='S5.R2/S5.R3', load='S5.R4', drop='S5.R5', fwd='S5.R6', c='S5.R7/S5.C', wrap='S5.R8', peak='S5.R9')
    keys = fh_swing(S, tm, src, sweet=[0.62, 0.66, 1.00])
    keys += [
        # --- feet (S5 feet list)
        K(T(7.74), 'S5.F2', rf_foot=[W / 2, f0], lf_foot=[-W / 2, f0 + 0.02], lf_heel=14.0, pel=[0.05, 0.0, -0.01]),
        K(T(7.89), 'S5.F3', lf_foot=[-W / 2 - 0.05, f0 + 0.02], lf_heel=0.0),
        K(T(8.04), 'S5.F4', lf_heel=12.0, pel=[0.07, 0.0, -0.03]),
        K(T(8.19), 'S5.F5', lf_heel=0.0, pel=[0.10, 0.0, -0.04]),
        K(T(8.49), 'S5.F6', pel=[0.12, 0.0, -0.06], lf_foot=[-W / 2 - 0.05, f0 + 0.10]),
        K(T(8.74), 'S5.F6', pel=[0.12, 0.0, -0.06]),
        K(T(8.89), 'S5.F7', rf_heel=14.0, pel=[0.06, 0.0, -0.05]),
        K(T(8.99), 'S5.F8', rf_heel=8.0, pel=[0.0, 0.03, -0.04]),
        K(T(9.04), 'S5.F9', rf_heel=40.0),
        K(T(9.19), 'S5.F9', rf_heel=45.0, rf_foot=[W / 2 - 0.12, f0 + 0.12], pel=[-0.05, 0.06, -0.02]),
        K(T(9.34), 'S5.F10', rf_heel=0.0, rf_foot=[W / 2 - 0.10, f0 + 0.10], lf_foot=[-W / 2 - 0.05, f0 + 0.10], pel=[-0.03, 0.04, 0.0]),
        K(T(9.64), 'S5.F11', rf_foot=[W / 2, f0], lf_foot=[-W / 2, f0 + 0.02], pel=[0.0, 0.0, 0.0]),
    ]
    return base('Forehand', contact=T(8.99), keys=keys)


# ---------------------------------------------------------------------------------------------------------------- 6. ForehandOpen
def ForehandOpen(S):
    R = S.ready
    W = 0.74
    f0 = R['rf_foot'][1]
    # S6: the clip starts at the low point of the loop (no unit turn / take-back in it): the take-back is borrowed from S5 as S6 instructs, with the
    # S5 whole-swing contact fraction 0.74 (window 0.05 .. 0.79 s -> contact 0.60 s).  S6 supplies the open stance (feet parallel to the baseline,
    # chest square to the net at contact), the weight on the R leg alone with the L foot 10-15 cm off the ground, the off-hand up at the chin and the high finish.
    tm = dict(turn=0.12, vert=0.22, load=0.31, drop=0.42, fwd=0.52, c=0.60, post=0.64, wrap=0.70, peak=0.79, back=1.0)
    src = dict(turn='S5.R2', vert='S5.R3', load='S5.R4', drop='S5.R5', fwd='S6.R2', c='S6.R3/S6.C', wrap='S6.R4', peak='S6.R6')
    chin = [0.02, 0.58, 0.32]
    keys = fh_swing(S, tm, src, sweet=[0.60, 0.62, 0.92], yaw_load=(50, 55), yaw_c=(-26, 26), yaw_fin=(-55, -38), lean=(9, 7),
                    fin_hand=RS(S, -20, 62, 0.45, 'R'), fin_shaft=D(-150, 55), l_chin=chin, l_load=chin, c_shaft=D(55, 8), wrap_el=(52, 58))
    keys += [K(0.90, 'LOCK', rk_pos=[0.04, 0.55, -0.20], shaft=D(-30, 66), face=D(-100, 0), rk_w=[0.2, 1.0], l_attach=0.6, l_hand=[-0.1, 0.5, -0.1])]
    keys += FT('rf', [(0.04, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0), (0.08, (0.36, f0 + 0.01), 0.04, 5.0, 0.0), (0.12, (W / 2, f0), 0.0, 0.0, 0.0),
                      (0.64, (W / 2, f0), 0.0, 0.0, 0.0), (0.72, (W / 2, f0), 0.0, 0.0, 35.0), (0.80, (W / 2, f0), 0.0, 0.0, 30.0), (0.88, (W / 2, f0), 0.0, 0.0, 0.0),
                      (0.96, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0)], 'S6.F1/S6.F3')
    keys += FT('lf', [(0.04, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0), (0.08, (-0.36, f0 + 0.03), 0.04, -5.0, 0.0), (0.12, (-W / 2, f0 + 0.02), 0.0, 0.0, 0.0),
                      (0.28, (-W / 2, f0 + 0.02), 0.0, 0.0, 0.0), (0.36, (-0.24, f0 + 0.04), 0.13, 0.0, 55.0), (0.84, (-0.24, f0 + 0.04), 0.13, 0.0, 55.0),
                      (0.92, (-0.28, f0 + 0.02), 0.05, -4.0, 20.0), (0.97, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0)], 'S6.F2/LOCK')
    keys += BODY([(0.12, (0.04, 0.0, -0.02), None, None), (0.22, (0.14, 0.0, -0.04), None, None), (0.31, (0.26, 0.0, -0.08), None, None),
                  (0.52, (0.28, 0.0, -0.09), None, None), (0.60, (0.26, 0.03, -0.06), None, None), (0.72, (0.18, 0.04, -0.03), None, None),
                  (0.88, (0.08, 0.02, -0.01), None, None), (0.97, (0.0, 0.0, 0.0), None, None)], 'S6.F1')
    return base('ForehandOpen', contact=0.60, keys=keys)


# ---------------------------------------------------------------------------------------------------------------- 7. ForehandWide
def ForehandWide(S):
    R = S.ready
    W = 0.66
    f0 = R['rf_foot'][1]
    tm = dict(turn=0.44, vert=0.50, load=0.56, drop=0.76, fwd=0.84, c=0.89, post=0.93, wrap=0.97, peak=1.04, back=1.3)
    src = dict(turn='S7.R2', vert='S7.R2', load='S7.R2', drop='S7.R3', fwd='S7.R4', c='S7.R5/S7.C', wrap='S7.R6', peak='S7.R6')
    keys = fh_swing(S, tm, src, sweet=[1.10, 0.38, 0.95], yaw_load=(38, 62), yaw_c=(-5, -6), yaw_fin=(-38, -34), lean=(15, 10),
                    sweet_post=[1.02, 0.50, 1.02])
    # S7.R1: racket carried in front at chest height in both hands, head up, body leaning forward, while running to his R (in place: lateral plants)
    keys += [K(0.04, 'S7.R1', rk_pos=[0.08, 0.50, -0.30], shaft=D(15, 74), face=D(-60, 0), rk_w=[0.2, 1.0], pel_rot=[8, 15, 0], chest_rot=[6, 10, 0]),
             K(0.40, 'S7.R1', rk_pos=[0.08, 0.50, -0.30], shaft=D(15, 74), face=D(-60, 0), rk_w=[0.2, 1.0], pel_rot=[10, 15, 0], chest_rot=[8, 10, 0])]
    # S7.F: alternating strides towards his R (4-5 plants), the last steps shorten and the knees bend; the order of the last two steps could not be read
    # -> the strides go straight into the planted wide lunge (outside R leg loaded, trailing L leg extended behind on its toes)
    keys += FT('rf', [(0.03, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0), (0.09, (0.42, f0 + 0.06), 0.10, 10.0, 0.0), (0.15, (0.50, f0 + 0.08), 0.0, 15.0, 0.0),
                      (0.27, (0.50, f0 + 0.08), 0.0, 15.0, 0.0), (0.33, (0.58, f0 + 0.08), 0.10, 15.0, 0.0), (0.39, (0.66, f0 + 0.10), 0.0, 20.0, 0.0),
                      (0.47, (0.66, f0 + 0.10), 0.0, 20.0, 0.0), (0.53, (0.84, f0 + 0.12), 0.08, 30.0, 0.0), (0.58, (0.90, f0 + 0.13), 0.0, 38.0, 0.0),
                      (1.00, (0.90, f0 + 0.13), 0.0, 38.0, 0.0), (1.08, (0.74, f0 + 0.10), 0.05, 25.0, 0.0), (1.15, (0.60, f0 + 0.05), 0.0, 15.0, 0.0),
                      (1.22, (R['rf_foot'][0], f0), 0.02, 10.0, 0.0), (1.28, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0)], 'S7.F1/S7.F2/S7.F4')
    keys += FT('lf', [(0.03, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0), (0.06, (-0.20, f0 + 0.04), 0.10, -8.0, 0.0), (0.12, (0.02, f0 + 0.08), 0.0, -5.0, 0.0),
                      (0.21, (0.02, f0 + 0.08), 0.0, -5.0, 0.0), (0.24, (0.18, f0 + 0.08), 0.12, 0.0, 0.0), (0.30, (0.30, f0 + 0.10), 0.0, 0.0, 0.0),
                      (0.36, (0.30, f0 + 0.10), 0.0, 0.0, 0.0), (0.40, (0.26, f0 + 0.04), 0.10, 0.0, 20.0), (0.48, (0.18, f0 - 0.14), 0.05, 5.0, 45.0),
                      (0.58, (0.10, f0 - 0.26), 0.0, 5.0, 58.0), (1.00, (0.10, f0 - 0.26), 0.0, 5.0, 58.0), (1.07, (0.12, f0 - 0.16), 0.08, 0.0, 30.0),
                      (1.14, (-0.10, f0 - 0.02), 0.10, -4.0, 0.0), (1.20, (-0.30, f0 + 0.02), 0.04, -10.0, 0.0), (1.28, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0)], 'S7.F3/S7.F4')
    keys += BODY([(0.03, (0.0, 0.0, 0.0), None, None), (0.15, (0.10, 0.02, -0.02), None, None), (0.30, (0.22, 0.03, -0.03), None, None),
                  (0.47, (0.34, 0.03, -0.06), None, None), (0.58, (0.46, 0.0, -0.10), None, None), (0.84, (0.46, 0.0, -0.10), None, None),
                  (0.89, (0.44, 0.02, -0.09), None, None), (1.00, (0.42, 0.03, -0.08), None, None), (1.10, (0.28, 0.02, -0.04), None, None),
                  (1.20, (0.08, 0.0, -0.01), None, None), (1.28, (0.0, 0.0, 0.0), None, None)], 'S7.F3')
    return base('ForehandWide', contact=0.89, keys=keys)


# ---------------------------------------------------------------------------------------------------------------- 18. ForehandShort
def ForehandShort(S):
    R = S.ready
    W = 0.66
    f0 = R['rf_foot'][1]
    rs = lambda az, el, d: RS(S, az, el, d, 'R')
    ls = lambda az, el, d: RS(S, az, el, d, 'L')
    keys = []
    # S18: run-in diagonally forward (strides alternate, body leaning forward), gather step with the feet together, lunge onto the R foot with the L leg trailing
    # on its toes; racket hand low at the R side with the head below the hand (the take-back itself is hidden -> the ready hold goes straight to this pose),
    # L arm out to the left as a counterweight; contact at hip height ahead of the R hip with the racket going low to high; after the hit both feet
    # side by side, racket vertical above the head, then over and down behind the head (wrap), then down to the R side.
    keys += FT('rf', [(0.03, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0), (0.09, (0.30, f0 + 0.16), 0.10, 8.0, 0.0), (0.14, (0.28, f0 + 0.20), 0.0, 8.0, 0.0),
                      (0.19, (0.24, f0 + 0.04), 0.06, 5.0, 0.0), (0.24, (0.16, f0 + 0.02), 0.0, 5.0, 0.0),
                      (0.27, (0.16, f0 + 0.02), 0.0, 5.0, 0.0), (0.31, (0.34, f0 + 0.38), 0.10, 15.0, 0.0), (0.35, (0.40, f0 + 0.46), 0.0, 20.0, 0.0),
                      (0.52, (0.40, f0 + 0.46), 0.0, 20.0, 0.0), (0.58, (0.34, f0 + 0.30), 0.0, 12.0, 0.0), (0.70, (0.30, f0 + 0.12), 0.05, 8.0, 0.0),
                      (0.78, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0)], 'S18.F1/S18.F2/S18.F4/S18.F5')
    keys += FT('lf', [(0.03, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0), (0.06, (-0.26, f0 - 0.10), 0.0, -8.0, 40.0), (0.09, (-0.26, f0 - 0.10), 0.0, -8.0, 40.0),
                      (0.13, (-0.20, f0 + 0.20), 0.11, -5.0, 0.0), (0.18, (-0.16, f0 + 0.24), 0.0, -5.0, 0.0),
                      (0.21, (-0.12, f0 + 0.16), 0.0, 0.0, 30.0), (0.24, (0.02, f0 + 0.04), 0.06, 0.0, 0.0), (0.28, (0.04, f0 + 0.02), 0.0, 0.0, 0.0),
                      (0.31, (0.00, f0 - 0.06), 0.03, 0.0, 45.0), (0.37, (-0.12, f0 - 0.40), 0.0, -4.0, 60.0), (0.50, (-0.12, f0 - 0.40), 0.01, -4.0, 62.0),
                      (0.55, (0.02, f0 - 0.10), 0.10, 0.0, 20.0), (0.60, (-0.04, f0 + 0.26), 0.0, -4.0, 0.0), (0.70, (-0.08, f0 + 0.12), 0.05, -6.0, 0.0),
                      (0.78, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0)], 'S18.F1/S18.F2/S18.F6/S18.F7')
    keys += BODY([(0.03, (0.0, 0.0, 0.0), (0, 9, 0), (0, 8, 0)), (0.09, (0.0, 0.05, -0.02), (-6, 16, 0), (-6, 12, 0)), (0.21, (0.02, 0.10, -0.04), (4, 18, 0), (4, 12, 0)),
                  (0.31, (0.06, 0.28, -0.14), (20, 24, 4), (22, 14, 4)), (0.35, (0.10, 0.36, -0.20), (24, 28, 5), (28, 14, 5)), (0.47, (0.10, 0.36, -0.20), (10, 28, 5), (22, 12, 5)),
                  (0.52, (0.06, 0.32, -0.16), (-12, 24, 3), (8, 10, 3)), (0.60, (0.02, 0.22, -0.08), (-30, 16, 0), (-20, 8, 0)), (0.70, (0.0, 0.10, -0.03), (-12, 11, 0), (-8, 8, 0)),
                  (0.78, (0.0, 0.0, 0.0), (0, 9, 0), (0, 8, 0))], 'S18.F5/S18.F6')
    # racket (S18.R): racket hand low at her right side with the head below the hand, L arm out to the left; F1: racket hand at hip height; contact: racket head up,
    # ball in line with the strings at hip height ahead of the R hip; 67.07 racket vertical above the head, L arm bent in front of the chest; then wrap; then down
    keys += [K(0.03, 'READY', l_attach=1.0),
             K(0.08, 'S18.R2', rk_pos=rs(45, -75, 0.62), shaft=D(100, -35), face=D(-70, 0), rk_w=[0.2, 1.0], l_attach=0.0, l_hand=ls(-90, 10, 0.8), l_palm=D(-30, -60)),
             K(0.20, 'S18.R2', rk_pos=rs(45, -75, 0.62), shaft=D(100, -35), face=D(-70, 0), rk_w=[0.2, 1.0], l_hand=ls(-90, 10, 0.8)),
             K(0.33, 'S18.R3', rk_pos=rs(50, -68, 0.66), shaft=D(110, -40), face=D(-60, -5), rk_w=[0.2, 1.0], l_hand=ls(-90, 10, 0.85), rk_abs=0.0),
             K(0.40, 'S18.R4', rk_pos=rs(55, -62, 0.70), shaft=D(105, -42), face=D(-40, -5), rk_w=[0.2, 1.0], l_hand=ls(-90, 10, 0.85)),
             K(0.47, 'S18.R5/S18.C', rk_pos=rs(40, -40, 0.85), shaft=D(70, 15), face=D(0, 0), rk_sweet=[0.55, 0.92, 0.92], rk_abs=1.0, rk_w=[2.5, 0.5], l_hand=ls(-90, 10, 0.85)),
             K(0.52, 'S18.R6', rk_pos=rs(15, 70, 0.80), shaft=D(10, 80), face=D(-20, 0), rk_abs=0.0, rk_w=[0.2, 1.0], l_hand=ls(40, 0, 0.45)),
             K(0.58, 'S18.R7', rk_pos=rs(-20, 55, 0.55), shaft=D(-150, 45), face=D(-90, 10), rk_w=[0.2, 1.0], l_hand=ls(40, 0, 0.45)),
             K(0.66, 'S18.R8', rk_pos=rs(35, -70, 0.60), shaft=D(60, -20), face=D(-60, 0), rk_w=[0.2, 1.0], l_hand=ls(-60, -30, 0.7)),
             K(0.68, 'LOCK', l_attach=0.0),
             K(0.78, 'LOCK', rk_pos=[0.08, 0.55, -0.52], shaft=D(15, 68), face=D(-60, 0), rk_w=[0.2, 1.0]),
             K(0.86, 'LOCK', l_attach=1.0)]
    return base('ForehandShort', contact=0.47, keys=keys)


# ---------------------------------------------------------------------------------------------------------------- authoring helpers
def FT(side, wps, src):
    """foot keys from waypoints (t, (r, f), lift, yaw, heel).  A waypoint with lift 0 is a plant (zero velocity, so two equal plants hold)."""
    out = []
    for w in wps:
        t, pos, lift, yaw, heel = (list(w) + [0.0, None, 0.0][len(w) - 2:])[:5] if len(w) < 5 else w
        planted = lift <= 1e-6
        ch = {f'{side}_foot': list(pos), f'{side}_lift': float(lift), f'{side}_heel': float(heel)}
        if yaw is not None:
            ch[f'{side}_yaw'] = float(yaw)
        out.append(K(t, src, ease=1.0 if planted else None, **ch))
    return out


def BODY(wps, src):
    """body keys from waypoints (t, pel(r,f,u), pel_rot(yaw,pitch,roll), chest_rot(yaw,pitch,roll)) - any of the three may be None"""
    out = []
    for w in wps:
        t, pel, pr, cr = w[:4]
        ch = {}
        if pel is not None:
            ch['pel'] = list(pel)
        if pr is not None:
            ch['pel_rot'] = list(pr)
        if cr is not None:
            ch['chest_rot'] = list(cr)
        out.append(K(t, src, **ch))
    return out


# ---------------------------------------------------------------------------------------------------------------- 2. SplitToForehand
def SplitToForehand(S):
    R = S.ready
    W = 0.66
    f0 = R['rf_foot'][1]
    rs = lambda az, el, d: RS(S, az, el, d, 'R')
    ls = lambda az, el, d: RS(S, az, el, d, 'L')
    keys = []
    # S2.F: first move = R leg strides wide to the right while the L leg pushes off; stance ~2x shoulder width; R foot planted flat on the outside;
    # L leg trails behind on its toe (not stepped through); knees bent, R knee takes the load.  (No split-step hop: not seen -> not authored.)
    keys += FT('rf', [(0.05, (W / 2, f0), 0.0, 10.0, 0.0), (0.10, (0.43, f0 + 0.02), 0.075, 18.0, 0.0), (0.15, (0.52, f0 + 0.05), 0.0, 25.0, 0.0),
                      (0.35, (0.52, f0 + 0.05), 0.0, 25.0, 0.0), (0.40, (0.44, f0 + 0.03), 0.04, 18.0, 0.0), (0.47, (W / 2, f0), 0.0, 10.0, 0.0)], 'S2.F2/S2.F3')
    keys += FT('lf', [(0.05, (-W / 2, f0 + 0.02), 0.0, -10.0, 0.0), (0.09, (-0.30, f0 - 0.03), 0.02, -8.0, 35.0), (0.15, (-0.20, f0 - 0.14), 0.0, -4.0, 55.0),
                      (0.31, (-0.20, f0 - 0.14), 0.0, -4.0, 55.0), (0.38, (-0.28, f0 - 0.08), 0.03, -8.0, 40.0), (0.47, (-W / 2, f0 + 0.02), 0.0, -10.0, 0.0)], 'S2.F4')
    keys += BODY([(0.05, (0.03, 0.0, -0.02), (10, 9, 0), (8, 8, 0)), (0.10, (0.08, 0.0, -0.05), (25, 10, 0), (28, 8, 0)),
                  (0.16, (0.18, 0.02, -0.09), (38, 10, 0), (48, 8, 0)), (0.31, (0.18, 0.02, -0.09), (38, 10, 0), (48, 8, 0)),
                  (0.41, (0.09, 0.0, -0.04), (15, 9, 0), (18, 8, 0)), (0.50, (0.0, 0.0, 0.0), (0, 9, 0), (0, 8, 0))], 'S2.R2')
    # racket goes back on the R side with the shoulders turned 70-90 deg (S2.R2); racket back and slightly low, head up (S2.R3)
    keys += [K(0.05, 'S2.R1', rk_pos=[0.08, 0.55, -0.52], shaft=D(15, 68), face=D(-60, 0), rk_w=[0.2, 1.0], l_attach=1.0),
             K(0.10, 'S2.R2', rk_pos=rs(100, 0, 0.55), shaft=D(100, 62), face=D(0, 5), rk_w=[0.2, 1.0], l_attach=0.0, l_hand=ls(-90, 0, 0.7), l_palm=D(-30, -60)),
             K(0.16, 'S2.R3', rk_pos=rs(115, -5, 0.58), shaft=D(120, 55), face=D(20, 5), rk_w=[0.2, 1.0], l_hand=ls(-90, 8, 0.95)),
             K(0.31, 'S2.R3', rk_pos=rs(115, -5, 0.58), shaft=D(120, 55), face=D(20, 5), rk_w=[0.2, 1.0], l_hand=ls(-90, 8, 0.95), l_attach=0.0),
             K(0.40, 'LOCK', rk_pos=[0.12, 0.52, -0.50], shaft=D(30, 66), face=D(-50, 0), rk_w=[0.2, 1.0], l_attach=0.4, l_hand=ls(-30, -30, 0.7)),
             K(0.50, 'LOCK', l_attach=1.0)]
    return base('SplitToForehand', keys=keys)


# ---------------------------------------------------------------------------------------------------------------- 3. SplitToBackhand
def SplitToBackhand(S):
    R = S.ready
    W = 0.66
    f0 = R['rf_foot'][1]
    rs = lambda az, el, d: RS(S, az, el, d, 'R')
    keys = []
    # S3.F: L foot steps out wide to the left (stance ~2x), R stays; L foot planted wide, L knee bent, weight on L, R leg trails behind on its toes;
    # R foot lifted behind the L leg, swings forward next to the L foot; feet close together, flat; both heels up as the racket drops low.
    keys += FT('lf', [(0.04, (-W / 2, f0 + 0.02), 0.0, -10.0, 0.0), (0.09, (-0.46, f0 + 0.02), 0.06, -14.0, 0.0), (0.14, (-0.56, f0 + 0.02), 0.0, -18.0, 0.0),
                      (0.40, (-0.56, f0 + 0.02), 0.0, -18.0, 0.0), (0.45, (-0.46, f0 + 0.02), 0.02, -14.0, 0.0), (0.52, (-W / 2, f0 + 0.02), 0.0, -10.0, 0.0)], 'S3.F2/S3.F3')
    keys += FT('rf', [(0.04, (W / 2, f0), 0.0, 10.0, 0.0), (0.11, (0.30, f0 - 0.06), 0.0, 6.0, 50.0), (0.20, (0.26, f0 - 0.12), 0.0, 4.0, 55.0),
                      (0.24, (0.10, f0 - 0.16), 0.08, 0.0, 30.0), (0.31, (-0.28, f0 - 0.02), 0.07, -10.0, 15.0), (0.37, (-0.30, f0), 0.0, -12.0, 0.0),
                      (0.42, (-0.30, f0), 0.0, -12.0, 40.0), (0.46, (-0.30, f0), 0.0, -12.0, 40.0), (0.52, (W / 2, f0), 0.02, 8.0, 0.0), (0.58, (W / 2, f0), 0.0, 10.0, 0.0)], 'S3.F4/S3.F5/S3.F6/S3.F7')
    keys += BODY([(0.04, (0.0, 0.0, 0.0), (0, 9, 0), (0, 8, 0)), (0.09, (-0.04, 0.0, -0.03), (-20, 10, 0), (-30, 8, 0)),
                  (0.15, (-0.16, 0.0, -0.08), (-40, 10, 0), (-50, 8, 0)), (0.30, (-0.16, 0.0, -0.08), (-42, 10, 0), (-52, 8, 0)),
                  (0.40, (-0.12, 0.0, -0.08), (-40, 12, 0), (-50, 12, 0)), (0.46, (-0.12, 0.0, -0.10), (-40, 14, 0), (-50, 14, 0)),
                  (0.52, (-0.04, 0.0, -0.03), (-12, 10, 0), (-14, 9, 0))], 'S3.R2')
    # S3.R: racket tip up at the L hip, hands low (both hands on it); held vertical at the L hip (0.4 s); drops low at his L near ankle height (bottom of the drop)
    keys += [K(0.04, 'S3.R1', rk_pos=[0.08, 0.55, -0.52], shaft=D(15, 68), face=D(-60, 0), rk_w=[0.2, 1.0], l_attach=1.0, l_grip=1.0),
             K(0.09, 'S3.R2', rk_pos=[-0.16, 0.34, -0.70], shaft=D(-60, 70), face=D(-120, 0), rk_w=[0.2, 1.0]),
             K(0.15, 'S3.R3', rk_pos=[-0.22, 0.22, -0.80], shaft=D(-95, 76), face=D(-170, 0), rk_w=[0.2, 1.0]),
             K(0.40, 'S3.R3', rk_pos=[-0.22, 0.22, -0.80], shaft=D(-95, 76), face=D(-170, 0), rk_w=[0.2, 1.0]),
             K(0.46, 'S3.R4', rk_pos=[-0.28, 0.26, -0.88], shaft=D(-100, 20), face=D(-150, 0), rk_w=[0.2, 1.0]),
             K(0.54, 'LOCK', rk_pos=[0.08, 0.55, -0.52], shaft=D(15, 68), face=D(-60, 0), rk_w=[0.2, 1.0], l_grip=0.0)]
    return base('SplitToBackhand', keys=keys)


# ---------------------------------------------------------------------------------------------------------------- 4. RecoverCenter
def RecoverCenter(S):
    R = S.ready
    W = 0.66
    f0 = R['rf_foot'][1]
    ls = lambda az, el, d: RS(S, az, el, d, 'L')
    rs = lambda az, el, d: RS(S, az, el, d, 'R')
    keys = []
    # S4: long recovery strides (trailing leg extended behind, body leaning forward, racket carried in the R hand at hip height, L arm swinging),
    # the steps shorten and slow while he turns back towards the net, then standing relaxed with the racket low.  In place: each stride is a plant
    # and a weight shift; gameplay moves the actor.
    keys += FT('rf', [(0.05, (W / 2, f0), 0.0, 10.0, 0.0), (0.10, (0.28, f0 + 0.16), 0.10, 5.0, 0.0), (0.16, (0.30, f0 + 0.22), 0.0, 5.0, 0.0),
                      (0.26, (0.30, f0 + 0.22), 0.0, 5.0, 25.0), (0.32, (0.27, f0 - 0.14), 0.11, 5.0, 40.0), (0.39, (0.30, f0 - 0.20), 0.0, 5.0, 30.0),
                      (0.48, (0.30, f0 + 0.10), 0.07, 5.0, 0.0), (0.54, (0.32, f0 + 0.12), 0.0, 8.0, 0.0), (0.68, (W / 2, f0), 0.03, 10.0, 0.0), (0.74, (W / 2, f0), 0.0, 10.0, 0.0)], 'S4.F2/S4.F3')
    keys += FT('lf', [(0.05, (-W / 2, f0 + 0.02), 0.0, -10.0, 0.0), (0.10, (-0.30, f0 - 0.18), 0.0, -5.0, 45.0), (0.18, (-0.30, f0 - 0.20), 0.0, -5.0, 45.0),
                      (0.22, (-0.28, f0 + 0.18), 0.10, -5.0, 0.0), (0.28, (-0.28, f0 + 0.24), 0.0, -5.0, 0.0), (0.40, (-0.30, f0 + 0.24), 0.0, -5.0, 25.0),
                      (0.45, (-0.30, f0 - 0.10), 0.08, -5.0, 35.0), (0.52, (-0.30, f0 - 0.14), 0.0, -5.0, 35.0), (0.60, (-0.30, f0 + 0.08), 0.06, -6.0, 0.0),
                      (0.66, (-0.31, f0 + 0.10), 0.0, -8.0, 0.0), (0.74, (-W / 2, f0 + 0.02), 0.0, -10.0, 0.0)], 'S4.F2/S4.F3')
    keys += BODY([(0.05, (0.0, 0.0, 0.0), (0, 9, 0), (0, 8, 0)), (0.10, (0.00, 0.04, -0.02), (-8, 14, 0), (-6, 12, 0)),
                  (0.22, (0.02, 0.04, -0.02), (6, 14, 0), (8, 12, 0)), (0.35, (-0.02, 0.04, -0.02), (-8, 13, 0), (-8, 11, 0)),
                  (0.48, (0.0, 0.02, -0.01), (4, 11, 0), (4, 9, 0)), (0.60, (0.0, 0.01, 0.0), (-2, 9, 0), (-2, 8, 0)), (0.74, (0.0, 0.0, 0.0), (0, 9, 0), (0, 8, 0))], 'S4.R2')
    # racket carried at hip height in the R hand, L arm swinging; by the end the racket is brought back to the ready hold (lock)
    keys += [K(0.05, 'S4.R1', rk_pos=[0.08, 0.55, -0.52], shaft=D(15, 68), face=D(-60, 0), rk_w=[0.2, 1.0], l_attach=1.0),
             K(0.10, 'S4.R2', rk_pos=rs(30, -70, 0.65), shaft=D(20, -10), face=D(-70, 0), rk_w=[0.2, 1.0], l_attach=0.0, l_hand=ls(-30, -35, 0.75), l_palm=D(-60, 0)),
             K(0.22, 'S4.R2', rk_pos=rs(25, -72, 0.65), shaft=D(15, -15), face=D(-70, 0), rk_w=[0.2, 1.0], l_hand=ls(25, -20, 0.7)),
             K(0.35, 'S4.R2', rk_pos=rs(25, -72, 0.65), shaft=D(15, -15), face=D(-70, 0), rk_w=[0.2, 1.0], l_hand=ls(-25, -30, 0.7)),
             K(0.48, 'S4.R3', rk_pos=rs(20, -78, 0.62), shaft=D(10, -25), face=D(-70, 0), rk_w=[0.2, 1.0], l_hand=ls(-10, -45, 0.62)),
             K(0.62, 'S4.R4', rk_pos=rs(15, -80, 0.60), shaft=D(5, -30), face=D(-70, 0), rk_w=[0.2, 1.0], l_hand=ls(-5, -55, 0.55), l_attach=0.3),
             K(0.74, 'LOCK', rk_pos=[0.08, 0.55, -0.52], shaft=D(15, 68), face=D(-60, 0), rk_w=[0.2, 1.0], l_attach=1.0)]
    return base('RecoverCenter', keys=keys)


# ---------------------------------------------------------------------------------------------------------------- two-handed backhand generator
def bh_swing(S, tm, src, sweet, yaw_load=(-38, -46), yaw_c=(-12, -6), yaw_fin=(48, 44), lean=(18, 14), release=None):
    """torso + racket keys of a right-handed TWO-handed backhand (WATCH S9 order): hands low at the L hip, contact low on his L, racket sweeps up and over
    the R shoulder, wraps behind the head.  Both hands stay on the handle (l_attach 1, l_grip 1) until `release`."""
    rs = lambda az, el, d: RS(S, az, el, d, 'R')
    ls = lambda az, el, d: RS(S, az, el, d, 'L')
    p0, c0 = lean
    release = release or (tm['peak'] + 0.05)
    keys = [
        K(tm['turn'], src['turn'], pel_rot=[-18, p0 - 2, 0], chest_rot=[-24, c0 - 2, 0]),
        K(tm['hip'], src['hip'], pel_rot=[yaw_load[0] + 10, p0, 0], chest_rot=[yaw_load[1] + 10, c0, 0]),
        K(tm['load'], src['load'], pel_rot=[yaw_load[0], p0 + 3, 0], chest_rot=[yaw_load[1], c0 + 2, 0]),
        K(tm['fwd'], src['fwd'], pel_rot=[yaw_load[0] + 14, p0 + 3, 0], chest_rot=[yaw_load[1] + 20, c0 + 2, 0]),
        K(tm['c'], src['c'], pel_rot=[yaw_c[0], p0 + 2, 0], chest_rot=[yaw_c[1], c0, 0]),
        K(tm['up'], src['up'], pel_rot=[10, p0 - 4, 0], chest_rot=[18, c0 - 4, 0]),
        K(tm['wrap'], src['wrap'], pel_rot=[38, p0 - 6, 0], chest_rot=[34, c0 - 6, 0]),
        K(tm['peak'], src['peak'], pel_rot=[yaw_fin[0], p0 - 8, 0], chest_rot=[yaw_fin[1], c0 - 8, 0]),
        # racket (positions chest-relative, orientation stance frame); l_grip 1 = handle
        K(tm['turn'], src['turn'], rk_pos=[-0.10, 0.52, -0.58], shaft=D(-30, 62), face=D(-100, 0), rk_w=[0.2, 1.0], l_attach=1.0, l_grip=1.0),
        K(tm['hip'], src['hip'], rk_pos=[-0.18, 0.42, -0.72], shaft=D(-60, 62), face=D(-120, 0), rk_w=[0.2, 1.0]),
        K(tm['load'], src['load'], rk_pos=[-0.22, 0.32, -0.80], shaft=D(-130, -35), face=D(-60, -10), rk_w=[0.2, 1.0]),
        K(tm['fwd'], src['fwd'], rk_pos=[-0.20, 0.44, -0.80], shaft=D(-105, -8), face=D(-30, -5), rk_w=[0.2, 1.0], rk_abs=0.0),
        K(tm['c'], src['c'], rk_pos=[-0.20, 0.62, -0.74], shaft=D(-80, 20), face=D(0, 0), rk_sweet=sweet, rk_abs=1.0, rk_w=[2.5, 0.5]),
        K(tm['post'], src['c'], rk_sweet=[sweet[0] + 0.08, sweet[1] + 0.10, sweet[2] + 0.10], rk_abs=0.6),
        K(tm['post'], src['up'], rk_pos=[-0.10, 0.62, -0.30], shaft=D(-30, 55), face=D(-40, 5), rk_w=[0.2, 1.0]),
        K(tm['up'], src['up'], rk_pos=[0.05, 0.60, 0.15], shaft=D(40, 70), face=D(-10, 5), rk_w=[0.2, 1.0], rk_abs=0.0),
        K(tm['wrap'], src['wrap'], rk_pos=[0.20, 0.22, 0.50], shaft=D(140, 50), face=D(70, 10), rk_w=[0.2, 1.0]),
        K(tm['peak'], src['peak'], rk_pos=[0.16, 0.14, 0.46], shaft=D(135, 55), face=D(60, 15), rk_w=[0.2, 1.0]),
        # the off hand: on the handle through the contact, lets go on the finish, back on the throat for the ready hold (lock)
        K(release - 0.06, src['peak'], l_attach=1.0),
        K(release, src['peak'], l_attach=0.0, l_hand=[-0.30, 0.30, 0.35], l_palm=D(-60, -40)),
        K(tm['back'] - 0.06, 'LOCK', l_attach=0.0, l_hand=[-0.25, 0.45, -0.35]),
        K(tm['back'], 'LOCK', l_attach=1.0, l_grip=0.0, rk_pos=[0.08, 0.55, -0.52], shaft=D(15, 68), face=D(-60, 0), rk_w=[0.2, 1.0]),
    ]
    return keys


# ---------------------------------------------------------------------------------------------------------------- 9. Backhand
def Backhand(S):
    R = S.ready
    L = LENGTH['Backhand']
    f0 = R['rf_foot'][1]

    def T(v):                                       # DGIkk video seconds 1010.19 .. 1011.89 (1.7 s) onto 1.2 s
        return round((v - 1010.19) / 1.7 * L * 30) / 30
    tm = dict(turn=T(1010.39), hip=T(1010.59), load=T(1010.74), fwd=T(1011.00), c=T(1011.19), post=T(1011.24), up=T(1011.34), wrap=T(1011.49), peak=T(1011.60), back=T(1011.89))
    src = dict(turn='S9.R2', hip='S9.R3', load='S9.R4', fwd='S9.R4', c='S9.R5/S9.C', up='S9.R6', wrap='S9.R7', peak='S9.R7')
    keys = bh_swing(S, tm, src, sweet=[-0.50, 0.62, 0.85], release=T(1011.72))
    # S9 feet (Djokovic, real time): wide ready (1.6x); weight shifts; stance narrows slightly, knees bend, R heel starts to rise; deep knee bend with the R heel up;
    # contact with both knees bent, torso inclined over the ball; legs extend (up on the toes) while the racket rises over the R shoulder
    keys += [
        K(T(1010.39), 'S9.F2', rf_foot=[0.31, f0], lf_foot=[-0.31, f0 + 0.04], rf_yaw=8.0, lf_yaw=-14.0, pel=[-0.04, 0.0, -0.02]),
        K(T(1010.54), 'S9.F3', rf_heel=22.0, pel=[-0.08, 0.0, -0.04]),
        K(T(1010.74), 'S9.F4', rf_heel=30.0, pel=[-0.10, 0.02, -0.06]),
        K(T(1011.04), 'S9.F5', rf_heel=26.0, pel=[-0.10, 0.04, -0.06]),
        K(T(1011.19), 'S9.F6', rf_heel=22.0, pel=[-0.08, 0.05, -0.05]),
        K(T(1011.34), 'S9.F7', rf_heel=40.0, lf_heel=34.0, pel=[-0.02, 0.05, 0.0]),
        K(T(1011.64), 'S9.F9', rf_heel=0.0, lf_heel=0.0, pel=[0.0, 0.03, 0.0]),
        K(T(1011.89), 'LOCK', rf_foot=[R['rf_foot'][0], f0], lf_foot=[R['lf_foot'][0], f0 + 0.02], rf_yaw=10.0, lf_yaw=-10.0, pel=[0.0, 0.0, 0.0]),
    ]
    return base('Backhand', contact=tm['c'], keys=keys)


# ---------------------------------------------------------------------------------------------------------------- 10. BackhandWide
def BackhandWide(S):
    R = S.ready
    L = LENGTH['BackhandWide']
    f0 = R['rf_foot'][1]
    tm = dict(turn=0.16, hip=0.30, load=0.50, fwd=0.74, c=0.85, post=0.89, up=0.93, wrap=1.00, peak=1.06, back=1.30)
    src = dict(turn='S10.R2', hip='S10.R3', load='S10.R4', fwd='S10.R5', c='S10.R6/S10.C', up='S10.R7', wrap='S10.R8', peak='S10.R8')
    keys = bh_swing(S, tm, src, sweet=[-0.55, 0.58, 0.80], yaw_load=(-42, -56), yaw_c=(-8, -4), yaw_fin=(46, 44), lean=(20, 14), release=1.12)
    # S10 feet: narrow, knees flexed; R foot flat, L toe steps out and lands wide on the ball of the foot; stance ~1.5x with knees ~120 deg (60 deg flexion), held;
    # forward swing: the stance narrows to ~0.8x as he pushes up and in; contact with both feet flat at hip width, torso square; feet together with the heels slightly up; back to shoulder width
    keys += FT('lf', [(0.05, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0), (0.10, (-0.22, f0 + 0.02), 0.0, -8.0, 0.0), (0.19, (-0.22, f0 + 0.02), 0.0, -8.0, 0.0),
                      (0.26, (-0.40, f0 + 0.04), 0.07, -14.0, 40.0), (0.31, (-0.62, f0 + 0.06), 0.0, -22.0, 20.0), (0.36, (-0.62, f0 + 0.06), 0.0, -22.0, 0.0),
                      (0.70, (-0.62, f0 + 0.06), 0.0, -22.0, 0.0), (0.80, (-0.22, f0 + 0.04), 0.0, -10.0, 0.0), (0.97, (-0.20, f0 + 0.04), 0.0, -10.0, 0.0),
                      (1.04, (-0.20, f0 + 0.04), 0.0, -10.0, 25.0), (1.14, (-0.28, f0 + 0.02), 0.0, -10.0, 0.0), (1.24, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0)], 'S10.F1/S10.F2/S10.F3/S10.F7/S10.F9')
    keys += FT('rf', [(0.05, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0), (0.10, (0.20, f0), 0.0, 6.0, 0.0), (0.19, (0.20, f0), 0.0, 6.0, 0.0), (0.36, (0.22, f0 - 0.02), 0.0, 8.0, 0.0),
                      (0.70, (0.22, f0 - 0.02), 0.0, 8.0, 0.0), (0.80, (0.24, f0 - 0.02), 0.0, 8.0, 0.0), (0.97, (0.24, f0 - 0.02), 0.0, 8.0, 0.0),
                      (1.04, (0.24, f0 - 0.02), 0.0, 8.0, 25.0), (1.14, (0.30, f0), 0.0, 8.0, 0.0), (1.24, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0)], 'S10.F1/S10.F8')
    keys += BODY([(0.10, (-0.04, 0.0, -0.02), None, None), (0.31, (-0.22, 0.02, -0.05), None, None), (0.50, (-0.26, 0.03, -0.08), None, None),
                  (0.70, (-0.26, 0.04, -0.08), None, None), (0.80, (-0.08, 0.04, -0.06), None, None), (0.85, (-0.04, 0.05, -0.04), None, None),
                  (0.97, (0.0, 0.03, -0.02), None, None), (1.14, (0.0, 0.0, 0.0), None, None)], 'S10.F5')
    return base('BackhandWide', contact=0.85, keys=keys)


# ---------------------------------------------------------------------------------------------------------------- 13. Return
def Return(S):
    R = S.ready
    f0 = R['rf_foot'][1]
    tm = dict(turn=0.12, hip=0.18, load=0.24, fwd=0.34, c=0.47, post=0.50, up=0.53, wrap=0.57, peak=0.60, back=0.90)
    src = dict(turn='S13.R2', hip='S13.R2', load='S13.R3', fwd='S13.R3', c='S13.R4/S13.C', up='S13.R5', wrap='S13.R5', peak='S13.R5')
    keys = bh_swing(S, tm, src, sweet=[-0.58, 0.56, 0.88], yaw_load=(-34, -40), yaw_c=(-6, -2), yaw_fin=(30, 30), lean=(14, 12), release=0.66)
    # S13.F: static wide stance (~2x shoulder width, knees ~30 deg), then the L foot steps out wide with the knee bent and the weight goes onto it, the R leg trails
    # behind; compact lunge; contact; still moving to the L as the racket finishes high; small recovery steps (no split-step hop: not seen)
    keys += FT('lf', [(0.02, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0), (0.06, (-0.40, f0 + 0.02), 0.0, -10.0, 0.0), (0.20, (-0.40, f0 + 0.02), 0.0, -10.0, 0.0),
                      (0.25, (-0.52, f0 + 0.04), 0.07, -16.0, 0.0), (0.30, (-0.66, f0 + 0.06), 0.0, -22.0, 0.0), (0.58, (-0.66, f0 + 0.06), 0.0, -22.0, 0.0),
                      (0.64, (-0.58, f0 + 0.04), 0.05, -16.0, 0.0), (0.70, (-0.46, f0 + 0.02), 0.0, -12.0, 0.0), (0.82, (-0.40, f0 + 0.02), 0.04, -10.0, 0.0),
                      (0.88, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0)], 'S13.F1/S13.F3')
    keys += FT('rf', [(0.02, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0), (0.06, (0.40, f0), 0.0, 10.0, 0.0), (0.22, (0.40, f0), 0.0, 10.0, 0.0),
                      (0.28, (0.30, f0 - 0.12), 0.05, 8.0, 40.0), (0.34, (0.26, f0 - 0.20), 0.0, 6.0, 45.0), (0.58, (0.26, f0 - 0.20), 0.0, 6.0, 45.0),
                      (0.64, (0.30, f0 - 0.10), 0.06, 8.0, 20.0), (0.70, (0.34, f0), 0.0, 10.0, 0.0), (0.82, (0.36, f0), 0.03, 10.0, 0.0),
                      (0.88, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0)], 'S13.F4')
    keys += BODY([(0.06, (0.0, 0.0, -0.02), None, None), (0.20, (-0.04, 0.0, -0.03), None, None), (0.30, (-0.20, 0.03, -0.09), None, None),
                  (0.47, (-0.22, 0.05, -0.09), None, None), (0.58, (-0.20, 0.06, -0.07), None, None), (0.70, (-0.10, 0.03, -0.04), None, None),
                  (0.88, (0.0, 0.0, 0.0), None, None)], 'S13.F3')
    return base('Return', contact=0.47, keys=keys)


# ---------------------------------------------------------------------------------------------------------------- 14. VolleyForehand
def VolleyForehand(S):
    R = S.ready
    f0 = R['rf_foot'][1]
    rs = lambda az, el, d: RS(S, az, el, d, 'R')
    ls = lambda az, el, d: RS(S, az, el, d, 'L')
    keys = []
    # S14 (A): ready 1.2-1.3x, racket upright in front of the R shoulder; small turn, racket to the R, head up beside the head; head extends toward the ball at head
    # height to the R; follows the ball down (head from eye level to knee level, shoulders ~90 deg, torso bends forward, L arm out for balance); contact at knee height
    # on his R, arm extended, weight on the R side, deep R knee bend, rear foot behind; racket whips up and behind the head (high wrap); lowers to the hip; wide ready
    keys += FT('rf', [(0.03, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0), (0.12, (0.30, f0 + 0.06), 0.0, 14.0, 0.0), (0.30, (0.34, f0 + 0.12), 0.0, 20.0, 0.0),
                      (0.42, (0.34, f0 + 0.12), 0.0, 20.0, 0.0), (0.56, (0.30, f0 + 0.04), 0.0, 14.0, 0.0), (0.66, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0)], 'S14.F2/S14.F3/S14.F5')
    keys += FT('lf', [(0.03, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0), (0.12, (-0.22, f0 - 0.04), 0.0, -6.0, 20.0), (0.30, (-0.14, f0 - 0.20), 0.0, 0.0, 35.0),
                      (0.42, (-0.14, f0 - 0.20), 0.0, 0.0, 35.0), (0.56, (-0.22, f0 - 0.06), 0.0, -6.0, 15.0), (0.66, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0)], 'S14.F3/S14.F4')
    keys += BODY([(0.03, (0.0, 0.0, 0.0), (0, 9, 0), (0, 8, 0)), (0.10, (0.03, 0.0, -0.03), (10, 12, 0), (12, 10, 0)), (0.17, (0.08, 0.02, -0.07), (20, 14, 0), (24, 12, 0)),
                  (0.26, (0.14, 0.04, -0.14), (34, 20, 0), (44, 22, 0)), (0.325, (0.14, 0.05, -0.16), (36, 24, 0), (46, 26, 0)),
                  (0.36, (0.10, 0.04, -0.12), (20, 18, 0), (22, 16, 0)), (0.42, (0.04, 0.02, -0.06), (-10, 12, 0), (-16, 10, 0)),
                  (0.50, (0.02, 0.0, -0.03), (-30, 10, 0), (-34, 8, 0)), (0.62, (0.0, 0.0, 0.0), (-6, 9, 0), (-6, 8, 0)), (0.69, (0.0, 0.0, 0.0), (0, 9, 0), (0, 8, 0))], 'S14.R5')
    keys += [K(0.03, 'S14.R1', rk_pos=[0.20, 0.50, -0.10], shaft=D(10, 75), face=D(-60, 0), rk_w=[0.2, 1.0], l_attach=1.0),
             K(0.10, 'S14.R2', rk_pos=rs(60, -10, 0.5), shaft=D(25, 75), face=D(-50, 0), rk_w=[0.2, 1.0], l_attach=0.6),
             K(0.17, 'S14.R3', rk_pos=rs(70, 15, 0.45), shaft=D(60, 78), face=D(-20, 0), rk_w=[0.2, 1.0], l_attach=0.0, l_hand=ls(-60, 10, 0.8), l_palm=D(-30, -50)),
             K(0.22, 'S14.R4', rk_pos=rs(55, 20, 0.80), shaft=D(70, 40), face=D(0, 0), rk_w=[0.2, 1.0], l_hand=ls(-80, 10, 0.9)),
             K(0.26, 'S14.R5', rk_pos=rs(50, -20, 0.80), shaft=D(75, 10), face=D(0, 0), rk_w=[0.2, 1.0], l_hand=ls(-90, 10, 0.9), rk_abs=0.0),
             K(0.325, 'S14.R6/S14.C', rk_pos=rs(45, -45, 0.85), shaft=D(55, 0), face=D(0, 0), rk_sweet=[0.58, 0.62, 0.55], rk_abs=1.0, rk_w=[2.5, 0.5], l_hand=ls(-90, 10, 0.9)),
             K(0.36, 'S14.R7', rk_pos=rs(10, 55, 0.70), shaft=D(-20, 78), face=D(-40, 5), rk_abs=0.0, rk_w=[0.2, 1.0], l_hand=ls(-60, -10, 0.6)),
             K(0.42, 'S14.R8', rk_pos=rs(-10, 55, 0.50), shaft=D(-100, 55), face=D(-110, 5), rk_w=[0.2, 1.0]),
             K(0.50, 'S14.R8', rk_pos=rs(-15, 45, 0.50), shaft=D(-120, 45), face=D(-140, 5), rk_w=[0.2, 1.0]),
             K(0.62, 'S14.R9', rk_pos=[0.12, 0.50, -0.45], shaft=D(15, 68), face=D(-60, 0), rk_w=[0.2, 1.0], l_attach=0.5),
             K(0.69, 'LOCK', l_attach=1.0, l_grip=0.0)]
    return base('VolleyForehand', contact=0.325, keys=keys)


# ---------------------------------------------------------------------------------------------------------------- 15. VolleyBackhand
def VolleyBackhand(S):
    R = S.ready
    f0 = R['rf_foot'][1]
    ls = lambda az, el, d: RS(S, az, el, d, 'L')
    keys = []
    # S15: feet wide and flat, racket hangs low in front of the R thigh; racket hand moves to his L, deep knee bend; both hands on the racket (L above R), racket low
    # at his L side at knee height, torso bent forward, rear foot up on its toes; contact at ankle-to-knee height at the lower left; racket sweeps up and over his R
    # shoulder with both arms rising; vertical, wrapped behind the head (peak); (foot-by-foot order not seen -> feet stay planted, only heels and knees move)
    keys += FT('rf', [(0.03, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0), (0.20, (0.34, f0 - 0.10), 0.0, 8.0, 40.0), (0.34, (0.34, f0 - 0.10), 0.0, 8.0, 45.0),
                      (0.44, (0.34, f0 - 0.10), 0.0, 8.0, 20.0), (0.56, (0.34, f0 - 0.06), 0.0, 8.0, 0.0), (0.66, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0)], 'S15.F1/S15.F3')
    keys += FT('lf', [(0.03, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0), (0.20, (-0.36, f0 + 0.06), 0.0, -18.0, 0.0), (0.44, (-0.36, f0 + 0.06), 0.0, -18.0, 0.0),
                      (0.56, (-0.34, f0 + 0.04), 0.0, -14.0, 0.0), (0.66, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0)], 'S15.F1')
    keys += BODY([(0.03, (0.0, 0.0, 0.0), (0, 9, 0), (0, 8, 0)), (0.10, (-0.04, 0.02, -0.08), (-8, 14, 0), (-10, 12, 0)),
                  (0.20, (-0.08, 0.05, -0.12), (-14, 24, 0), (-20, 24, 0)), (0.316, (-0.10, 0.07, -0.15), (-16, 28, 0), (-20, 28, 0)),
                  (0.38, (-0.06, 0.05, -0.11), (-10, 22, 0), (-6, 18, 0)), (0.46, (-0.02, 0.02, -0.08), (22, 14, 0), (24, 12, 0)),
                  (0.52, (0.0, 0.0, -0.04), (26, 12, 0), (26, 10, 0)), (0.62, (0.0, 0.0, -0.01), (6, 9, 0), (6, 8, 0)), (0.69, (0.0, 0.0, 0.0), (0, 9, 0), (0, 8, 0))], 'S15.R2')
    keys += [K(0.03, 'S15.R1', rk_pos=[0.22, 0.40, -0.92], shaft=D(20, -50), face=D(-60, -10), rk_w=[0.2, 1.0], l_attach=0.0, l_grip=1.0, l_hand=ls(-20, -60, 0.6), l_palm=D(-40, -50)),
             K(0.12, 'S15.R2', l_attach=0.0, l_hand=ls(-10, -45, 0.55)),
             K(0.19, 'S15.R3', l_attach=0.7),
             K(0.24, 'S15.R3', l_attach=1.0),
             K(0.12, 'S15.R2', rk_pos=[-0.04, 0.46, -0.84], shaft=D(-60, -30), face=D(-80, -10), rk_w=[0.2, 1.0]),
             K(0.20, 'S15.R3', rk_pos=[-0.16, 0.46, -0.84], shaft=D(-90, -10), face=D(-40, -5), rk_w=[0.2, 1.0], rk_abs=0.0),
             K(0.316, 'S15.R4/S15.C', rk_pos=[-0.16, 0.52, -0.84], shaft=D(-85, 5), face=D(0, 0), rk_sweet=[-0.42, 0.56, 0.54], rk_abs=1.0, rk_w=[2.5, 0.5]),
             K(0.36, 'S15.R5', rk_sweet=[-0.40, 0.62, 0.60], rk_abs=0.5, rk_pos=[-0.14, 0.52, -0.30], shaft=D(-40, 50), face=D(-10, 5), rk_w=[0.2, 1.0]),
             K(0.40, 'S15.R5', rk_pos=[0.05, 0.55, 0.15], shaft=D(35, 70), face=D(-10, 5), rk_abs=0.0, rk_w=[0.2, 1.0]),
             K(0.47, 'S15.R6', rk_pos=[0.20, 0.20, 0.48], shaft=D(150, 55), face=D(60, 10), rk_w=[0.2, 1.0]),
             K(0.52, 'S15.R6', rk_pos=[0.16, 0.14, 0.46], shaft=D(135, 60), face=D(60, 15), rk_w=[0.2, 1.0], l_attach=1.0),
             K(0.58, 'LOCK', l_attach=0.0, l_hand=[-0.25, 0.45, -0.35]),
             K(0.69, 'LOCK', rk_pos=[0.08, 0.55, -0.52], shaft=D(15, 68), face=D(-60, 0), rk_w=[0.2, 1.0], l_attach=1.0, l_grip=0.0)]
    return base('VolleyBackhand', contact=0.316, keys=keys)


# ---------------------------------------------------------------------------------------------------------------- 17. SliceApproach
def SliceApproach(S):
    R = S.ready
    f0 = R['rf_foot'][1]
    rs = lambda az, el, d: RS(S, az, el, d, 'R')
    ls = lambda az, el, d: RS(S, az, el, d, 'L')
    keys = []
    # S17 (THIN on contact): base on the baseline line with the L foot (front) flat and the R foot behind on its toe, bent forward from the hips; both hands on the racket
    # across the belly (L hand at the throat); racket low at his left; the L hand leaves just before contact (as the forward swing starts); NO key inside the contact
    # window 0.43-0.52 s -> the racket face at contact is not authored, it is interpolated between the keys either side; T-shaped finish (racket arm out right with the head
    # above the hand, L arm out left); first run step with the R (rear) foot, jog steps with the arms out for the first two, wide athletic landing (no hop: not seen)
    keys += FT('lf', [(0.04, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0), (0.10, (-0.24, f0 + 0.10), 0.03, -8.0, 0.0), (0.16, (-0.20, f0 + 0.18), 0.0, -8.0, 0.0),
                      (0.58, (-0.20, f0 + 0.18), 0.0, -8.0, 0.0), (0.74, (-0.20, f0 + 0.18), 0.0, -8.0, 0.0), (0.80, (-0.16, f0 + 0.32), 0.12, -5.0, 0.0),
                      (0.86, (-0.16, f0 + 0.34), 0.0, -5.0, 0.0), (0.96, (-0.16, f0 + 0.34), 0.0, -5.0, 0.0), (1.02, (-0.26, f0 + 0.18), 0.05, -10.0, 0.0),
                      (1.08, (-0.29, f0 + 0.10), 0.0, -12.0, 0.0), (1.20, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0)], 'S17.F4/S17.F8/S17.F9')
    keys += FT('rf', [(0.04, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0), (0.10, (0.22, f0 - 0.08), 0.03, 8.0, 20.0), (0.16, (0.14, f0 - 0.12), 0.0, 6.0, 40.0),
                      (0.64, (0.14, f0 - 0.12), 0.0, 6.0, 40.0), (0.70, (0.14, f0 + 0.10), 0.15, 8.0, 10.0), (0.76, (0.14, f0 + 0.40), 0.0, 10.0, 0.0),
                      (0.84, (0.14, f0 + 0.40), 0.0, 10.0, 0.0), (0.90, (0.14, f0 + 0.46), 0.12, 10.0, 0.0), (0.96, (0.14, f0 + 0.50), 0.0, 10.0, 0.0),
                      (1.02, (0.20, f0 + 0.30), 0.05, 10.0, 0.0), (1.08, (0.29, f0 + 0.10), 0.0, 10.0, 0.0), (1.20, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0)], 'S17.F6/S17.F7/S17.F8/S17.F9')
    keys += BODY([(0.04, (0.0, 0.0, 0.0), (0, 9, 0), (0, 8, 0)), (0.12, (-0.03, 0.04, -0.04), (-20, 18, 0), (-26, 14, 0)),
                  (0.22, (-0.06, 0.12, -0.07), (-30, 26, 0), (-40, 20, 0)), (0.40, (-0.06, 0.14, -0.08), (-32, 27, 0), (-42, 22, 0)),
                  (0.47, (-0.04, 0.16, -0.08), (-14, 27, 0), (-8, 20, 0)), (0.55, (-0.02, 0.18, -0.07), (6, 22, 0), (14, 14, 0)),
                  (0.66, (-0.02, 0.18, -0.10), (8, 20, 0), (16, 12, 0)), (0.76, (0.0, 0.20, -0.06), (4, 16, 0), (8, 12, 0)),
                  (0.96, (0.0, 0.14, -0.05), (0, 14, 0), (0, 10, 0)), (1.08, (0.0, 0.08, -0.07), (0, 12, 0), (0, 9, 0)), (1.20, (0.0, 0.0, 0.0), (0, 9, 0), (0, 8, 0))], 'S17.R4/S17.F9')
    keys += [K(0.04, 'S17.R1', rk_pos=[0.08, 0.55, -0.52], shaft=D(15, 68), face=D(-60, 0), rk_w=[0.2, 1.0], l_attach=1.0, l_grip=0.0),
             K(0.14, 'S17.R2', rk_pos=[-0.05, 0.48, -0.72], shaft=D(-80, 12), face=D(-10, -5), rk_w=[0.2, 1.0]),
             K(0.22, 'S17.R4', rk_pos=[-0.24, 0.42, -0.84], shaft=D(-100, -50), face=D(-30, -25), rk_w=[0.2, 1.0]),
             K(0.40, 'S17.R4', rk_pos=[-0.26, 0.40, -0.86], shaft=D(-100, -58), face=D(-30, -28), rk_w=[0.2, 1.0], l_attach=1.0),
             K(0.44, 'S17.R5/S17.R6', l_attach=0.5),
             K(0.47, 'S17.R6', l_attach=0.0, l_hand=ls(-95, 8, 0.90), l_palm=D(-60, 0)),
             K(0.55, 'S17.R7', rk_pos=rs(95, 8, 0.92), shaft=D(88, 62), face=D(0, 5), rk_w=[0.05, 1.0], l_attach=0.0, l_hand=ls(-95, 8, 0.95)),
             K(0.64, 'S17.R8', rk_pos=rs(96, 8, 0.92), shaft=D(88, 68), face=D(0, 5), rk_w=[0.05, 1.0], l_hand=ls(-95, 8, 0.95)),
             K(0.86, 'S17.R9', rk_pos=rs(96, 6, 0.90), shaft=D(88, 64), face=D(0, 5), rk_w=[0.05, 1.0], l_hand=ls(-95, 8, 0.95)),
             K(0.96, 'S17.R9', rk_pos=rs(40, -60, 0.65), shaft=D(30, 55), face=D(-50, 0), rk_w=[0.2, 1.0], l_hand=ls(-40, -50, 0.7)),
             K(1.06, 'LOCK', rk_pos=[0.10, 0.52, -0.55], shaft=D(15, 66), face=D(-60, 0), rk_w=[0.2, 1.0], l_attach=0.3, l_hand=ls(-20, -55, 0.55)),
             K(1.20, 'LOCK', rk_pos=[0.08, 0.55, -0.52], shaft=D(15, 68), face=D(-60, 0), rk_w=[0.2, 1.0], l_attach=1.0)]
    return base('SliceApproach', contact=0.47, keys=keys, contact_window=(0.43, 0.52))


# ---------------------------------------------------------------------------------------------------------------- 12. Serve
def Serve(S):
    R = S.ready
    f0 = R['rf_foot'][1]
    rs = lambda az, el, d: RS(S, az, el, d, 'R')
    ls = lambda az, el, d: RS(S, az, el, d, 'L')
    sh_z = float(S.rig.J['shoulder_L'][2])
    zs = sh_z + 0.16 + (S.A_arm + 0.10 + 0.30) - 0.10          # contact height: shoulder + a little jump + arm + hand + racket (scaled to THIS hero)

    def T(v):                                       # rxo1uEdLouY video seconds (slow motion): pendulum 179.05 -> 0.20 s ... racket at the hip 180.50 -> 1.00 s
        return round((0.20 + (v - 179.05) * 0.80 / 1.45) * 30) / 30
    tc = T(180.24)
    keys = []
    # S12 feet: shoulder width, flat, slow rocking; knees bend (130 -> 110-120 deg), deepest bend, both feet leave the ground together; airborne legs extended; one leg
    # (the R) kicks back and up while the other reaches down and lands first; landing leg bent and planted; the kicked leg swings forward and steps through; running steps
    # (in place here); then back to the ready stance (lock).
    keys += FT('rf', [(0.04, (0.21, f0 - 0.02), 0.0, 25.0, 0.0), (T(179.27), (0.21, f0 - 0.02), 0.0, 25.0, 0.0), (T(180.00), (0.21, f0 - 0.02), 0.0, 25.0, 0.0),
                      (T(180.10), (0.21, f0 - 0.02), 0.03, 20.0, 40.0), (T(180.24), (0.20, f0), 0.20, 10.0, 65.0), (T(180.30), (0.17, f0 - 0.20), 0.30, 5.0, 40.0),
                      (T(180.40), (0.15, f0 - 0.42), 0.50, 0.0, 20.0), (T(180.50), (0.15, f0 - 0.46), 0.46, 0.0, 20.0), (T(180.60), (0.18, f0 - 0.16), 0.28, 5.0, 10.0),
                      (T(180.80), (0.22, f0 + 0.30), 0.10, 10.0, 0.0), (T(180.90), (0.22, f0 + 0.34), 0.0, 10.0, 0.0), (1.28, (0.22, f0 + 0.34), 0.0, 10.0, 0.0),
                      (1.38, (0.28, f0 + 0.20), 0.08, 10.0, 0.0), (1.48, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0)], 'S12.F1/S12.F6/S12.F8/S12.F10')
    keys += FT('lf', [(0.04, (-0.21, f0 + 0.06), 0.0, -5.0, 0.0), (T(180.00), (-0.21, f0 + 0.06), 0.0, -5.0, 0.0), (T(180.10), (-0.21, f0 + 0.06), 0.03, -5.0, 40.0),
                      (T(180.24), (-0.20, f0 + 0.10), 0.20, -5.0, 65.0), (T(180.30), (-0.20, f0 + 0.12), 0.18, -5.0, 40.0), (T(180.40), (-0.18, f0 + 0.14), 0.0, -8.0, 0.0),
                      (T(180.50), (-0.18, f0 + 0.14), 0.0, -8.0, 0.0), (1.10, (-0.18, f0 + 0.14), 0.0, -8.0, 0.0), (1.20, (-0.20, f0 + 0.22), 0.10, -8.0, 0.0),
                      (1.28, (-0.22, f0 + 0.24), 0.0, -8.0, 0.0), (1.38, (-0.24, f0 + 0.20), 0.08, -8.0, 0.0), (1.48, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0)], 'S12.F7/S12.F9/S12.F10')
    keys += BODY([(0.04, (0.0, 0.0, 0.0), (30, 10, 0), (40, 16, 0)), (0.12, (0.01, 0.0, -0.01), (30, 11, 0), (40, 16, 0)), (T(179.27), (0.0, -0.01, -0.06), (36, 8, 0), (50, 8, 0)),
                  (T(179.60), (-0.02, -0.03, -0.08), (50, -4, 0), (78, -12, 0)), (T(179.90), (0.0, -0.01, -0.13), (54, -6, 0), (84, -14, 0)),
                  (T(180.00), (0.02, 0.0, -0.15), (50, -6, 0), (76, -10, 0)), (T(180.10), (0.04, 0.03, -0.06), (24, 0, 0), (28, -6, 0)),
                  (T(180.20), (0.04, 0.05, 0.14), (4, 0, 0), (-4, -6, -8)), (tc, (0.04, 0.06, 0.20), (0, -2, 0), (-14, -8, -12)),
                  (T(180.30), (0.04, 0.08, 0.16), (-12, 6, 0), (-30, 8, -6)), (T(180.40), (0.04, 0.10, -0.03), (-24, 22, 0), (-40, 24, 0)),
                  (T(180.50), (0.02, 0.10, -0.07), (-20, 24, 0), (-32, 26, 0)), (T(180.80), (0.0, 0.14, -0.05), (-10, 18, 0), (-12, 16, 0)),
                  (1.28, (0.0, 0.12, -0.08), (0, 14, 0), (0, 12, 0)), (1.48, (0.0, 0.0, 0.0), (0, 9, 0), (0, 8, 0))], 'S12.F5')
    # S12.R: racket hangs low in the R hand, the L hand holds the ball at the throat; pendulum (toss arm forward and up, racket arm back and down); racket rises behind the shoulder;
    # toss arm fully up at release; trophy; racket drops behind the back, toss arm folds down in front of the chest; torso rotates, racket arm swings up to full extension; contact;
    # racket swings down across the front of the body to the hip
    keys += [K(0.04, 'S12.R1', rk_pos=[0.12, 0.50, -0.70], shaft=D(5, -35), face=D(-70, 0), rk_w=[0.2, 1.0], l_attach=1.0, l_grip=0.0),
             K(0.20, 'S12.R1', rk_pos=[0.12, 0.50, -0.70], shaft=D(5, -35), face=D(-70, 0), rk_w=[0.2, 1.0], l_attach=1.0),
             K(0.24, 'S12.R2', rk_pos=rs(165, -62, 0.62), shaft=D(175, -50), face=D(-90, 0), rk_w=[0.2, 1.0], l_attach=0.0, l_hand=ls(5, 40, 0.85), l_palm=D(0, -80)),
             K(T(179.27), 'S12.R3', rk_pos=rs(145, 5, 0.52), shaft=D(165, 68), face=D(-80, 5), rk_w=[0.2, 1.0], l_hand=ls(5, 70, 0.95)),
             K(T(179.45), 'S12.R4', rk_pos=rs(130, 28, 0.48), shaft=D(165, 76), face=D(-70, 5), rk_w=[0.2, 1.0], l_hand=ls(0, 88, 1.0)),
             K(T(179.60), 'S12.R5', rk_pos=rs(125, 42, 0.45), shaft=D(160, 72), face=D(-60, 5), rk_w=[0.2, 1.0], l_hand=ls(0, 88, 1.0)),
             K(T(179.78), 'S12.R5', rk_pos=rs(125, 42, 0.45), shaft=D(160, 72), face=D(-60, 5), rk_w=[0.2, 1.0], l_hand=ls(0, 88, 1.0)),
             K(T(179.95), 'S12.R6', rk_pos=rs(150, 5, 0.50), shaft=D(175, -50), face=D(-80, -5), rk_w=[0.2, 1.0], l_hand=ls(15, -5, 0.45)),
             K(T(180.10), 'S12.R7', rk_pos=rs(70, 70, 0.75), shaft=D(120, 60), face=D(-10, 10), rk_w=[0.2, 1.0], l_hand=ls(15, -5, 0.45), rk_abs=0.0),
             K(tc, 'S12.R8/S12.C', rk_pos=rs(15, 82, 0.98), shaft=D(10, 72), face=D(0, 15), rk_sweet=[0.20, 0.55, zs], rk_abs=1.0, rk_w=[2.5, 0.5], l_hand=ls(20, -20, 0.45)),
             K(T(180.30), 'S12.R9', rk_pos=rs(-10, 0, 0.80), shaft=D(-40, 20), face=D(-20, 20), rk_abs=0.0, rk_w=[0.2, 1.0], l_hand=ls(25, -30, 0.45)),
             K(T(180.45), 'S12.R10', rk_pos=rs(-5, -55, 0.65), shaft=D(-50, -10), face=D(-40, 10), rk_w=[0.2, 1.0], l_hand=ls(-20, -40, 0.6)),
             K(1.25, 'LOCK', rk_pos=rs(30, -60, 0.65), shaft=D(25, 20), face=D(-60, 0), rk_w=[0.2, 1.0], l_hand=ls(-30, -50, 0.65), l_attach=0.0),
             K(1.48, 'LOCK', rk_pos=[0.08, 0.55, -0.52], shaft=D(15, 68), face=D(-60, 0), rk_w=[0.2, 1.0], l_attach=1.0, l_hand=ls(-30, -50, 0.6))]
    return base('Serve', contact=tc, keys=keys)


# ---------------------------------------------------------------------------------------------------------------- 16. Overhead
def Overhead(S):
    R = S.ready
    f0 = R['rf_foot'][1]
    rs = lambda az, el, d: RS(S, az, el, d, 'R')
    ls = lambda az, el, d: RS(S, az, el, d, 'L')
    sh_z = float(S.rig.J['shoulder_L'][2])
    zs = sh_z + 0.14 + (S.A_arm + 0.10 + 0.30) - 0.10
    keys = []
    # S16: upright, feet staggered at shoulder width; small adjusting shuffles while he turns sideways (L shoulder to the net); racket up in front of the chest, then cocked
    # behind the head while the L arm points up at the ball; racket drops behind the back as the knees bend; two-foot push (both feet off), contact in the air near the top,
    # arm straight overhead, back arched; both feet land (L slightly first), knees slightly bent; racket swings down in front of the body to the hip; relax
    keys += FT('rf', [(0.04, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0), (0.18, (0.28, f0 - 0.14), 0.04, 30.0, 0.0), (0.24, (0.26, f0 - 0.20), 0.0, 40.0, 0.0),
                      (0.56, (0.26, f0 - 0.20), 0.0, 40.0, 0.0), (0.62, (0.26, f0 - 0.20), 0.14, 40.0, 70.0), (0.71, (0.26, f0 - 0.20), 0.20, 40.0, 75.0),
                      (0.80, (0.26, f0 - 0.18), 0.04, 40.0, 30.0), (0.84, (0.26, f0 - 0.18), 0.0, 40.0, 0.0), (0.96, (0.26, f0 - 0.18), 0.0, 40.0, 0.0),
                      (1.08, (R['rf_foot'][0], f0), 0.0, 10.0, 0.0)], 'S16.F1/S16.F2/S16.F4/S16.F6')
    keys += FT('lf', [(0.04, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0), (0.18, (-0.20, f0 + 0.12), 0.04, 5.0, 0.0), (0.24, (-0.18, f0 + 0.16), 0.0, 10.0, 0.0),
                      (0.56, (-0.18, f0 + 0.16), 0.0, 10.0, 0.0), (0.62, (-0.18, f0 + 0.16), 0.14, 10.0, 70.0), (0.71, (-0.18, f0 + 0.16), 0.20, 10.0, 75.0),
                      (0.78, (-0.18, f0 + 0.16), 0.03, 10.0, 25.0), (0.82, (-0.18, f0 + 0.16), 0.0, 10.0, 0.0), (0.96, (-0.18, f0 + 0.16), 0.0, 10.0, 0.0),
                      (1.08, (R['lf_foot'][0], f0 + 0.02), 0.0, -10.0, 0.0)], 'S16.F1/S16.F2/S16.F4/S16.F6')
    keys += BODY([(0.04, (0.0, 0.0, 0.0), (0, 9, 0), (0, 8, 0)), (0.18, (0.0, 0.0, 0.0), (30, 8, 0), (46, 6, 0)), (0.30, (0.0, 0.0, 0.0), (42, 6, 0), (66, 4, 0)),
                  (0.46, (0.0, 0.0, -0.04), (46, 4, 0), (74, -4, 0)), (0.56, (0.0, -0.02, -0.08), (48, 2, 0), (78, -8, 0)),
                  (0.66, (0.0, 0.0, 0.10), (36, 0, 0), (50, -8, 0)), (0.71, (0.02, 0.03, 0.20), (0, -2, 0), (-8, -8, -10)),
                  (0.78, (0.02, 0.06, 0.14), (-10, 4, 0), (-24, 6, -4)), (0.84, (0.02, 0.06, -0.08), (-8, 14, 0), (-10, 12, 0)),
                  (0.96, (0.0, 0.03, -0.04), (-4, 11, 0), (-4, 9, 0)), (1.08, (0.0, 0.0, 0.0), (0, 9, 0), (0, 8, 0))], 'S16.F3/S16.F4')
    keys += [K(0.04, 'S16.R1', rk_pos=[0.12, 0.52, -0.10], shaft=D(10, 75), face=D(-60, 0), rk_w=[0.2, 1.0], l_attach=1.0),
             K(0.14, 'S16.R2', rk_pos=rs(90, 10, 0.5), shaft=D(30, 78), face=D(-50, 0), rk_w=[0.2, 1.0], l_attach=0.0, l_hand=ls(5, 50, 0.9), l_palm=D(0, -60)),
             K(0.30, 'S16.R3', rk_pos=rs(125, 60, 0.38), shaft=D(165, 62), face=D(-60, 5), rk_w=[0.2, 1.0], l_hand=ls(0, 85, 1.0)),
             K(0.46, 'S16.R3', rk_pos=rs(130, 55, 0.40), shaft=D(170, 55), face=D(-60, 5), rk_w=[0.2, 1.0], l_hand=ls(0, 88, 1.0)),
             K(0.56, 'S16.R4', rk_pos=rs(150, 8, 0.50), shaft=D(176, -52), face=D(-80, -5), rk_w=[0.2, 1.0], l_hand=ls(15, -5, 0.45)),
             K(0.66, 'S16.R5', rk_pos=rs(70, 70, 0.75), shaft=D(120, 60), face=D(-10, 10), rk_w=[0.2, 1.0], l_hand=ls(15, -5, 0.45), rk_abs=0.0),
             K(0.71, 'S16.R6/S16.C', rk_pos=rs(15, 82, 0.98), shaft=D(10, 72), face=D(0, 15), rk_sweet=[0.18, 0.50, zs], rk_abs=1.0, rk_w=[2.5, 0.5], l_hand=ls(20, -20, 0.45)),
             K(0.78, 'S16.R7', rk_pos=rs(-10, 0, 0.80), shaft=D(-40, 20), face=D(-20, 20), rk_abs=0.0, rk_w=[0.2, 1.0], l_hand=ls(25, -30, 0.45)),
             K(0.86, 'S16.R7', rk_pos=rs(-5, -55, 0.65), shaft=D(-50, -10), face=D(-40, 10), rk_w=[0.2, 1.0], l_hand=ls(-20, -40, 0.6)),
             K(0.96, 'S16.R8', rk_pos=rs(30, -60, 0.65), shaft=D(25, 20), face=D(-60, 0), rk_w=[0.2, 1.0], l_hand=ls(-30, -50, 0.65), l_attach=0.0),
             K(1.12, 'LOCK', rk_pos=[0.08, 0.55, -0.52], shaft=D(15, 68), face=D(-60, 0), rk_w=[0.2, 1.0], l_attach=1.0, l_hand=ls(-30, -50, 0.6))]
    return base('Overhead', contact=0.71, keys=keys)


BUILDERS = dict(SliceApproach=SliceApproach, Serve=Serve, Overhead=Overhead, Backhand=Backhand, BackhandWide=BackhandWide, Return=Return, VolleyForehand=VolleyForehand, VolleyBackhand=VolleyBackhand, ReadyIdle=ReadyIdle, Forehand=Forehand, ForehandOpen=ForehandOpen, ForehandWide=ForehandWide, ForehandShort=ForehandShort, SplitToForehand=SplitToForehand, SplitToBackhand=SplitToBackhand, RecoverCenter=RecoverCenter)


WARP = dict(
    Forehand=([(0, 0), (1.01, 0.86), (1.2, 1.2)], (0.86, 0.96)),
    ForehandOpen=([(0, 0), (0.79, 0.70), (1.0, 1.0)], (0.70, 0.84)),
    ForehandWide=([(0, 0), (1.04, 1.0), (1.3, 1.3)], (1.0, 1.1)),
    ForehandShort=([(0, 0), (1.0, 1.0)], (0.58, 0.68)),
    Backhand=([(0, 0), (1.0, 0.90), (1.2, 1.2)], (0.90, 1.0)),
    BackhandWide=([(0, 0), (1.06, 0.96), (1.3, 1.3)], (0.96, 1.06)),
    Return=([(0, 0), (0.60, 0.54), (0.9, 0.9)], (0.54, 0.64)),
    VolleyForehand=([(0, 0), (0.03, 0.08), (0.50, 0.44), (0.7, 0.7)], (0.44, 0.54)),
    VolleyBackhand=([(0, 0), (0.03, 0.08), (0.52, 0.44), (0.7, 0.7)], (0.44, 0.54)),
    Serve=([(0, 0), (0.04, 0.10), (1.6, 1.6)], None),
    Overhead=([(0, 0), (0.04, 0.10), (1.2, 1.2)], None),
    SliceApproach=([(0, 0), (0.04, 0.10), (1.2, 1.2)], None),
)


RACKET_LEN = 0.688          # Racket_Classic: butt cap to head tip (racket_<hero>.json bounding box)


def limit_reach(d, S, margin=0.04):
    """keep the racket sweet spot at the named contact within shoulder -> sweet spot <= arm length + 0.45 x racket length (the CONTACT_NAMED reach test):
    the pinned sweet-spot target of the contact key is pulled towards the hero's own shoulder by the excess.  A contact that has no pinned key (SliceApproach:
    the racket face / position at contact is not authored) gets a position-only pin built from the solved pose, so nothing about the face is invented."""
    import clipkit
    if d['contact'] is None:
        return d
    lmax = S.A_arm + 0.45 * RACKET_LEN - margin
    keys = d['keys']
    pinned = [k for k in keys if k['ch'].get('rk_abs') == 1.0 and k['ch'].get('rk_sweet') is not None]
    if not pinned:
        # probe the unpinned pose at the contact time; pin only if it is out of reach
        clip = clipkit.Clip(d, S.ready)
        P = clip.params(clip.d['contact'])
        P['rk_mode'] = 'fit'
        S.reset()
        b, h, info = S.solve(P)
        sw_w = np.asarray(info['sweet'], float)
        sh_w = np.asarray(info['R_shoulder'], float)
        dist = float(np.linalg.norm(sw_w - sh_w))
        if dist <= lmax:
            return d
        tgt = sh_w + (sw_w - sh_w) * (lmax / dist)
        import kin
        sweet_a = [float(x) for x in kin.w2a(tgt - S.O)]
        tc = d['contact']
        src = 'S%d.R6' % d['section']
        d['keys'] = keys + [K(tc - 0.09, src, rk_abs=0.0), K(tc, src, rk_sweet=sweet_a, rk_abs=1.0), K(tc + 0.09, src, rk_abs=0.0)]
        d['reach_limited'] = float(dist)
        return d
    import kin
    for it in range(3):
        clip = clipkit.Clip(d, S.ready)
        P = clip.params(clip.d['contact'])
        P['rk_mode'] = 'fit'
        S.reset()
        b, h, info = S.solve(P)
        sw_w = np.asarray(info['sweet'], float)
        sh_w = np.asarray(info['R_shoulder'], float)
        dist = float(np.linalg.norm(sw_w - sh_w))
        if dist <= lmax:
            break
        tgt = sh_w + (sw_w - sh_w) * (lmax / dist)
        sweet_a = [float(x) for x in kin.w2a(tgt - S.O)]
        for k in pinned:
            k['ch']['rk_sweet'] = list(sweet_a)
        d['reach_limited'] = float(dist)
    return d


def build(name, solver):
    d = BUILDERS[name](solver)
    if name in WARP:
        w, hold = WARP[name]
        d['warp'] = w
        if hold:
            d['hold'] = hold
    return limit_reach(d, solver)
