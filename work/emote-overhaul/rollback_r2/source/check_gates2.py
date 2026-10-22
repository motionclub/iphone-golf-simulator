"""GATE: EMOTE OVERHAUL (Spike / Scuba / Thrust).  Measures the pre-registered file work/emote-overhaul/GATE_DEFS_preregistered.md on the RE-IMPORTED FBX (data/trace_<hero>_<clip>.npz from trace_fbx2.py),
the solver (for the fidelity and the clearance-track lines) and the collide3.py results.  Run it with Blender's python so that the clearance track can be rebuilt:

  blender -b --factory-startup --python check_gates2.py -- [male|female|both]

Writes work/emote-overhaul/data/checks2.json and prints one PASS / FAIL line per gate id, hero and clip.  Every threshold below is the one written in the pre-registered file."""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts'))
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
import emo_hero as EH
import emo_clips2 as EC
import kin
from kin import w2a

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
OL = REPO + '/work/emote-overhaul'
DATA = OL + '/data'
LEN = dict(Emote_Spike=3.2, Emote_Thrust=3.5, Emote_Scuba=4.7)
CLIPS = list(LEN)
FPS = 30.0
FINGER = ('Thumb', 'Index', 'Middle', 'Ring', 'Little')
FWD = np.array([0.0, -1.0, 0.0])
RK_SCALE = 1.0                                   # racket drawn at 1.0 on the match heroes


def line(ok, **kw):
    out = {}
    for k, v in kw.items():
        if isinstance(v, (np.floating, float)):
            out[k] = round(float(v), 4)
        elif isinstance(v, np.ndarray):
            out[k] = [round(float(x), 4) for x in v.ravel()[:12]]
        elif isinstance(v, (np.integer,)):
            out[k] = int(v)
        else:
            out[k] = v
    return dict(ok=bool(ok), **out)


class Hero:
    def __init__(self, tag):
        self.tag = tag
        self.H = EH.EmoHero(tag)
        self.rig = self.H.rig
        self.ix = self.rig.idx
        self.names = self.rig.names
        self.O = self.H.O
        self.T = {}
        for c in CLIPS + ['ReadyIdle']:
            z = np.load(f'{DATA}/trace_{tag}_{c}.npz', allow_pickle=True)
            self.T[c] = dict(M=z['M'], HR=z['HR'], RC=z['RC'], ARM=z['ARM'], ROOT=z['ROOT'], meta=json.loads(str(z['meta'])), n=int(z['frames']))
        self.rk_pts = np.load(f'{EH.DATA}/racket_pts.npz')['pts']
        # racket tip = the racket point farthest along the shaft axis (local y)
        self.rk_tip_local = self.rk_pts[np.argmax(self.rk_pts[:, 1])]

    def P(self, c, name):
        return self.T[c]['M'][:, self.ix[name], :3, 3]

    def A(self, c, name):
        """authoring frame (r right, f forward, u up; floor origin) position of a bone head"""
        p = self.P(c, name) - self.O
        return np.stack([-p[:, 0], -p[:, 1], p[:, 2]], axis=1)

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

    def rk_world(self, c, pts):
        RC = self.T[c]['RC']
        return np.einsum('nij,mj->nmi', RC[:, :3, :3], RK_SCALE * pts) + RC[:, None, :3, 3]

    def rk_lowest(self, c):
        RC = self.T[c]['RC']
        pts = RK_SCALE * self.rk_pts
        out = np.zeros(len(RC))
        for f in range(len(RC)):
            out[f] = RC[f, 2, 3] + (pts @ RC[f, :3, :3].T)[:, 2].min()
        return out

    def rk_tipw(self, c):
        RC = self.T[c]['RC']
        return RC[:, :3, 3] + np.einsum('nij,j->ni', RC[:, :3, :3], RK_SCALE * self.rk_tip_local)

    def mesh(self, c, f):
        return self.H.mesh_M(self.T[c]['M'][f])


def rot_deg(A, B):
    return math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(A @ B.T) - 1.0) / 2.0))))


def ang(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    return math.degrees(math.acos(max(-1.0, min(1.0, float(a @ b)))))


def flexion(h, c, side):
    S = 'Left' if side == 'L' else 'Right'
    hip, knee, ank = h.P(c, S + 'UpperLeg'), h.P(c, S + 'LowerLeg'), h.P(c, S + 'Foot')
    a, b = knee - hip, ank - knee
    cs = np.einsum('ni,ni->n', a, b) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1))
    return np.degrees(np.arccos(np.clip(cs, -1, 1)))


# ---------------------------------------------------------------------------------------------------------------------------------------------- the checks
def check_hero(h, solver_clips):
    R = {c: {} for c in CLIPS}
    ix = h.ix
    T = h.T
    ready = T['ReadyIdle']
    nonfinger = [i for i, n in enumerate(h.names) if n != 'Root' and not any(f in n for f in FINGER)]
    toe0 = {s: h.P('ReadyIdle', s + 'Toes')[0] for s in ('Left', 'Right')}
    O = h.O
    for c in CLIPS:
        r = R[c]
        nF = T[c]['n']
        fbx = f'{REPO}/work/emotes/export/fbx/{"Male" if h.tag == "male" else "Female"}_{c}.fbx'
        same_bones = T[c]['meta']['bones'] == ready['meta']['bones'] and sorted(map(tuple, T[c]['meta']['parents'])) == sorted(map(tuple, ready['meta']['parents']))
        same_objs = T[c]['meta']['objects'] == ready['meta']['objects']
        r['G1'] = line(os.path.exists(fbx) and same_bones and same_objs and T[c]['meta']['armatures'] == 1 and nF == int(round(LEN[c] * 30)) + 1, frames=nF, expected=int(round(LEN[c] * 30)) + 1, bones=len(T[c]['meta']['bones']), objects=T[c]['meta']['objects'])
        arm_dev = float(np.abs(T[c]['ARM'] - T[c]['ARM'][0]).max())
        root_dev = float(np.abs(T[c]['ROOT'] - T[c]['ROOT'][0]).max())
        r['G2'] = line(arm_dev <= 1e-6 and root_dev <= 1e-6, arm_dev=arm_dev, root_dev=root_dev)
        Qr0 = ready['M'][0, :, :3, :3]

        def rot_err(f):
            Qc = T[c]['M'][f, :, :3, :3]
            d = [rot_deg(Qc[i], Qr0[i]) for i in nonfinger]
            return float(np.mean(d)), float(np.max(d))
        e0, e1 = rot_err(0), rot_err(nF - 1)
        r['G3'] = line(e0[0] <= 4 and e0[1] <= 12 and e1[0] <= 4 and e1[1] <= 12, start_mean_deg=e0[0], start_max_deg=e0[1], end_mean_deg=e1[0], end_max_deg=e1[1])
        slide, endd = {}, {}
        for s in ('Left', 'Right'):
            p = h.P(c, s + 'Toes')
            z0 = toe0[s][2]
            planted = p[:, 2] <= z0 + 0.04
            d = np.linalg.norm(p[:, :2] - toe0[s][:2], axis=1)
            slide[s] = float(d[planted].max()) if planted.any() else 0.0
            endd[s] = float(np.linalg.norm(p[-1] - toe0[s]))
        zmin = min(float(h.mesh(c, f)[:, 2].min()) for f in range(nF))
        r['G4'] = line(max(slide.values()) <= 0.01 and max(endd.values()) <= 0.02 and zmin >= -0.03, slide_max_m=max(slide.values()), end_toe_max_m=max(endd.values()), mesh_min_z_m=zmin)
        # ---- G5 fidelity FBX vs solver
        C = solver_clips[c]
        worst = 0.0
        for k in np.linspace(0, nF - 1, 12).astype(int):
            d = C.solve(k / FPS)
            for nm in ('Head', 'LeftHand', 'RightHand', 'Hips'):
                worst = max(worst, float(np.linalg.norm(d['info']['Pos'][ix[nm]] - T[c]['M'][k, ix[nm], :3, 3])))
        r['G5'] = line(worst <= 0.002, worst_mm=1000 * worst)
        # ---- G6 racket in hand (Spike, Thrust)
        HR, RC = T[c]['HR'], T[c]['RC']
        if c != 'Emote_Scuba':
            dp = float(np.linalg.norm(RC[:, :3, 3] - HR[:, :3, 3], axis=1).max())
            da = max(rot_deg(RC[f, :3, :3], HR[f, :3, :3]) for f in range(nF))
            floor = max(rot_deg(ready['RC'][f, :3, :3], ready['HR'][f, :3, :3]) for f in range(ready['n']))
            no_anim = not json.loads(str(np.load(f'{EH.DATA}/gen_{c}_{h.tag}.npz', allow_pickle=True)['meta'])).get('racket_detaches', False)
            r['G6'] = line(dp <= 1e-4 and da <= 0.25 and no_anim, racket_hand_pos_m=dp, racket_hand_deg=da, readyidle_floor_deg=floor, no_racket_animation=no_anim)
        # ---- G7 no arm through the body (collide3.py results)
        jp = f'{OL}/proof/collide/{c}_{h.tag}_c3.json'
        if os.path.exists(jp):
            rows = json.load(open(jp))['rows']
            worst, wf, over, over_list = 0.0, None, 0, []
            for row in rows:
                t = row['t']
                lim = 0.020 if (t < 0.25 or t > LEN[c] - 0.25) else 0.012
                pen = max(row['L']['pen_skin'], row['R']['pen_skin'], row['racket']['pen_skin'])
                if pen > worst:
                    worst, wf = pen, row['frame']
                if pen > lim:
                    over += 1
                    over_list.append((row['frame'], round(1000 * pen, 1)))
            r['G7'] = line(over == 0 and len(rows) == nF, frames_checked=len(rows), frames_over_limit=over, worst_mm=1000 * worst, worst_frame=wf, over_limit_frames_mm=over_list[:8])
        else:
            r['G7'] = line(False, note='collide3 json missing: ' + jp)
        # ---- G8 smooth clearance track, no speed spikes added
        xs = C.clearance_track()
        if xs is None:
            r['G8'] = line(True, note='clearance off')
        else:
            tt = np.arange(len(xs)) / FPS
            wfade = np.array([EC.sm(t, 0.0, 0.20) * (1.0 - EC.sm(t, LEN[c] - 0.20, LEN[c])) for t in tt])
            aw = np.array([C.arm_weight(t_) for t_ in tt])
            applied = xs * wfade[:, None, None] * aw[:, :, None]
            jump = float(np.max(np.linalg.norm(np.diff(applied[:, :, :3], axis=0), axis=2)))
            sjump = float(np.degrees(np.max(np.abs(np.diff(applied[:, :, 3], axis=0)))))
            spike = 0.0
            saved = C._track
            C._track = np.zeros_like(saved)                                       # the same final solve (contact solves included) with the clearance switched off
            nominal_pos = {nm: np.array([C.solve(k / FPS)['info']['Pos'][ix[nm]] for k in range(nF)]) for nm in ('LeftHand', 'RightHand')}
            C._track = saved
            for nm, sd in (('LeftHand', 0), ('RightHand', 1)):
                cleared = T[c]['M'][:, ix[nm], :3, 3]
                nominal = nominal_pos[nm]
                vc = np.linalg.norm(np.diff(cleared, axis=0), axis=1) * FPS
                vn = np.linalg.norm(np.diff(nominal, axis=0), axis=1) * FPS
                spike = max(spike, float(np.max(vc - vn)))
            r['G8'] = line(jump <= 0.04 and sjump <= 12.0 and spike <= 0.5, max_correction_step_m=jump, max_swing_step_deg=sjump, max_speed_added_m_s=spike, corrected_frames=int(np.sum(np.any(np.abs(applied) > 1e-9, axis=(1, 2)))))

    # ============================================================================ SPIKE
    c = 'Emote_Spike'
    nF = T[c]['n']
    t = np.arange(nF) / FPS
    wl, shl = h.P(c, 'LeftHand'), h.P(c, 'LeftUpperArm')
    win = (t >= 0.45) & (t <= 2.80)
    below = (shl[:, 2] - wl[:, 2]) >= 0.25
    rkw = h.rk_world(c, h.rk_pts[::4])
    dist_rk = np.array([np.linalg.norm(rkw[f] - wl[f], axis=1).min() for f in range(nF)])
    vrel = np.linalg.norm(np.diff(wl - shl, axis=0), axis=1) * FPS
    R[c]['S1'] = line(bool(below[win].all()) and bool((dist_rk[win] >= 0.15).all()) and float(vrel[win[:-1]].max()) <= 2.5, min_below_shoulder_m=float((shl[:, 2] - wl[:, 2])[win].min()), min_dist_to_racket_m=float(dist_rk[win].min()), max_rel_speed_m_s=float(vrel[win[:-1]].max()))
    low = h.rk_lowest(c)
    contact = low <= 0.010
    groups = []
    for f in range(nF):
        if contact[f] and (not groups or f - groups[-1][-1] > 1):
            groups.append([f])
        elif contact[f]:
            groups[-1].append(f)
    cf = [g[int(np.argmin(low[g]))] for g in groups]
    far = len(cf) >= 2 and (cf[-1] - cf[0]) / FPS >= 0.5          # some pair of contacts at least 0.5 s apart
    R[c]['S3'] = line(len(cf) >= 2 and far and low.min() >= -0.010, contacts=len(cf), contact_times=[round(f / FPS, 3) for f in cf], lowest_m=float(low.min()))
    tip = h.rk_tipw(c)
    speed = np.linalg.norm(np.diff(tip, axis=0), axis=1) * FPS
    if cf:
        f1 = cf[0]
        ks = [k for k in range(f1 - 1) if speed[k] <= 3.0]
        t_start = (ks[-1] + 1) / FPS if ks else 0.0
        dur = f1 / FPS - t_start
        pk = float(speed[max(0, f1 - 3):f1].max())
        R[c]['S2'] = line(0.15 <= dur <= 0.35 and pk >= 6.0, downswing_s=dur, peak_tip_speed_m_s=pk)
    else:
        R[c]['S2'] = line(False, note='no contact')
    hp, nk = h.P(c, 'Hips'), h.P(c, 'Neck') if 'Neck' in ix else h.P(c, 'Head')
    fl = []
    for f in cf[:2]:
        v = nk[f] - hp[f]
        fl.append(ang(v, np.array([0.0, 0.0, 1.0])))
    R[c]['S4'] = line(len(fl) == 2 and all(55.0 <= a <= 90.0 for a in fl), trunk_flexion_at_contacts_deg=fl)
    h_hi = lambda lo, hi: float(np.max([(h.rk_world(c, h.rk_pts[::6])[f][:, 2]).max() for f in range(int(lo * FPS), int(hi * FPS) + 1)]))
    top1, top2 = h_hi(0.5, 1.1), h_hi(1.5, 1.9)
    R[c]['S5'] = line(top2 <= 0.75 * top1 and top1 > 0.0, first_lift_top_m=top1, second_lift_top_m=top2, ratio=top2 / top1)
    head_top = h.tip(c, 'Head')
    tipz = h.rk_tipw(c)[:, 2]
    above = (tipz >= head_top[:, 2] + 0.20)
    run = 0
    best = 0
    for f in range(int(0.3 * FPS), int(1.3 * FPS)):
        run = run + 1 if above[f] else 0
        best = max(best, run)
    R[c]['S6'] = line(best / FPS >= 0.15, racket_tip_0p20_above_head_top_s=best / FPS, max_tip_above_head_top_m=float((tipz - head_top[:, 2])[int(0.3 * FPS):int(1.3 * FPS)].max()))

    # ============================================================================ SCUBA
    c = 'Emote_Scuba'
    nF = T[c]['n']
    t = np.arange(nF) / FPS
    loop = (t >= 16 / FPS - 1e-9) & (t <= (16 + 4 * 22) / FPS + 1e-9)
    d_pad = np.linalg.norm(h.pad(c, 'L') - h.nose(c), axis=1)
    R[c]['C1'] = line(float(d_pad[loop].max()) <= 0.01, max_pad_to_nose_m=float(d_pad[loop].max()), mean_m=float(d_pad[loop].mean()))
    wr, nk = h.A(c, 'RightHand'), h.A(c, 'Neck') if 'Neck' in ix else h.A(c, 'Head')
    sh = h.A(c, 'RightUpperArm')
    ahead = wr[:, 1] - nk[:, 1]
    below_sh = sh[:, 2] - wr[:, 2]
    R[c]['C2'] = line(float(ahead[loop].min()) >= 0.30 and float(below_sh[loop].min()) >= 0.05 and float(below_sh[loop].max()) <= 0.40, min_ahead_of_neck_m=float(ahead[loop].min()), below_shoulder_range_m=[float(below_sh[loop].min()), float(below_sh[loop].max())])
    lat = wr[loop][:, 0] - sh[loop][:, 0]
    p2p = float(lat.max() - lat.min())
    s = np.sign(lat - lat.mean())
    zc = np.where(np.diff(s) != 0)[0]
    period = 2.0 * float(np.mean(np.diff(zc))) / FPS if len(zc) > 3 else 0.0
    cycles = len(zc) / 2.0
    R[c]['C3'] = line(p2p >= 0.20 and abs(period - 0.733) <= 0.04 and cycles >= 3.5, wrist_lateral_p2p_m=p2p, period_s=period, cycles=cycles)
    kl, kr = h.P(c, 'LeftLowerLeg'), h.P(c, 'RightLowerLeg')
    dk = np.abs(kl[:, 0] - kr[:, 0])[loop]
    s2 = np.sign(dk - dk.mean())
    zc2 = np.where(np.diff(s2) != 0)[0]
    period_k = 2.0 * float(np.mean(np.diff(zc2))) / FPS if len(zc2) > 3 else 0.0
    R[c]['C4'] = line(float(dk.max() - dk.min()) >= 0.10 and abs(period_k - 0.733) <= 0.06, knee_lateral_p2p_m=float(dk.max() - dk.min()), period_s=period_k, feet_slide_m=R[c]['G4']['slide_max_m'])
    HRp, RCp = T[c]['HR'][:, :3, 3], T[c]['RC'][:, :3, 3]
    dhr = np.linalg.norm(RCp - HRp, axis=1)
    leave = next((k for k in range(nF) if dhr[k] > 1e-3), None)
    low = h.rk_lowest(c)
    rest = (t >= 0.8) & (t <= 3.8)
    z_rest_ok = bool(((low[rest] >= -0.005) & (low[rest] <= 0.010)).all())
    moved = float(np.linalg.norm(RCp[rest] - RCp[rest].mean(axis=0), axis=1).max())
    out_of_hand = bool((dhr[(t >= 0.3) & (t <= 3.8)] > 0.05).all())
    R[c]['C5'] = line(leave is not None and leave / FPS <= 0.25 and z_rest_ok and moved <= 0.005 and out_of_hand, leaves_s=(leave / FPS) if leave is not None else None, lowest_m_range=[float(low[rest].min()), float(low[rest].max())], moved_m=moved, min_dist_to_hand_m=float(dhr[(t >= 0.3) & (t <= 3.8)].min()))
    att = next((k for k in range(100, nF) if all(dhr[k:] <= 1e-4)), None)
    da_after = max(rot_deg(T[c]['RC'][f, :3, :3], T[c]['HR'][f, :3, :3]) for f in range(att, nF)) if att is not None else 99.0
    pre = np.linalg.norm(np.diff(RCp[max(0, (att or 0) - 5):(att or 0) + 1], axis=0), axis=1) if att else np.array([9.0])
    reach = float(dhr[int((att or 0) - 6):int(att or 0)].min()) if att else 9.0
    floor6 = max(rot_deg(ready['RC'][f, :3, :3], ready['HR'][f, :3, :3]) for f in range(ready['n']))
    R[c]['C6'] = line(att == 123 and da_after <= 0.25 and float(pre.max()) <= 0.08 and reach <= 0.02, attach_frame=att, hand_to_racket_before_attach_m=reach, max_racket_jump_before_attach_m=float(pre.max()), after_attach_deg=da_after, readyidle_floor_deg=floor6)

    # ============================================================================ THRUST
    c = 'Emote_Thrust'
    nF = T[c]['n']
    t = np.arange(nF) / FPS
    hips = h.A(c, 'Hips')
    hips_ready = h.A('ReadyIdle', 'Hips')[0]
    hit_t = [18 / 30.0, 35 / 30.0, 51 / 30.0]
    hold = [0.06, 0.06, 0.50]
    wl, wr = h.A(c, 'LeftHand'), h.A(c, 'RightHand')
    mid = 0.5 * (wl + wr)
    pel_to_mid = np.linalg.norm(mid - hips, axis=1)
    trav, back_off, syncs, crossed, nearp, back_far = [], [], [], [], [], []
    for i, th in enumerate(hit_t):
        lo = 0.0 if i == 0 else hit_t[i - 1] + hold[i - 1] + 0.1
        bw = [k for k in range(nF) if lo <= t[k] <= th - 0.1]
        hw = [k for k in range(nF) if th - 0.15 <= t[k] <= th + hold[i] + 0.10]
        fb = min(hips[k, 1] for k in bw)
        kb = bw[int(np.argmin([hips[k, 1] for k in bw]))]
        fmax = max(hips[k, 1] for k in hw)
        trav.append(fmax - fb)
        back_off.append(hips_ready[1] - fb)
        kf = next(k for k in hw if hips[k, 1] >= fmax - 0.005)
        dmin = min(pel_to_mid[k] for k in hw)
        kw = next(k for k in hw if pel_to_mid[k] <= dmin + 0.005)
        syncs.append(abs(kf - kw))
        kh = int(round(th * FPS))
        crossed.append(float(wl[kh, 0] - wr[kh, 0]))
        nearp.append((float(np.linalg.norm(wl[kh] - hips[kh])), float(np.linalg.norm(wr[kh] - hips[kh])), float(max(wl[kh, 2], wr[kh, 2]) - hips[kh, 2])))
        back_far.append((float(np.linalg.norm(wl[kb] - hips[kb])), float(np.linalg.norm(wr[kb] - hips[kb])), float(min(wl[kb, 2], wr[kb, 2]) - hips[kb, 2])))
    R[c]['T1'] = line(all(x >= 0.33 for x in trav) and all(x >= 0.10 for x in back_off), pelvis_travel_m=trav, back_behind_ready_m=back_off)
    R[c]['T2'] = line(all(s_ <= 1 for s_ in syncs), frames_apart=syncs)
    ok3 = all(x >= 0.04 for x in crossed) and all(a <= 0.50 and b <= 0.50 and u <= 0.35 for a, b, u in nearp) and all(a >= 0.45 and b >= 0.45 and u >= 0.30 for a, b, u in back_far)
    R[c]['T3'] = line(ok3, crossed_lateral_m=crossed, wrist_pelvis_dist_and_height_at_hits=nearp, back_position_dist_and_min_height=back_far)
    Qc = h.Q(c, 'UpperChest') @ h.rig.Rrest[ix['UpperChest']].T
    Qr = h.Q('ReadyIdle', 'UpperChest')[0] @ h.rig.Rrest[ix['UpperChest']].T
    yaw = lambda Q_: np.degrees(np.arctan2((Q_ @ FWD)[..., 0], -(Q_ @ FWD)[..., 1]))
    cyaw = yaw(Qc) - float(yaw(Qr))
    Qh = h.Q(c, 'Head') @ h.rig.Rrest[ix['Head']].T
    Qhr = h.Q('ReadyIdle', 'Head')[0] @ h.rig.Rrest[ix['Head']].T
    hyaw = yaw(Qh) - float(yaw(Qhr))
    R[c]['T4'] = line(float(np.abs(cyaw).max()) <= 15.0 and float(np.abs(hyaw).max()) <= 25.0, max_chest_yaw_deg=float(np.abs(cyaw).max()), max_head_yaw_deg=float(np.abs(hyaw).max()))
    mid_w = (t >= 0.5) & (t <= 3.0)
    fkl, fkr = flexion(h, c, 'L'), flexion(h, c, 'R')
    toe_yaw = []
    for S_ in ('Left', 'Right'):
        v = h.P(c, S_ + 'Toes') - h.P(c, S_ + 'Foot')
        toe_yaw.append(np.abs(np.degrees(np.arctan2(v[:, 0], -v[:, 1]))))
    R[c]['T5'] = line(float(min(fkl[mid_w].min(), fkr[mid_w].min())) >= 15.0 and float(min(toe_yaw[0][mid_w].min(), toe_yaw[1][mid_w].min())) >= 20.0, min_knee_flexion_deg=float(min(fkl[mid_w].min(), fkr[mid_w].min())), min_toe_yaw_deg=float(min(toe_yaw[0][mid_w].min(), toe_yaw[1][mid_w].min())))
    v = Qh @ FWD
    hpitch = np.degrees(np.arcsin(np.clip(v[:, 2], -1, 1)))
    cw = (t >= 1.95) & (t <= 2.5)
    R[c]['T6'] = line(float(hpitch[cw].max() - hpitch[cw].min()) >= 6.0, head_pitch_p2p_deg=float(hpitch[cw].max() - hpitch[cw].min()))
    return R


def main():
    a_ = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    which = a_[0] if a_ else 'both'
    tags = ['male', 'female'] if which == 'both' else [which]
    out = {}
    allok = True
    for tag in tags:
        h = Hero(tag)
        solver = {c: EC.build(c, h.H) for c in CLIPS}
        R = check_hero(h, solver)
        out[tag] = R
        for c in CLIPS:
            for gid in sorted(R[c], key=lambda g: (g[0], int(g[1:]))):
                r = R[c][gid]
                allok &= r['ok']
                detail = {k: v for k, v in r.items() if k != 'ok'}
                print('GATE %-3s %-6s %-12s %s  %s' % (gid, tag, c, 'PASS' if r['ok'] else 'FAIL', json.dumps(detail)[:260]))
    json.dump(out, open(f'{DATA}/checks2.json', 'w'), indent=1)
    print('GATES_DONE', 'ALL PASS' if allok else 'SOME FAIL')


main()
