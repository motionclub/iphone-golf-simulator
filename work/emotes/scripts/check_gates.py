"""GATE EMOTES, animation lines: measures the re-imported FBX data (data/trace_<hero>_<clip>.npz from trace_fbx.py) against work/emotes/GATE_DEFS_preregistered.md.

  python3.13 check_gates.py            -> data/checks_anim.json  + prints one PASS / FAIL line per gate id and hero

Every threshold below is the one written in the pre-registered file; nothing here is tuned to a result."""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import emo_hero as EH
import kin

W = EH.W
DATA = EH.DATA
CLIPS = ['Emote_Scuba', 'Emote_Thrust', 'Emote_Spike', 'Intro_Wave', 'Intro_BringIt', 'Intro_Pushups']
TARGET = dict(Emote_Scuba=2.0, Emote_Thrust=2.0, Emote_Spike=2.0, Intro_Wave=2.0, Intro_BringIt=3.0, Intro_Pushups=3.0)
FPS = 30.0
FWD = np.array([0.0, -1.0, 0.0])
FINGER = ('Thumb', 'Index', 'Middle', 'Ring', 'Little')
RK_SCALE = 1.3


# ----------------------------------------------------------------------------------------------------------------------------- signal helpers
def compress(x, tol=1e-4):
    idx = [0]
    for i in range(1, len(x)):
        if abs(x[i] - x[idx[-1]]) > tol:
            idx.append(i)
    return idx


def peak_idx(x, prom, tol=1e-4):
    """indices of local maxima with prominence >= prom (a plateau counts once, at its first sample)"""
    x = np.asarray(x, float)
    ci = compress(x, tol)
    y = x[ci]
    out = []
    n = len(y)
    for k in range(n):
        left = y[k - 1] if k > 0 else -np.inf
        right = y[k + 1] if k < n - 1 else -np.inf
        if y[k] > left and y[k] > right or (k == 0 and n > 1 and y[0] > y[1]) or (k == n - 1 and n > 1 and y[-1] > y[-2]):
            # prominence
            lmin = y[k]
            j = k - 1
            while j >= 0 and y[j] < y[k]:
                lmin = min(lmin, y[j])
                j -= 1
            rmin = y[k]
            j = k + 1
            while j < n and y[j] < y[k]:
                rmin = min(rmin, y[j])
                j += 1
            base = max(lmin if k > 0 else -np.inf, rmin if k < n - 1 else -np.inf)
            if k == 0:
                base = rmin
            if k == n - 1:
                base = lmin
            if y[k] - base >= prom:
                out.append(ci[k])
    return out


def longest_run(mask):
    best, cur, start, bs = 0, 0, 0, 0
    for i, m in enumerate(mask):
        if m:
            if cur == 0:
                start = i
            cur += 1
            if cur > best:
                best, bs = cur, start
        else:
            cur = 0
    return best, bs


def runs(mask):
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def crossings(x):
    x = np.asarray(x, float) - np.mean(x)
    s = np.sign(x)
    s[s == 0] = 1
    return int(np.sum(s[1:] != s[:-1]))


def ang(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    return math.degrees(math.acos(max(-1, min(1, float(a @ b)))))


# ----------------------------------------------------------------------------------------------------------------------------- one hero
class Hero:
    def __init__(self, tag):
        self.tag = tag
        self.H = EH.EmoHero(tag)
        self.rig = self.H.rig
        self.ix = self.rig.idx
        self.names = self.rig.names
        self.T = {}
        for c in CLIPS + ['ReadyIdle', 'RunForward']:
            z = np.load(f'{DATA}/trace_{tag}_{c}.npz', allow_pickle=True)
            self.T[c] = dict(M=z['M'], HR=z['HR'], RC=z['RC'], ARM=z['ARM'], ROOT=z['ROOT'], meta=json.loads(str(z['meta'])), n=int(z['frames']))
        self.gen = {c: json.loads(str(np.load(f'{DATA}/gen_{c}_{tag}.npz', allow_pickle=True)['meta'])) for c in CLIPS}
        self.rk_pts = np.load(f'{DATA}/racket_pts.npz')['pts']

    def P(self, c, name):
        return self.T[c]['M'][:, self.ix[name], :3, 3]

    def Q(self, c, name):
        return self.T[c]['M'][:, self.ix[name], :3, :3]

    def tip(self, c, name):
        i = self.ix[name]
        M = self.T[c]['M'][:, i]
        return M[:, :3, 3] + np.einsum('nij,j->ni', M[:, :3, :3], np.array([0.0, self.rig.length[i], 0.0]))

    def nose(self, c):
        M = self.T[c]['M'][:, self.ix['Head']]
        return M[:, :3, 3] + np.einsum('nij,j->ni', M[:, :3, :3], self.H.nose_local)

    def pad(self, c, side):
        S = 'Left' if side == 'L' else 'Right'
        return 0.5 * (self.tip(c, S + 'IndexDistal') + self.tip(c, S + 'MiddleDistal'))

    def pitch(self, c):
        Q = self.Q(c, 'Hips')
        Rp = Q @ self.rig.Rrest[self.ix['Hips']].T
        v = Rp @ np.array([0.0, 0.0, 1.0])
        return np.degrees(np.arctan2(-v[:, 1], v[:, 2]))

    def head_yaw(self, c):
        Q = self.Q(c, 'Head') @ self.rig.Rrest[self.ix['Head']].T
        v = Q @ FWD
        return np.degrees(np.arctan2(v[:, 0], -v[:, 1]))

    def finger_angle(self, c, name):
        i = self.ix[name]
        p = self.rig.parent[i]
        Qi = self.T[c]['M'][:, i, :3, :3]
        Qp = self.T[c]['M'][:, p, :3, :3]
        B = np.einsum('ij,njk->nik', self.rig.rel_rot[i].T, np.einsum('nkj,nkl->njl', Qp, Qi))
        return np.degrees(np.arctan2(B[:, 2, 1], B[:, 1, 1]))

    def prox_mean(self, c, side):
        S = 'Left' if side == 'L' else 'Right'
        return np.mean([self.finger_angle(c, S + f + 'Proximal') for f in FINGER[1:]], axis=0)

    def open_prox(self, side):
        S = 'Left' if side == 'L' else 'Right'
        o = self.H.S.open[side]
        return float(np.mean([o.get(S + f + 'Proximal', 0.0) for f in FINGER[1:]]))

    def rk_origin(self, c):
        return self.T[c]['RC'][:, :3, 3]

    def rk_attach(self, c):
        return np.linalg.norm(self.T[c]['RC'][:, :3, 3] - self.T[c]['HR'][:, :3, 3], axis=1)

    def rk_lowest(self, c):
        RC = self.T[c]['RC']
        pts = RK_SCALE * self.rk_pts
        out = np.zeros(len(RC))
        for f in range(len(RC)):
            out[f] = RC[f, 2, 3] + (pts @ RC[f, :3, :3].T)[:, 2].min()
        return out

    def mesh(self, c, f):
        return self.H.mesh_M(self.T[c]['M'][f])


# ----------------------------------------------------------------------------------------------------------------------------- the lines
def line(ok, **kw):
    return dict(ok=bool(ok), **{k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in kw.items()})


def check_hero(h):
    R = {}
    ix = h.ix
    T = h.T
    ready = h.T['ReadyIdle']
    nonfinger = [i for i, n in enumerate(h.names) if n != 'Root' and not any(f in n for f in FINGER)]
    toe0 = {s: h.P('ReadyIdle', s + 'Toes')[0] for s in ('Left', 'Right')}
    toe0q = {s: toe0[s] for s in toe0}
    for c in CLIPS:
        r = {}
        nF = T[c]['n']
        n_s = (nF - 1) / FPS
        # ---- L1 length
        r['L1'] = line(abs(n_s - TARGET[c]) <= 0.35, length=n_s, target=TARGET[c])
        # ---- P1 in place
        arm_dev = float(np.abs(T[c]['ARM'] - T[c]['ARM'][0]).max())
        root_dev = float(np.abs(T[c]['ROOT'] - T[c]['ROOT'][0]).max())
        Qr0 = ready['M'][0, :, :3, :3]
        def rot_err(f):
            Qc = T[c]['M'][f, :, :3, :3]
            d = [math.degrees(math.acos(max(-1, min(1, (np.trace(Qc[i] @ Qr0[i].T) - 1) / 2)))) for i in nonfinger]
            return float(np.mean(d)), float(np.max(d))
        e0, e1 = rot_err(0), rot_err(nF - 1)
        slide, endd = {}, {}
        for s in ('Left', 'Right'):
            p = h.P(c, s + 'Toes')
            z0 = toe0[s][2]
            planted = p[:, 2] <= z0 + 0.04
            d = np.linalg.norm(p[:, :2] - toe0[s][:2], axis=1)
            slide[s] = float(d[planted].max()) if planted.any() else 0.0
            endd[s] = float(np.linalg.norm(p[-1] - toe0[s]))
        ok = arm_dev <= 1e-6 and root_dev <= 1e-6 and e0[0] <= 4 and e0[1] <= 12 and e1[0] <= 4 and e1[1] <= 12 and max(slide.values()) <= 0.02 and max(endd.values()) <= 0.03
        r['P1'] = line(ok, arm_dev=arm_dev, root_dev=root_dev, start_mean_deg=e0[0], start_max_deg=e0[1], end_mean_deg=e1[0], end_max_deg=e1[1], slide_max_m=max(slide.values()), end_toe_max_m=max(endd.values()))
        # ---- B1 bones / objects
        same_bones = T[c]['meta']['bones'] == ready['meta']['bones'] and sorted(map(tuple, T[c]['meta']['parents'])) == sorted(map(tuple, ready['meta']['parents']))
        same_objs = T[c]['meta']['objects'] == ready['meta']['objects']
        r['B1'] = line(same_bones and same_objs and T[c]['meta']['armatures'] == 1, bones=len(T[c]['meta']['bones']), objects=T[c]['meta']['objects'])
        # ---- R1 racket on the hand
        HR, RC = T[c]['HR'], T[c]['RC']
        hand_rel = np.array([np.linalg.inv(T[c]['M'][f, ix['RightHand']]) @ HR[f] for f in range(nF)])
        rel_dev = float(np.abs(hand_rel - hand_rel[0]).max())
        if c in ('Emote_Spike', 'Intro_Pushups'):
            r['R1'] = line(rel_dev <= 1e-5, hand_racket_const_dev=rel_dev, note='racket may leave: see K3 / U4')
        else:
            dp = float(np.linalg.norm(RC[:, :3, 3] - HR[:, :3, 3], axis=1).max())
            da = max(math.degrees(math.acos(max(-1, min(1, (np.trace(RC[f, :3, :3] @ HR[f, :3, :3].T) - 1) / 2)))) for f in range(nF))
            r['R1'] = line(dp <= 1e-4 and da <= 0.01 and rel_dev <= 1e-5, racket_hand_pos_m=dp, racket_hand_deg=da, hand_racket_const_dev=rel_dev)
        # ---- F1 floor
        zmin = min(float(h.mesh(c, f)[:, 2].min()) for f in range(nF))
        r['F1'] = line(zmin >= -0.03, mesh_min_z_m=zmin)
        R[c] = r

    # ============================================================================ SCUBA
    c = 'Emote_Scuba'
    nose = h.nose(c)
    dL = np.linalg.norm(h.pad(c, 'L') - nose, axis=1)
    dR = np.linalg.norm(h.pad(c, 'R') - nose, axis=1)
    side = 'L' if dL.mean() < dR.mean() else 'R'
    d = dL if side == 'L' else dR
    pinch = d <= 0.03
    n_run, s_run = longest_run(pinch)
    other = 'R' if side == 'L' else 'L'
    Oname = 'Right' if other == 'R' else 'Left'
    w = h.P(c, Oname + 'Hand')
    win = slice(s_run, s_run + n_run)
    dist_o = np.linalg.norm(w[win] - nose[win], axis=1)
    front = (-w[win][:, 1]) - (-nose[win][:, 1])
    frac_ok = float(np.mean((dist_o <= 0.30) & (front >= 0.0))) if n_run else 0.0
    xs = w[win][:, 0]
    cross, p2p = crossings(xs), float(xs.max() - xs.min()) if n_run else 0.0
    R[c]['S1'] = line(n_run / FPS >= 1.0, pinch_hand=side, pinch_seconds=n_run / FPS, mean_dist_m=float(d[pinch].mean()) if pinch.any() else None)
    R[c]['S2'] = line(frac_ok >= 0.8 and cross >= 4 and p2p >= 0.04, fraction_in_front_within_0p30=frac_ok, lateral_crossings=cross, lateral_p2p_m=p2p)
    kk = np.linalg.norm(h.P(c, 'LeftLowerLeg') - h.P(c, 'RightLowerLeg'), axis=1)
    pk = peak_idx(kk, 0.04)
    last = pk[-1] if pk else 0
    hold_after = bool(pinch[last:last + 6].all()) if pk else False
    R[c]['S3'] = line(len(pk) == 2, knee_maxima=len(pk), knee_dist_range_m=[float(kk.min()), float(kk.max())], peak_frames=pk)
    R[c]['S4'] = line(hold_after, last_knee_max_frame=int(last), pinch_held_0p15s_after=hold_after)

    # ============================================================================ THRUST
    c = 'Emote_Thrust'
    hp = h.P(c, 'Hips')
    fwd = -(hp[:, 1] - hp[0, 1])
    pk = peak_idx(fwd, 0.12)
    p2p = float(fwd.max() - fwd.min())
    R[c]['T1'] = line(len(pk) == 2 and p2p >= 0.15, hips_forward_maxima=len(pk), hips_forward_p2p_m=p2p, peak_frames=pk)
    pit = h.pitch(c)
    runp = h.P('RunForward', 'Hips')
    run_p2p = float(max((runp.max(0) - runp.min(0))))
    thr = fwd.min() + 0.4 * (fwd.max() - fwd.min())
    idx = np.where(fwd >= thr)[0]
    wsl = slice(int(idx[0]), int(idx[-1]) + 1)
    R[c]['T2'] = line((pit.max() - pit.min()) >= 20 and p2p >= 2 * run_p2p, pitch_swing_deg=float(pit.max() - pit.min()), hips_p2p_m=p2p, run_hips_p2p_m=run_p2p)
    okw = []
    for S_, s in (('Left', 'L'), ('Right', 'R')):
        wr, el, sh = h.P(c, S_ + 'Hand'), h.P(c, S_ + 'LowerArm'), h.P(c, S_ + 'UpperArm')
        up = (wr[:, 2] >= el[:, 2] - 0.02) & (np.linalg.norm(wr - sh, axis=1) <= 0.45)
        clo = h.prox_mean(c, s) - h.open_prox(s)
        need = 60.0 if s == 'L' else 25.0
        okw.append((float(np.mean(up[wsl])), float(np.mean(clo[wsl] >= need)), float(clo[wsl].mean())))
    R[c]['T3'] = line(all(a >= 0.8 and b >= 0.8 for a, b, _ in okw), left_up_frac=okw[0][0], left_closed_frac=okw[0][1], left_closure_deg=okw[0][2], right_up_frac=okw[1][0], right_closed_frac=okw[1][1], right_closure_deg=okw[1][2])
    dmin = min(float(np.linalg.norm(h.P(c, S_ + 'Hand') - hp, axis=1).min()) for S_ in ('Left', 'Right'))
    R[c]['T4'] = line(dmin >= 0.22, min_wrist_to_hips_m=dmin)

    # ============================================================================ SPIKE
    c = 'Emote_Spike'
    att = h.rk_attach(c)
    iv = runs(att > 0.02)
    low = h.rk_lowest(c)
    org = h.rk_origin(c)
    if len(iv) == 1:
        a, b = iv[0]
        dur = (b - a + 1) / FPS
        after_ok = bool((att[b + 1:] <= 0.001).all()) and (len(att) - (b + 1)) / FPS >= 0.5
        k3 = 0.6 <= dur <= 1.4 and after_ok
    else:
        a = b = 0
        dur, after_ok, k3 = 0.0, False, False
    R[c]['K3'] = line(k3, intervals=len(iv), off_seconds=dur, attached_after_return=after_ok, release_frame=int(a), return_frame=int(b + 1))
    contact = runs(low <= 0.01)
    rise = None
    if len(contact) >= 1 and len(iv) == 1:
        cf = contact[0][1]
        rise = float(org[cf:b + 1, 2].max() - org[contact[0][0]:contact[0][1] + 1, 2].min())
    R[c]['K4'] = line(len(contact) == 1 and rise is not None and rise >= 0.25, contact_events=len(contact), contact_frames=[list(x) for x in contact], origin_rise_m=rise, lowest_vertex_apex_m=float(low[a:b + 1].max()) if len(iv) == 1 else None)
    wr = h.P(c, 'RightHand')
    head_top = h.P(c, 'Head')[:, 2] + (h.rig.J['head_top'][2] - h.rig.J['head'][2])
    best = 0.0
    start_ok = False
    for i in range(max(0, a - 12), a + 1):
        for j in range(i + 1, min(a + 1, i + 8)):
            dz = wr[i, 2] - wr[j, 2]
            if dz > best:
                best, start_ok = dz, bool(wr[i, 2] >= head_top[i] - 0.15)
    R[c]['K1'] = line(best >= 0.6 and start_ok, descent_m=float(best), start_above_head_minus_0p15=start_ok)
    sp = np.linalg.norm(np.diff(wr, axis=0), axis=1) * FPS
    dn = -np.diff(wr[:, 2]) * FPS
    pit = h.pitch(c)
    toeL = h.P(c, 'LeftToes')
    rise_t = toeL[:, 2] - toe0['Left'][2]
    lifted = np.where(rise_t >= 0.04)[0]
    stamp = False
    if len(lifted):
        lf = lifted[-1]
        back = np.where(rise_t[lf:] <= 0.02)[0]
        stamp = bool(len(back) and (lf + back[0]) / FPS <= (a / FPS) + 0.15 + 1e-9)
    R[c]['K2'] = line(float(sp[:a + 3].max()) >= 6.0 and float(dn[:a + 3].max()) >= 5.0 and float(pit.max()) >= 40.0 and stamp, peak_wrist_speed_mps=float(sp[:a + 3].max()), peak_down_mps=float(dn[:a + 3].max()), pelvis_pitch_max_deg=float(pit.max()), stamp=stamp, left_toe_max_rise_m=float(rise_t.max()))
    hips = h.P(c, 'Hips')
    hipL = hips + np.array([0.19, 0.0, 0.08])
    hipR = hips + np.array([-0.19, 0.0, 0.08])
    onhip = (np.linalg.norm(h.P(c, 'LeftHand') - hipL, axis=1) <= 0.14) & (np.linalg.norm(h.P(c, 'RightHand') - hipR, axis=1) <= 0.14)
    onhip[:b + 1] = False
    nrun, srun = longest_run(onhip)
    yaw = h.head_yaw(c)[srun:srun + nrun] if nrun else np.zeros(1)
    dy = np.sign(np.diff(yaw)) if len(yaw) > 2 else np.zeros(1)
    dy = dy[dy != 0]
    revs = int(np.sum(dy[1:] != dy[:-1])) if len(dy) > 1 else 0
    R[c]['K5'] = line(nrun / FPS >= 0.3 and float(yaw.max() - yaw.min()) >= 25 and revs >= 2, on_hips_seconds=nrun / FPS, head_yaw_p2p_deg=float(yaw.max() - yaw.min()), head_yaw_reversals=revs)

    # ============================================================================ WAVE
    c = 'Intro_Wave'
    best = None
    for S_, s in (('Left', 'L'), ('Right', 'R')):
        wz = h.P(c, S_ + 'Hand')[:, 2] >= h.P(c, S_ + 'UpperArm')[:, 2]
        n_, s_ = longest_run(wz)
        if best is None or n_ > best[0]:
            best = (n_, s_, S_, s)
    n_, s_, S_, s = best
    sl = slice(s_, s_ + n_)
    Mh = T[c]['M'][:, ix[S_ + 'Hand']]
    fd = Mh[:, :3, 1]
    lat = np.degrees(np.arctan2(fd[:, 0], fd[:, 2]))[sl]
    palm = Mh[:, :3, 2][sl] @ FWD
    other = 'Right' if S_ == 'Left' else 'Left'
    wo = h.P(c, other + 'Hand')[sl]
    shaft = T[c]['HR'][:, :3, 1][sl]
    shaft_ch = max(ang(shaft[i], shaft.mean(0)) for i in range(len(shaft)))
    R[c]['W1'] = line(n_ / FPS >= 0.6 and crossings(lat) >= 4 and float(lat.max() - lat.min()) >= 40 and float(np.mean(palm >= 0.5)) >= 0.8, wave_hand=S_, wave_seconds=n_ / FPS, crossings=crossings(lat), lateral_p2p_deg=float(lat.max() - lat.min()), palm_forward_frac=float(np.mean(palm >= 0.5)))
    R[c]['W2'] = line(float(np.linalg.norm(wo - wo.mean(0), axis=1).max()) <= 0.03 and shaft_ch <= 8.0, other_wrist_excursion_m=float(np.linalg.norm(wo - wo.mean(0), axis=1).max()), shaft_change_deg=float(shaft_ch))

    # ============================================================================ BRING IT
    c = 'Intro_BringIt'
    t0, t1 = h.gen[c].get('times_list', [0, 0.45, 2.4, 3.0])[1:3]
    sl = slice(int(round(t0 * FPS)), int(round(t1 * FPS)) + 1)
    S_ = 'Left'
    Mh = T[c]['M'][:, ix['LeftHand']]
    chest = 0.5 * (h.P(c, 'LeftUpperArm') + h.P(c, 'RightUpperArm'))
    to_chest = chest - h.P(c, 'LeftHand')
    to_chest /= np.linalg.norm(to_chest, axis=1)[:, None]
    palm_dot = np.einsum('ni,ni->n', Mh[:, :3, 2], to_chest)[sl]
    tuck = h.prox_mean(c, 'L')[sl]
    pk = peak_idx(tuck, 17.5)
    wr = h.P(c, 'LeftHand')[sl]
    exc = float(np.linalg.norm(wr - wr.mean(0), axis=1).max())
    shaft = T[c]['HR'][:, :3, 1]
    head = T[c]['HR'][:, :3, 3] + shaft * (0.577 * RK_SCALE)
    hs = float((np.linalg.norm(np.diff(head, axis=0), axis=1) * FPS).max())
    R[c]['C1'] = line(float(np.mean(palm_dot >= 0.35)) >= 0.7 and len(pk) >= 3 and float(tuck.max() - tuck.min()) >= 35 and exc <= 0.12 and hs <= 2.0, palm_to_chest_frac=float(np.mean(palm_dot >= 0.35)), tuck_peaks=len(pk), tuck_p2p_deg=float(tuck.max() - tuck.min()), wrist_excursion_m=exc, racket_head_max_mps=hs)
    sh = shaft[sl]
    azi = [ang(np.array([v[0], v[1], 0.0]), FWD) for v in sh]
    ele = np.degrees(np.arcsin(np.clip(sh[:, 2], -1, 1)))
    R[c]['C2'] = line(max(azi) <= 25 and np.abs(ele).max() <= 35, azimuth_max_deg=float(max(azi)), elevation_abs_max_deg=float(np.abs(ele).max()))
    ev = []
    for s_ in ('Left', 'Right'):
        p = h.P(c, s_ + 'Toes')
        lift = p[:, 2] - toe0[s_][2]
        for a_, b_ in runs(lift >= 0.03):
            back = float(np.linalg.norm(p[min(b_ + 3, len(p) - 1)] - p[max(a_ - 3, 0)]))
            ev.append((s_, a_, b_, back))
    R[c]['C3'] = line(len(ev) == 2 and all(e[3] <= 0.03 for e in ev), lift_events=[[e[0], e[1], e[2], round(e[3], 4)] for e in ev])

    # ============================================================================ PUSHUPS
    c = 'Intro_Pushups'
    hl, hr_ = h.P(c, 'LeftHand')[:, 2], h.P(c, 'RightHand')[:, 2]
    chest_z = h.P(c, 'UpperChest')[:, 2]
    floor = (hl <= 0.12) & (hr_ <= 0.12) & (chest_z <= 0.65)
    n_run, s_run = longest_run(floor)
    R[c]['U1'] = line(n_run / FPS >= 0.8, floor_seconds=n_run / FPS, window=[int(s_run), int(s_run + n_run - 1)])
    sl = slice(s_run, s_run + n_run)
    cz = chest_z[sl]
    mins = peak_idx(-cz, 0.15)
    flex = []
    for S_ in ('Left', 'Right'):
        u = h.P(c, S_ + 'LowerArm') - h.P(c, S_ + 'UpperArm')
        l = h.P(c, S_ + 'Hand') - h.P(c, S_ + 'LowerArm')
        flex.append(np.array([ang(u[i], l[i]) for i in range(len(u))]))
    fl = np.minimum(flex[0], flex[1])[sl]
    rep_ok = len(mins) == 2 and all(fl[m] - fl[max(0, m - 8):m + 9].min() >= 0 for m in mins) and float(fl.max() - fl.min()) >= 60
    R[c]['U2'] = line(len(mins) == 2 and rep_ok, chest_minima=len(mins), chest_range_m=float(cz.max() - cz.min()), elbow_flex_range_deg=float(fl.max() - fl.min()))
    R[c]['U3'] = line(float(h.P(c, 'Hips')[-1, 2]) >= 0.80, hips_z_end=float(h.P(c, 'Hips')[-1, 2]))
    att = h.rk_attach(c)
    iv = runs(att > 0.02)
    low = h.rk_lowest(c)
    org = h.rk_origin(c)
    if len(iv) == 1:
        a, b = iv[0]
        dur = (b - a + 1) / FPS
        after = bool((att[b + 1:] <= 0.001).all()) and len(att) - (b + 1) >= 3
        rest = runs((low[a:b + 1] <= 0.03))
        rest = max(rest, key=lambda x: x[1] - x[0]) if rest else (0, 0)
        ra, rb = a + rest[0], a + rest[1]
        move = float(np.linalg.norm(org[ra:rb + 1] - org[ra:rb + 1].mean(0), axis=1).max()) if rb > ra else 99.0
        # clearance of the lying racket from the body
        pts = RK_SCALE * h.rk_pts[::12]
        clear = 99.0
        for f in range(ra + 2, rb - 1, 4):
            M = T[c]['RC'][f]
            wp = (pts @ M[:3, :3].T) + M[:3, 3]
            body = h.mesh(c, f)
            dmin = float(np.sqrt(((wp[:, None, :] - body[None, ::4, :]) ** 2).sum(-1)).min())
            clear = min(clear, dmin)
        R[c]['U4'] = line(dur >= 1.2 and after and move <= 0.02 and (rb - ra + 1) / FPS >= 1.0 and clear >= 0.01, intervals=1, off_seconds=dur, attached_after=after, rest_seconds=(rb - ra + 1) / FPS, rest_origin_move_m=move, min_clearance_m=clear, release_frame=int(a), return_frame=int(b + 1))
    else:
        R[c]['U4'] = line(False, intervals=len(iv))
    return R


def main():
    out = {}
    for tag in ('male', 'female'):
        out[tag] = check_hero(Hero(tag))
    # same frame counts / key times on both heroes
    same = {}
    for c in CLIPS:
        gm = json.loads(str(np.load(f'{DATA}/gen_{c}_male.npz', allow_pickle=True)['meta']))
        gf = json.loads(str(np.load(f'{DATA}/gen_{c}_female.npz', allow_pickle=True)['meta']))
        same[c] = line(gm['frames'] == gf['frames'] and gm.get('times') == gf.get('times') and gm.get('times_list') == gf.get('times_list'), male_frames=gm['frames'], female_frames=gf['frames'])
    out['same_timing'] = same
    json.dump(out, open(f'{DATA}/checks_anim.json', 'w'), indent=1, default=float)
    ids = ['L1', 'P1', 'B1', 'R1', 'F1']
    per = dict(Emote_Scuba=['S1', 'S2', 'S3', 'S4'], Emote_Thrust=['T1', 'T2', 'T3', 'T4'], Emote_Spike=['K1', 'K2', 'K3', 'K4', 'K5'], Intro_Wave=['W1', 'W2'], Intro_BringIt=['C1', 'C2', 'C3'], Intro_Pushups=['U1', 'U2', 'U3', 'U4'])
    allok = True
    for c in CLIPS:
        for gid in ids + per[c]:
            m, f = out['male'][c][gid], out['female'][c][gid]
            ok = m['ok'] and f['ok']
            allok &= ok
            print(f"{'PASS' if ok else 'FAIL'} {c:14s} {gid}  male {'ok' if m['ok'] else 'NO'}  female {'ok' if f['ok'] else 'NO'}")
            if not ok:
                print('     male  ', {k: v for k, v in m.items() if k != 'ok'})
                print('     female', {k: v for k, v in f.items() if k != 'ok'})
        print(f"{'PASS' if same[c]['ok'] else 'FAIL'} {c:14s} same timing {same[c]}")
        allok &= same[c]['ok']
    print('ANIMATION LINES', 'PASS' if allok else 'FAIL')


if __name__ == '__main__':
    main()
