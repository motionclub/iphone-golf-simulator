"""Hole set pieces (HOLE_BRIEFS.md 'Set pieces' / FWD / BACK columns). Front of every piece = Blender -Y."""
import math
from mathutils import Vector, noise
from kit import Asset, Cards, P, mix, lin
from registry import asset

WOOD = lambda c, n: P['wood'] if abs(n.z) < 0.7 else P['wood_lt']
OCT = [(math.cos(i * math.pi / 4 + math.pi / 8), math.sin(i * math.pi / 4 + math.pi / 8)) for i in range(8)]


def log(a, p0, p1, r, col, segs=8):
    """Round log between two points (octagonal sweep; 6 sides on LOD1)."""
    n = segs if a.lod0 else 6
    sec = [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    d = Vector(p1) - Vector(p0)
    up = (1, 0, 0) if abs(d.normalized().z) > 0.9 else (0, 0, 1)
    a.sweep([p0, p1], sec, col=col, up=up)


def window(a, c, w, h, normal='-y', glow=0.8, frame=None, glass=None):
    x, y, z = c
    frame = frame or P['white']; glass = glass or P['window']
    t = 0.14
    dims = (w, t, h) if normal in ('-y', '+y') else (t, w, h)
    fd = (w + 0.24, t * 0.6, h + 0.24) if normal in ('-y', '+y') else (t * 0.6, w + 0.24, h + 0.24)
    a.box(dims, loc=c, col=glass, glow=glow, bevel=0.03)
    if a.lod0:
        a.box(fd, loc=c, col=frame, bevel=0.03)
        if normal in ('-y', '+y'):
            a.box((0.07, t * 1.3, h), loc=c, col=frame); a.box((w, t * 1.3, 0.07), loc=c, col=frame)
        else:
            a.box((t * 1.3, 0.07, h), loc=c, col=frame); a.box((t * 1.3, w, 0.07), loc=c, col=frame)


def gable_x(a, w, d, h, loc, col, bevel=0.08):
    """Triangular roof prism: ridge along X (length d), span w across Y, rise h; loc = centre of the base."""
    a.prism([(-w / 2, 0), (w / 2, 0), (0, h)], -d / 2, d / 2, loc=loc, rot=(90, 0, 90), col=col, bevel=bevel)


def gable_y(a, w, d, h, loc, col, bevel=0.08):
    """Ridge along Y (length d), span w across X (gable end faces -Y)."""
    x, y, z = loc
    a.prism([(-w / 2, 0), (w / 2, 0), (0, h)], -d / 2, d / 2, loc=(x, y, z), rot=(90, 0, 0), col=col, bevel=bevel)


def hip(a, half, h, loc, col, segs=4):
    """Square pyramid roof with half-width 'half' (edges axis-aligned)."""
    a.cyl(half * math.sqrt(2), 0, h, loc=loc, col=col, segs=segs, phase=math.pi / 4)


def by_normal(side, top, under=None):
    return lambda c, n: top if n.z > 0.6 else (under if (under is not None and n.z < -0.6) else side)


def smoke(name, base, h=6.0, w=1.2, col='#b9a7c8'):
    c = Cards(name)
    for side in ((1, 0, 0), (0, 1, 0)):
        x, y, z = base
        c.strip([(x, y, z), (x + 0.4, y + 0.2, z + h * 0.4), (x + 1.2, y + 0.5, z + h)], [w, w * 1.8, w * 3.0], lin(col), alpha=(0.8, 0.0), side=side, vrep=1)
    return c


# ======================================================================= course B
@asset('LookoutTower', course='B', holes=[13], kind='hole set piece', budget=6000, dims=dict(z=(9, 12)), match=(25, 8), target='LookoutTower',
       where='h13 FWD: the summit green on the pine hill, a red-roofed lookout tower at the top (behind/above the green).',
       features=['four splayed log legs on stone footings', 'X cross-braces at two levels', 'railed platform with plank half-walls',
                 'red pyramid roof on corner posts', 'flag on the roof', 'ladder'])
def lookout_tower(q):
    a = Asset('LookoutTower', q, seed=13)
    zb, zp = 0.0, 6.2
    for sx in (-1, 1):
        for sy in (-1, 1):
            a.box((0.7, 0.7, 0.5), loc=(sx * 1.7, sy * 1.7, 0.25), col=P['stone'], bevel=0.1)
            log(a, (sx * 1.7, sy * 1.7, 0.4), (sx * 1.25, sy * 1.25, zp + 2.3), 0.17, P['wood'])
    for z0, z1 in ((0.9, 3.4), (3.4, 5.9)):
        for side in range(4):
            ang = side * math.pi / 2
            for k in (-1, 1):
                f = lambda z: 1.7 - 0.45 * z / (zp + 2.3)
                p0 = Vector((k * f(z0), -f(z0), z0)); p1 = Vector((-k * f(z1), -f(z1), z1))
                rot = lambda p: (p.x * math.cos(ang) - p.y * math.sin(ang), p.x * math.sin(ang) + p.y * math.cos(ang), p.z)
                log(a, rot(p0), rot(p1), 0.08, P['wood_dk'], segs=6)
    a.box((3.5, 3.5, 0.25), loc=(0, 0, zp), col=WOOD, bevel=0.06)
    for i, (dx, dy, sx_, sy_) in enumerate(((0, -1.65, 3.4, 0.12), (0, 1.65, 3.4, 0.12), (-1.65, 0, 0.12, 3.4), (1.65, 0, 0.12, 3.4))):
        a.box((sx_, sy_, 0.75), loc=(dx, dy, zp + 0.5), col=P['wood_lt'], bevel=0.03)
        a.box((sx_ + 0.06, sy_ + 0.06, 0.1), loc=(dx, dy, zp + 1.0), col=P['wood_dk'], bevel=0.02)
    hip(a, 2.25, 1.5, loc=(0, 0, zp + 2.3), col=P['red'])
    a.box((4.4, 4.4, 0.16), loc=(0, 0, zp + 2.32), col=P['red_dk'], bevel=0.04)
    a.cyl(0.04, 0.04, 1.4, loc=(0, 0, zp + 3.6), col=P['iron'], segs=6)
    a.box((0.9, 0.04, 0.5), loc=(0.46, 0, zp + 4.7), col=P['red'], bevel=0.01)
    for sx in (-0.3, 0.3):
        log(a, (sx, -2.2, 0.0), (sx, -1.75, zp), 0.05, P['wood_dk'], segs=6)
    for k in range(9 if a.lod0 else 5):
        t = (k + 0.5) / (9 if a.lod0 else 5)
        a.box((0.6, 0.06, 0.06), loc=(0, -2.2 + 0.45 * t, zp * t), col=P['wood_dk'])
    return dict(body=a)


@asset('WitchCottage', course='B', holes=[14], kind='hole set piece', budget=8000, dims=dict(z=(9, 16)), match=(-20, 8), target='WitchCottage',
       where="h14 FWD: the green sunk in the crater ringed by gnarled trees, a crooked witch's cottage with a glowing window and a cauldron chimney.",
       features=['crooked stone ground floor + leaning timber upper floor', 'tall steep purple roof leaning off-axis + dormer',
                 'crooked stacked chimney topped by a cauldron with green glow', 'glowing warm windows, round-top door',
                 'rocky moss mound base', 'purple chimney smoke card (shared FX)'],
       animated=[('Smoke', 'cauldron top; scroll UV0.y')], dynamic=['Smoke'], fx_shared=['Smoke'])
def witch_cottage(q):
    a = Asset('WitchCottage', q, seed=14)
    a.blob(5.2, scale=(1.2, 1.1, 0.32), col=by_normal(P['stone_dk'], P['moss']), sub=2, amp=0.2, seed=4)
    zb = 1.2
    a.box((5.0, 4.2, 3.0), loc=(0, 0, zb + 1.5), rot=(0, 2, 0), col=lambda c, n: P['stone'] if (int(c.z * 1.4) + int(c.x)) % 2 else P['stone_dk'], bevel=0.2)
    a.box((5.6, 4.7, 2.6), loc=(0.15, 0, zb + 4.2), rot=(2, -4, 3), col=lambda c, n: P['purple'] if abs(n.z) < 0.7 else P['wood_dk'], bevel=0.15)
    if a.lod0:   # timber framing on the upper floor
        for dx in (-2.4, -0.8, 0.8, 2.4):
            a.box((0.18, 4.85, 2.5), loc=(0.15 + dx, 0, zb + 4.2), rot=(2, -4, 3), col=P['wood_dk'])
    a.prism([(-3.3, 0), (3.3, 0), (0.5, 5.2)], -3.2, 3.2, loc=(0.25, 0, zb + 5.4), rot=(90, -6, 90 + 3),
            col=lambda c, n: P['purple_dk'] if n.z > -0.2 else P['wood_dk'], bevel=0.12)
    gable_y(a, 1.8, 1.6, 1.6, (-1.1, -2.3, zb + 6.0), P['purple_dk'])
    a.box((1.5, 1.2, 1.2), loc=(-1.1, -2.1, zb + 5.6), col=P['purple'], bevel=0.08)
    window(a, (-1.1, -2.75, zb + 5.6), 0.7, 0.7, glow=1.0, frame=P['wood_dk'])
    for x in (-1.4, 1.4):
        window(a, (x, -2.13, zb + 1.6), 0.8, 0.9, glow=1.0, frame=P['wood_dk'])
    window(a, (1.4, -2.4, zb + 4.1), 0.8, 0.8, glow=1.0, frame=P['wood_dk'])
    a.box((1.1, 0.25, 1.9), loc=(0, -2.15, zb + 0.95), col=P['wood_dk'], bevel=0.08)
    a.cyl(0.55, 0.55, 0.25, loc=(0, -2.15, zb + 1.9), rot=(90, 0, 0), col=P['wood_dk'], segs=12, base=False)
    # crooked chimney + cauldron
    x, y, z = 2.1, 1.7, zb + 6.6
    for k, (dx, ang) in enumerate(((0.0, 4), (0.2, -7), (0.45, 9), (0.3, -5))):
        a.cyl(0.55, 0.5, 1.5, loc=(x + dx, y, z + k * 1.4), rot=(ang, ang * 0.5, 0), col=P['stone'] if k % 2 else P['stone_dk'], segs=8, bevel=0.1)
    zc = z + 5.6
    a.revolve([(0.3, zc), (0.75, zc + 0.15), (0.95, zc + 0.6), (0.85, zc + 1.0), (0.95, zc + 1.12), (0.7, zc + 1.12), (0.7, zc + 1.0), (0, zc + 1.0)],
              loc=(x + 0.35, y, 0), col=P['iron'], segs=16)
    a.cyl(0.72, 0.72, 0.08, loc=(x + 0.35, y, zc + 0.92), col=lin('#8fff6a'), glow=1.0, segs=16)
    return dict(body=a, fx=dict(Smoke=smoke('Smoke', (x + 0.35, y, zc + 1.0), h=7.0, w=1.0)), pivots=dict(Smoke=(x + 0.35, y, zc + 1.0)))


@asset('RopeBridge', course='B', holes=[14, 18], kind='hole set piece (shared)', budget=5000, dims=dict(x=(15, 17)), match=(30, 15), target='RopeBridge',
       pivot='anchor', where='h14 set piece: rope bridge over the root window; h18 set piece: rope bridge across the chasm. 16 m span along X; '
                             'scale X for other spans (planks stretch). Pivot = mid-span at the anchor (post-foot) height; the deck sags below it.',
       features=['log end posts on both banks', 'plank deck on a sagging catenary', 'two rope hand-lines', 'vertical hanger ropes'])
def rope_bridge(q):
    a = Asset('RopeBridge', q, seed=18)
    L, W, sag = 16.0, 1.3, 1.1
    zf = lambda x: -sag * (1 - (2 * x / L) ** 2)
    n = 26 if a.lod0 else 13
    for k in range(n):
        x = -L / 2 + 0.4 + (L - 0.8) * (k + 0.5) / n
        a.box((L / n * 0.82 * (L - 0.8) / L, W, 0.09), loc=(x, 0, zf(x) + 0.05), col=WOOD if k % 3 else P['wood_lt'], bevel=0.02)
    for sx in (-1, 1):
        for sy in (-1, 1):
            log(a, (sx * L / 2, sy * 0.75, -0.3), (sx * L / 2, sy * 0.75, 1.35), 0.12, P['wood'])
        log(a, (sx * L / 2, -0.85, 1.25), (sx * L / 2, 0.85, 1.25), 0.07, P['wood_dk'], segs=6)
    m = 14 if a.lod0 else 7
    for sy in (-1, 1):
        for base_z, k in (((1.2, 0.45), (0.65, 0.7)) if a.lod0 else ((1.2, 0.45),)):
            pts = [(-L / 2 + L * i / m, sy * 0.72, base_z + k * zf(-L / 2 + L * i / m)) for i in range(m + 1)]
            a.sweep(pts, [(-.03, -.03), (.03, -.03), (.03, .03), (-.03, .03)], col=P['rope'])
        pts2 = [(-L / 2 + L * i / m, sy * 0.66, zf(-L / 2 + L * i / m) + 0.12) for i in range(m + 1)]
        a.sweep(pts2, [(-.03, -.03), (.03, -.03), (.03, .03), (-.03, .03)], col=P['rope'])
        if True:
            for i in range(1, m, 1 if a.lod0 else 2):
                x = -L / 2 + L * i / m
                ztop = zf(x) * 0.45 + 1.2
                a.box((0.03, 0.03, ztop - zf(x) - 0.12), loc=(x, sy * 0.7, (ztop + zf(x) + 0.12) / 2), col=P['rope'])
    return dict(body=a)


@asset('AlpineChalet', course='B', holes=[17], kind='hole set piece', budget=8000, dims=dict(z=(7, 11)), match=(-25, 6), target='AlpineChalet',
       where='h17 FWD: green beyond the frozen lake, an alpine chalet with smoke (left of the green, below the fjord walls).',
       features=['stacked log walls with crossed corner ends', 'stone foundation', 'steep gable roof, front-facing, under a thick snow cap',
                 'warm glowing windows + front balcony', 'stone chimney with snow cap + smoke card', 'snow drifts at the base'],
       animated=[('Smoke', 'chimney top; scroll UV0.y')], dynamic=['Smoke'], fx_shared=['Smoke'])
def alpine_chalet(q):
    a = Asset('AlpineChalet', q, seed=17)
    a.box((9.2, 7.2, 0.8), loc=(0, 0, 0.4), col=P['stone'], bevel=0.15)
    a.box((8.2, 6.2, 2.6), loc=(0, 0, 2.1), col=P['wood'])
    nlog = 7 if a.lod0 else 4
    for k in range(nlog):
        z = 0.85 + (k + 0.5) * 2.5 / nlog
        for sy in (-1, 1):
            a.cyl(0.18 if a.lod0 else 0.3, 0.18 if a.lod0 else 0.3, 9.0, loc=(-4.5, sy * 3.12, z), rot=(0, 90, 0), col=P['wood'], segs=8)
        for sx in (-1, 1):
            a.cyl(0.18 if a.lod0 else 0.3, 0.18 if a.lod0 else 0.3, 7.0, loc=(sx * 4.12, -3.5, z + 0.1), rot=(-90, 0, 0), col=P['wood_lt'], segs=8)
    zr = 3.4
    a.prism([(-4.9, 0), (4.9, 0), (0, 3.6)], -4.0, 4.0, loc=(0, 0, zr), rot=(90, 0, 0),
            col=lambda c, n: P['wood_lt'] if abs(n.y) > 0.9 else P['wood_dk'], bevel=0.1)
    a.prism([(-5.3, 0), (5.3, 0), (0, 3.95)], -4.25, 4.25, loc=(0, 0, zr + 0.28), rot=(90, 0, 0),
            col=lambda c, n: P['snow'] if n.z > 0.2 else P['snow_sh'], bevel=0.25)
    a.box((0.5, 0.5, 3.0), loc=(0, -3.18, zr + 1.2), col=P['wood_dk'])             # gable post
    for x in (-2.6, 2.6):
        window(a, (x, -3.3, 1.9), 1.1, 1.0, glow=0.9, frame=P['wood_dk'])
    for x in (-1.4, 1.4):
        window(a, (x, -3.95, zr + 1.0), 0.8, 0.9, glow=0.9, frame=P['wood_dk'])
    a.box((1.2, 0.25, 2.0), loc=(0, -3.3, 1.8), col=P['wood_dk'], bevel=0.06)
    a.box((5.6, 1.3, 0.2), loc=(0, -4.0, zr - 0.1), col=P['wood_lt'], bevel=0.05)
    a.box((5.6, 0.12, 0.8), loc=(0, -4.6, zr + 0.4), col=P['wood'], bevel=0.03)
    if a.lod0:
        for x in (-2.7, -1.35, 0, 1.35, 2.7):
            a.box((0.12, 0.12, 0.8), loc=(x, -4.6, zr + 0.4), col=P['wood_dk'])
    a.box((1.0, 1.0, 4.2), loc=(2.6, 1.5, zr + 2.2), col=P['stone'], bevel=0.1)
    a.box((1.25, 1.25, 0.35), loc=(2.6, 1.5, zr + 4.4), col=P['snow'], bevel=0.12)
    r = a.rng
    for k in range(6 if a.lod0 else 3):
        t = r.uniform(0, 2 * math.pi)
        a.blob(1.6, loc=(5.0 * math.cos(t), 4.0 * math.sin(t), 0), scale=(1.6, 1.1, 0.45), col=P['snow'], sub=2, amp=0.15, seed=k)
    return dict(body=a, fx=dict(Smoke=smoke('Smoke', (2.6, 1.5, zr + 4.6), h=7, w=0.9, col='#e8e8f0')), pivots=dict(Smoke=(2.6, 1.5, zr + 4.6)))


@asset('IceFishingHut', minz=(-0.06, 0.06), course='B', holes=[17], kind='hole set piece', budget=3000, dims=dict(z=(2.4, 4.0)), match=(-30, 18), target='IceFishingHut',
       where='h17 off-line: snowdrifts, laden pines, an ice-fishing hut on the frozen lake (R of the line in the flyover).',
       features=['red-brown plank hut on skids', 'snow-capped gable roof', 'stovepipe', 'glowing window, door', 'fishing hole + stool beside it'])
def ice_fishing_hut(q):
    a = Asset('IceFishingHut', q, seed=171)
    plank = lambda c, n: lin('#8a3a2a') if abs(n.z) < 0.7 else lin('#6e2e22')
    for sx in (-0.8, 0.8):
        a.box((0.18, 2.9, 0.18), loc=(sx, 0, 0.09), col=P['wood_dk'], bevel=0.05)
    a.box((2.1, 2.5, 1.9), loc=(0, 0, 0.18 + 0.95), col=plank, bevel=0.06)
    if a.lod0:
        for k in range(5):
            a.box((2.14, 0.04, 0.05), loc=(0, -1.26, 0.45 + k * 0.36), col=lin('#6e2e22'))
    gable_x(a, 2.8, 2.6, 0.9, (0, 0, 2.08), P['wood_dk'])
    gable_x(a, 3.0, 2.8, 0.98, (0, 0, 2.2), lambda c, n: P['snow'] if n.z > 0.2 else P['snow_sh'], bevel=0.12)
    a.cyl(0.09, 0.09, 1.1, loc=(0.6, 0.6, 2.6), col=P['iron'], segs=8)
    a.cyl(0.16, 0.16, 0.12, loc=(0.6, 0.6, 3.7), col=P['iron'], segs=8)
    window(a, (0.5, -1.29, 1.35), 0.5, 0.45, glow=1.0, frame=P['wood_lt'])
    a.box((0.65, 0.12, 1.35), loc=(-0.45, -1.28, 0.9), col=P['wood_dk'], bevel=0.03)
    a.cyl(0.42, 0.42, 0.04, loc=(-1.7, -1.8, 0.0), col=lin('#1f4f7a'), segs=14)
    a.cyl(0.55, 0.52, 0.06, loc=(-1.7, -1.8, -0.01), col=P['ice'], segs=14)
    a.cyl(0.2, 0.2, 0.42, loc=(-1.1, -2.2, 0), col=P['wood_lt'], segs=8)
    a.cyl(0.03, 0.03, 1.0, loc=(-1.6, -1.9, 0.3), rot=(30, 0, 0), col=P['wood_dk'], segs=6)
    return dict(body=a)


@asset('Waterwheel', minz=(-0.3, 0.06), course='B', holes=[13], kind='hole set piece', budget=5000, dims=dict(z=(4, 6)), match=(35, 12), target=None,
       where='h13 set piece: a waterwheel on a stream beside the winding road (L of the corridor in the flyover).',
       features=['small stone + timber mill house with roof', 'wooden wheel with rims, spokes and paddles (separate part)', 'water chute onto the wheel'],
       animated=[('Wheel', 'hub; spin about local X (Unity -X)')])
def waterwheel(q):
    a = Asset('Waterwheel', q, seed=131)
    a.box((3.6, 3.0, 1.4), loc=(0, 0, 0.7), col=P['stone'], bevel=0.12)
    a.box((3.4, 2.8, 1.8), loc=(0, 0, 2.3), col=WOOD, bevel=0.08)
    gable_x(a, 3.6, 4.0, 1.5, (0, 0, 3.2), P['roof_red'])
    window(a, (0, -1.47, 2.3), 0.7, 0.6, glow=0.5, frame=P['wood_dk'])
    a.box((0.8, 0.2, 1.3), loc=(-1.0, -1.45, 0.75), col=P['wood_dk'], bevel=0.04)
    a.box((0.5, 0.5, 0.5), loc=(2.0, 0, 1.6), col=P['wood_dk'], bevel=0.05)          # axle bearing
    a.box((0.7, 3.0, 0.35), loc=(2.6, 1.9, 3.6), rot=(8, 0, 0), col=P['wood'], bevel=0.04)  # chute
    hub = (2.6, 0, 1.6)
    w = Asset('Waterwheel_Wheel', q, seed=132)
    R, half = 1.65, 0.38
    nseg = 24 if w.lod0 else 12
    for sx in (-half, half):
        ring = [(hub[0] + sx, R * math.cos(2 * math.pi * i / nseg), hub[2] + R * math.sin(2 * math.pi * i / nseg)) for i in range(nseg)]
        w.sweep(ring, [(-.06, -.09), (.06, -.09), (.06, .09), (-.06, .09)], col=P['wood_dk'], closed=True, up=(1, 0, 0))
    npad = 12 if w.lod0 else 8
    for i in range(npad):
        t = 2 * math.pi * i / npad
        w.box((half * 2 + 0.1, 0.06, 0.5), loc=(hub[0], (R - 0.15) * math.cos(t), hub[2] + (R - 0.15) * math.sin(t)),
              rot=(math.degrees(t) + 90, 0, 0), col=P['wood'])
    for i in range(6 if w.lod0 else 4):
        t = math.pi * i / (6 if w.lod0 else 4)
        w.box((0.12, 2 * R, 0.1), loc=hub, rot=(math.degrees(t), 0, 0), col=P['wood_dk'])
    w.cyl(0.22, 0.22, half * 2 + 0.4, loc=hub, rot=(0, 90, 0), col=P['iron'], segs=10, base=False)
    return dict(body=a, parts=dict(Wheel=w), pivots=dict(Wheel=hub))


@asset('MesaArch', course='B', holes=[18], kind='hole set piece', budget=6000, dims=dict(x=(14, 24), z=(9, 13)), minz=(-0.2, 0.06), match=(-15, 6), target='MesaArch',
       where='h18 FWD: far red mesa with the green on top, a desert rock arch (on the mesa beyond/right of the green).',
       features=['thick red-sandstone arch, legs flaring to the ground', 'layered strata bands', 'boulder feet', 'flat-ish top with desert scrub tufts'])
def mesa_arch(q):
    a = Asset('MesaArch', q, seed=181)
    strata = lambda c, n: mix(P['sandstone'], P['sandstone_lt'] if int(c.z / 1.1) % 2 else P['sandstone_dk'], 0.5 + 0.5 * math.sin(c.z * math.pi / 1.1)) if n.z < 0.75 else P['sandstone_lt']
    m = 64 if a.lod0 else 36
    path = [(7.2 * math.cos(math.pi * (1 - i / m)), 0, 9.6 * math.sin(math.pi * (1 - i / m)) ** 0.85) for i in range(m + 1)]
    sq = lambda v: math.copysign(abs(v) ** 0.55, v)     # superellipse: blocky rock section
    nk = 16 if a.lod0 else 10
    sec = [(1.8 * sq(math.cos(2 * math.pi * k / nk)), 2.7 * sq(math.sin(2 * math.pi * k / nk))) for k in range(nk)]
    a.sweep(path, sec, col=strata, up=(0, 1, 0), vcol=True, scale=lambda i, t: (1.0 + 1.3 * abs(2 * t - 1) ** 3, 1.0 + 0.25 * abs(2 * t - 1) ** 2))
    for sx in (-1, 1):
        a.blob(2.8, loc=(sx * 7.4, 0, 0), scale=(1.3, 1.1, 0.9), col=strata, sub=2, amp=0.25, seed=sx + 5)
        a.blob(1.4, loc=(sx * 9.6, -1.6, 0), scale=(1.2, 1, 0.7), col=strata, sub=1, amp=0.3, seed=sx + 9)
    if a.lod0:
        for x in (-2.5, 0.5, 3.0):
            a.blob(0.6, loc=(x, 0, 9.0 + 0.6 * math.cos(x / 5)), scale=(1.2, 1.2, 0.6), col=P['cactus'], sub=1, amp=0.3, seed=int(x * 3))
    return dict(body=a)


@asset('WaterTower', course='B', holes=[18], kind='hole set piece', budget=5000, dims=dict(z=(8, 11)), match=(20, 5), target='WaterTower',
       where='h18 BACK: the tee mesa with a desert-ranch fence and a water tower (tee side, left).',
       features=['wooden barrel tank with dark iron hoops', 'conical roof with finial', 'four-leg trestle with X braces', 'ladder up to the tank'])
def water_tower(q):
    a = Asset('WaterTower', q, seed=182)
    zt = 5.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            a.box((0.5, 0.5, 0.35), loc=(sx * 1.6, sy * 1.6, 0.17), col=P['stone'], bevel=0.08)
            a.box((0.28, 0.28, zt + 0.1), loc=(sx * 1.55 * 0.92, sy * 1.55 * 0.92, (zt + 0.1) / 2), rot=(sy * 3, -sx * 3, 0), col=P['wood_dk'], bevel=0.04)
    for z0, z1 in ((0.6, 2.8), (2.8, 4.9)):
        for side in range(4):
            ang = side * math.pi / 2
            for k in (-1, 1):
                p0 = Vector((k * 1.45, -1.45, z0)); p1 = Vector((-k * 1.45, -1.45, z1))
                rot = lambda p: (p.x * math.cos(ang) - p.y * math.sin(ang), p.x * math.sin(ang) + p.y * math.cos(ang), p.z)
                log(a, rot(p0), rot(p1), 0.07, P['wood'], segs=6)
    a.box((3.6, 3.6, 0.25), loc=(0, 0, zt + 0.12), col=P['wood'], bevel=0.05)
    staves = lambda c, n: P['wood'] if int((math.atan2(c.y, c.x) + math.pi) / (2 * math.pi) * 24) % 2 else P['wood_lt']
    a.revolve([(0, zt + 0.25), (1.7, zt + 0.25), (1.78, zt + 1.2), (1.8, zt + 2.0), (1.76, zt + 2.9), (0, zt + 2.9)], col=staves, segs=24)
    for z in (zt + 0.6, zt + 1.5, zt + 2.4):
        a.cyl(1.84, 1.84, 0.1, loc=(0, 0, z), col=P['iron'], segs=24)
    a.revolve([(0, zt + 2.85), (2.0, zt + 2.85), (1.9, zt + 3.0), (0.25, zt + 4.2), (0, zt + 4.25)], col=P['wood_dk'], segs=24)
    a.sphere(0.15, loc=(0, 0, zt + 4.3), col=P['iron'], segs=8)
    for sx in (-0.25, 0.25):
        a.box((0.06, 0.06, zt + 0.25), loc=(sx, -1.95, (zt + 0.25) / 2), col=P['wood_dk'])
    for k in range(10 if a.lod0 else 5):
        a.box((0.5, 0.05, 0.05), loc=(0, -1.95, 0.4 + k * zt / (10 if a.lod0 else 5)), col=P['wood_dk'])
    return dict(body=a)


@asset('StoneGate', course='B', holes=[19], kind='hole set piece', budget=6000, dims=dict(z=(4.5, 6.5)), match=(20, 6), target='StoneGate',
       where='h19 BACK: the jungle tee, palms, a carved stone gate (frames the tee; pillars seen at the edges of the tee view).',
       features=['two stacked-block pillars', 'carved tiki faces on the top blocks', 'heavy lintel with carved band', 'vines and leaf clumps'])
def stone_gate(q):
    a = Asset('StoneGate', q, seed=191)
    st = lambda c, n: P['jungle_moss'] if n.z > 0.7 else lin('#9a8f72')
    span = 3.4
    for sx in (-1, 1):
        x = sx * (span / 2 + 0.65)
        a.box((1.6, 1.6, 0.5), loc=(x, 0, 0.25), col=P['stone'], bevel=0.12)
        for k, (h, dx) in enumerate(((1.4, 0.05), (1.4, -0.06), (1.5, 0.03))):
            a.box((1.25, 1.25, h - 0.06), loc=(x + dx * sx, 0, 0.5 + 1.42 * k + h / 2), col=st, bevel=0.14)
        zf = 0.5 + 1.42 * 2 + 0.75
        if a.lod0:   # tiki face
            a.box((1.1, 0.2, 0.22), loc=(x, -0.68, zf + 0.35), col=P['stone'], bevel=0.05)
            for ex in (-0.28, 0.28):
                a.box((0.26, 0.12, 0.2), loc=(x + ex, -0.66, zf + 0.12), col=P['purple_dk'], bevel=0.04)
            a.box((0.24, 0.3, 0.5), loc=(x, -0.72, zf - 0.15), col=P['jungle_stone'], bevel=0.08)
            a.box((0.7, 0.14, 0.18), loc=(x, -0.66, zf - 0.55), col=P['purple_dk'], bevel=0.04)
        for k in range(3):
            a.box((0.14, 0.14, 0.7 + 0.3 * k), loc=(x + sx * 0.66, -0.4 + 0.4 * k, 1.2 + 0.8 * k), col=P['leaf'], bevel=0.04)
        if not a.lod0:
            a.box((1.1, 0.2, 0.22), loc=(x, -0.68, zf + 0.35), col=P['stone'])
            for ex in (-0.28, 0.28):
                a.box((0.26, 0.12, 0.2), loc=(x + ex, -0.66, zf + 0.12), col=P['purple_dk'])
            a.box((0.24, 0.3, 0.5), loc=(x, -0.72, zf - 0.15), col=P['jungle_stone'])
            a.box((0.7, 0.14, 0.18), loc=(x, -0.66, zf - 0.55), col=P['purple_dk'])
    zl = 0.5 + 1.42 * 3 + 0.05
    a.box((span + 3.4, 1.5, 1.0), loc=(0, 0, zl + 0.5), col=st, bevel=0.18)
    a.box((span + 2.6, 1.56, 0.25), loc=(0, 0, zl + 0.45), col=P['stone'], bevel=0.05)
    a.box((1.2, 1.3, 0.5), loc=(0, 0, zl + 1.25), col=st, bevel=0.12)
    r = a.rng
    for k in range(7):
        a.blob(0.55, loc=(r.uniform(-3, 3), r.uniform(-0.6, 0.6), zl + 0.95), scale=(1.4, 1.2, 0.6), col=P['leaf'], sub=1, amp=0.3, seed=k)
    return dict(body=a)


@asset('StiltHut', course='B', holes=[19], kind='hole set piece', budget=6000, dims=dict(z=(7, 10)), match=(15, 4), target='StiltHut',
       pivot='waterline', where='h19 R: jungle lagoon, stilt huts (L and R of the tee view over the water). Pivot at the waterline; stilts go 1.5 m below.',
       features=['thatched two-tier pyramid roof', 'timber hut on a railed deck', 'stilt grid into the water', 'ladder + short pier'])
def stilt_hut(q):
    a = Asset('StiltHut', q, seed=192)
    zd = 2.3
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            a.cyl(0.13, 0.13, zd + 1.5, loc=(i * 2.0, j * 2.0, -1.5), col=P['wood_dk'], segs=8)
    for j in range(1, 4):
        a.cyl(0.11, 0.11, zd + 1.5, loc=(-0.55 if j % 2 else 0.55, 2.0 + j * 1.3, -1.5), col=P['wood_dk'], segs=6)
    a.box((4.6, 4.6, 0.3), loc=(0, 0, zd), col=WOOD, bevel=0.05)
    a.box((1.3, 4.2, 0.2), loc=(0, 4.2, zd - 0.05), col=WOOD, bevel=0.04)
    a.box((3.2, 3.2, 2.0), loc=(0, 0, zd + 1.15), col=lambda c, n: P['wood_lt'] if abs(n.z) < 0.7 else P['wood'], bevel=0.06)
    a.box((0.9, 0.15, 1.6), loc=(0, -1.62, zd + 0.95), col=P['wood_dk'], bevel=0.03)
    window(a, (1.62, 0, zd + 1.3), 0.7, 0.6, normal='+x', glow=0.6, frame=P['wood_dk'])
    th = lambda c, n: P['thatch'] if n.z > -0.3 else P['thatch_dk']
    a.revolve([(0, zd + 1.9), (3.9, zd + 1.9), (3.8, zd + 2.2), (2.6, zd + 3.0), (2.7, zd + 3.15), (1.5, zd + 4.1), (1.55, zd + 4.25), (0.3, zd + 5.3), (0, zd + 5.4)],
              col=th, segs=16)
    for i in (-1, 1):
        for j in (-1, 0, 1):
            log(a, (i * 2.0, j * 2.0 - 0.0, -0.2), (i * 2.0, j * 2.0 + (2.0 if j < 1 else -2.0), zd - 0.2), 0.06, P['wood'], segs=6)
    if a.lod0:
        for sx, sy, lx, ly in ((0, -2.25, 4.5, 0.08), (-2.25, 0, 0.08, 4.5), (2.25, 0, 0.08, 4.5)):
            a.box((lx, ly, 0.08), loc=(sx, sy, zd + 0.9), col=P['wood_dk'])
        for k in range(-2, 3):
            for sx, sy in ((k * 1.1, -2.25), (-2.25, k * 1.1), (2.25, k * 1.1)):
                a.box((0.09, 0.09, 0.9), loc=(sx, sy, zd + 0.5), col=P['wood_dk'])
        for k in range(6):
            a.box((0.5, 0.05, 0.05), loc=(1.6, -2.4, -0.2 + k * 0.45), col=P['wood_dk'])
    return dict(body=a)


@asset('Windmill', course='B', holes=[20], kind='hole set piece (hero)', budget=8000, dims=dict(z=(15, 26)), match=(-20, 6), target='Windmill',
       where='h20 FWD: big Dutch windmill turning beside the green; a second, smaller copy (scale 0.6) on the far side of the tulip fields.',
       features=['brick octagonal base + red octagonal tapered body', 'stage gallery with railing', 'dark rounded cap', 'white-framed windows + door',
                 'four lattice sails with cloth panels (separate part, pivot at the hub)'],
       animated=[('Sails', 'hub; spin about local Y (Unity Z, the sails face -Y in Blender)')])
def windmill(q):
    a = Asset('Windmill', q, seed=201)
    a.cyl(4.4, 4.2, 3.2, col=lambda c, n: P['brick'] if (int(c.z * 3) % 2 or abs(n.z) > 0.7) else P['brick_dk'], segs=8, phase=math.pi / 8, bevel=0.12)
    body = lambda c, n: P['red'] if abs(n.z) < 0.7 else P['red_dk']
    a.revolve([(0, 3.2), (3.7, 3.2), (3.4, 6.0), (2.9, 10.0), (2.45, 13.4), (0, 13.4)], col=body, segs=8, phase=math.pi / 8, smooth=False)
    if a.lod0:   # white corner trims on the octagon
        for i in range(8):
            t = i * math.pi / 4 + math.pi / 8
            p0 = Vector((3.72 * math.cos(t), 3.72 * math.sin(t), 3.2)); p1 = Vector((2.47 * math.cos(t), 2.47 * math.sin(t), 13.4))
            log(a, tuple(p0), tuple(p1), 0.07, P['white'], segs=4)
    a.cyl(5.2, 5.2, 0.28, loc=(0, 0, 5.0), col=P['wood_lt'], segs=8, phase=math.pi / 8, bevel=0.06)
    if a.lod0:
        for i in range(16):
            t = i * math.pi / 8
            a.box((0.08, 0.08, 1.0), loc=(5.0 * math.cos(t), 5.0 * math.sin(t), 5.75), col=P['white'])
        for i in range(8):
            t0 = i * math.pi / 4 + math.pi / 8; t1 = t0 + math.pi / 4
            p0 = (5.05 * math.cos(t0), 5.05 * math.sin(t0), 6.25); p1 = (5.05 * math.cos(t1), 5.05 * math.sin(t1), 6.25)
            log(a, p0, p1, 0.05, P['white'], segs=4)
    a.revolve([(0, 13.3), (2.8, 13.3), (2.9, 13.8), (2.6, 15.0), (1.8, 16.0), (0.8, 16.5), (0, 16.6)], col=lin('#4a3a34'), segs=16)
    for z, w in ((8.0, 1.0), (11.2, 0.85)):
        window(a, (0, -(3.4 - (z - 6) * 0.122) - 0.08, z), w, w * 1.2, glow=0.25, glass=P['glass'])
    a.box((1.3, 0.3, 2.2), loc=(0, -4.3, 1.1), col=P['wood_dk'], bevel=0.06)
    window(a, (2.4, -3.75, 1.9), 0.6, 0.6, glow=0.4, glass=P['glass'])
    hub = (0, -3.15, 14.3)
    a.box((0.55, 1.4, 0.55), loc=(0, -2.5, 14.3), col=P['wood_dk'], bevel=0.08)
    s = Asset('Windmill_Sails', q, seed=202)
    s.cyl(0.42, 0.42, 0.6, loc=(hub[0], hub[1] - 0.2, hub[2]), rot=(90, 0, 0), col=P['wood_dk'], segs=12, base=False)
    for k in range(4):
        ang = k * math.pi / 2 + math.radians(15)
        ca, sa = math.cos(ang), math.sin(ang)
        R0, R1 = 0.4, 9.2
        pt = lambda r, o: (hub[0] + r * ca - o * sa, hub[1] - 0.45, hub[2] + r * sa + o * ca)
        s.box((R1, 0.22, 0.22), loc=pt((R0 + R1) / 2, 0), rot=(0, -math.degrees(ang), 0), col=P['wood'])
        s.box((R1 - 2.0, 0.08, 1.75), loc=pt((R1 + 2.0) / 2, 1.05), rot=(0, -math.degrees(ang), 0), col=P['cream'])
        if s.lod0:
            for o in (0.18, 1.95):
                s.box((R1 - 2.0, 0.12, 0.09), loc=(pt((R1 + 2.0) / 2, o)[0], hub[1] - 0.55, pt((R1 + 2.0) / 2, o)[2]),
                      rot=(0, -math.degrees(ang), 0), col=P['wood_lt'])
            for j in range(8):
                r = 2.0 + (R1 - 2.0) * (j + 0.5) / 8
                s.box((0.08, 0.12, 1.9), loc=(pt(r, 1.05)[0], hub[1] - 0.55, pt(r, 1.05)[2]), rot=(0, -math.degrees(ang), 0), col=P['wood_lt'])
    return dict(body=a, parts=dict(Sails=s), pivots=dict(Sails=hub))


@asset('CanalBridge', course='B', holes=[20], kind='hole set piece', budget=4000, dims=dict(x=(11, 13)), match=(25, 8), target='CanalBridge',
       pivot='waterline', where='h20 set piece: canals with small brick bridges (R of the line beyond the canal lock; tee BACK by the farmhouse).',
       features=['humped brick bridge with a round arch', 'darker brick voussoirs round the arch', 'parapets with cream coping', 'stone path deck'])
def canal_bridge(q):
    a = Asset('CanalBridge', q, seed=203)
    na = 14 if a.lod0 else 7
    arch = [(2.4 * math.cos(math.pi * (1 - i / na)), 2.4 * math.sin(math.pi * (1 - i / na))) for i in range(na + 1)]
    poly = [(-6.2, -1.0), (-2.4, -1.0)] + arch + [(2.4, -1.0), (6.2, -1.0), (6.2, 0.9), (3.2, 2.9), (-3.2, 2.9), (-6.2, 0.9)]
    col = lambda c, n: P['sand_wet'] if n.z > 0.7 and c.z > 0.5 else (P['brick_dk'] if math.hypot(c.x, c.z) < 3.0 and c.z > -0.2 else P['brick'])
    a.prism(poly, -1.5, 1.5, rot=(90, 0, 0), col=col, bevel=0.06)
    top = [(-6.2, 0.9), (-3.2, 2.9), (3.2, 2.9), (6.2, 0.9)]
    par = top + [(x, z + 0.55) for x, z in reversed(top)]
    for sy in (-1, 1):
        a.prism(par, -0.17, 0.17, loc=(0, sy * 1.45, 0), rot=(90, 0, 0), col=P['brick'], bevel=0.04)
        cop = [(p[0] * 1.0, p[1] + 0.55) for p in top]
        a.sweep([(x, sy * 1.45, z + 0.06) for x, z in cop], [(-.24, -.08), (.24, -.08), (.24, .08), (-.24, .08)], col=P['cream'])
    ring = [(2.55 * math.cos(math.pi * (1 - i / na)), 0, 2.55 * math.sin(math.pi * (1 - i / na))) for i in range(na + 1)]
    for sy in (-1, 1):
        a.sweep([(x, sy * 1.52, z) for x, _, z in ring], [(-.3, -.08), (.3, -.08), (.3, .08), (-.3, .08)], col=P['brick_dk'], up=(0, 1, 0))
        if a.lod0:
            for x in (-5.2, -3.6, -1.8, 0, 1.8, 3.6, 5.2):
                zt = (0.9 + (2.9 - 0.9) * min(1, (6.2 - abs(x)) / 3.0)) + 0.55
                a.box((0.12, 0.12, 0.6), loc=(x, sy * 1.45, zt + 0.42), col=P['white'])
            a.sweep([(x, sy * 1.45, zt + 1.12) for x, zt in ((-6.2, 1.45), (-3.2, 3.45), (3.2, 3.45), (6.2, 1.45))],
                    [(-.06, -.06), (.06, -.06), (.06, .06), (-.06, .06)], col=P['white'])
    return dict(body=a)


@asset('Farmhouse', course='B', holes=[20], kind='hole set piece', budget=6000, dims=dict(z=(7, 10)), match=(30, 6), target='Farmhouse',
       where='h20 BACK: red-brick farmhouse and a canal lock by the tee (left of the tee view).',
       features=['red brick body', 'steep red tile gable roof with white barge trim', 'white-framed windows with glowing panes',
                 'green door with step', 'brick chimney'])
def farmhouse(q):
    a = Asset('Farmhouse', q, seed=204)
    br = lambda c, n: P['brick'] if (int(c.z * 4) % 3) else P['brick_dk']
    a.box((8.0, 6.0, 3.6), loc=(0, 0, 1.8), col=br, bevel=0.1)
    gable_y(a, 6.6, 8.6, 4.4, (0, 0, 3.6), lambda c, n: br(c, n) if abs(n.y) > 0.9 else P['red_dk'])
    for sx in (-1, 1):            # white barge boards
        for sy in (-1, 1):
            p0 = (sx * 3.35, sy * 4.32, 3.55); p1 = (0, sy * 4.32, 8.05)
            log(a, p0, p1, 0.1, P['white'], segs=4)
    a.box((0.8, 0.8, 2.2), loc=(1.6, 1.5, 7.4), col=P['brick_dk'], bevel=0.06)
    gl = lin('#5a7a9a')
    for x in (-2.6, 2.6):
        window(a, (x, -3.06, 1.9), 1.0, 1.3, glow=0.1, glass=gl)
    window(a, (0, -4.36, 5.5), 1.0, 1.1, glow=0.1, glass=gl)
    for y in (-1.5, 1.5):
        window(a, (4.06, y, 1.9), 1.0, 1.3, normal='+x', glow=0.1, glass=gl)
    for x in (-2.6, 2.6):         # flower boxes under the front windows
        a.box((1.2, 0.35, 0.25), loc=(x, -3.2, 1.1), col=P['wood'], bevel=0.04)
        if a.lod0:
            for k in range(5):
                a.sphere(0.13, loc=(x - 0.45 + 0.225 * k, -3.25, 1.33), col=(P['tulip_r'], P['tulip_y'], P['tulip_p'])[k % 3], segs=8)
        else:
            a.box((1.1, 0.3, 0.2), loc=(x, -3.25, 1.3), col=P['tulip_r'], bevel=0.05)
    a.box((1.1, 0.2, 2.1), loc=(0, -3.08, 1.05), col=lin('#2f7a4a'), bevel=0.05)
    a.box((1.8, 0.8, 0.2), loc=(0, -3.4, 0.1), col=P['stone'], bevel=0.04)
    return dict(body=a)


# ======================================================================= course A
@asset('StoneGazebo', course='A', holes=[8, 15], kind='hole set piece', budget=6000, dims=dict(z=(5, 8)), match=(0, 10), target='StoneGazebo',
       where='h08 BACK: the tee terrace with a stone gazebo (end of the knife-edge path); h15 FWD: the little temple-gazebo on the three-tier island green.',
       features=['three round stone steps', 'eight cream columns with bases + capitals', 'ring entablature', 'terracotta dome with finial'])
def stone_gazebo(q):
    a = Asset('StoneGazebo', q, seed=81)
    for k, r in enumerate((3.5, 3.15, 2.8)):
        a.cyl(r, r, 0.26, loc=(0, 0, 0.26 * k), col=P['limestone'] if k % 2 else P['cream'], segs=32, bevel=0.04)
    z0 = 0.78
    for i in range(8):
        t = 2 * math.pi * i / 8 + math.pi / 8
        x, y = 2.3 * math.cos(t), 2.3 * math.sin(t)
        a.box((0.55, 0.55, 0.25), loc=(x, y, z0 + 0.12), rot=(0, 0, math.degrees(t)), col=P['cream'], bevel=0.04)
        a.cyl(0.21, 0.18, 2.9, loc=(x, y, z0 + 0.25), col=P['white'], segs=12)
        a.box((0.5, 0.5, 0.2), loc=(x, y, z0 + 3.25), rot=(0, 0, math.degrees(t)), col=P['cream'], bevel=0.04)
    a.cyl(2.75, 2.75, 0.55, loc=(0, 0, z0 + 3.35), col=P['cream'], segs=32, bevel=0.06)
    a.cyl(2.9, 2.9, 0.14, loc=(0, 0, z0 + 3.88), col=P['limestone'], segs=32, bevel=0.03)
    zd = z0 + 4.0
    a.revolve([(2.65, zd), (2.55, zd + 0.6), (2.15, zd + 1.4), (1.4, zd + 2.0), (0.6, zd + 2.3), (0, zd + 2.36)],
              col=lambda c, n: P['terracotta'], segs=32)
    if a.lod0:
        for i in range(8):
            t = 2 * math.pi * i / 8
            arc = [(rr * math.cos(t), rr * math.sin(t), zz + 0.04) for rr, zz in ((2.66, zd), (2.57, zd + 0.6), (2.17, zd + 1.4), (1.42, zd + 2.0), (0.62, zd + 2.3))]
            a.sweep(arc, [(-.06, 0), (.06, 0), (.06, .08), (-.06, .08)], col=P['cream'])
    a.cyl(0.18, 0.12, 0.35, loc=(0, 0, zd + 2.3), col=P['cream'], segs=10)
    a.sphere(0.2, loc=(0, 0, zd + 2.8), col=P['cream'], segs=10)
    return dict(body=a)


@asset('Balustrade', course='A', holes=[8, 15], kind='hole set piece (tileable)', budget=3000, dims=dict(x=(2.9, 3.6)), match=(25, 8), target='Balustrade',
       where='h15 BACK: tee platform with a stone balustrade and planters (both sides of the tee); also h08 tee terrace. Tiles every 3 m along X; '
             'the post sits at the -X end, so close a run with one extra post (scale X of this segment to 0.15 for a lone post).',
       features=['plinth + moulded top rail', 'turned vase balusters', 'square end post with cap'])
def balustrade(q):
    a = Asset('Balustrade', q, seed=82)
    a.box((3.0, 0.5, 0.3), loc=(0, 0, 0.15), col=P['limestone'], bevel=0.05)
    a.box((3.0, 0.48, 0.16), loc=(0, 0, 1.02), col=P['cream'], bevel=0.05)
    a.box((2.9, 0.4, 0.08), loc=(0, 0, 0.94), col=P['limestone'], bevel=0.02)
    nb = 6
    for k in range(nb):
        x = -1.5 + 0.45 + 2.55 * (k + 0.5) / nb + 0.0
        prof = [(0, 0.3), (0.11, 0.3), (0.13, 0.36), (0.07, 0.48), (0.14, 0.66), (0.07, 0.84), (0.11, 0.9), (0, 0.9)]
        a.revolve(prof if a.lod0 else [prof[0], prof[1], prof[3], prof[4], prof[5], prof[7]], loc=(x, 0, 0), col=P['white'], segs=12 if a.lod0 else 6)
    a.box((0.48, 0.6, 1.15), loc=(-1.5 + 0.24, 0, 0.58), col=P['cream'], bevel=0.05)
    a.box((0.6, 0.72, 0.14), loc=(-1.5 + 0.24, 0, 1.2), col=P['limestone'], bevel=0.04)
    a.sphere(0.16, loc=(-1.5 + 0.24, 0, 1.38), col=P['cream'], segs=10)
    return dict(body=a)


@asset('Planter', course='A', holes=[8, 15], kind='hole set piece', budget=3000, dims=dict(z=(1.4, 2.2)), match=(20, 8), target='Balustrade',
       where='h15 BACK: planters on the tee balustrade posts / at its ends (h15 tee: flower urns left and right).',
       features=['square plinth', 'cream stone urn', 'flower clump: pink, white, yellow, violet over a leafy mound'])
def planter(q):
    a = Asset('Planter', q, seed=83)
    a.box((0.7, 0.7, 0.4), loc=(0, 0, 0.2), col=P['limestone'], bevel=0.05)
    a.revolve([(0, 0.4), (0.3, 0.4), (0.24, 0.5), (0.18, 0.62), (0.26, 0.72), (0.46, 0.92), (0.58, 1.12), (0.56, 1.22), (0, 1.22)],
              col=P['cream'], segs=20)
    a.blob(0.5, loc=(0, 0, 1.1), scale=(1, 1, 0.5), col=P['leaf'], sub=2, amp=0.35, seed=1)
    r = a.rng
    cols = [P['blossom'], P['flower_w'], P['tulip_y'], lin('#9a6ad0'), P['tulip_p']]
    for k in range(18 if a.lod0 else 12):
        t = r.uniform(0, 2 * math.pi); d = 0.55 * math.sqrt(r.uniform(0, 1))
        a.sphere(0.16 if a.lod0 else 0.22, loc=(d * math.cos(t), d * math.sin(t), 1.3 + 0.28 * (1 - d / 0.55)), col=cols[k % len(cols)],
                 segs=10 if a.lod0 else 6, rings=6 if a.lod0 else 4)
    if a.lod0:
        for k in range(8):
            t = 2 * math.pi * k / 8
            a.blob(0.16, loc=(0.6 * math.cos(t), 0.6 * math.sin(t), 1.0), scale=(1.4, 0.7, 0.5), rot=(0, 0, math.degrees(t)), col=P['leaf_lt'], sub=1, amp=0.2, seed=k)
    return dict(body=a)


# ======================================================================= course C
@asset('ToriiGate', course='C', holes=[10], kind='hole set piece', budget=4000, dims=dict(z=(5.5, 7.5)), match=(15, 6), target=None,
       where='h10 BACK: the tee on a basalt shelf with a stone torii-style gate and lanterns (frames the tee; seen in green-back views).',
       features=['two tapered basalt pillars on base stones', 'kasagi top beam curving up at the ends', 'nuki tie beam', 'glowing ember plaque'])
def torii_gate(q):
    a = Asset('ToriiGate', q, seed=101)
    for sx in (-1, 1):
        a.cyl(0.62, 0.55, 0.5, loc=(sx * 2.3, 0, 0), col=P['basalt_lt'], segs=8, bevel=0.06)
        a.cyl(0.36, 0.3, 5.3, loc=(sx * 2.3, 0, 0.45), col=P['basalt'], segs=16)
    a.box((6.2, 0.38, 0.45), loc=(0, 0, 4.25), col=P['basalt_lt'], bevel=0.06)
    m = 16 if a.lod0 else 8
    path = [(-3.7 + 7.4 * i / m, 0, 5.45 + 0.42 * (abs(-3.7 + 7.4 * i / m) / 3.7) ** 3) for i in range(m + 1)]
    a.sweep(path, [(-0.42, -0.22), (0.42, -0.22), (0.5, 0.22), (-0.5, 0.22)], col=P['obsidian'],
            scale=lambda i, t: (1.0, 1.0 + 0.4 * abs(2 * t - 1) ** 2))
    a.box((5.6, 0.5, 0.3), loc=(0, 0, 5.15), col=P['basalt'], bevel=0.05)
    a.box((0.32, 0.32, 0.95), loc=(0, 0, 4.7), col=P['basalt'], bevel=0.04)
    a.box((0.9, 0.12, 0.62), loc=(0, -0.22, 4.72), col=P['ember'], glow=0.8, bevel=0.03)
    return dict(body=a)


@asset('StoneLantern', course='C', holes=[10, 16], kind='hole set piece', budget=2000, dims=dict(z=(1.6, 2.4)), match=(10, 4), target='StoneLantern',
       where='h10 BACK: lanterns on the basalt tee shelf (pairs either side of the torii); reusable along the h16 rim path.',
       features=['hex basalt base + post', 'light box with glowing panes', 'wide pyramid roof', 'finial'])
def stone_lantern(q):
    a = Asset('StoneLantern', q, seed=102)
    a.cyl(0.42, 0.4, 0.22, col=P['basalt_lt'], segs=6, bevel=0.03)
    a.cyl(0.14, 0.14, 0.8, loc=(0, 0, 0.22), col=P['basalt'], segs=6)
    a.cyl(0.4, 0.36, 0.15, loc=(0, 0, 1.02), col=P['basalt_lt'], segs=6, bevel=0.03)
    a.box((0.42, 0.42, 0.42), loc=(0, 0, 1.38), col=lin('#ffb347'), glow=0.8)
    for sx in (-1, 1):
        for sy in (-1, 1):
            a.box((0.1, 0.1, 0.46), loc=(sx * 0.24, sy * 0.24, 1.38), col=P['basalt'], bevel=0.02)
    a.sphere(0.09, loc=(0, 0, 2.08), col=P['basalt_lt'], segs=10)
    hip(a, 0.5, 0.42, (0, 0, 1.6), P['basalt'])
    a.box((0.9, 0.9, 0.08), loc=(0, 0, 1.6), col=P['basalt'], bevel=0.03)
    return dict(body=a)


@asset('RangerHut', course='C', holes=[16], kind='hole set piece', budget=6000, dims=dict(z=(3.8, 5.5)), match=(35, 6), target='RangerHut',
       where='h16 BACK: tee ledge with a ranger hut and a lava-glass sign (left of the tee).',
       features=['plank hut on a basalt plinth', 'layered thatch hip roof', 'porch with posts', 'warm glowing window, door',
                 'lava-glass sign: dark board with glowing orange inset on posts'])
def ranger_hut(q):
    a = Asset('RangerHut', q, seed=161)
    a.box((5.2, 4.2, 0.45), loc=(0, 0, 0.22), col=P['basalt_lt'], bevel=0.1)
    a.box((4.2, 3.4, 2.3), loc=(0, 0.2, 1.6), col=lambda c, n: P['wood'] if abs(n.z) < 0.7 else P['wood_dk'], bevel=0.06)
    if a.lod0:
        for k in range(6):
            a.box((4.25, 3.45, 0.05), loc=(0, 0.2, 0.7 + k * 0.38), col=P['wood_dk'])
    th = lambda c, n: P['thatch'] if n.z > -0.3 else P['thatch_dk']
    for k, (hw, h, z) in enumerate(((3.2, 1.0, 2.7), (2.6, 0.95, 3.25), (1.9, 1.0, 3.8))):
        hip(a, hw, h + 0.4, (0, 0.2, z), th)
    for x in (-1.9, 1.9):
        a.box((0.16, 0.16, 2.3), loc=(x, -1.85, 1.6), col=P['wood_dk'])
    a.box((1.0, 0.15, 1.9), loc=(-0.8, -1.52, 1.4), col=P['wood_dk'], bevel=0.04)
    window(a, (1.0, -1.55, 1.65), 0.9, 0.7, glow=1.0, frame=P['wood_dk'])
    for x in (2.9, 4.1):
        a.box((0.14, 0.14, 1.5), loc=(x, -2.4, 0.75), col=P['wood_dk'])
    a.box((1.6, 0.14, 0.8), loc=(3.5, -2.45, 1.3), col=P['obsidian'], bevel=0.04)
    a.box((1.2, 0.08, 0.45), loc=(3.5, -2.53, 1.3), col=P['lava'], glow=0.9, bevel=0.02)
    return dict(body=a)


def arch(a, span, height, sec_w, sec_d, col, wob=0.0, seed=0, glow_crack=False):
    m = 30 if a.lod0 else 14
    path = []
    for i in range(m + 1):
        t = math.pi * (1 - i / m)
        w = wob * noise.noise(Vector((i * 0.35, seed, 0))) * math.sin(t)     # no wobble at the feet: they stay on z 0
        path.append((span / 2 * math.cos(t) + w, w * 0.5, height * math.sin(t) ** 0.8 + w))
    k = 10 if a.lod0 else 6
    sec = [(sec_w * math.cos(2 * math.pi * j / k) * (1 + 0.12 * ((j * 7 + seed) % 3 - 1)), sec_d * math.sin(2 * math.pi * j / k)) for j in range(k)]
    a.sweep(path, sec, col=col, up=(0, 1, 0), scale=lambda i, t: (1.0 + 1.1 * abs(2 * t - 1) ** 3, 1.0 + 0.2 * abs(2 * t - 1) ** 2))
    return path


@asset('ObsidianArch', course='C', holes=[22], kind='hole set piece', budget=6000, dims=dict(x=(10, 17), z=(6, 9)), minz=(-0.2, 0.06), match=(-15, 6), target='ObsidianArch',
       where="h22 BACK: the causeway's start with an obsidian archway (the tee view sees it on the left; frames green-back views).",
       features=['chunky irregular black-glass arch', 'glowing ember crack lines on the face', 'boulder feet', 'glowing seam at the base'])
def obsidian_arch(q):
    a = Asset('ObsidianArch', q, seed=221)
    col = lambda c, n: P['obsidian'] if n.z < 0.6 else P['basalt']
    path = arch(a, 10.0, 7.0, 1.6, 2.2, col, wob=0.6, seed=3)
    for sx in (-1, 1):
        a.blob(2.2, loc=(sx * 5.2, 0, 0), scale=(1.3, 1.1, 0.8), col=col, sub=2, amp=0.25, seed=sx + 2)
    for side, off in ((-1, -2.25), (1, 2.25)):
        for j in range(4 if a.lod0 else 2):
            sub = path[2 + j * 7: 2 + j * 7 + 8: 2]
            pts = [(x + 0.1 * math.sin(i * 1.7 + j), off * (1.0 + 0.18 * abs(math.cos(i))), z + 0.15 * math.cos(i * 2.1)) for i, (x, y, z) in enumerate(sub)]
            a.sweep(pts, [(-.08, -.08), (.08, -.08), (.08, .08), (-.08, .08)], col=P['lava'], glow=0.9, up=(0, 1, 0))
    for sx in (-1, 1):
        a.cyl(1.8, 1.7, 0.1, loc=(sx * 5.2, 0, 0.0), col=P['ember'], glow=0.8, segs=14)
    return dict(body=a)


@asset('BasaltSpire', course='C', holes=[22, 23], kind='hole set piece', budget=5000, dims=dict(z=(16, 22)), match=(0, 4), target='BasaltSpire',
       where='h22 FWD: the plateau green at the end of the winding black causeway, a basalt spire (beyond the green); h23 L lagoon islet spire.',
       features=['tall ridged spire tapering to a rounded tip', '7 vertical ridges', 'glowing seams in the troughs low down', 'ring of hex columns at the base'])
def basalt_spire(q):
    a = Asset('BasaltSpire', q, seed=222)
    rf = lambda t, z, r: r * (0.86 + 0.18 * abs(math.cos(3.5 * t)))
    def col(c, n):
        t = math.atan2(c.y, c.x)
        if abs(math.cos(3.5 * t)) < 0.2 and c.z < 12:
            return P['ember']
        return P['basalt_lt'] if abs(math.cos(3.5 * t)) > 0.85 else P['basalt']
    gl = lambda c: 0.7 * max(0.0, 1 - c.z / 12) if abs(math.cos(3.5 * math.atan2(c.y, c.x))) < 0.2 and c.z < 12 else 0.0
    zs = [0, 2, 5, 8, 11, 13.5, 15.5, 17, 18.1, 18.8, 19.1]
    rs = [3.7, 3.5, 3.25, 3.0, 2.75, 2.45, 2.05, 1.55, 1.0, 0.5, 0.0]
    a.revolve(list(zip(rs, zs)), col=col, glow=gl, segs=42 if a.lod0 else 28, rfn=rf)
    r = a.rng
    for k in range(9 if a.lod0 else 5):
        t = 2 * math.pi * k / (9 if a.lod0 else 5) + 0.3
        h = r.uniform(0.8, 2.8)
        a.cyl(0.75, 0.75, h, loc=(4.6 * math.cos(t), 4.6 * math.sin(t), 0), col=lambda c, n: P['basalt_lt'] if n.z > 0.7 else P['basalt'],
              segs=6, smooth=False, phase=r.uniform(0, 1))
    return dict(body=a)
