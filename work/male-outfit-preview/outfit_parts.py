"""Shirt / shorts / socks / shoes / wristbands for the male example outfit (procedural colour zones)."""
import math
import numpy as np
import bpy
from mathutils import Vector
from preview_common import material, hex_rgb
from outfit import (Body, build_shell, loop_tube, boundary_loops, plane_snap, func_snap, sm01)
import shader_zones as sz

# ------------------------------------------------------------------------------------------------ colourways
COLORWAYS = {
    'coral_court': dict(
        Shirt=dict(base='#FF5B4A', trim='#F7F4EC', stripe='#0E2A47'),
        Shorts=dict(base='#0E2A47', trim='#F7F4EC', stripe='#FF5B4A'),
        Socks=dict(base='#F7F4EC', band='#38C6FF'),
        Shoes=dict(base='#FF5B4A', accent='#F7F4EC', sole='#0E2A47'),
        Lace=dict(base='#F7F4EC'),
        Band=dict(base='#FFD21F'),
        Emblem=dict(base='#FFD21F'), Seam=dict(base='#FFFFFF'),
        Hair=dict(base='#241810')),
    'sky_doubles': dict(
        Shirt=dict(base='#38C6FF', trim='#FFFFFF', stripe='#0E2A47'),
        Shorts=dict(base='#F7F4EC', trim='#38C6FF', stripe='#38C6FF'),
        Socks=dict(base='#FFFFFF', band='#D3F34B'),
        Shoes=dict(base='#38C6FF', accent='#FFFFFF', sole='#FFFFFF'),
        Lace=dict(base='#FFFFFF'),
        Band=dict(base='#D3F34B'),
        Emblem=dict(base='#D3F34B'), Seam=dict(base='#FFFFFF'),
        Hair=dict(base='#241810')),
    'violet_smash': dict(
        Shirt=dict(base='#5B2BD9', trim='#F7F4EC', stripe='#FFD21F'),
        Shorts=dict(base='#16123A', trim='#5B2BD9', stripe='#FFD21F'),
        Socks=dict(base='#F7F4EC', band='#FFD21F'),
        Shoes=dict(base='#5B2BD9', accent='#F7F4EC', sole='#FFD21F'),
        Lace=dict(base='#F7F4EC'),
        Band=dict(base='#FFD21F'),
        Emblem=dict(base='#FFD21F'), Seam=dict(base='#16123A'),
        Hair=dict(base='#241810')),
}

S_END = -0.108          # sleeve end along the arm axis (m from ARM_C); upper arm spans about -0.25 .. 0.0
Z_HEM = 0.885
Z_WAIST = 1.000
Z_SHORT_HEM = 0.560
Z_SOCK = 0.262
Z_SHOE_TOP = 0.118
SOLE_T = 0.012
ARM_C = (0.407, -0.052, 1.096)
_A = np.array([0.665, -0.156, -0.730])
ARM_A = tuple(_A / np.linalg.norm(_A))


def get_mats(cw='coral_court'):
    c = COLORWAYS[cw]
    M = {}
    M['Shirt'] = sz.build_material('Outfit_Shirt', c['Shirt']['base'], [
        ('stripe', c['Shirt']['stripe'], lambda Z: Z.mul(Z.band(Z.z, 1.200, 1.232), Z.inv(Z.up(Z.absx(), 0.214, 0.004)))),
        ('trim', c['Shirt']['trim'], lambda Z: Z.mul(Z.up(Z.arm_s(ARM_C, ARM_A), S_END - 0.019, 0.001), Z.inv(Z.up(Z.arm_r(ARM_C, ARM_A), 0.095, 0.010)))),
    ], rough=.72, sheen=0.15)
    M['Shorts'] = sz.build_material('Outfit_Shorts', c['Shorts']['base'], [
        ('trim', c['Shorts']['trim'], lambda Z: Z.add(Z.up(Z.z, Z_WAIST - 0.034, 0.001), Z.inv(Z.up(Z.z, Z_SHORT_HEM + 0.016, 0.001)))),
        ('stripe', c['Shorts']['stripe'], lambda Z: Z.mul(Z.up(Z.absx(), 0.13, 0.010), Z.band(Z.y, -0.0525, -0.0185), Z.band(Z.z, Z_SHORT_HEM + 0.016, Z_WAIST - 0.034))),
    ], rough=.70, sheen=0.12)
    M['Socks'] = sz.build_material('Outfit_Socks', c['Socks']['base'], [
        ('band', c['Socks']['band'], lambda Z: Z.up(Z.z, Z_SOCK - 0.028, 0.001)),
    ], rough=.82)
    M['Shoes'] = sz.build_material('Outfit_Shoes', c['Shoes']['base'], [
        ('accent', c['Shoes']['accent'], lambda Z: Z.add(Z.ellipse(Z.y, -0.212, 0.075, Z.z, 0.012, 0.100, 0.10),
                                                         Z.ellipse(Z.y, 0.070, 0.062, Z.z, 0.075, 0.095, 0.10))),
        ('sole', c['Shoes']['sole'], lambda Z: Z.inv(Z.up(Z.z, 0.004, 0.0008))),
    ], rough=.52, spec=.3)
    M['Lace'] = sz.build_material('Outfit_Lace', c['Lace']['base'], [], rough=.6)
    M['Band'] = sz.build_material('Outfit_Band', c['Band']['base'], [], rough=.72, sheen=0.1)
    M['Emblem'] = sz.build_material('Outfit_Emblem', c['Emblem']['base'], [], rough=.55, spec=.3)
    M['Seam'] = sz.build_material('Outfit_Seam', c['Seam']['base'], [], rough=.6)
    M['Hair'] = sz.build_material('Outfit_Hair', c['Hair']['base'], [], rough=.55, spec=.35)
    return M


def recolor(cw):
    for gname, cols in COLORWAYS[cw].items():
        sz.set_colors('Outfit_' + gname, cols)


# ------------------------------------------------------------------------------------------------ shirt
def zneck(P):
    y = P[:, 1]
    return 1.408 - 0.025 * sm01(-0.005, -0.085, y)


def make_shirt(B, coll, M, thickness=0.0042):
    A = B.ARM_A

    def zones(V):
        sR, rR = B.arm_coords(V, +1)
        sL, rL = B.arm_coords(V, -1)
        right = V[:, 0] > 0
        s = np.where(right, sR, sL)
        r = np.where(right, rR, rL)
        arm = (r < 0.085) & (s > -0.20)
        return s, r, arm

    def pred(V):
        s, r, arm = zones(V)
        torso = (~arm) & (V[:, 2] >= Z_HEM) & (np.abs(V[:, 0]) < 0.36)
        sleeve = arm & (s <= S_END)
        return (V[:, 2] <= zneck(V)) & (torso | sleeve)

    snaps = [
        func_snap(lambda P: (P[:, 2] < Z_HEM + 0.035) & (np.abs(P[:, 0]) < 0.30), lambda P: np.full(len(P), Z_HEM)),
        func_snap(lambda P: (P[:, 2] > 1.30) & (np.abs(P[:, 0]) < 0.17), lambda P: zneck(P)),
    ]
    for sign in (+1, -1):
        Ad = np.array([A[0] * sign, A[1], A[2]])
        Cd = np.array([B.ARM_C[0] * sign, B.ARM_C[1], B.ARM_C[2]])
        pp = Cd + Ad * S_END
        snaps.append(plane_snap(lambda P, sg=sign: ((P[:, 0] * sg) > 0.24) & (zones(P)[0] > S_END - 0.035), pp, Ad, Ad))

    def d_fn(P0, idx):
        z = P0[:, 2]
        s, r, arm = zones(P0)
        d = 0.0072 + 0.0035 * sm01(1.22, 1.02, z) + 0.0075 * sm01(1.0, Z_HEM, z)
        d = d + np.where(arm, 0.0080 * sm01(S_END - 0.14, S_END, s), 0.0)
        d = d + np.where(arm & (s > S_END - 0.020), 0.0015, 0.0)
        return d

    obj, info = build_shell(B, 'Shirt', pred, d_fn, None, [M['Shirt']], coll, snaps=snaps,
                            thickness=thickness, min_gap=thickness + 0.0025, smooth_iters=15)
    Q = info['Q']
    for lp in boundary_loops(info):
        pts = Q[lp]
        zc = pts[:, 2].mean()
        xc = pts[:, 0].mean()
        if len(lp) < 8:
            continue
        ctr = pts.mean(0)
        v = pts - ctr
        v[:, 2] = 0
        nrm = np.linalg.norm(v, axis=1, keepdims=True)
        pts2 = pts - v / np.maximum(nrm, 1e-9) * (thickness * 0.5)
        if abs(xc) < 0.08 and zc > 1.3:
            loop_tube(coll, 'Collar', [tuple(p) for p in pts2], 0.0064, M['Shirt'], n=10)
        elif abs(xc) > 0.2 and zc > 0.9:
            loop_tube(coll, 'Cuff_' + ('R' if xc > 0 else 'L'), [tuple(p) for p in pts2], 0.0046, M['Shirt'], n=10)
    return obj, info


# ------------------------------------------------------------------------------------------------ shorts
def make_shorts(B, coll, M, thickness=0.0042):
    def pred(V):
        return (np.abs(V[:, 0]) <= 0.25) & (V[:, 2] >= Z_SHORT_HEM) & (V[:, 2] <= Z_WAIST)

    snaps = [
        func_snap(lambda P: P[:, 2] < Z_SHORT_HEM + 0.045, lambda P: np.full(len(P), Z_SHORT_HEM)),
        func_snap(lambda P: P[:, 2] > Z_WAIST - 0.045, lambda P: np.full(len(P), Z_WAIST)),
    ]

    def d_fn(P0, idx):
        z = P0[:, 2]
        d = 0.0062 + 0.0030 * sm01(0.97, 0.86, z) + 0.0125 * sm01(0.80, Z_SHORT_HEM, z)
        d = d + np.where(z > Z_WAIST - 0.034, 0.0018, 0.0)
        return d

    return build_shell(B, 'Shorts', pred, d_fn, None, [M['Shorts']], coll, snaps=snaps,
                       thickness=thickness, min_gap=thickness + 0.0025, smooth_iters=15)


# ------------------------------------------------------------------------------------------------ socks / shoes
def make_socks(B, coll, M, thickness=0.0026):
    def pred(V):
        return (np.abs(V[:, 0]) > 0.06) & (V[:, 2] <= Z_SOCK) & (V[:, 2] > 0.0)

    snaps = [func_snap(lambda P: P[:, 2] > Z_SOCK - 0.040, lambda P: np.full(len(P), Z_SOCK))]

    def d_fn(P0, idx):
        d = np.full(len(P0), 0.0036)
        return d + np.where(P0[:, 2] > Z_SOCK - 0.028, 0.0012, 0.0)

    return build_shell(B, 'Socks', pred, d_fn, None, [M['Socks']], coll, snaps=snaps,
                       thickness=thickness, min_gap=thickness + 0.0012, smooth_iters=9)


def shoe_top(P):
    """collar height: high at the heel, dipping toward the instep"""
    return 0.170 - 0.058 * sm01(0.000, -0.105, P[:, 1])


def make_shoes(B, coll, M, thickness=0.0050):
    def pred(V):
        return (np.abs(V[:, 0]) > 0.06) & (V[:, 2] <= shoe_top(V))

    snaps = [func_snap(lambda P: P[:, 2] > shoe_top(P) - 0.040, lambda P: shoe_top(P))]

    def d_fn(P0, idx):
        z = P0[:, 2]
        d = 0.0082 + 0.0030 * sm01(0.03, 0.0, z) - 0.0020 * sm01(0.06, 0.115, z)
        d = d + 0.0030 * sm01(-0.10, -0.19, P0[:, 1]) * sm01(0.10, 0.03, z)
        return d

    obj, info = build_shell(B, 'Shoes', pred, d_fn, None, [M['Shoes']], coll, snaps=snaps,
                            thickness=thickness, min_gap=thickness + 0.0035, smooth_iters=12)
    me = obj.data
    for v in me.vertices:
        w = float(sm01(0.030, 0.006, v.co.z))
        v.co.z -= 0.009 * w
    me.update()
    # padded collar + laces
    Q = np.array([v.co[:] for v in me.vertices])
    Q0 = info['Q'].copy()
    Q0[:, 2] -= 0.009 * np.array([float(sm01(0.030, 0.006, z)) for z in Q0[:, 2]])
    for lp in boundary_loops(info):
        if len(lp) < 12:
            continue
        pts = Q0[lp]
        ctr = pts.mean(0)
        v = pts - ctr
        v[:, 2] = 0
        pts2 = pts - v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9) * (thickness * 0.5)
        side = 'R' if pts[:, 0].mean() > 0 else 'L'
        loop_tube(coll, 'ShoeCollar_' + side, [tuple(p_) for p_ in pts2], 0.0062, M['Shoes'], n=10)
    from mathutils.bvhtree import BVHTree
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    for sign in (+1, -1):
        cx = 0.195 * sign
        for k, y in enumerate((-0.150, -0.132, -0.114)):
            pts = []
            for t in np.linspace(-1, 1, 15):
                x = cx + 0.034 * t * (1.0 - 0.1 * abs(t))
                hit = tree.ray_cast(Vector((x, y, 0.5)), Vector((0, 0, -1)), 1.0)
                if hit[0] is None:
                    continue
                pts.append((x, y, hit[0].z + 0.0022))
            if len(pts) > 6:
                loop_tube(coll, 'Lace_%s%d' % ('R' if sign > 0 else 'L', k), pts, 0.0021, M['Lace'], n=8, closed=False)
    return obj, info


# ------------------------------------------------------------------------------------------------ wristbands
def make_wristbands(B, coll, M, s0=0.126, s1=0.160):
    """band conforming to the forearm: rings of ray-cast surface points (robust where the mesh topology is irregular)."""
    from preview_common import make_mesh_obj
    A = B.ARM_A
    prof = [(s0, 0.0008), (s0, 0.0036), (s0 + 0.0045, 0.0056), (s1 - 0.0045, 0.0056), (s1, 0.0036), (s1, 0.0008)]
    n = 48
    objs = []
    for sign in (+1, -1):
        Ad = np.array([A[0] * sign, A[1], A[2]])
        Cd = np.array([B.ARM_C[0] * sign, B.ARM_C[1], B.ARM_C[2]])
        u = np.cross(Ad, [0, 0, 1.0])
        u /= np.linalg.norm(u)
        v = np.cross(Ad, u)
        verts = []
        rings = []
        for (s, off) in prof:
            # local arm centre: mean of nearby arm vertices
            sa, ra = B.arm_coords(B.V, sign)
            sel = ((B.V[:, 0] * sign) > 0.3) & (np.abs(sa - s) < 0.008) & (ra < 0.07)
            ctr = B.V[sel].mean(0)
            ring = []
            for j in range(n):
                t = math.tau * j / n
                d = u * math.cos(t) + v * math.sin(t)
                hit = B.tree.ray_cast(Vector(ctr), Vector(d), 0.12)
                if hit[0] is None:
                    raise ValueError('wristband ray missed')
                p_ = np.array(hit[0][:]) + d * off
                ring.append(len(verts))
                verts.append(tuple(p_))
            rings.append(ring)
        faces = []
        for i in range(len(prof)):
            a, b = rings[i], rings[(i + 1) % len(prof)]
            for j in range(n):
                faces.append((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]))
        objs.append(make_mesh_obj('Wristband_' + ('R' if sign > 0 else 'L'), verts, faces, M['Band'], coll))
    return objs


# ------------------------------------------------------------------------------------------------ chest emblem (tennis-ball badge)
def make_emblem(coll, shirt, M, cx=0.092, cz=1.128, rad=0.0310):
    import bmesh
    from mathutils.bvhtree import BVHTree
    from preview_common import make_mesh_obj
    bm = bmesh.new()
    bm.from_mesh(shirt.data)
    tree = BVHTree.FromBMesh(bm)
    bm.free()

    def surf(x, z, lift):
        hit = tree.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)), 2.0)
        if hit[0] is None:
            raise ValueError('emblem missed the shirt')
        n = hit[1]
        return (hit[0].x + n.x * lift, hit[0].y + n.y * lift, hit[0].z + n.z * lift)

    n_ang, n_rad = 48, 6
    verts = [surf(cx, cz, 0.0013)]
    rings = []
    faces = []
    for j in range(1, n_rad + 1):
        rho = j / n_rad
        ring = []
        for i in range(n_ang):
            a = math.tau * i / n_ang
            ring.append(len(verts))
            lift = 0.0013 - 0.0004 * rho ** 4
            verts.append(surf(cx + rad * rho * math.cos(a), cz + rad * rho * math.sin(a), lift))
        rings.append(ring)
    for i in range(n_ang):
        faces.append((0, rings[0][i], rings[0][(i + 1) % n_ang]))
    for a, b in zip(rings, rings[1:]):
        for i in range(n_ang):
            faces.append((a[i], a[(i + 1) % n_ang], b[(i + 1) % n_ang], b[i]))
    disc = make_mesh_obj('Emblem', verts, faces, M['Emblem'], coll)
    # two seam arcs (like a tennis ball)
    for side, ox in (('A', -1), ('B', +1)):
        pts = []
        for t in np.linspace(-1.0, 1.0, 40):
            ang = t * 0.95
            x = cx + ox * (0.0405 - 0.0405 * math.cos(ang) + 0.0)       # arc bulging towards the centre
            xx = cx + ox * 0.036 - ox * 0.036 * math.cos(ang) * 0 + 0
            px = cx - ox * (0.038 * math.cos(ang)) + ox * 0.0500
            pz = cz + 0.038 * math.sin(ang)
            if (px - cx) ** 2 + (pz - cz) ** 2 > (rad * 0.86) ** 2:
                continue
            pts.append(surf(px, pz, 0.0021))
        if len(pts) > 5:
            from outfit import loop_tube
            loop_tube(coll, 'EmblemSeam_' + side, pts, 0.0007, M['Seam'], n=6, closed=False)
    return disc
