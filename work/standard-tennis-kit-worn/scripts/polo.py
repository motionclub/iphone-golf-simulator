"""Polo builder (male + female): SDF shell -> clips -> rims/inner bands -> collar, placket, buttons, cuffs, seams, piping."""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from kitlib import *
from sdf import *
from fitbody import *
from shell import build_shell
from kit_common import *

PARAMS = {
    'male': dict(
        set='male', h=0.0165, lo=(-0.52, -0.30, 0.80), hi=(0.52, 0.22, 1.60),
        ease_chest=0.0145, ease_waist=0.0180, hem_side_rise=0.0, taper=(0.985, 1.10), blur=20.0, min_clear=0.0100, enforce=0.0100,
        hem_front=0.950, hem_back=0.947, vent_h=0.030, pipe_end=0.966, tv=0.0030,      # UNTUCKED: hem 15 mm (front/sides) .. 18 mm (back) below the band top 0.965
        sleeve_end=0.135, r_arm=0.075, axis_c=(0.25, -0.04, 1.30), axis_d=(0.72, -0.03, -0.69), axis_r=0.075, axis_s=(0.04, 0.30),
        neck_a=0.086, neck_b=0.092, neck_cy=-0.020, neck_z=1.425, neck_slope=0.30,
        collar_h=0.022, placket_len=0.098, placket_w=0.030, collar_gap=0.22, collar_shear=0.36,
        raglan=dict(front_end=(0.215, -0.085, 1.225), back_end=(0.215, 0.050, 1.225)),
        side_y=-0.050, side_top=1.150,
    ),
    'female': dict(
        set='female', h=0.0140, lo=(-0.40, -0.25, 0.80), hi=(0.40, 0.22, 1.60),
        ease_chest=0.0115, ease_waist=0.0175, side_extra=0.0, hem_side_rise=0.0, taper=(0.985, 1.03), blur=6.0, min_clear=0.0100, enforce=0.0100,
        crevice=dict(ease_torso=0.0085, ease_arm=0.0035, mc_torso=0.0085, mc_arm=0.0035),
        hem_front=0.980, hem_back=0.977, vent_h=0.026, pipe_end=0.994, tv=0.0030,      # UNTUCKED: hem 15 mm (front/sides) .. 18 mm (back) below the band top 0.995
        sleeve_end=0.135, r_arm=0.047, axis_c=(0.17, 0.0, 1.25), axis_d=(0.06, 0.0, -1.0), axis_r=0.05, axis_s=(0.04, 0.26),
        neck_a=0.068, neck_b=0.073, neck_cy=0.003, neck_z=1.372, neck_slope=0.25,
        collar_h=0.019, placket_len=0.085, placket_w=0.026, collar_gap=0.24, collar_shear=0.36,
        raglan=dict(front_end=(0.150, -0.075, 1.225), back_end=(0.150, 0.075, 1.225)),
        side_y=0.0, side_top=1.050,
    ),
}


def make_cut_fn(P, bodies):
    # shared sleeve plane per side: mean of the variants' arm axes
    mean_ax = {}
    for side in ('axR', 'axL'):
        Cm = np.mean([b[side][0] for b in bodies], 0)
        dm = unit(np.mean([b[side][1] for b in bodies], 0))
        mean_ax[side] = (Cm, dm)

    def cut_fn(Pv):
        x, y, z = Pv[:, 0], Pv[:, 1], Pv[:, 2]
        bey = np.maximum((Pv - mean_ax['axR'][0]) @ mean_ax['axR'][1], (Pv - mean_ax['axL'][0]) @ mean_ax['axL'][1]) - P['sleeve_end']
        c_sleeve = np.full(len(Pv), -1e3)
        if P.get('torso_cut'):
            # hanging arm (female): the sleeve tube and the torso wall are only ~1 voxel apart, so 'nearest surface' classification tears a ragged hole in
            # the side wall.  Cut instead with a clean vertical surface just outside the torso wall (torso half-width + local ease + margin), below the
            # armpit and beyond the cuff plane.
            zt, xt = P['torso_cut']['z'], P['torso_cut']['x']
            ease_z = np.minimum(P['ease_waist'] + (P['ease_chest'] - P['ease_waist']) * smoothstep(P['taper'][0], P['taper'][1], z), P['torso_cut']['ease'])
            xcut = np.interp(z, zt, xt) + ease_z + P['torso_cut']['margin']
            c_sleeve = np.minimum.reduce([bey, np.abs(x) - xcut, z - P['torso_cut']['zmin']])
        else:
            for b in bodies:
                m = arm_vertex_mask(b['V'], [b['axR'], b['axL']], P['r_arm'], P['sleeve_end'] - 0.065)
                ta, tt = split_trees(b['V'], b['F'], m)
                dA, dT = tree_dist(ta, Pv), tree_dist(tt, Pv)
                c_sleeve = np.maximum(c_sleeve, np.minimum(bey, dT - dA))
        # hem: back longer; plus a small vent at each side seam
        t = smoothstep(P['neck_cy'] - 0.06, P['neck_cy'] + 0.12, y)
        z_hem = P['hem_front'] + (P['hem_back'] - P['hem_front']) * t + P['hem_side_rise'] * smoothstep(0.085, 0.145, np.abs(x))
        c_hem = z_hem - z
        c_vent = np.full(len(z), -1e3)          # (side vents dropped: a 4 mm slit is below the shell resolution)
        # neck: elliptical funnel that widens upward so the head / chin shell is removed too
        grow = 0.6 * np.maximum(0.0, z - P['neck_z'])
        a, bb = P['neck_a'] + grow, P['neck_b'] + grow
        ell = np.sqrt((x / a) ** 2 + ((y - P['neck_cy']) / bb) ** 2)
        floor = P['neck_z'] + P['neck_slope'] * (y - P['neck_cy'])
        c_neck = np.minimum((1.0 - ell) * min(P['neck_a'], P['neck_b']), z - floor)
        return np.maximum.reduce([c_hem, c_vent, c_neck, c_sleeve])
    return cut_fn, mean_ax


def setup_axes(bodies, P):
    for b in bodies:
        CR, dR = arm_axis(b['V'], P['axis_c'], P['axis_d'], s_range=P['axis_s'], r=P['axis_r'])
        c0l = np.array(P['axis_c']) * np.array([-1, 1, 1])
        d0l = np.array(P['axis_d']) * np.array([-1, 1, 1])
        CL, dL = arm_axis(b['V'], c0l, d0l, s_range=P['axis_s'], r=P['axis_r'])
        b['axR'] = (CR, dR)
        b['axL'] = (CL, dL)
        print('   axes', b['name'], 'R', CR.round(3), dR.round(3), ' L', CL.round(3), dL.round(3))


def build_collar(acc, neck_pts, surf, P, tip_mat=1, trees=None, bodies_ref=None):
    """spread collar: short stand + fold + leaf that follows the shell, front gap with longer tips. Returns (neck centre, ring)."""
    c = neck_pts.mean(0)
    phi = np.arctan2(neck_pts[:, 0] - c[0], -(neck_pts[:, 1] - c[1]))
    order = np.argsort(phi)
    phis, pts = phi[order], neck_pts[order]
    Ns = 64
    gap = P.get('collar_gap', 0.34)
    samp = np.concatenate([np.linspace(gap, np.pi, Ns // 2, endpoint=True), np.linspace(-np.pi, -gap, Ns // 2, endpoint=True)])
    ring = np.stack([np.interp(samp, phis, pts[:, a], period=2 * np.pi) for a in range(3)], 1)
    rad = ring - c
    rad[:, 2] = 0
    rad /= np.linalg.norm(rad, axis=1, keepdims=True)
    up = np.array([0, 0, 1.0])
    front = 1.0 - smoothstep(0.08 * np.pi, 0.75 * np.pi, np.abs(samp))        # 1 at front, 0 at back
    H = P['collar_h'] * (0.62 + 0.38 * (1 - front))                           # stand height
    L = 0.024 + 0.028 * front                                                  # leaf length (long pointed tips at the front)
    n = len(ring)
    ts = [0.15, 0.38, 0.62, 0.82, 0.92, 1.0]
    thick = [0.0046, 0.0036, 0.0031, 0.0027, 0.0024, 0.0022]
    shear = P.get('collar_shear', 0.20)
    sg = np.sign(samp)

    def rot(q, t):
        """shear the leaf toward the front (pointed tips): rotate about the vertical neck axis by an amount growing with t and the front weight."""
        ang = +sg * shear * front * (t ** 1.5)
        d = q - c
        ca, sa = np.cos(ang), np.sin(ang)
        return np.stack([c[0] + d[:, 0] * ca - d[:, 1] * sa, c[1] + d[:, 0] * sa + d[:, 1] * ca, q[:, 2]], 1)
    # leaf points projected on the shell
    leaf_top, leaf_nrm = [], []
    for t in ts:
        q = rot(ring + rad * (0.0035 + t * L)[:, None], t)
        q = q + up * 0.08
        loc, nrm = surf.cast(q, (0, 0, -1))
        leaf_top.append(loc)
        leaf_nrm.append(nrm)
    under = []
    for t in (0.62, 0.12):
        q = rot(ring + rad * (0.0035 + t * L)[:, None], t) + up * 0.08
        loc, nrm = surf.cast(q, (0, 0, -1))
        under.append(loc + nrm * 0.0005)
    cols = []   # list of (n,3) arrays per profile point
    cols.append(ring + rad * -0.0035 + up * -0.003)                                   # A0
    cols.append(ring + rad * -0.0040 + up * (0.55 * H)[:, None])                       # A1
    cols.append(ring + rad * -0.0030 + up * (0.92 * H)[:, None])                       # A2
    cols.append(ring + rad * 0.0010 + up * (1.05 * H)[:, None])                        # A3 fold
    for i, t in enumerate(ts):
        cols.append(leaf_top[i] + leaf_nrm[i] * thick[i])                              # B_i
    cols.append(leaf_top[-1] + leaf_nrm[-1] * 0.0004)                                  # C edge bottom
    cols.append(under[0])                                                              # U3
    cols.append(under[1])                                                              # U1
    npf = len(cols)
    V = np.stack(cols, 1).reshape(-1, 3)                                               # index k*npf + j
    stripe = {(7, 8)}           # white tipping line on the leaf's free edge (between B(t=.82) and B(t=.92))
    F, M = [], []
    for k in range(n - 1):
        for j in range(npf):
            j2 = (j + 1) % npf
            a, b, c2, d = k * npf + j, (k + 1) * npf + j, (k + 1) * npf + j2, k * npf + j2
            F += [(a, b, c2), (a, c2, d)]
            mm = tip_mat if (j, j2) in stripe else 0
            M += [mm, mm]
    for k, rev in ((0, False), (n - 1, True)):
        base = k * npf
        for j in range(1, npf - 1):
            tri = (base, base + j, base + j + 1)
            F.append(tri[::-1] if rev else tri)
            M.append(0)
    F = np.array(F)
    # orient outward w.r.t. the profile section centroid, then smooth normals from geometry
    sec_c = V.reshape(n, npf, 3).mean(1)
    fc = V[F].mean(1)
    kk = F[:, 0] // npf
    fnrm = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    outv = fc - sec_c[kk]
    bad = np.einsum('ij,ij->i', fnrm, outv) < 0
    if bad.sum() > 0.5 * len(F):
        F = F[:, [0, 2, 1]]
    if trees is not None:
        V = enforce_clearance(V, F, trees, 0.0030, iters=6, verbose=False)
        V = resolve_overlaps_body(V, F, [(b['V'], b['F']) for b in bodies_ref], step=0.0015, iters=14, verbose=False)
    NV = vertex_normals(V, F)
    acc.add(V, F, NV, np.array(M), 'collar')
    return c, ring


def sleeve_loops(loops, V):
    out = []
    for li, l in enumerate(loops):
        cen = V[l].mean(0)
        out.append((li, cen))
    return out


def build_polo(gender, colorway='white', verbose=True, preview_body=None):
    P = dict(PARAMS[gender])
    t0 = time.time()
    bodies = load_set(P['set'])
    setup_axes(bodies, P)
    use_fit = (gender == 'female')                          # the hanging arms below the armpit must not bridge to the (now looser) waist/hem shell
    if use_fit:
        add_nohand_trees(bodies, 'female', zmax=1.04)

    if gender == 'female':
        P = dict(P)
        zt = np.arange(0.98, 1.20, 0.01)
        xt = []
        Vb0, Fb0 = bodies[0]['V'], bodies[0]['F']
        for zz in zt:
            loops = [Lp for Lp in slice_plane(Vb0, Fb0, 2, float(zz)) if len(Lp) >= 10]
            torso = max(loops, key=lambda q: abs(poly_area_xy(q)))                      # the torso loop (largest; the hanging arms are separate loops below the armpit)
            xt.append(float(np.abs(torso[:, 0]).max()))
        pass                                                       # (vertical torso-wall cut kept in make_cut_fn but disabled: the wall's true lateral extent is 2-3 mm beyond the body table, so the cut bites into the wall)
    cut_fn, mean_ax = make_cut_fn(P, bodies)

    def ease_fn(X, Y, Z):
        e = P['ease_waist'] + (P['ease_chest'] - P['ease_waist']) * smoothstep(P['taper'][0], P['taper'][1], Z)
        if P.get('crevice') is not None:
            m_t, m_a = crevice_masks(X, Z)
            e = e * (1 - m_t) + P['crevice']['ease_torso'] * m_t
            e = e * (1 - m_a) + P['crevice']['ease_arm'] * m_a
        return np.asarray(e).astype(np.float32)

    def crevice_masks(X, Z):
        """hanging arm (female): in the crevice between the sleeve and the ribs (z 1.04-1.18) the torso side wall and the arm's torso-facing half are
        relaxed to a small ease, so the two shells stay separate.  At the full ease the offsets leave ~11 mm of air, which the field blur / one voxel
        closes into a single membrane and the sleeve cut then tears a ragged hole in the side wall.  Both sides face each other: never visible."""
        ax = np.abs(X)
        zwin = smoothstep(1.040, 1.060, Z) * smoothstep(1.190, 1.150, Z)             # the hanging arm only enters the fit field above z = 1.04
        m_t = smoothstep(0.080, 0.098, ax) * smoothstep(0.131, 0.118, ax) * zwin          # torso side wall (x ~ 0.11)
        m_a = smoothstep(0.126, 0.138, ax) * smoothstep(0.200, 0.180, ax) * zwin          # arm inner half (x ~ 0.14 .. 0.19)
        return m_t, m_a

    def min_clear_fn(X, Y, Z):
        mc = np.float32(P['min_clear']) + 0.0 * Z
        if P.get('crevice') is not None:
            m_t, m_a = crevice_masks(X, Z)
            mc = mc * (1 - m_t) + P['crevice']['mc_torso'] * m_t
            mc = mc * (1 - m_a) + P['crevice']['mc_arm'] * m_a
        return np.asarray(mc).astype(np.float32)

    def enforce_fn(p):
        cm = P['enforce']
        if P.get('crevice') is not None:
            m_t, m_a = crevice_masks(np.array([[[p[0]]]]), np.array([[[p[2]]]]))
            cm = cm * (1 - float(m_t)) + P['crevice']['mc_torso'] * float(m_t)
            cm = cm * (1 - float(m_a)) + P['crevice']['mc_arm'] * float(m_a)
        return cm

    # the polo hem must lap OVER the waistband with its inner wall >= 1.5 mm outside the band: build against the band surface (shorts/skort build first)
    bz = np.load(f"{WORK}/data/band_{gender}.npz")
    tree_band = bvh_from(bz['V'], bz['F'])
    zb_lo, zb_hi = float(bz['V'][:, 2].min()), float(bz['V'][:, 2].max())
    sh = build_shell(bodies, P['set'], 'polo', P['lo'], P['hi'], P['h'], ease_fn, blur_mm=P['blur'], min_clear=min_clear_fn,
                     cut_fn=cut_fn, verbose=verbose, fit=use_fit, enforce=([b['tree'] for b in bodies], enforce_fn, [(b['V'], b['F']) for b in bodies]),
                     obstacles=[(tree_band, P['tv'] + 0.0015, zb_lo - 0.02, zb_hi + 0.06, tuple(bz['V'][:, :2].mean(0)))])
    V, F = sh.V, sh.F
    N = vertex_field_normals(sh.g, sh.Sg, V)
    loops = boundary_loops(F)
    cz = [V[l][:, 2].mean() for l in loops]
    cx = [abs(V[l][:, 0].mean()) for l in loops]
    neck_i = int(np.argmax(cz))
    hem_i = int(np.argmin(cz))
    sl_i = [i for i in range(len(loops)) if i not in (neck_i, hem_i) and len(loops[i]) >= 12]
    # vents create tiny extra loops only if the slit is closed; the hem loop absorbs them
    acc = Acc()
    V = fix_inner_overlaps(V, F, N, P['tv'], [b['tree'] for b in bodies])             # no inner-wall triangle may cut into the body (arm crevice)
    # closed double-walled shell: outer sheet + inner sheet (tv inward) + bullnose rims on neck, sleeve openings and the (now visible) hem
    add_closed_shell(acc, V, F, N, P['tv'], 0, tag='polo')
    surf = Surface(V, F, sh.g, sh.Sg)
    hem_loop = loops[hem_i]
    info = dict(loops=len(loops), neck=neck_i, hem=hem_i, sleeves=sl_i,
                hem_z_min=float(V[hem_loop][:, 2].min()), hem_z_max=float(V[hem_loop][:, 2].max()), tv=P['tv'])
    # hem stitch line 11 mm above the hem edge (same fabric colour: reads as a hem fold, not a stripe)
    hp = V[hem_loop][::max(1, len(hem_loop) // 44)] + np.array([0, 0, 0.011])
    ribbon(acc, surf, hp, 0.0030, 0.0008, 0, spacing=0.012, closed=True, tag='hemstitch')

    # ---- collar
    neck_pts = V[loops[neck_i]]
    c, ring = build_collar(acc, neck_pts, surf, P, trees=[b['tree'] for b in bodies], bodies_ref=bodies)
    info['neck_center'] = c.tolist()

    # ---- placket + buttons (front centre, from the neck loop down)
    front_top = np.interp(0.0, *(lambda ph, pts: (ph[np.argsort(ph)], pts[np.argsort(ph)][:, 2]))(
        np.arctan2(neck_pts[:, 0] - c[0], -(neck_pts[:, 1] - c[1])), neck_pts))
    z_top = float(front_top)
    zs = np.linspace(z_top - 0.004, z_top - P['placket_len'], 8)
    ctrl = [(0.0, -0.60, z) for z in zs]
    flat = [(-0.5, 0.0, -80), (-0.46, 1.0, -8), (0.46, 1.0, 8), (0.5, 0.0, 80)]
    # (profile with a near-flat top)
    center_line = ribbon(acc, surf, ctrl, P['placket_w'], 0.0011, 0, spacing=0.004, taper_end=0.0, tag='placket', profile=flat, ray=(0, 1, 0))
    info['placket_z'] = [float(center_line[:, 2].min()), float(center_line[:, 2].max())]
    info['placket_y'] = [float(center_line[:, 1].min()), float(center_line[:, 1].max())]
    info['z_top'] = z_top
    # buttons along the centre line
    for fz in (0.17, 0.46, 0.75):
        zt = z_top - fz * P['placket_len']
        i = int(np.argmin(np.abs(center_line[:, 2] - zt)))
        loc, nrm = surf.nearest(center_line[i:i + 1] + np.array([[0, 0, 0.0]]))
        dome(acc, loc[0] + nrm[0] * 0.0011, nrm[0], 0.0052, 0.0022, 0, seg=12, rings=3, tag=f'button{fz}')
    # ---- raglan seams (tone on tone), both sides front + back
    for sgn in (+1, -1):
        for key in ('front_end', 'back_end'):
            e = np.array(P['raglan'][key]) * np.array([sgn, 1, 1])
            front = key == 'front_end'
            ph = 0.62 * np.pi if not front else 0.38 * np.pi
            ang = ph if sgn > 0 else -ph
            start = c + np.array([np.sin(ang) * (P['neck_a'] + 0.020), -np.cos(ang) * (P['neck_b'] + 0.020), 0.012])
            mid = (start + e) / 2 + np.array([sgn * 0.01, (-0.015 if front else 0.015), 0.012])
            ctrl = [np.array([p[0], p[1], 1.75]) for p in (start, mid, e)]
            ribbon(acc, surf, ctrl, 0.0028, 0.0007, 0, spacing=0.004, taper_end=0.012, tag='raglan', ray=(0, 0, -1))
    # ---- side seam piping (underarm -> hem)
    for sgn in (+1, -1):
        ctrl = [(0.0, P['side_y'], z) for z in np.linspace(P['side_top'], P['pipe_end'], 7)]
        ribbon(acc, surf, ctrl, 0.0034, 0.0008, 1, spacing=0.004, taper_end=0.01, tag='sidepipe', ray=(sgn, 0, 0))
    # ---- sleeve cuffs: band + white stripe, 10 mm in from the sleeve opening
    for li in sl_i:
        l = loops[li]
        pts = V[l]
        side = 1.0 if pts[:, 0].mean() > 0 else -1.0
        ax = mean_ax['axR'] if side > 0 else mean_ax['axL']
        d = ax[1]
        for off, w, lift, mat in ((0.0075, 0.0150, 0.0006, 0), (0.0115, 0.0028, 0.0010, 1), (0.0052, 0.0024, 0.0010, 1)):
            ctrl = pts[::max(1, len(pts) // 24)] - d * off
            ribbon(acc, surf, ctrl, w, lift, mat, spacing=0.0075, closed=True, tag=f'cuff{li}')
    res = finalize_acc(acc)
    info['tris'] = int(len(res['F']))
    info['sheet_tris'] = int(len(F))
    info['topo'] = res['topo']
    if verbose:
        print(f'  polo[{gender}] total tris {len(res["F"])} (sheet {len(F)}) in {time.time()-t0:.1f}s  info={info}')
    res.update(info=info, sheet=(V, F), bodies=bodies)
    return res


if __name__ == '__main__':
    import scene_utils as su
    gender = sys.argv[sys.argv.index('--') + 1]
    cw = sys.argv[sys.argv.index('--') + 2] if len(sys.argv) > sys.argv.index('--') + 2 else 'white'
    res = build_polo(gender)
    b0 = res['bodies'][0]
    save_part(f'{WORK}/data/polo_{gender}.npz', res)
    json.dump(res['info'], open(f'{WORK}/data/polo_{gender}_info.json', 'w'), indent=1)
