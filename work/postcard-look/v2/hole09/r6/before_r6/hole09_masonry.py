"""hole09_masonry.py - irregular rubble masonry for the Split ruin (POSTCARD_LOOK, repair round 1, 2026-10-04).

Replaces PL.build_ruin / PL.build_masonry_arch for hole 9 (the props library is not edited). Why: the review called the ruin "stacked Lego boxes, floating slabs and
an unsupported lintel": every block was an axis-aligned box, every face carried the same tiled brick texture, a block was kept or dropped by its own height test
(so a slab could hang over a gap) and nothing was buried.

What this module does instead (every number is a constant below):

    blocks      convex hulls of a jittered, partly chamfered box (six non-parallel faces + chips), 0.7-1.5 m long, 0.36-0.58 m high courses, a 2.5 cm gap between blocks,
                +-0.025 rad yaw and +-0.015 rad tilt per block, random depth (0.88-1.0 of the wall) and +-4 cm out-of-line: no ruler lines
    support     a block exists only if its centre lies over a block of the course below (coverage list per course), the first course is buried 0.25-0.45 m in the
                ground, the lintel is ONE long stone that bears 0.55 m on each jamb, every course joint is nudged >= 0.2 m off the joint below (running bond)
    broken      a seeded height profile (full stretches, stubs, collapsed gaps) decides where a course stops; the last block under the profile is cut lower (ragged top)
    arch        two rubble piers + a ring of wedge-shaped voussoirs (broken: the crown wedges are missing and lie on the ground, a heap of stones fills the gap)
    rubble      small irregular stones round the wall feet (never in the doorway)
    texture     LK_MASONRY only. Each face gets its own UV window: a random brick ROW INTERIOR of Masonry_C.png (the mortar lines are skipped), a random column offset,
                a random flip and a 0.6-1.6 x density: the painted grid cannot read across blocks and no horizontal mortar line runs through a stone.

Everything is visual only (DRESS_RUIN_nn_pp / DRESS_ARCH_nn_pp, no collider prefix).
"""
import math
import random
import sys

sys.dont_write_bytecode = True
import numpy as np
import bpy
from mathutils import Vector, Matrix

import postcard_lib as P
import postcard_look_lib as L
import postcard_props_lib as PL

YD = P.YD

# --------------------------------------------------------------------------------------------- constants
BLOCK_L = (0.7, 1.5)          # block length along the wall (m); 7 % of the blocks are long stones (LONG_L)
LONG_L = (1.8, 2.3)
COURSE_H = (0.36, 0.56)       # course height above the lintel (m)
LINTEL_H = (0.50, 0.58)
GAP = 0.025                   # gap between neighbouring blocks (m, each side)
FOUNDATION_TOP = (0.25, 0.40)  # first course top above the ground (m); its bottom is -0.45 (buried)
BURY = 0.25                   # the first course bottom is at least this far under the local ground
MIN_STACK = 0.30              # a course exists at a place only if the broken profile leaves >= 0.30 m of it
LINTEL_BEARING = 0.55         # the lintel stone bears this far on each jamb (m)
TIGHT_JOINT = 0.20            # a joint nearer than this to a joint of the course below is nudged away
MAS_ROW = dict(y0=31.0, period=64.0, pad=9.0, h=46.0, size=512.0)   # px of the brick rows of Masonry_C.png (mortar line centres at y = 31 + 64 k from the bottom)
UV_DENS = (0.6, 1.6)          # per-face UV density as a factor of the contract density (1 / 4 m); verify allows 1/3 .. 3


# --------------------------------------------------------------------------------------------- stone shapes
def _corners_box(rng, sx, sy, sz, top_rag=0.0):
    """8 corners (ix, iy, iz in {0, 1}) of a hand-hewn block: origin = centre of the bottom face, x along the wall, y thickness, z up. The block is a box pushed through a random
    taper + shear (so no two faces are parallel and every face stays PLANAR: independent corner jitter made warped quads whose two triangles shaded differently) with a tilted top
    plane; top_rag lowers and slopes the top (a broken top course)."""
    tx, ty = rng.uniform(-0.04, 0.05), rng.uniform(-0.05, 0.05)            # taper with height (+ = wider at the top)
    shx, shy = rng.uniform(-0.05, 0.05) * sz, rng.uniform(-0.05, 0.05) * sz  # lean of the top over the bottom (m)
    twist = rng.uniform(-0.03, 0.03)                                         # top face twist about z (rad)
    sl_x, sl_y = rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05)           # top plane slope (fraction of sz per fraction of the width)
    drop = rng.uniform(0.0, 0.04) + top_rag * rng.uniform(0.4, 1.0)
    rag_x, rag_y = top_rag * rng.uniform(-0.9, 0.9), top_rag * rng.uniform(-0.9, 0.9)
    C = {}
    for ix in (0, 1):
        for iy in (0, 1):
            for iz in (0, 1):
                u, v = (ix - 0.5), (iy - 0.5)
                k = 1.0 + (iz - 0.5) * 2.0 * 0.5
                x, y = u * sx * (1.0 + tx * (iz * 2 - 1)), v * sy * (1.0 + ty * (iz * 2 - 1))
                if iz:
                    c, sn = math.cos(twist), math.sin(twist)
                    x, y = c * x - sn * y, sn * x + c * y
                    x, y = x + shx, y + shy
                    z = sz * (1.0 - drop - (sl_x + rag_x) * u - (sl_y + rag_y) * v)
                else:
                    z = sz * 0.012 * (u + v)                                   # the bed is almost flat
                C[(ix, iy, iz)] = np.array([x, y, z])
    return C


def _hull_stone(rng, C, chamfer=0.35, frac=(0.08, 0.22)):
    """Points of a chipped stone: every corner of C is either kept or replaced by its three chamfer points (a fraction of each edge). Convex hull = planar faces + chip facets."""
    pts = []
    for key, p in C.items():
        if rng.random() < chamfer:
            for ax in range(3):
                nb = list(key)
                nb[ax] ^= 1
                q = C[tuple(nb)]
                pts.append(p + (q - p) * rng.uniform(*frac))
        else:
            pts.append(p)
    return pts


class StoneSet:
    """Collects blocks into DRESS_<kind>_<nn>_<pp> meshes of <= max_faces faces (LK_MASONRY, per-face UV windows)."""

    def __init__(self, D, prefix, seed, clip=None, max_faces=380):
        self.D, self.prefix = D, prefix
        self.rng = random.Random(seed)
        self.clip = clip                       # clip(X, Y) -> bool array: every vertex of a block must pass
        self.base = L._next_name(D, prefix)
        self.mat = L.look_material("LK_MASONRY", D)
        self.max_faces = max_faces
        self.part = 0
        self.objs = []
        self.n_blocks = 0
        self.n_refused = 0
        self.refused = []                      # (x, y) of every refused stone
        self.records = []                      # (kind, bottom z, centre x, y) of every block (for the report)
        self._reset()

    def _reset(self):
        self.V, self.F, self.UV = [], [], []

    def flush(self):
        if not self.F:
            return
        name = f"{self.base}_{self.part:02d}"
        ob = L._new_piece(self.D, name, self.V, self.F, self.UV, [0] * len(self.F), [self.mat], col="STRUCTURES", sharp_deg=32.0)
        ob["h9_class"] = "masonry"
        self.objs.append(ob)
        self.part += 1
        self._reset()

    # per-face UV window (the Masonry_C.png brick row interiors, see the module docstring)
    def _uv(self, pts):
        rng = self.rng
        p = np.array([tuple(q) for q in pts], float)
        n = np.zeros(3)
        for i in range(len(p)):
            a, b = p[i], p[(i + 1) % len(p)]
            n += np.array([(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])])
        ln = float(np.linalg.norm(n))
        n = n / ln if ln > 1e-12 else np.array([0.0, 0.0, 1.0])
        kd = 1.0 / L.LOOK["LK_MASONRY"][2]
        if abs(n[2]) < 0.75:                                   # a standing face: a brick row interior, no mortar line across it
            up = np.array([0.0, 0.0, 1.0])
            vax = up - n * float(up @ n)
            vax /= max(float(np.linalg.norm(vax)), 1e-9)
            uax = np.cross(vax, n)
            a, b = p @ uax, p @ vax
            h = float(b.max() - b.min())
            kk = min(max(MAS_ROW["h"] / MAS_ROW["size"] / max(h, 0.05), UV_DENS[0] * kd), UV_DENS[1] * kd)
            row = rng.randrange(8)
            v0 = (MAS_ROW["y0"] + MAS_ROW["period"] * row + MAS_ROW["pad"]) / MAS_ROW["size"]
            u0 = rng.random()
            fl = -1.0 if rng.random() < 0.5 else 1.0
            return [(u0 + fl * kk * float(a[i] - a.min()), v0 + kk * float(b[i] - b.min())) for i in range(len(p))]
        kk = kd * rng.uniform(*UV_DENS)
        u0, v0 = rng.random(), rng.random()
        return [(u0 + kk * float(p[i, 0]), v0 + kk * float(p[i, 1])) for i in range(len(p))]

    def add(self, local_pts, origin, R, kind="block"):
        """Add one stone: hull of local_pts, placed at origin (world, m) with the 3x3 rotation R. Returns True when it was kept (every vertex passes the clip)."""
        verts, faces = PL._hull(local_pts, merge=0.012, dissolve_deg=2.0)
        W = [Vector(origin) + R @ Vector(v) for v in verts]
        if self.clip is not None:
            xy = np.array([(w.x, w.y) for w in W])
            if not bool(np.all(self.clip(xy[:, 0], xy[:, 1]))):
                self.n_refused += 1
                self.refused.append((float(origin[0]), float(origin[1])))
                return False
        if len(self.F) + len(faces) > self.max_faces:
            self.flush()
        base = len(self.V)
        self.V.extend((float(w.x), float(w.y), float(w.z)) for w in W)
        for f in faces:
            self.F.append(tuple(base + i for i in f))
            self.UV.append(self._uv([W[i] for i in f]))
        self.n_blocks += 1
        self.records.append((kind, float(min(w.z for w in W)), float(origin[0]), float(origin[1])))
        return True

    def stone(self, origin, yaw, sx, sy, sz, top_rag=0.0, chamfer=0.35, tilt=0.015, kind="block"):
        rng = self.rng
        R = Matrix.Rotation(yaw, 3, 'Z') @ Matrix.Rotation(rng.uniform(-tilt, tilt), 3, 'X') @ Matrix.Rotation(rng.uniform(-tilt, tilt), 3, 'Y')
        return self.add(_hull_stone(rng, _corners_box(rng, sx, sy, sz, top_rag), chamfer), origin, R, kind)


# --------------------------------------------------------------------------------------------- walls
def course_bounds(rng, hd, hmax, n_below=5):
    """Course boundaries (m, relative to the ground). Course 0 is the buried foundation row (-0.45 .. FOUNDATION_TOP), courses 1 .. n_below-1 fill the rest of the way up to
    hd (the doorway / spring height) exactly, then one lintel course, then ordinary courses up to hmax."""
    zb = [-0.45, rng.uniform(*FOUNDATION_TOP)]
    w = [rng.uniform(0.88, 1.12) for _ in range(n_below - 1)]
    span = hd - zb[1]
    for x in w:
        zb.append(zb[-1] + span * x / sum(w))
    zb[-1] = hd
    zb.append(hd + rng.uniform(*LINTEL_H))
    while zb[-1] < hmax + 0.6:
        zb.append(zb[-1] + rng.uniform(*COURSE_H))
    return zb


def make_profile(rng, total, hmax_of_s, door=None):
    """Broken height profile h(s) (m above the ground) along the path of length `total`: random control points every ~1.9 m (full stretches, stubs, collapsed gaps),
    low at both free ends, never lower than `door[2]` within door[1]/2 + 1.3 m of the doorway axis door[0]."""
    n = max(5, int(total / 1.9))
    vals = []
    for _ in range(n + 1):
        r = rng.random()
        vals.append(rng.uniform(0.80, 1.0) if r < 0.35 else rng.uniform(0.46, 0.76) if r < 0.65 else rng.uniform(0.2, 0.4) if r < 0.88 else rng.uniform(0.0, 0.14))
    vals[0] = min(vals[0], 0.5)
    vals[-1] = min(vals[-1], 0.5)

    def h(s):
        f = min(max(s / total, 0.0), 1.0) * n
        i = min(int(f), n - 1)
        t = f - i
        v = vals[i] * (1 - t) + vals[i + 1] * t
        out = v * hmax_of_s(s)
        if door is not None:                                           # the wall beside the doorway stays high for 0.6 m, then steps down over 2.4 m (no lone jamb towers)
            k = min(1.0, max(0.0, 1.0 - (abs(s - door[0]) - (door[1] / 2 + 0.6)) / 2.4))
            out = max(out, door[2] * k)
        return out
    return h


def _lay(rng, lo, hi, anchor, avoid, first_len=None):
    """Block extents [(s0, s1)] filling [lo, hi]. anchor 'hi' / 'lo' = the flush end the blocks are counted from (a doorway jamb, the other end is cut), None = random start.
    Of 14 random draws the one whose joints stay farthest from `avoid` (the joints of the course below) wins."""
    span = hi - lo
    if span < 0.3:
        return []
    best, best_c = None, 1e9
    for _ in range(14):
        lens, rem = [], span
        fst = first_len
        while rem > 0.05:
            if fst is not None and not lens:
                l = fst
            elif anchor is None and not lens:
                l = rng.uniform(*BLOCK_L) * rng.uniform(0.35, 1.0)
            else:
                l = rng.uniform(*LONG_L) if rng.random() < 0.07 else rng.uniform(*BLOCK_L)
            if rem - l < 0.55:
                l = rem
            l = min(l, rem)
            lens.append(l)
            rem -= l
        if anchor == 'hi':
            lens = lens[::-1]
        cuts = [lo + sum(lens[:k + 1]) for k in range(len(lens) - 1)]
        c = sum(1 for x in cuts for a in avoid if abs(x - a) < TIGHT_JOINT)
        if c < best_c:
            best, best_c = (lens, cuts), c
            if c == 0:
                break
    lens, cuts = best
    edges = [lo] + cuts + [hi]
    return [(edges[k], edges[k + 1]) for k in range(len(edges) - 1)]


def _covered(cov, s):
    return any(a - 1e-6 <= s <= b + 1e-6 for a, b in cov)


def _supported(cov, s0, s1, ln, share=0.6):
    """A block [s0, s1] (along a segment of length ln) is supported when its centre is over the course below AND >= `share` of its bed (the part inside the segment: a corner block
    also rests on the other wall) lies over the course below."""
    sm = 0.5 * (s0 + s1)
    if not _covered(cov, min(max(sm, 0.12), ln - 0.12)):
        return False
    a0, a1 = max(s0, 0.0), min(s1, ln)
    if a1 - a0 < 0.15:
        return True
    ov = sum(max(0.0, min(a1, b) - max(a0, a)) for a, b in cov)
    return ov >= share * (a1 - a0)


def build_wall_path(ss, pts, seg_h, T, zb, door, seed, ground, G0, door_course=5, prof=None):
    """Rubble wall along the polyline pts (world metres). seg_h[i] = max height of segment i, T = wall thickness, zb = course_bounds, door = (segment index, centre s along that
    segment, width, height) or None. prof = optional height profile h(s) (m above the ground; default: a broken random profile). Returns dict(blocks, joints, tight, lintels, door_world)."""
    rng = random.Random(seed)
    segs = []
    for i in range(len(pts) - 1):
        a, b = np.array(pts[i], float), np.array(pts[i + 1], float)
        ln = float(np.hypot(*(b - a)))
        segs.append((a, b, ln, (b - a) / ln))
    s0g, tot = [], 0.0
    for sg in segs:
        s0g.append(tot)
        tot += sg[2]
    door_g = None if door is None else (s0g[door[0]] + door[1], door[2], door[3] + 0.58 + 0.60)

    def hmax_of_s(s):
        i = max(k for k in range(len(segs)) if s0g[k] <= s + 1e-9)
        return seg_h[i]
    if prof is None:
        prof = make_profile(rng, tot, hmax_of_s, door=door_g)
    stat = dict(blocks=0, joints=0, tight=0, lintels=0)
    for i, (a, b, ln, d) in enumerate(segs):
        nrm = np.array([-d[1], d[0]])
        yaw = math.atan2(d[1], d[0])
        cov = []                                                      # per course: the (s0, s1) extents that exist
        prev_cuts = []
        for c in range(len(zb) - 1):
            z0, z1 = zb[c], zb[c + 1]
            s_lo = -(T * 0.5) if (i > 0 and c % 2 == 0) else 0.0
            s_hi = ln + (T * 0.5) if (i < len(segs) - 1 and c % 2 == 1) else ln
            runs = []                                                 # (lo, hi, anchor, first_len)
            lintel = None
            if door is not None and door[0] == i and c <= door_course:
                sd, w = door[1], door[2]
                if c < door_course:
                    jl = rng.uniform(1.0, 1.3) if c % 2 == 0 else rng.uniform(0.8, 1.0)         # quoin pattern: long, short, long ... (the short one is >= 62 % of the long one, so the jamb column always stands)
                    runs = [(s_lo, sd - w / 2, 'hi', jl), (sd + w / 2, s_hi, 'lo', jl)]
                else:                                                  # the lintel course: ONE long stone bearing on both jambs, ordinary blocks outside it
                    l0, l1 = sd - w / 2 - LINTEL_BEARING, sd + w / 2 + LINTEL_BEARING
                    lintel = (l0, l1)
                    runs = [(s_lo, l0, 'hi', None), (l1, s_hi, 'lo', None)]
            else:
                runs = [(s_lo, s_hi, None, None)]
            cov_c, cuts_c = [], []
            for (lo, hi, anc, fl) in runs:
                ext_ = _lay(rng, lo, hi, anc, prev_cuts, fl)
                for k_, (e0, e1) in enumerate(ext_):
                    cuts_c += [e0, e1]
                    s0, s1 = e0 + GAP, e1 - GAP
                    if s1 - s0 < 0.3:
                        continue
                    sm = 0.5 * (s0 + s1)
                    hp = prof(s0g[i] + min(max(sm, 0.0), ln))
                    jamb = c < door_course and door is not None and door[0] == i and ((anc == 'hi' and k_ == len(ext_) - 1) or (anc == 'lo' and k_ == 0))   # the flush block at the doorway: always there
                    if hp - z0 < MIN_STACK and not jamb:
                        stat.setdefault('drops', []).append((i, c, round(s0, 2), round(s1, 2), 'profile'))
                        continue
                    if c > 0 and not jamb and not _supported(cov[c - 1], s0, s1, ln):
                        stat.setdefault('drops', []).append((i, c, round(s0, 2), round(s1, 2), 'support'))
                        continue                                      # < 60 % of its bed over the course below (or nothing under its centre): a floating / cantilevered block is never made
                    ztop = z1 - rng.uniform(0.0, 0.03)
                    rag = 0.0
                    if hp < z1 - 0.02:                                 # the profile ends inside this course: the last block is cut lower and slopes (ragged top)
                        ztop = min(ztop, z0 + max(0.28, (hp - z0) * rng.uniform(0.85, 1.05)))
                        rag = 0.30
                    cpos = a + d * sm + nrm * rng.uniform(-0.04, 0.04)
                    g_loc = float(ground(np.array([cpos[0]]), np.array([cpos[1]]))[0])
                    zbot = (min(G0 + z0, g_loc - BURY) if c == 0 else G0 + z0 + 0.006)
                    ok = ss.stone((cpos[0], cpos[1], zbot), yaw + rng.uniform(-0.025, 0.025), s1 - s0, T * rng.uniform(0.88, 1.0), max(0.2, ztop - z0 - 0.006 * (c > 0)),
                                  top_rag=rag, chamfer=0.35, kind="wall")
                    if ok:
                        cov_c.append((s0, s1))
                        stat["blocks"] += 1
            if lintel is not None:
                l0, l1 = lintel
                jam_ok = _covered(cov[c - 1], l0 + 0.25) and _covered(cov[c - 1], l1 - 0.25)    # both jambs stand under its ends
                stat["jamb"] = (jam_ok, round(l0, 2), round(l1, 2), [(round(a_, 2), round(b_, 2)) for a_, b_ in cov[c - 1] if l0 - 1.0 < a_ < l1 + 1.0])
                if jam_ok:
                    sm = 0.5 * (l0 + l1)
                    cpos = a + d * sm
                    ztop = z1 - rng.uniform(0.0, 0.02)
                    ok = ss.stone((cpos[0], cpos[1], G0 + z0 + 0.006), yaw + rng.uniform(-0.01, 0.01), (l1 - l0) - 2 * GAP, T * rng.uniform(0.96, 1.0), ztop - z0 - 0.006,
                                  top_rag=0.0, chamfer=0.25, tilt=0.006, kind="lintel")
                    if ok:
                        cov_c.append((l0 + GAP, l1 - GAP))
                        stat["lintels"] += 1
                        stat["blocks"] += 1
            cov.append(cov_c)
            stat.setdefault('per_course', {}).setdefault(i, []).append(len(cov_c))
            for x in cuts_c:
                stat["joints"] += 1
                stat["tight"] += any(abs(x - y) < 0.12 for y in prev_cuts)
            prev_cuts = cuts_c
    if door is not None:
        a, b, ln, d = segs[door[0]]
        stat["door_world"] = tuple(a + d * door[1])
    stat["segments"] = len(segs)
    return stat


# --------------------------------------------------------------------------------------------- arch
def build_arch(ss, center, phi_deg, ground, G0, r=2.0, t=0.75, depth=1.3, pier_w=1.7, spring=2.7, left_top=6.0, right_top=3.9, seed=0):
    """Broken masonry arch: two rubble piers + a ring of wedge voussoirs. center = (x, y) midway between the piers (world, m); phi_deg = the direction you look THROUGH the opening
    (clockwise from +Y, the postcard_lib build_arch convention). Voussoirs 0..6 stand on the left, the two on the right spring; the crown wedges are missing (they lie on the ground).
    Returns dict(missing=[fallen wedge info], opening centre, height)."""
    rng = random.Random(seed)
    phi = math.radians(phi_deg)
    xl = np.array([math.cos(phi), -math.sin(phi)])            # across the opening (local x)
    yl = np.array([math.sin(phi), math.cos(phi)])             # through the opening (local y)
    c0 = np.array(center, float)
    zb = course_bounds(rng, spring, max(left_top, right_top), n_below=5)
    for side, top in ((-1, left_top), (1, right_top)):
        a = c0 + xl * side * (r + pier_w)
        b = c0 + xl * side * r
        # a straight path across the pier (so the pier is a short 2-3 block wall of thickness `depth` in the through direction)
        path = [tuple(a), tuple(b)] if side < 0 else [tuple(b), tuple(a)]
        build_wall_path(ss, path, [top], depth, zb, None, seed * 7 + (1 if side < 0 else 2), ground, G0,
                        prof=lambda s_, top=top, ph=rng.uniform(0, 6.0): top * (0.9 + 0.1 * math.sin(2.6 * s_ + ph)))
    n = 11
    Rl = Matrix.Rotation(-phi, 3, 'Z')
    missing = []
    present = set(range(0, 7)) | {9, 10}
    for i in range(n):
        th0 = i * math.pi / n + 0.006
        th1 = (i + 1) * math.pi / n - 0.006
        corners = {}
        dy = depth * rng.uniform(0.9, 1.0)
        for ia, th in ((0, th0), (1, th1)):
            for iy in (0, 1):
                for ir, rad in ((0, r - 0.03), (1, r + t)):
                    rr = rad + rng.uniform(-0.02, 0.02)
                    th_j = th + rng.uniform(-0.005, 0.005)
                    corners[(ia, iy, ir)] = np.array([-rr * math.cos(th_j), (iy - 0.5) * dy * (1.0 + rng.uniform(-0.04, 0.04)), spring + rr * math.sin(th_j)])
        pts_ = _hull_stone(rng, corners, chamfer=0.30, frac=(0.07, 0.16))
        origin = (c0[0], c0[1], G0)
        if i in present:
            ss.add([tuple(p) for p in pts_], origin, Rl, kind="voussoir")
        else:
            missing.append((i, pts_, corners))
    # the fallen crown wedges: lie near the foot of the left pier, tilted, half buried
    for k, (i, pts_, corners) in enumerate(missing):
        ang = rng.uniform(-0.6, 0.6)
        rel = np.array([-(r + 0.2) * 0.3 + rng.uniform(-0.3, 0.3), -depth * 0.9 - rng.uniform(0.0, 0.8), 0.0])
        posx = c0 + xl * rel[0] + yl * rel[1]
        mid = np.mean([np.array(p) for p in pts_], axis=0)
        loc = [tuple(np.array(p) - mid) for p in pts_]
        Rf = Matrix.Rotation(rng.uniform(0, math.tau), 3, 'Z') @ Matrix.Rotation(rng.uniform(-0.35, 0.35), 3, 'X') @ Matrix.Rotation(rng.uniform(-0.35, 0.35), 3, 'Y')
        gz = float(ground(np.array([posx[0]]), np.array([posx[1]]))[0])
        ss.add(loc, (posx[0], posx[1], gz + 0.10), Rf, kind="fallen")
    # a heap of small stones in the gap between the piers (under the broken crown): a half-buried first layer, then a few stones resting on it
    heap, first = [], []
    for k in range(7):
        sx = rng.uniform(0.5, 0.85)
        rel = np.array([rng.uniform(-r * 0.7, r * 0.7), rng.uniform(-0.45, 0.45)])
        p = c0 + xl * rel[0] + yl * rel[1]
        gz = float(ground(np.array([p[0]]), np.array([p[1]]))[0])
        sz_h = sx * rng.uniform(0.55, 0.8)
        if ss.stone((p[0], p[1], gz - 0.14), rng.uniform(0, math.tau), sx, sx * rng.uniform(0.6, 1.0), sz_h, top_rag=0.0, chamfer=0.6, tilt=0.06, kind="rubble"):
            first.append((float(p[0]), float(p[1]), gz - 0.14 + sz_h * 0.95))
            heap.append((float(p[0]), float(p[1])))
    for (px, py, tz) in first[:4]:
        sx = rng.uniform(0.32, 0.5)
        ss.stone((px + rng.uniform(-0.1, 0.1), py + rng.uniform(-0.1, 0.1), tz - 0.05), rng.uniform(0, math.tau), sx, sx * rng.uniform(0.6, 1.0), sx * rng.uniform(0.5, 0.75),
                 top_rag=0.0, chamfer=0.6, tilt=0.06, kind="rubble")
    return dict(missing=len(missing), height=max(left_top, right_top), center=tuple(c0), phi=phi_deg, heap=heap)


# --------------------------------------------------------------------------------------------- rubble round the wall feet
def scatter_rubble(ss, pts, T, ground, keep_out, seed, n_per_100m=34.0, along_clear=None):
    """Small irregular stones (0.28-0.65 m) 0.15-1.5 m off the wall faces, half buried. keep_out(x, y) -> True where nothing may lie (the doorway)."""
    rng = random.Random(seed)
    n_made = 0
    for i in range(len(pts) - 1):
        a, b = np.array(pts[i], float), np.array(pts[i + 1], float)
        ln = float(np.hypot(*(b - a)))
        d = (b - a) / ln
        nrm = np.array([-d[1], d[0]])
        for _ in range(max(1, int(round(ln * n_per_100m / 100.0 * 2.2)))):
            s = rng.uniform(0.2, ln - 0.2)
            side = rng.choice((-1, 1))
            off = side * (T * 0.5 + rng.uniform(0.15, 1.5))
            p = a + d * s + nrm * off
            if keep_out(p[0], p[1]):
                continue
            sx = rng.uniform(0.28, 0.65)
            gz = float(ground(np.array([p[0]]), np.array([p[1]]))[0])
            if ss.stone((p[0], p[1], gz - 0.10), rng.uniform(0, math.tau), sx, sx * rng.uniform(0.6, 1.0), sx * rng.uniform(0.45, 0.8), top_rag=0.1, chamfer=0.6, tilt=0.12, kind="rubble"):
                n_made += 1
    return n_made
