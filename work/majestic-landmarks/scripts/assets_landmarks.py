"""Course landmarks: Lighthouse (A), TwinFallsIsle + StepTemple (B), CalderaVolcano + CalderaWall (C)."""
import math
from mathutils import Vector, noise
from kit import Asset, Cards, P, mix, lin
from registry import asset


def grass_top(base, top=P['grass'], k=0.55, zmin=None):
    """Grass on up-facing faces; with zmin also only above that height (gives a clean contour edge)."""
    return lambda c, n: top if n.z > k and (zmin is None or c.z > zmin) else base


# ======================================================================= A: lighthouse
@asset('Lighthouse', course='A', holes=[7, 8, 9, 12, 15], kind='course landmark',
       where='Cliffside course landmark on a headland, seen from every tee (h07 FWD beyond-right of the green; h08 far R; '
             'h12 on the island green; h15 R across the bay). Brief chat 9 rule: one landmark visible from every tee.',
       budget=15000, dims=dict(z=(16, 24)), match=(18, 6), target='Lighthouse', target_aspect=2.55,
       features=['white tapered tower', 'two red bands + red lantern housing', 'dark gallery with railing', 'glowing lantern glass',
                 'red dome + finial', "keeper's house with red roof at the base", 'rock headland mound with grass cap'],
       animated=[('Beam', 'lantern centre, spin about local Z (Unity Y)')], dynamic=['Beam'], fx_shared=['Beam'])
def lighthouse(q):
    a = Asset('Lighthouse', q, seed=7)
    rock = grass_top(P['limestone'], k=0.35, zmin=2.0)
    a.blob(7.5, scale=(1.25, 1.0, 0.28), col=rock, sub=3, amp=0.22, freq=1.1, seed=3)
    # tower: rings at every colour boundary so bands stay crisp
    z0, z1 = 2.4, 15.8
    r0, r1 = 2.15, 1.45
    R = lambda z: r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    bands = [(7.2, 8.8), (11.4, 13.0)]
    zs = sorted({z0, z1, 3.4, 5.0, 10.0, 14.4} | {b for ab in bands for b in ab})
    prof = [(0, z0)] + [(R(z), z) for z in zs] + [(0, z1)]
    red = lambda c, n: P['red'] if any(b0 - 1e-3 < c.z < b1 + 1e-3 for b0, b1 in bands) or c.z > 14.4 else P['white']
    a.revolve(prof, col=red, segs=28)
    # gallery deck + railing
    a.cyl(2.35, 2.35, 0.32, loc=(0, 0, z1 - 0.05), col=P['iron'], segs=28, bevel=0.08)
    a.sweep([(2.2 * math.cos(t), 2.2 * math.sin(t), z1 + 1.0) for t in [i * 2 * math.pi / 24 for i in range(24)]],
            [(-.05, -.05), (.05, -.05), (.05, .05), (-.05, .05)], col=P['iron'], closed=True)
    if a.lod0:
        for i in range(16):
            t = i * 2 * math.pi / 16
            a.box((0.07, 0.07, 0.95), loc=(2.2 * math.cos(t), 2.2 * math.sin(t), z1 + 0.75), col=P['iron'])
    # lantern room: red base ring, glowing glass, mullions, red dome, finial
    zl = z1 + 0.27
    a.cyl(1.3, 1.3, 0.45, loc=(0, 0, zl), col=P['red'], segs=24, bevel=0.06)
    a.cyl(1.12, 1.12, 1.6, loc=(0, 0, zl + 0.45), col=P['window'], segs=16, glow=0.9)
    if a.lod0:
        for i in range(8):
            t = i * 2 * math.pi / 8 + math.pi / 8
            a.box((0.1, 0.1, 1.6), loc=(1.14 * math.cos(t), 1.14 * math.sin(t), zl + 1.25), rot=(0, 0, math.degrees(t)), col=P['red_dk'])
    zd = zl + 2.05
    a.cyl(1.38, 1.38, 0.18, loc=(0, 0, zd), col=P['red_dk'], segs=24, bevel=0.05)
    a.revolve([(1.32, zd + 0.18), (1.25, zd + 0.5), (1.0, zd + 0.9), (0.6, zd + 1.2), (0.2, zd + 1.35), (0, zd + 1.38)], col=P['red'], segs=24)
    a.cyl(0.08, 0.02, 0.9, loc=(0, 0, zd + 1.3), col=P['iron'], segs=8)
    a.sphere(0.16, loc=(0, 0, zd + 1.5), col=P['iron'], segs=10)
    # door + windows (front = -Y)
    a.box((0.9, 0.3, 1.7), loc=(0, -R(3.6) + 0.05, 3.6), col=P['red_dk'], bevel=0.08)
    if a.lod0:
        for z in (6.0, 9.6, 13.2):
            a.box((0.45, 0.25, 0.75), loc=(0, -R(z) + 0.03, z), col=P['glass'], bevel=0.06)
    # keeper's house at the base, right side
    hx, hy, hz = 3.7, 1.4, 2.7
    a.box((3.6, 2.8, 2.6), loc=(hx, hy, hz + 1.3), col=P['white'], bevel=0.12)
    a.box((3.6, 2.8, hz), loc=(hx, hy, hz / 2), col=P['stone'])          # plinth into the rock
    roof = [(-1.95, 0), (1.95, 0), (0, 1.35)]
    a.prism(roof, -1.6, 1.6, loc=(hx, hy, hz + 2.55), rot=(90, 0, 90), col=P['roof_red'], bevel=0.08)
    a.box((0.5, 0.5, 1.2), loc=(hx + 1.0, hy + 0.6, hz + 3.3), col=P['brick'], bevel=0.05)
    a.box((0.8, 0.2, 1.5), loc=(hx, hy - 1.42, hz + 0.75), col=P['wood'], bevel=0.05)
    if a.lod0:
        for dx in (-1.1, 1.1):
            a.box((0.6, 0.2, 0.6), loc=(hx + dx, hy - 1.42, hz + 1.5), col=P['glass'], bevel=0.04)
    # beam: two crossed tapered fan strips from the lantern centre (FX, spins)
    c = Cards('Beam')
    for ang in (0, 180):
        t = math.radians(ang)
        d = Vector((math.cos(t), math.sin(t), -0.02))
        pts = [Vector((0, 0, zl + 1.25)) + d * s for s in (0.0, 8.0, 20.0, 40.0)]
        c.strip(pts, [0.6, 3.0, 6.0, 10.0], P['window'], alpha=(0.5, 0.0), side=(0, 0, 1))
    return dict(body=a, fx=dict(Beam=c), pivots=dict(Beam=(0, 0, zl + 1.25)))


# ======================================================================= B: stepped temple + twin falls isle
def temple(a, base=(0, 0, 0), w=18.0, tiers=4, th=2.6, ruin=True):
    """Stepped pyramid with a front stair (-Y) and a shrine on top; mossy carved stone."""
    bx, by, bz = base
    stone = lambda c, n: P['jungle_moss'] if n.z > 0.7 else (P['jungle_stone'] if (int(c.x * 0.7) + int(c.z * 1.1)) % 3 else P['stone'])
    widths = [w * (1 - i * 0.19) for i in range(tiers)]
    for i, wi in enumerate(widths):
        a.box((wi, wi, th), loc=(bx, by, bz + i * th + th / 2), col=stone, bevel=0.35)
        if True:     # carved band on each tier face
            a.box((wi * 0.86, wi + 0.12, th * 0.22), loc=(bx, by, bz + i * th + th * 0.55), col=P['stone_dk'], bevel=0.05)
    top = bz + tiers * th
    sw = w * 0.2
    y_bot = by - w / 2 - 2.2
    y_top = by - widths[-1] / 2
    n = tiers * 4
    for k in range(n):
        z = bz + (k + 0.5) * (top - bz) / n
        yk = y_bot + (y_top - y_bot) * (k + 0.5) / n
        depth = (y_top - y_bot) / n + 0.3
        a.box((sw, depth, (top - bz) / n + 0.05), loc=(bx, yk, z), col=P['stone'], bevel=0.06)
    for sx in (-1, 1):   # stair side walls
        a.prism([(y_bot, 0), (y_top, top - bz), (y_top, 0)], -0.5, 0.5, loc=(bx + sx * (sw / 2 + 0.5), 0, bz), rot=(90, 0, 90),
                col=P['jungle_stone'], bevel=0.12)
    # shrine
    sw2 = widths[-1] * 0.62
    a.box((sw2, sw2 * 0.8, 3.2), loc=(bx, by, top + 1.6), col=P['jungle_stone'], bevel=0.25)
    a.box((sw2 * 1.25, sw2 * 1.05, 0.6), loc=(bx, by, top + 3.5), col=P['stone_dk'], bevel=0.2)
    a.box((sw2 * 0.8, sw2 * 0.6, 0.9), loc=(bx, by, top + 4.2), col=stone, bevel=0.2)
    a.box((sw2 * 0.34, 0.6, 2.1), loc=(bx, by - sw2 * 0.4, top + 1.05), col=P['purple_dk'], bevel=0.08)
    if a.lod0:
        for sx in (-1, 1):
            a.cyl(0.35, 0.3, 3.2, loc=(bx + sx * sw2 * 0.36, by - sw2 * 0.42, top), col=P['stone'], segs=10)
        if ruin:   # tumbled blocks + hanging vines
            r = a.rng
            for k in range(7):
                t = r.uniform(0, 2 * math.pi); d = w * r.uniform(0.55, 0.7)
                a.box((r.uniform(1, 2), r.uniform(1, 1.8), r.uniform(.7, 1.3)), loc=(bx + d * math.cos(t), by + d * math.sin(t), bz + 0.4),
                      rot=(r.uniform(-15, 15), r.uniform(-15, 15), r.uniform(0, 90)), col=stone, bevel=0.2)
            for k in range(10):
                i = k % tiers; wi = widths[i]; side = r.choice((-1, 1))
                x = bx + r.uniform(-wi * 0.45, wi * 0.45)
                a.box((0.35, 0.18, th * r.uniform(0.6, 1.0)), loc=(x, by - wi / 2 - 0.08, bz + i * th + th * 0.55), col=P['leaf'], bevel=0.06)


def canopy(a, x, y, z, s=1.0, k=3):
    r = a.rng
    for j in range(k if a.lod0 else 1):
        a.blob(2.6 * s * r.uniform(0.8, 1.15), loc=(x + r.uniform(-1.8, 1.8) * s, y + r.uniform(-1.8, 1.8) * s, z - 0.6),
               scale=(1, 1, 0.8), col=lambda c, n: P['leaf_lt'] if n.z > 0.5 else P['leaf'], sub=1, amp=0.25, seed=r.randint(0, 99))


@asset('StepTemple', course='B', holes=[19], kind='hole set piece (close-up)',
       where='h19 FWD: the green sits under the stone temple, the twin falls behind (brief). Also the shrine of the TwinFallsIsle landmark.',
       budget=8000, dims=dict(x=(14, 26), z=(10, 18)), match=(8, 8), target='StepTemple',
       features=['4-tier stepped pyramid', 'central front stair with side walls', 'shrine with dark doorway + roof slab',
                 'mossy tops, carved bands', 'ruin blocks + hanging vines'])
def step_temple(q):
    a = Asset('StepTemple', q, seed=19)
    a.box((22, 22, 0.8), loc=(0, 0, 0.4), col=lambda c, n: P['jungle_moss'] if n.z > 0.7 else P['jungle_stone'], bevel=0.3)
    temple(a, base=(0, 0, 0.8), w=18)
    return dict(body=a)


def isle_r(t, z, r):
    lobe = 0.16 * noise.noise(Vector((math.cos(t) * 1.2, math.sin(t) * 1.2, 0.3))) + 0.08 * noise.noise(Vector((math.cos(t) * 3, math.sin(t) * 3, z * 0.08)))
    return r * (1 + lobe + 0.025 * math.sin(t * 13 + z * 0.11))


ISLE = [(0, 0), (50, 0), (47, 3), (42, 6), (40, 12), (38.5, 16), (37, 20), (36, 27), (33.5, 30), (30.5, 31.2), (29.5, 34), (28.8, 38),
        (28, 42), (27, 46), (25.5, 51), (21, 54.5), (12, 56.4), (0, 56.8)]


@asset('TwinFallsIsle', course='B', holes=[13, 14, 17, 18, 19, 20], kind='course landmark (far + h19 close-up)',
       where='Wild Isles course landmark: high central isle with a ruined stepped temple on top and twin waterfalls; on h19 FWD behind '
             'the green, in the distance from 13/14/17/18/20 (brief: a misty glow marks it). LOD2 impostor for the far views.',
       budget=15000, dims=dict(x=(80, 115), z=(65, 80)), match=(0, 6), target='TwinFallsIsle',
       features=['tall two-tier cliff isle with a jungle ledge, lobed outline', 'jungle canopy clumps on the summit and the ledge',
                 'stepped temple + shrine on the summit', 'twin two-stage waterfall cards (scroll UVs)', 'mist band at the plunge pool'])
def twin_falls_isle(q):
    a = Asset('TwinFallsIsle', q, seed=23)
    def col(c, n):
        t = math.atan2(c.y, c.x)
        streak = noise.noise(Vector((math.cos(t) * 4, math.sin(t) * 4, c.z * 0.02)))
        if n.z > 0.5 and c.z > 7:
            return P['leaf_lt'] if streak > 0.15 else P['leaf']
        if c.z < 6:
            return P['sand_wet'] if n.z > 0.4 else P['stone_dk']
        if streak > 0.2 or (c.z > 44 and streak > -0.3) or (26 < c.z < 31):
            return P['jungle_moss']
        return P['jungle_stone'] if streak > -0.3 else P['stone']
    a.revolve(ISLE, col=col, segs=60, rfn=isle_r, vcol=True)
    temple(a, base=(0, 4, 56.4), w=24, ruin=a.lod0)
    r = a.rng
    for k in range(28 if a.lod0 else 12):          # summit jungle
        t = r.uniform(0, 2 * math.pi); d = r.uniform(13, 26)
        x, y = d * math.cos(t), d * math.sin(t)
        if abs(x) < 14.5 and -19 < y < 17:
            continue
        canopy(a, x, y, 56.6 if d < 21 else 55.0, s=r.uniform(1.1, 1.8))
    for k in range(30 if a.lod0 else 12):          # ledge jungle ring at z~31
        t = r.uniform(0, 2 * math.pi)
        if abs((math.degrees(t) + 90) % 360 - 180) > 166:   # keep the falls' front gap clear (theta ~ -90)
            continue
        d = isle_r(t, 31, 33.5)
        canopy(a, d * math.cos(t), d * math.sin(t), 31.5, s=r.uniform(0.8, 1.2), k=2)
    fx = Cards('Falls')
    for sx in (-1, 1):
        t = math.radians(-90 + sx * 9)
        up = [(isle_r(t, z, R) + 1.3, z) for z, R in ((50.5, 26.0), (46, 27.0), (40, 28.4), (33, 29.4))]
        fx.strip([(rr * math.cos(t), rr * math.sin(t), z) for rr, z in up], [3.6, 4.0, 4.6, 5.2], P['foam'], alpha=(0.95, 0.85), side=(1, 0, 0), vrep=4)
        lo = [(isle_r(t, z, R) + 1.4, z) for z, R in ((30.5, 34.5), (26, 36.0), (16, 38.5), (6, 42.0), (1.5, 46))]
        fx.strip([(rr * math.cos(t), rr * math.sin(t), z) for rr, z in lo], [5.0, 5.6, 6.4, 7.4, 9.0], P['foam'], alpha=(0.9, 0.7), side=(1, 0, 0), vrep=4)
    mist = Cards('Mist')
    for k, z in enumerate((2.5, 6.5)):
        mist.strip([(-22, -47 - k, z), (0, -49 - k, z), (22, -47 - k, z)], 8 + 4 * k, (0.95, 0.97, 1.0), alpha=(0.5, 0.5), normal_up=(0, -1, 0), side=(0, 0, 1))
    return dict(body=a, fx=dict(Falls=fx, Mist=mist))


# ======================================================================= C: caldera volcano + wall ring
VPROF = [(r * 0.8, z * 1.3) for r, z in [(0, 0), (180, 0), (172, 4), (150, 14), (122, 32), (95, 55), (70, 78), (50, 96), (40, 106),
                                       (36, 110), (31, 111.5), (26, 108), (19, 101), (10, 99), (0, 98.6)]]
ZC = VPROF[-1][1]   # crater floor


def vol_r(t, z, r):
    ridge = 0.06 * math.sin(t * 15 + 0.6 * math.sin(t * 3)) + 0.06 * noise.noise(Vector((math.cos(t) * 2, math.sin(t) * 2, z * 0.02)))
    return r * (1 + ridge * min(1, z / 30) * max(0.0, 1 - z / 150))


def vol_surface(t, z):
    """Outer flank radius at height z (piecewise-linear on the outer profile) incl. ridges."""
    outer = VPROF[1:10]
    for (r0, z0), (r1, z1) in zip(outer, outer[1:]):
        if z0 <= z <= z1:
            r = r0 + (r1 - r0) * (z - z0) / max(1e-6, z1 - z0)
            return vol_r(t, z, r)
    return vol_r(t, z, outer[-1][0])


@asset('CalderaVolcano', course='C', holes=[10, 16, 21, 22, 23], kind='course landmark (far)',
       where='Magma Open course landmark: the great caldera volcano with a glowing crater and a slow plume, visible from every hole; '
             'h16 sits right under it (looms large), h10/h21-23 see it beyond the green / caldera wall.',
       budget=15000, dims=dict(x=(250, 330), z=(130, 160)), match=(0, 4), match_lens=50, target='CalderaVolcano',
       features=['broad ridged cone, dark basalt with ash-lit ridges', 'deep crater with glowing lava floor', 'glowing lava rivers down the front flank',
                 'plume card (separate, shared by all LODs)'],
       animated=[('Plume', 'crater centre; scroll/billow UV0.y, sway')], dynamic=['Plume'], fx_shared=['Plume'])
def caldera_volcano(q):
    a = Asset('CalderaVolcano', q, seed=31)
    def col(c, n):
        rr = math.hypot(c.x, c.y)
        if c.z < ZC + 4 and rr < 18:
            return P['lava_hot'] if rr < 11 else P['lava']
        if c.z > ZC + 6:
            return P['basalt']
        lit = max(0.0, math.sin(math.atan2(c.y, c.x) * 15 + 0.6 * math.sin(math.atan2(c.y, c.x) * 3)))
        base = mix(P['basalt'], P['ash'], 0.15 + 0.3 * min(1, c.z / 130))
        return mix(base, P['basalt_lt'], lit * 0.8)
    glow = lambda c: (1.0 if (c.z < ZC + 4 and math.hypot(c.x, c.y) < 18) else 0.0)
    a.revolve(VPROF, col=col, segs=96, rfn=vol_r, glow=glow, vcol=True)
    for k, th in enumerate((-97, -78, -120)):
        if not a.lod0 and k > 1:
            break
        t0 = math.radians(th)
        pts = []
        z = ZC + 9.0
        while z > 5:
            t = t0 + 0.04 * math.sin(z / 9 + k * 2)
            r = vol_surface(t, z) + 0.2
            pts.append((r * math.cos(t), r * math.sin(t), z))
            z -= (5 if a.lod0 else 10) * (1 + (ZC - z) / 60)
            if z < ZC * (0.35 + 0.15 * k):
                break
        radial = Vector((math.cos(t0), math.sin(t0), 0))
        a.sweep(pts, [(-1, 0), (1, 0), (1, 0.7), (-1, 0.7)], col=lambda c, n: P['lava_hot'] if c.z > ZC - 15 else P['lava'],
                scale=lambda i, t: (0.9 + 2.4 * t, 1.0), glow=1.0, up=tuple(radial))
    plume = Cards('Plume')
    for side in ((1, 0, 0), (0, 1, 0)):
        pts = [(0, 0, ZC + 4), (4, 2, ZC + 40), (14, 6, ZC + 85), (30, 10, ZC + 135), (52, 14, ZC + 185)]
        plume.strip(pts, [22, 40, 62, 90, 125], lin('#9a8a96'), alpha=(0.95, 0.0), side=side, vrep=2)
    return dict(body=a, fx=dict(Plume=plume), pivots=dict(Plume=(0, 0, ZC + 4)))


RW, SPAN = 200.0, 15.0   # caldera ring radius (m) and degrees per segment: 24 segments close the ring


def caldera_wall(q, name, fall):
    a = Asset(name, q, seed=41)
    L = RW * math.radians(SPAN)
    D = 26.0
    kfl = max(1, round(L / 2.6))
    def warp(yu):
        t = (yu + D / 2) / D
        return D * t ** 1.8
    def H(x):
        h = 38 + 4 * math.sin(2 * math.pi * 2 * x / L + 1.0) + 2.5 * math.sin(2 * math.pi * 5 * x / L)
        if fall:
            h -= 5 * math.exp(-(x / 4.0) ** 2)
        return h
    def flute(x):   # vertical basalt columns: radial bulge, periodic over the segment so tiles match
        return 1.3 * abs(math.sin(math.pi * kfl * x / L))
    def hfn(x, yu):
        yy = warp(yu)
        u = yy / 3.2
        if u < 1:
            return H(x) * (u ** 0.6)
        back = (yy - 3.2) / (D - 3.2)
        return H(x) + 3 * math.sin(math.pi * min(1, back * 2.5)) - 14 * max(0, back - 0.4)
    def xyfn(x, yu):
        yy = warp(yu)
        yy = yy + flute(x) * min(1.0, yy / 0.6)
        th = x / RW
        return ((RW + yy) * math.sin(th), (RW + yy) * math.cos(th) - RW)
    def trough(x):
        return abs(math.sin(math.pi * kfl * x / L)) > 0.92
    def col(c, n):
        if c.z < 1.2:
            return P['ember']
        if fall and abs(c.x) < 2.4 and n.z < 0.6:
            return P['lava_hot']
        if n.z > 0.6:
            return P['ash'] if c.z > 30 else P['basalt_lt']
        if trough(c.x) and c.z < 14:
            return P['ember']
        return P['basalt_lt'] if abs(math.sin(math.pi * kfl * c.x / L)) < 0.35 else P['basalt']
    def glow(c):
        if c.z < 1.2:
            return 0.9
        if fall and abs(c.x) < 2.4 and c.z < 36:
            return 1.0
        return 0.6 * (1 - c.z / 14) if trough(c.x) and c.z < 14 and c.y < 6 else 0.0
    a.slab(40, 18, L, D, hfn, base_z=-3.0, col=col, glow=glow, xyfn=xyfn, vcol=False)
    out = dict(body=a)
    if fall:
        fx = Cards('LavaFall')
        top = H(0) - 0.5
        pts = [(0, -0.6, top), (0, -1.4, top - 4), (0, -2.0, top * 0.55), (0, -2.4, 1.0), (0, -3.5, 0.1)]
        fx.strip(pts, [3.2, 3.6, 4.4, 5.4, 7.0], P['lava_hot'], alpha=(1, 1), side=(1, 0, 0), vrep=5)
        out['fx'] = dict(LavaFall=fx)
    return out


_wall_meta = dict(tile=dict(kind='arc', c=(0, -RW), s=1, span=SPAN), course='C', holes=[21, 22, 23], kind='edge kit (tileable ring segment)', budget=8000, dims=dict(z=(36, 52)), minz=(-3.1, -2.9),
                  match=(0, 10), target='CalderaWall', no_impostor=False,
                  where='Caldera wall ring around the 21-23 lava lake: hides the lava-disc rim seam from green-back, off-line and flyover views '
                        '(PLAN 4.2). 24 segments of 15 deg at radius 200 m close the ring; ring centre = local (0, -200, 0) Blender '
                        '(Unity (0, 0, 200) before placement). Mix A (lava fall) and B (plain).')


@asset('CalderaWall_A', features=['tileable 15 deg arc (ends identical)', 'vertical basalt flutes', 'glowing seams at the lava line + cracks',
                                  'lava-fall channel + LavaFall card'], animated=[('LavaFall', 'UV0.y scroll')], **_wall_meta)
def caldera_wall_a(q):
    return caldera_wall(q, 'CalderaWall_A', True)


@asset('CalderaWall_B', features=['tileable 15 deg arc (ends identical)', 'vertical basalt flutes', 'glowing seams at the lava line + cracks'],
       **_wall_meta)
def caldera_wall_b(q):
    return caldera_wall(q, 'CalderaWall_B', False)
