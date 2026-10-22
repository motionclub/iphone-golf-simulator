"""Shore kit (PLAN 4.1 MajesticShore, 4.3 zone Z3): island edges are never a bare bevel.
All strips are 20 m along X and tile end to end (every x-variation is periodic over 20 m). Pivot = waterline (z 0 = sea level,
y 0 = mean shoreline); land is +Y, sea is -Y. They are flat ground pieces, so there is no impostor (LOD2): beyond the LOD1 range the
golf track's island bevel + MajesticShore shader carry the edge."""
import math
from mathutils import Vector, noise
from kit import Asset, Cards, P, mix, lin
from registry import asset

TL = 20.0          # tile length (m)
RING_N = 10        # arc tiles per full ring
RING_R = TL * RING_N / (2 * math.pi)   # 31.83 m: 10 arc tiles close a ring


def wav(x):
    """Shoreline wiggle, periodic over one tile."""
    return 0.8 * math.sin(2 * math.pi * 2 * x / TL) + 0.4 * math.sin(2 * math.pi * 5 * x / TL + 1.0)


def beach_h(x, y):
    yy = y - wav(x)
    if yy >= 4.0:
        return 0.32
    if yy >= 2.0:
        return 0.16 + 0.16 * (yy - 2.0) / 2.0
    if yy >= -1.0:
        return -0.04 + 0.2 * (yy + 1.0) / 3.0
    return -0.04 - 1.36 * min(1.0, (-1.0 - yy) / 5.0) ** 1.3


def beach_col(dry, wet, shallow, grass=P['grass']):
    def col(c, n):
        if c.z > 0.27:
            return grass
        if c.z > 0.16:
            return mix(dry, grass, (c.z - 0.16) / 0.11)
        if c.z > 0.03:
            return dry
        if c.z > -0.25:
            return mix(wet, dry, (c.z + 0.25) / 0.28)
        return mix(shallow, wet, max(0.0, (c.z + 1.0) / 0.75))
    return col


SHORE_NO_IMP = dict(no_impostor=True, no_impostor_why='flat ground strip: LOD1 to the end of its cull range, then the island bevel + shore shader')


@asset('ShoreBand', tile=dict(kind='x', L=TL), course='A', holes=[7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 20], kind='shore kit (tileable 20 m strip)', budget=4000,
       dims=dict(x=(19.9, 20.1)), match=(20, 35), target='ShoreBand', pivot='waterline',
       where='Z3 island rim on every sea hole with a sand edge (Cliffside lagoon/beaches h09/h12/h15, Wild Isles 13-20). Lays along the island '
             'edge, land +Y; tiles every 20 m. Pair with FoamStrip (same wiggle) and the shallows gradient of MajesticShore.',
       features=['grass lip -> dry sand -> wet sand -> turquoise shallows under the water', 'wavy shoreline, periodic so tiles match',
                 'beach rocks (LOD0)', 'slopes 1.4 m under sea level so no edge shows through the water'], **SHORE_NO_IMP)
def shore_band(q, name='ShoreBand', xyfn=None, pal=None, glow_line=False, rocks=P['limestone']):
    a = Asset(name, q, seed=301)
    dry, wet, sh = pal or (P['sand'], P['sand_wet'], mix(P['sand_wet'], P['sea'], 0.55))
    col = beach_col(dry, wet, sh)
    def colg(c, n):
        if glow_line and -0.08 < c.z < 0.05:
            return mix(P['ember'], P['lava_hot'], 1 - abs(c.z + 0.015) / 0.065)
        return col(c, n)
    gl = (lambda c: 0.9 if -0.08 < c.z < 0.05 else 0.0) if glow_line else 0.0
    a.slab(48, 20, TL, 12.0, beach_h, base_z=-1.8, col=colg, glow=gl, xyfn=xyfn)
    if a.lod0:
        r = a.rng
        for k in range(7):
            x = r.uniform(-8, 8); y = r.uniform(-0.5, 2.5) + wav(x)
            X, Y = xyfn(x, y) if xyfn else (x, y)
            a.blob(r.uniform(0.3, 0.7), loc=(X, Y, beach_h(x, y) - 0.15), scale=(1.3, 1, 0.7), col=rocks, sub=1, amp=0.3, seed=k)
    return dict(body=a)


def arc_xy(x, y):
    """Bend a strip round a ring of radius RING_R: land (+Y) toward the ring centre (0, RING_R)."""
    rho = RING_R - y
    th = x / RING_R
    return (rho * math.sin(th), RING_R - rho * math.cos(th))


@asset('ShoreBand_Arc', tile=dict(kind='arc', c=(0, RING_R), s=-1, span=360 / RING_N), course='A', holes=[8, 9, 12, 15, 19], kind='shore kit (ring arc tile)', budget=4000, dims=dict(z=(2.4, 2.7)),
       match=(10, 45), target='FoamRing', pivot='waterline',
       where=f'Island rims of round islands (h12 island green, h15 three-tier island, h19 lagoon islets): {RING_N} tiles of {360 / RING_N:.0f} deg '
             f'close a ring of radius {RING_R:.1f} m (centre = local (0, {RING_R:.1f}, 0)); scale XY uniformly for other islands.',
       features=['same profile as ShoreBand bent round a ring', 'ends identical so 10 tiles close the ring'], **SHORE_NO_IMP)
def shore_band_arc(q):
    return shore_band(q, 'ShoreBand_Arc', xyfn=arc_xy)


@asset('BlackSandShore', tile=dict(kind='x', L=TL), course='C', holes=[10, 16], kind='shore kit (tileable 20 m strip)', budget=4000, dims=dict(x=(19.9, 20.1)), match=(20, 35),
       target='BlackSandShore', pivot='waterline',
       where='h10 off-line: black sand beach with glowing tide line; h16 lava-river banks to the sea. Same layout/tiling as ShoreBand.',
       features=['black volcanic sand to dark wet sand', 'glowing ember tide line at the waterline (UV2 glow)', 'basalt pebbles (LOD0)'], **SHORE_NO_IMP)
def black_sand_shore(q):
    return shore_band(q, 'BlackSandShore', pal=(P['blacksand'], lin('#1f1c24'), lin('#203a48')), glow_line=True, rocks=P['basalt'])


def cliff_h(x, y):
    """Limestone cliff: turf top at +5.5 m (y > 3), steep bulging face y -0.5..3 with two soft ledges, rocky foot into the sea."""
    yy = y - 0.6 * math.sin(2 * math.pi * 3 * x / TL) - 0.3 * math.sin(2 * math.pi * 7 * x / TL + 2)
    if yy >= 3.0:
        return 5.5 + 0.15 * math.sin(2 * math.pi * 2 * x / TL)
    if yy >= -0.5:
        t = (yy + 0.5) / 3.5
        s = t * t * (3 - 2 * t)
        ledge = 0.35 * math.sin(math.pi * 2 * t) ** 2
        return -0.3 + 5.8 * min(1.0, s + ledge * 0.15)
    return -0.3 - 1.7 * min(1.0, (-0.5 - yy) / 3.5)


@asset('CliffSkirt', tile=dict(kind='x', L=TL), course='A', holes=[7, 8, 12, 15], kind='shore kit (tileable 20 m strip)', budget=5000, dims=dict(z=(6, 8.5)), match=(15, 15),
       target='RockShelf', pivot='waterline',
       where='Z3 cliff edges with surf (h07 R cliff drop, h08 sea-stack bases, h12 tee cliff, h15 island rim): turf lip 5.5 m above the sea. '
             'Pair with FoamStrip at the foot.',
       features=['grass cap on a terraced cream limestone face', 'dark wet foot + boulders', 'periodic so tiles match'], **SHORE_NO_IMP)
def cliff_skirt(q):
    a = Asset('CliffSkirt', q, seed=302)
    def col(c, n):
        if c.z > 5.25 and n.z > 0.5:
            return P['grass']
        if c.z < 0.5:
            return mix(P['stone_dk'], P['stone'], max(0.0, c.z + 0.5))
        k = 0.5 + 0.5 * math.sin(c.z * 2.4)
        return mix(P['limestone'], P['cream'], k) if n.z < 0.7 else P['moss']
    a.slab(50, 34, TL, 9.0, cliff_h, base_z=-2.4, col=col)
    r = a.rng
    for k in range(8 if a.lod0 else 3):
        x = r.uniform(-8.5, 8.5)
        a.blob(r.uniform(0.6, 1.2), loc=(x, r.uniform(-2.5, -0.6), -0.4), scale=(1.3, 1, 0.8), col=P['stone'], sub=1 if not a.lod0 else 2, amp=0.3, seed=k)
    return dict(body=a)


def foam_card(name, q, pts, width, closed=False, vrep=8.0):
    c = Cards(name)
    if closed:
        pts = pts + [pts[0]]
    c.strip(pts, width, P['foam'], alpha=(0.85, 0.85), vrep=vrep)
    return c


FOAM_NO_IMP = dict(no_impostor=True, no_impostor_why='flat FX card on the water; UV0.y runs along it for scrolling foam')


@asset('FoamRing', course='A', holes=[8, 9, 12, 15, 19], kind='shore kit (FX card)', budget=1000, dims=dict(x=(66, 70)), match=(10, 45), target='FoamRing',
       pivot='centre', where=f'Foam ring round island rims and sea stacks (h12 island, h08 stacks, h15). Pivot = ring centre at sea level; '
                             f'centre line radius {RING_R + 1.4:.1f} m (1.4 m outside the ShoreBand_Arc shoreline), 2.2 m wide, at z +0.03; scale XY for other islands.',
       features=['open annulus card, UV0.y around (8 repeats), UV0.x across', 'Col.a = 0.85'], **FOAM_NO_IMP)
def foam_ring(q):
    n = 96 if q >= 1 else 48
    R = RING_R + 1.4
    pts = [(R * math.sin(2 * math.pi * i / n), -R * math.cos(2 * math.pi * i / n), 0.03) for i in range(n)]
    return dict(fx=dict(Foam=foam_card('Foam', q, pts, 2.2, closed=True, vrep=12)))


@asset('FoamStrip', course='A', holes=[7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 20], kind='shore kit (FX card, tileable)', budget=1000, dims=dict(x=(19.9, 20.5)),
       match=(20, 35), target='ShoreBand', pivot='waterline',
       where='Foam line for ShoreBand / CliffSkirt tiles: follows the ShoreBand waterline wiggle 1.2 m seaward, tiles every 20 m.',
       features=['open strip card on the water, same periodic wiggle as ShoreBand', 'UV0.y along (scroll), UV0.x across'], **FOAM_NO_IMP)
def foam_strip(q):
    n = 48 if q >= 1 else 24
    pts = [(-TL / 2 + TL * i / n, -1.2 + wav(-TL / 2 + TL * i / n), 0.03) for i in range(n + 1)]
    return dict(fx=dict(Foam=foam_card('Foam', q, pts, 1.8, vrep=3)))


def shelf_h(x, y):
    edge = max(abs(x) / 6.0, abs(y) / 4.0)
    base = 0.35 + 0.12 * noise.noise(Vector((x * 0.35, y * 0.35, 1.0))) + 0.06 * noise.noise(Vector((x * 1.1, y * 1.1, 4.0)))
    for (px, py, rx, ry) in POOLS:
        d = ((x - px) / rx) ** 2 + ((y - py) / ry) ** 2
        if d < 1.0:
            base -= 0.55 * (1 - d) ** 0.7
    if edge > 0.8:
        base -= (edge - 0.8) / 0.2 * 1.2
    return base


POOLS = [(-2.6, -0.6, 1.5, 1.0), (1.6, 1.0, 1.2, 0.8), (2.6, -1.8, 0.8, 0.6)]


@asset('RockShelf', course='A', holes=[8, 9, 12], kind='shore kit (set piece)', budget=5000, dims=dict(x=(11.5, 12.5)), match=(20, 40), target='RockShelf',
       pivot='waterline', where='h08 off-line: rock shelves with tide pools at the sea-stack bases (both sides of the path); also h09/h12 shores.',
       features=['low limestone shelf sloping under the sea at its edges', 'three tide pools with turquoise water discs',
                 'wet dark rims, moss + anemone dots (LOD0)'], **SHORE_NO_IMP)
def rock_shelf(q):
    a = Asset('RockShelf', q, seed=303)
    def col(c, n):
        for (px, py, rx, ry) in POOLS:
            if ((c.x - px) / (rx + 0.3)) ** 2 + ((c.y - py) / (ry + 0.3)) ** 2 < 1.0:
                return P['stone_dk']
        if c.z < 0.05:
            return P['stone_dk']
        return P['moss'] if noise.noise(Vector((c.x * 0.5, c.y * 0.5, 7.0))) > 0.35 else (P['limestone'] if n.z > 0.8 else P['stone'])
    a.slab(40, 28, 12.0, 8.0, shelf_h, base_z=-1.6, col=col)
    for (px, py, rx, ry) in POOLS:
        a.revolve([(1.0, 0.0), (1.0, 0.06)], loc=(px, py, 0.02), col=mix(P['sea'], P['white'], 0.15), glow=0.15, segs=20,
                  rfn=lambda t, z, r, rx=rx, ry=ry: 0.9 / math.sqrt((math.cos(t) / rx) ** 2 + (math.sin(t) / ry) ** 2))
    if a.lod0:
        r = a.rng
        for k in range(10):
            px, py, rx, ry = POOLS[k % 3]
            t = r.uniform(0, 2 * math.pi)
            a.sphere(0.12, loc=(px + rx * 0.95 * math.cos(t), py + ry * 0.95 * math.sin(t), 0.08), col=(P['tulip_p'], lin('#ff8a4a'), P['purple'])[k % 3], segs=8)
    return dict(body=a)
