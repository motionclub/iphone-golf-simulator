"""Walk and run channel generators (see loco.py).  Every number is either read from WATCH.md (the step is named in a comment, `W:` = WATCH.md section.step) or is a
geometric consequence of the design speed.  One foot function is evaluated at phase u (right foot) and u + 0.5 (left foot).

The planted foot is pinned to a point of the court: in the Root frame its ball-of-foot point moves backwards along the direction of travel at exactly the design speed V
(s = s_td - V*T*u), so a clip played at rate  actor_speed / V  does not slide.  The swing foot leaves with that same velocity and lands with it (zero ground speed at touchdown).
Foot height is controlled through the LOWEST SKINNED VERTEX of the foot (loco.calibrate): planted = exactly on the floor, swing = the height keys below."""
import math

import numpy as np

import loco
from loco import PCurve, Hermite, smooth, FPS


def D(az, el):
    a, e = math.radians(az), math.radians(el)
    return [math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)]


class Foot:
    """one foot as a function of its own phase u in [0,1) (touchdown at u = 0).
    P: T, V, S (stance fraction), s_td (ball displacement along the travel axis at touchdown, relative to its mid-stance value), r_st (half foot spacing across the travel axis),
       r_arc, pitch [(u, deg)] heel-up +, s_mid [(u, s rel mid-stance)] swing keys, hgt_mid [(u, m)] swing lowest-vertex height keys, toe_off_rise, td_fall"""

    def __init__(self, P):
        self.P = P
        self.stride = P['V'] * P['T']
        self.S = P['S']
        s_td = P['s_td'] if 's_td' in P else self.stride * self.S / 2.0 + P.get('s_td_trim', 0.0)
        self.s_td = s_td
        self.s_to = s_td - self.stride * self.S
        sw = [(self.S, self.s_to, -self.stride)] + [(u, s, None) for (u, s) in P['s_mid']] + [(1.0, s_td, -self.stride)]
        self.s_sw = Hermite(sw)
        self.pitch = PCurve(P['pitch'])
        self.hgt = Hermite([(self.S, 0.0, P.get('toe_off_rise', 0.8))] + [(u, h, None) for (u, h) in P['hgt_mid']] + [(1.0, 0.0, -P.get('td_fall', 0.6))])

    def s(self, u):
        u = u % 1.0
        return self.s_td - self.stride * u if u <= self.S else float(self.s_sw(u))

    def lateral(self, u):
        u = u % 1.0
        if u <= self.S:
            return self.P['r_st']
        a = (u - self.S) / (1 - self.S)
        return self.P['r_st'] + self.P.get('r_arc', 0.0) * math.sin(math.pi * a)

    def height(self, u):
        u = u % 1.0
        return 0.0 if u <= self.S else max(0.0, float(self.hgt(u)))

    def heel(self, u):
        return float(self.pitch(u % 1.0))


def base_channels(hero):
    P = dict(hero.ready)
    P['rk_mode'] = 'fixed'
    P['rk_swivel'] = 0.0
    P['l_attach'] = 0.0
    P['r_fing'] = 1.0
    P['rk_abs'] = 0.0
    return P


def vec(psi):
    """unit vector in the authoring (r, f) plane for a heading psi (deg, 0 = forward, + = right)"""
    a = math.radians(psi)
    return np.array([math.sin(a), math.cos(a)])


def place_feet(hero, P, foot, u_R, psi_travel, psi_body, toe_out=5.0, knee_extra=3.0):
    """ball-of-foot ground points (Root frame) from the foot function.  The travel axis is psi_travel, the feet point along psi_body (+- toe_out), the pelvis stays at
    (0, hip_f); the ankle of a flat foot sits under the hip at mid-stance."""
    d = vec(psi_travel)
    nR = np.array([d[1], -d[0]])                          # to the right of the travel direction
    h = vec(psi_body)
    hip = np.array([0.0, hero.hip_f])
    for side, u, sg in (('R', u_R % 1.0, 1.0), ('L', (u_R + 0.5) % 1.0, -1.0)):
        key = 'rf' if side == 'R' else 'lf'
        mid = hip + hero.ankle_ball_f * h                 # ball position when the ankle is under the hip
        ball = mid + foot.s(u) * d + sg * foot.lateral(u) * nR
        P[f'{key}_foot'] = [float(ball[0]), float(ball[1])]
        P[f'{key}_heel'] = foot.heel(u)
        yaw = hero.toe_dir_to_yaw(side, psi_body + sg * toe_out)
        P[f'{key}_yaw'] = yaw
        sk = 1.0 if side == 'R' else -1.0                  # solver: outwards sign
        P[f'{key}_knee'] = float(sk * ((psi_body + sk * knee_extra) - yaw))
    return P


def heights_target(foot, u_R, N, k):
    return foot.height(u_R), foot.height(u_R + 0.5)


# ---------------------------------------------------------------------------------------------------------------------- WALK
def walk(hero, W=None):
    W = dict(name='Walk', frames=66, V=1.25, S=0.60, dz0=0.009, bob=0.017, td_trim=0.06, **(W or {}))
    N = W['frames']
    T = N / FPS
    # W: 2.1 one step every 0.5 s (cycle ~1.0 s), 2.2 heel first with the leg nearly straight, flat, heel rises while the toes stay down, toes leave last,
    # 2.3 swing foot clears about one shoe height (8-12 cm), always one foot down (60 % stance, 10 % double support at each end), 2.5 racket hangs low in the right hand,
    # little arm swing, left arm swings opposite the left leg
    fp = dict(T=T, V=W['V'], S=W['S'], s_td_trim=-W['td_trim'], r_st=0.115, r_arc=0.012,
              pitch=[(0.0, -8.0), (0.10, 0.0), (0.38, 0.0), (0.60, 42.0), (0.68, 30.0), (0.80, 8.0), (0.92, -2.0)],
              s_mid=[], hgt_mid=[(0.68, 0.040), (0.80, 0.095), (0.92, 0.045)], toe_off_rise=0.55, td_fall=0.45)
    foot = Foot(fp)
    Ps, tgt = [], dict(L=np.zeros(N), R=np.zeros(N))
    for k in range(N):
        u = k / N
        c1, s1, c2 = math.cos(2 * math.pi * u), math.sin(2 * math.pi * u), math.cos(4 * math.pi * u)
        P = base_channels(hero)
        place_feet(hero, P, foot, u, 0.0, 0.0)
        tgt['R'][k], tgt['L'][k] = heights_target(foot, u, N, k)
        P['pel'] = [0.012 * s1, 0.0, W['dz0'] - W['bob'] * c2]
        P['pel_rot'] = [-4.0 * c1, 3.0, -2.0 * s1]
        P['chest_rot'] = [7.0 * c1, 2.0, 0.0]
        P['head_rot'] = [-3.0 * c1, -4.0, 0.0]
        sh = hero.ready['sh_half_A']
        P['l_hand'] = [-max(sh + 0.040, 0.54), 0.03 + 0.26 * c1, -0.895 + 0.040 * c1]       # >= 0.27 m from the midline: the swinging hand clears the hip / thigh
        P['l_palm'] = [1.0, 0.0, 0.0]
        P['l_elbow'] = [-0.35, -0.75, -0.55]
        P['l_fing'] = 0.25
        P['rk_pos'] = [max(sh + 0.11, 0.58), 0.06 - 0.07 * c1, -0.86]
        P['rk_shaft'] = D(8, -25)
        P['rk_face'] = D(-65, 0)
        P['r_elbow'] = [0.30, -0.55, -0.80]
        Ps.append(P)
    stride = fp['V'] * T
    meta = dict(name=W['name'], frames=N, cycle_s=T, V=W['V'], S=W['S'], stride_m=stride, heading=0.0, loop=True, kind='walk',
                src='W:S2.1/S2.2/S2.3/S2.5 (JJEDwXeDjBc t=245.00-246.10, 309.00-310.10)')
    return Ps, tgt, meta


# ---------------------------------------------------------------------------------------------------------------------- RUN
def run_gen(hero, name, psi_travel, psi_body, psi_chest, psi_head, W=None):
    """psi_*: travel direction of the clip (the actor moves that way), heading of the pelvis, of the chest, of the head (deg, + = right of forward)"""
    W = dict(frames=34, S=0.38, dist=0.70, s_td=0.27, bob=0.026, dz0=0.012, lean=8.0, **(W or {}))
    N = W['frames']
    T = N / FPS
    W['V'] = W['dist'] / (T * W['S'])                              # planted-foot speed: the ball of the foot travels `dist` metres in the Root frame during the stance
    lat = abs(psi_travel) > 1.0
    # W: 1.1 alternate single-support steps with a short flight (1-3 frames at 60 fps), 1.2 heel up toward the buttock on the trailing foot, the swing foot passes with the knee
    # leading, 1.4 step period 0.27-0.33 s (here 0.283 s), 1.5 opposite arm swing (hand to chest height in front, hip behind), racket in the right hand with the head up,
    # 1.6 trunk lean 10-15 deg, head level looking to the ball
    fp = dict(T=T, V=W['V'], S=W['S'], s_td=W['s_td'], r_st=0.095 if lat else 0.080, r_arc=0.0,
              pitch=[(0.0, 14.0), (0.10, 4.0), (0.22, 0.0), (0.30, 14.0), (0.40, 50.0), (0.47, 70.0), (0.56, 60.0), (0.70, 30.0), (0.85, 14.0)],
              s_mid=[(0.70, -0.12)], hgt_mid=[(0.47, 0.150), (0.58, 0.200), (0.70, 0.195), (0.85, 0.095)], toe_off_rise=1.6, td_fall=1.0)
    foot = Foot(fp)
    sgn = 1.0 if psi_body >= 0 else -1.0
    Ps, tgt = [], dict(L=np.zeros(N), R=np.zeros(N))
    n_t = np.array([vec(psi_travel)[1], -vec(psi_travel)[0]])           # right of the travel direction
    for k in range(N):
        u = k / N
        c1, s1 = math.cos(2 * math.pi * u), math.sin(2 * math.pi * u)
        P = base_channels(hero)
        place_feet(hero, P, foot, u, psi_travel, psi_body, toe_out=3.0)
        tgt['R'][k], tgt['L'][k] = heights_target(foot, u, N, k)
        # pelvis: lowest at mid stance (u = 0.2, 0.7), highest in flight (0.45, 0.95); sways toward the stance foot
        bob = W['bob'] * math.cos(4 * math.pi * (u - 0.45))
        sway = 0.016 * s1
        P['pel'] = [float(sway * n_t[0]), float(sway * n_t[1]), W['dz0'] + bob - 0.5 * W['bob']]
        cnt = 6.0                                                    # pelvis counter-rotation against the shoulders (deg)
        shd = 9.0
        pel_yaw = psi_body - cnt * c1
        chest_abs = psi_chest + shd * c1
        P['pel_rot'] = [pel_yaw, W['lean'], -3.0 * s1]
        P['chest_rot'] = [chest_abs - pel_yaw, 5.0, 0.0]
        P['head_rot'] = [psi_head - chest_abs, -9.0, 0.0]
        # left arm (elbow ~90 deg): hand to chest height in front when the RIGHT leg is forward (u = 0), beside the hip behind
        sh = hero.ready['sh_half_A']
        P['l_hand'] = [-max(sh + 0.02, 0.50), 0.12 + 0.38 * c1, -0.52 + 0.10 * c1]
        P['l_palm'] = [1.0, 0.0, 0.0]
        P['l_elbow'] = [-0.40, -0.60, -0.70]
        P['l_fing'] = 0.45
        # right arm holds the racket, swings less (hand forward when the left leg is forward)
        P['rk_pos'] = [sh + 0.01, 0.32 - 0.13 * c1, -0.43 - 0.05 * c1]
        P['rk_shaft'] = D(psi_chest + 8, 32 - 14 * c1)
        P['rk_face'] = D(psi_chest - 115, 0)
        P['r_elbow'] = [0.30, -0.60, -0.60]
        Ps.append(P)
    stride = fp['V'] * T
    meta = dict(name=name, frames=N, cycle_s=T, V=W['V'], S=W['S'], stride_m=stride, heading=psi_body, travel=psi_travel, loop=True, kind='run',
                src='W:S1.1/S1.2/S1.4/S1.5/S1.6 (JJEDwXeDjBc t=301.70-302.37, 392.40-393.50)')
    return Ps, tgt, meta


def runf(hero):
    return run_gen(hero, 'RunForward', 0.0, 0.0, 0.0, 0.0)


def runr(hero):
    # lateral run to the hero's right: the body faces the way it runs (WATCH 1 lateral run: a short wide ball is shuffled half turned, a longer one is run facing the way he goes)
    return run_gen(hero, 'RunRight', 90.0, 70.0, 58.0, 38.0)


def runl(hero):
    return run_gen(hero, 'RunLeft', -90.0, -70.0, -58.0, -38.0)
