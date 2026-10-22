"""Landmarks -> rig spec for one hero (pure numpy; run with Blender's bundled python, or inside Blender).

Everything is measured from the hero's own body mesh: exact plane sections (geom.section_loops), limb centre lines (geom.track_limb), the
digit model of the dressed-look job for the hands (finger / thumb components, centre lines, joints; reused unchanged).  No joint position is
copied from another rig.  Output: a dict (bones with head / tail / roll reference) that scripts/rigbuild.py turns into an armature.

Conventions: Blender world, the hero faces -Y, so the hero's RIGHT is -X.  `L` = +x side (the hero's left)."""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'dressed-look', 'scripts'))
from geom import *                                      # noqa: E402,F401
from handlib import adjacency, hand_region, pca_frame     # noqa: E402  (reused unchanged from the dressed-look job)
from handmodel import build_model, landmark_frame         # noqa: E402

FWD = np.array([0.0, -1.0, 0.0])
UP = np.array([0.0, 0.0, 1.0])
SIDES = (('L', 1), ('R', -1))


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def line_fit(P):
    c = P.mean(0)
    _, _, vt = np.linalg.svd(P - c, full_matrices=False)
    return c, vt[0]


def at_z(track, z):
    """centroid of a (k,3) centre-line track at height z (linear interpolation, z ascending or descending)."""
    t = np.asarray(track)
    o = np.argsort(t[:, 2])
    t = t[o]
    return np.array([np.interp(z, t[:, 2], t[:, k]) for k in range(3)])


def lerp(a, b, f):
    return np.asarray(a) + f * (np.asarray(b) - np.asarray(a))


# ----------------------------------------------------------------------------------------------------------- legs / feet
def leg_info(m, s, tag, log):
    tmask = (s * m.tcent[:, 0] > 0.0)
    x0 = 0.175 if tag == 'male' else 0.11
    tr = track_limb(m, np.array([s * x0, 0.0, 0.20]), UP, step=0.01, nsteps=70, tri_mask=tmask, area_cap=1.0, jump_ratio=1.7)
    cl = np.array([r['centroid'] for r in tr if not r['merged']])
    ar = np.array([r['area'] for r in tr if not r['merged']])
    # ankle: smallest section area between z .07 and .16 (walk down from the leg)
    best = None
    for z in np.arange(0.07, 0.17, 0.005):
        loops = [L for L in section_loops(m, np.array([s * x0, 0.0, z]), UP, tri_mask=tmask) if L['area'] > 2e-4]
        if not loops:
            continue
        L = min(loops, key=lambda L: np.linalg.norm(L['centroid'][:2] - np.array([s * x0, 0.0])))
        if best is None or L['area'] < best[1]:
            best = (z, L['area'], L['centroid'])
    # popliteal (back of the knee) = local minimum of the back-most y of the leg between z .40 and .62
    xs = s * m.co[:, 0]
    legv = (xs > 0.03) & (xs < 0.30) & (m.co[:, 2] > 0.30) & (m.co[:, 2] < 0.66)
    zs = np.arange(0.40, 0.62, 0.01)
    backy = []
    for z in zs:
        sel = legv & (np.abs(m.co[:, 2] - z) < 0.012)
        backy.append(m.co[sel, 1].max() if sel.any() else np.nan)
    backy = np.array(backy)
    z_pop = float(zs[np.nanargmin(backy)])
    # foot
    foot = (xs > 0.04) & (m.co[:, 2] < 0.075) & (xs < 0.34)
    F = m.co[foot]
    heel_y, toe_y = float(F[:, 1].max()), float(F[:, 1].min())
    return dict(track=cl, area=ar, ankle_z=best[0], ankle_c=best[2], z_pop=z_pop, heel_y=heel_y, toe_y=toe_y, foot_verts=F)


# ----------------------------------------------------------------------------------------------------------- arms / hands
def arm_info(m, s, tag, hand_model, log):
    xc = 0.27 if tag == 'male' else 0.17
    cand = (s * m.co[:, 0] > xc) & (m.co[:, 2] > 0.55)
    comps = components_vertex(m, cand)
    arm = comps[0]
    sh_guess = np.array([s * (0.22 if tag == 'male' else 0.16), -0.03, 1.30])
    P = m.co[arm]
    dd = np.linalg.norm(P - sh_guess, axis=1)
    sel = P[(dd > 0.1) & (dd < (0.5 if tag == 'male' else 0.40))]
    c, ax = line_fit(sel)
    if ax[0] * s < 0:
        ax = -ax                         # axis points outwards / towards the hand
    if ax[2] > 0:
        ax = -ax
    ax = unit(ax)
    start = c + 0.05 * ax
    tmask = (s * m.tcent[:, 0] > 0.10)
    toward_hand = track_limb(m, start, ax, step=0.01, nsteps=60, tri_mask=tmask, area_cap=1.0, jump_ratio=2.5)
    toward_sh = track_limb(m, start, -ax, step=0.01, nsteps=90, tri_mask=tmask, area_cap=1.0, jump_ratio=1.32)
    return dict(axis=ax, start=start, hand_track=toward_hand, sh_track=toward_sh)


def hand_pipeline(m, adj, tag, log):
    """digit model for both hands; the left hand is analysed on the x-mirrored mesh and mirrored back."""
    out = {}
    for side, s in SIDES:
        c = m.co.copy()
        if s > 0:
            c[:, 0] = -c[:, 0]            # work in the right-hand frame of the dressed-look code (right hand on -x)
        hand = hand_region(c, adj, tag)
        fr0 = pca_frame(c[hand])
        uc, dig = build_model(c, adj, tag, hand, fr0)
        wr, mm, u, v, p = landmark_frame(c, hand, dig, fr0)

        def fl(x):
            x = np.array(x, float).copy()
            if s > 0:
                x[..., 0] = -x[..., 0]
            return x
        digits = {}
        for nm, d in dig.items():
            digits[nm] = dict(J=[fl(j) for j in d['J']], R=float(d['R']), comp=d['comp'], L=float(d['L']), dbase=fl(d['dbase']))
        out[side] = dict(hand=hand, wrist_cut=fl(wr), mid_mcp=fl(mm), u=fl(u), v=fl(v), p=fl(p), digits=digits, ucut=uc,
                         mirrored=(s > 0), frame0=fr0, raw=dig, p_raw=np.array(p, float), c_mirror=c)
    return out


def build_spec(tag, m, log=print):
    H = float(m.co[:, 2].max())
    adj_lists = adjacency(m.n, m.ed)
    hands = hand_pipeline(m, adj_lists, tag, log)
    dbg = {}
    J = {}          # joint name -> position
    # ================================================================ legs
    legs = {sd: leg_info(m, s, tag, log) for sd, s in SIDES}
    # crotch height
    z_cr = None
    for z in np.arange(0.60, 0.95, 0.005):
        loops = section_loops(m, np.array([0.0, 0.0, z]), UP)
        big = [L for L in loops if L['area'] > 0.012 and abs(L['centroid'][0]) < 0.03]
        if big and big[0]['ext'][0] > 0.2:
            z_cr = float(z)
            break
    log('crotch z', z_cr)
    dbg['crotch_z'] = z_cr
    z_hip = float(np.clip(0.52 * H, z_cr + 0.07, z_cr + 0.14))
    dbg['z_hip'] = z_hip
    for sd, s in SIDES:
        L = legs[sd]
        trk = L['track']
        # ankle: joint height 0.05 H; (x, y) from the shank centre line (z .20 .. .32) extrapolated downwards
        z_a = 0.05 * H
        sel_s = (trk[:, 2] > 0.19) & (trk[:, 2] < 0.34)
        cs, ds = line_fit(trk[sel_s])
        if ds[2] < 0:
            ds = -ds
        ank = cs + ds * ((z_a - cs[2]) / ds[2])
        ank[2] = z_a
        # knee: popliteal minus 3.5 cm
        z_k = L['z_pop'] - 0.035
        knee = at_z(trk, z_k)
        knee[2] = z_k
        # hip: thigh axis through the section centroids z in [crotch-.16, crotch-.03], extrapolated to z_hip
        sel = (trk[:, 2] > z_cr - 0.17) & (trk[:, 2] < z_cr - 0.03)
        c0, d0 = line_fit(trk[sel])
        if d0[2] < 0:
            d0 = -d0
        hip = c0 + d0 * ((z_hip - c0[2]) / d0[2])
        # the femoral head sits medial of the thigh axis; keep it inside the pelvis ring: x between .075 and .105 of the half pelvis
        hip[0] = s * float(np.clip(abs(hip[0]), 0.075, 0.105))
        hip[2] = z_hip
        # foot
        flen = L['heel_y'] - L['toe_y']
        ball_y = L['heel_y'] - 0.72 * flen
        F = L['foot_verts']
        near = F[np.abs(F[:, 1] - ball_y) < 0.02]
        ball_x = float(near[:, 0].mean()) if len(near) else float(ank[0])
        ball = np.array([ball_x, ball_y, 0.024])
        toe = np.array([ball_x, L['toe_y'] + 0.006, 0.014])
        J[f'ankle_{sd}'], J[f'knee_{sd}'], J[f'hip_{sd}'], J[f'ball_{sd}'], J[f'toe_{sd}'] = ank, knee, hip, ball, toe
        dbg[f'leg_{sd}'] = dict(ankle_z=L['ankle_z'], z_pop=L['z_pop'], heel_y=L['heel_y'], toe_y=L['toe_y'], foot_len=flen)
    # ================================================================ torso strip
    def strip(z, half=0.05, dz=0.012):
        sel = (np.abs(m.co[:, 0]) < half) & (np.abs(m.co[:, 2] - z) < dz)
        return m.co[sel]
    pel_c = 0.5 * (J['hip_L'] + J['hip_R'])
    # neck: smallest area near the axis between 1.36 and 1.52
    best = None
    for z in np.arange(1.36, 1.53, 0.005):
        loops = [Lp for Lp in section_loops(m, np.array([0, -0.03, z]), UP) if Lp['area'] > 5e-4 and abs(Lp['centroid'][0]) < 0.04 and Lp['ext'][0] < 0.20]
        if not loops:
            continue
        Lp = min(loops, key=lambda Lp: abs(Lp['centroid'][0]) + abs(Lp['centroid'][1] + 0.03))
        if best is None or Lp['area'] < best[1]:
            best = (z, Lp['area'], Lp['centroid'], Lp['ext'])
    z_nm, a_nm, c_nm, ext_nm = best
    log('neck min z %.3f area %.1f cm2 centre %s ext %s' % (z_nm, a_nm * 1e4, np.round(c_nm, 3), np.round(ext_nm, 3)))
    z_c7 = z_nm - 0.045
    z_sb = z_nm + 0.065
    dbg['neck'] = dict(z_nm=float(z_nm), area=float(a_nm), centre=c_nm.tolist())
    # torso axis (vertebral column) y(z): back surface minus 36% of the depth, measured on the central strip
    def y_axis(z):
        S = strip(z)
        if len(S) < 4:
            return None
        return float(S[:, 1].max() - 0.36 * (S[:, 1].max() - S[:, 1].min()))
    zs_t = np.arange(float(pel_c[2]) + 0.02, z_c7 + 0.01, 0.03)
    ys_t = [y_axis(z) for z in zs_t]
    ok = [i for i, y in enumerate(ys_t) if y is not None]
    zs_t = zs_t[ok]
    ys_t = np.array([ys_t[i] for i in ok])
    ys_s = np.convolve(np.pad(ys_t, 2, mode='edge'), np.ones(5) / 5, mode='valid')

    def spine_y(z):
        return float(np.interp(z, zs_t, ys_s))
    # chain heights
    z_h = float(pel_c[2])
    R0 = z_h + 0.095
    Rtot = z_c7 - R0
    z_sp, z_ch, z_uc = R0, R0 + 0.30 * Rtot, R0 + 0.62 * Rtot
    J['hips'] = np.array([0.0, float(pel_c[1]), z_h])
    J['spine'] = np.array([0.0, spine_y(z_sp), z_sp])
    J['chest'] = np.array([0.0, spine_y(z_ch), z_ch])
    J['upperchest'] = np.array([0.0, spine_y(z_uc), z_uc])
    J['neck'] = np.array([0.0, spine_y(z_c7) if z_c7 <= zs_t[-1] else float(c_nm[1]) + 0.02, z_c7])
    J['head'] = np.array([0.0, float(c_nm[1]) - 0.005, z_sb])
    J['head_top'] = np.array([0.0, float(c_nm[1]) - 0.01, H])
    # ================================================================ shoulders / arms
    arms = {sd: arm_info(m, s, tag, hands[sd], log) for sd, s in SIDES}
    for sd, s in SIDES:
        A = arms[sd]
        ht = A['hand_track']
        st = A['sh_track']
        hcl = np.array([r['centroid'] for r in ht])
        scl = np.array([r['centroid'] for r in st if not r['merged']])
        sar = np.array([r['area'] for r in st if not r['merged']])
        # --- wrist from the hand model
        Hm = hands[sd]
        mcp = Hm['mid_mcp']
        tip = Hm['digits']['middle']['J'][3]
        finger_len = float(np.linalg.norm(tip - mcp))
        palm_len = 1.10 * finger_len
        uvec = unit(mcp - Hm['wrist_cut'])
        wr = mcp - palm_len * uvec
        dsn = np.linalg.norm(hcl - wr, axis=1)
        wr_snap = hcl[int(np.argmin(dsn))]
        if np.linalg.norm(wr - wr_snap) < 0.04:
            wr = 0.5 * wr + 0.5 * wr_snap
        # --- full arm track, shoulder side -> hand side, with section areas
        sh_rings = [r for r in st if not r['merged']][::-1]
        full = np.vstack([np.array([r['centroid'] for r in sh_rings]), hcl])
        fa = np.array([r['area'] for r in sh_rings] + [r['area'] for r in ht])
        arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(full, axis=0), axis=1))])
        # --- elbow: girth valley (must be significant) between 34 % and 70 % of the way, else the 0.545 ratio along the segment
        S_tmp = full[0]
        frac = np.linalg.norm(full - S_tmp, axis=1) / (np.linalg.norm(full - S_tmp, axis=1) + np.linalg.norm(full - wr, axis=1))
        win = np.where((frac > 0.34) & (frac < 0.70))[0]
        E, tag_e = None, 'ratio'
        if len(win) > 3:
            k = win[np.argmin(fa[win])]
            before = fa[(arc > arc[k] - 0.09) & (arc < arc[k] - 0.02)]
            after = fa[(arc > arc[k] + 0.02) & (arc < arc[k] + 0.09)]
            if len(before) and len(after) and fa[k] < 0.90 * min(before.max(), after.max()):
                E, tag_e = full[k].copy(), 'valley'
        # --- shoulder joint: axis of the middle of the upper arm (rings between elbow+4 cm and the last clean ring - 2 cm) extended to z_sh
        Etmp = E if E is not None else lerp(full[0], wr, 0.545)
        selr = [r['centroid'] for r in sh_rings if Etmp[2] + 0.04 < r['centroid'][2] < sh_rings[0]['centroid'][2] - 0.01]
        if len(selr) < 4:
            selr = [r['centroid'] for r in sh_rings[:8]]
        c1, d1 = line_fit(np.array(selr))
        if d1[2] < 0:
            d1 = -d1
        xlo, xhi = (0.19, 0.30) if tag == 'male' else (0.13, 0.21)
        top = m.co[(s * m.co[:, 0] > xlo) & (s * m.co[:, 0] < xhi) & (m.co[:, 2] > 1.2) & (m.co[:, 2] < z_c7 + 0.02)]
        z_top = float(top[:, 2].max())
        z_sh = z_top - 0.045
        S = c1 + d1 * ((z_sh - c1[2]) / d1[2])
        if E is None:
            E = lerp(S, wr, 0.545)
            dsn = np.linalg.norm(full - E, axis=1)
            E = 0.5 * E + 0.5 * full[int(np.argmin(dsn))]
        J[f'shoulder_{sd}'], J[f'elbow_{sd}'], J[f'wrist_{sd}'] = S, E, wr
        dbg[f'arm_{sd}'] = dict(z_top=z_top, z_sh=z_sh, sh=S.tolist(), elbow_rule=tag_e, upper=float(np.linalg.norm(E - S)),
                                fore=float(np.linalg.norm(wr - E)), finger_len=finger_len, palm_len=palm_len, ring_window=len(selr))
        # clavicle (sternoclavicular joint)
        z_sc = z_c7 - 0.035
        Sx = strip(z_sc, half=0.05)
        y_sc = float(Sx[:, 1].min() + 0.30 * (Sx[:, 1].max() - Sx[:, 1].min())) if len(Sx) > 3 else float(J['neck'][1])
        J[f'sc_{sd}'] = np.array([s * 0.022, y_sc, z_sc])
    # symmetrize paired joints (the heroes are symmetric characters; the animations then mirror exactly).  Report the asymmetry that was removed.
    asym = {}
    for nm in ('ankle', 'knee', 'hip', 'ball', 'toe', 'shoulder', 'elbow', 'wrist', 'sc'):
        a, b = J[f'{nm}_L'], J[f'{nm}_R']
        bm = np.array([-b[0], b[1], b[2]])
        mean = 0.5 * (a + bm)
        asym[nm] = float(np.linalg.norm(a - bm))
        J[f'{nm}_L'] = mean.copy()
        J[f'{nm}_R'] = np.array([-mean[0], mean[1], mean[2]])
    dbg['asymmetry_removed_m'] = asym
    spec = dict(tag=tag, height=H, crotch_z=z_cr, joints={k: np.asarray(v).tolist() for k, v in J.items()}, debug=dbg)
    return spec, hands, J


def bone_list(tag, J, hands):
    """bones: (name, parent, head, tail, zref, connect).  zref = world direction the bone's local Z should point at."""
    B = []

    def add(name, parent, head, tail, zref, connect=False):
        B.append(dict(name=name, parent=parent, head=np.asarray(head, float).tolist(), tail=np.asarray(tail, float).tolist(),
                      zref=np.asarray(zref, float).tolist(), connect=connect))
    root_y = 0.5 * (J['ankle_L'][1] + J['ankle_R'][1])
    add('Root', None, [0, root_y, 0.0], [0, root_y, 0.10], FWD)
    add('Hips', 'Root', J['hips'], J['spine'], FWD)
    add('Spine', 'Hips', J['spine'], J['chest'], FWD, True)
    add('Chest', 'Spine', J['chest'], J['upperchest'], FWD, True)
    add('UpperChest', 'Chest', J['upperchest'], J['neck'], FWD, True)
    add('Neck', 'UpperChest', J['neck'], J['head'], FWD, True)
    add('Head', 'Neck', J['head'], J['head_top'], FWD, True)
    for sd, s in SIDES:
        Sd = 'Left' if sd == 'L' else 'Right'
        add(f'{Sd}Shoulder', 'UpperChest', J[f'sc_{sd}'], J[f'shoulder_{sd}'], UP)
        add(f'{Sd}UpperArm', f'{Sd}Shoulder', J[f'shoulder_{sd}'], J[f'elbow_{sd}'], FWD, True)
        add(f'{Sd}LowerArm', f'{Sd}UpperArm', J[f'elbow_{sd}'], J[f'wrist_{sd}'], FWD, True)
        Hm = hands[sd]
        add(f'{Sd}Hand', f'{Sd}LowerArm', J[f'wrist_{sd}'], Hm['mid_mcp'], Hm['p'], True)
        for nm, fn in (('thumb', 'Thumb'), ('index', 'Index'), ('middle', 'Middle'), ('ring', 'Ring'), ('pinky', 'Little')):
            Jd = Hm['digits'][nm]['J']
            a, b, c, d = Jd
            if nm == 'thumb':
                names = (f'{Sd}{fn}Proximal', f'{Sd}{fn}Intermediate', f'{Sd}{fn}Distal')
                add(names[0], f'{Sd}Hand', a, b, Hm['p'])
                add(names[1], names[0], b, c, Hm['p'], True)
                add(names[2], names[1], c, d, Hm['p'], True)
            else:
                names = (f'{Sd}{fn}Proximal', f'{Sd}{fn}Intermediate', f'{Sd}{fn}Distal')
                add(names[0], f'{Sd}Hand', a, b, Hm['p'])
                add(names[1], names[0], b, c, Hm['p'], True)
                add(names[2], names[1], c, d, Hm['p'], True)
        add(f'{Sd}UpperLeg', 'Hips', J[f'hip_{sd}'], J[f'knee_{sd}'], FWD)
        add(f'{Sd}LowerLeg', f'{Sd}UpperLeg', J[f'knee_{sd}'], J[f'ankle_{sd}'], FWD, True)
        add(f'{Sd}Foot', f'{Sd}LowerLeg', J[f'ankle_{sd}'], J[f'ball_{sd}'], UP, True)
        add(f'{Sd}Toes', f'{Sd}Foot', J[f'ball_{sd}'], J[f'toe_{sd}'], UP, True)
    return B


if __name__ == '__main__':
    tag = sys.argv[1]
    npz = sys.argv[2]
    out = sys.argv[3]
    d = np.load(npz)
    m = Mesh(d['co'], d['tri'], d['ed'])
    spec, hands, J = build_spec(tag, m)
    spec['bones'] = bone_list(tag, J, hands)
    for k, v in spec['debug'].items():
        print(k, v)
    json.dump(spec, open(out, 'w'), indent=1)
    print('bones', len(spec['bones']), '->', out)
