"""hole09_masonry.py - rough broken masonry for the Split ruin (POSTCARD_LOOK; repair round 1 + repair round 2, 2026-10-04 / 05).

Replaces PL.build_ruin / PL.build_masonry_arch for hole 9 (the props library is not edited).

Round 1 fixed "stacked Lego boxes, floating slabs and an unsupported lintel" (hulls of tapered stones, support by construction, buried first course, a lintel stone bearing on both
jambs). The round-2 review still found "stacked bricks": 8-9 rectangular courses of near-identical boxes with straight horizontal cut lines, diagonal triangle splits in the shading of
every block face, a regular paving-brick pattern on the tops, a crown that hangs with a gap to the right pier, ruler-straight tops. Causes measured on the round-1 stage (face_stats):
20.7 % of the faces had a loop normal more than 3 deg (up to 28 deg) off their own face normal (smooth shading averaged across the chamfer facets, so a large quad is shaded by 4 different
vertex normals and the triangulation shows as a diagonal), the UV windows were whole brick ROWS (a vertical mortar line ran through most faces), all stones of a course shared one top height.

What this module does now (every number is a constant below):

    shading     every stone is FLAT shaded (loop normal == face normal, so no triangle can shade differently from its neighbour)
    stone       a hull of a tapered, sheared, twisted box (no two faces parallel) with random corner chips (4-13 cm; <= 4 cm on the top of a stone that carries another one). A pillow apex on a face
                (rough_points p_bulge) was tried first and rejected: the hull turns it into a pyramid of 4-6 triangles and flat shading shows them as an X on every face (the review's triangle splits again);
                it is kept in the code at p_bulge = 0
    layout      SKYLINE rubble on wavy bed levels: stones are laid on the lowest run of the wall; a stone's top lands on one of 16 wavy levels of the wall (2-4 cm wave, 7-12 cm jogs, 27-44 cm apart) and
                it spans 1, 2 or 3 of them (height 0.27-0.85 m, length 0.34-2.4 m; 24 % short, 16 % long), so beds are NOT ruled courses; a bed rests on the highest cell of its run (hollow <= 4.5 cm
                + the tilt / chip of the stone below), joints keep >= 12 cm off the joints below where the run allows, depth 0.86-1.0 of the wall with a random out-of-line face (relief)
    tops        the last stone of a column is cut to the broken profile with a steeply sloped / chipped top (ragged), the wall profile is seeded (full stretches, stubs, collapsed gaps)
    doorway     jamb rows (quoin pattern, exact top) + ONE lintel stone bearing 0.55 m on each jamb
    arch        two rubble piers (6.2 m left, 4.4 m right) + a ring of 11 wedge voussoirs: the left half springs from the tall pier and rings up to the crown, the right four wedges are seated IN the
                right pier (its top is above the highest right wedge: nothing pokes out of it); ONE crown wedge (6) is missing and lies in a rubble heap under the gap (round 1: two wedges missing,
                the crown ended in the air beside the right pier and a tilted wedge stood on top of it)
    UV          every face has its OWN UV window inside ONE brick interior of Masonry_C.png (u AND v: no mortar line crosses a face; the interiors are the intersection of a pixel scan and the
                texture generator's own joint table; every face of a stone prefers the same brick, so a stone keeps one tone), 0.3-1.5 x the contract density (tops 0.26 x), random sub-window /
                flip / 90-degree turn for tops: the painted grid cannot read across blocks and the tops are not paving
    blocks      DRESS_BLOCK_A/B variants (make_block_variant): rounded, subdivided, noise-displaced, flat shaded, >= 64 welded vertices, per-face brick-interior UVs

Everything is visual only (DRESS_RUIN_nn_pp / DRESS_ARCH_nn_pp, no collider prefix).
"""
import math
import random
import sys

sys.dont_write_bytecode = True
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix

import postcard_lib as P
import postcard_look_lib as L
import postcard_props_lib as PL

YD = P.YD

# --------------------------------------------------------------------------------------------- constants
BLOCK_L = (0.70, 1.50)        # ordinary stone length along the wall (m)
LONG_L = (1.7, 2.4)           # 16 % of the stones are long stretchers
SHORT_L = (0.34, 0.62)        # 24 % are short headers / chinks
LEVEL_STEP = (0.27, 0.44)     # spacing of the (wavy) bed levels of a wall (m); a stone spans 1 level (72 %), 2 (24 %) or 3 (4 %): heights 0.27-0.85 m
LEVEL_WAVE = (0.015, 0.04)    # amplitude of the bed-level undulation along the wall (m), wavelength 7-14 m
LEVEL_JOG = (0.07, 0.12)      # a level jogs by this much at one place along the wall (70 % of the levels): the course steps up / down
GAP = 0.025                   # gap between neighbouring stones (m, each side)
BURY = (0.25, 0.45)           # the first row sits this far under the lowest ground of its span
FOUND_ABOVE = (0.12, 0.38)    # the first row stands this far over the highest ground of its span
MIN_STACK = 0.30              # a stone is laid at a place only if the broken profile leaves >= 0.30 m of height
MIN_STONE_H = 0.22
LINTEL_H = (0.50, 0.58)
LINTEL_BEARING = 0.55         # the lintel stone bears this far on each jamb (m)
JAMB_ZONE = 1.15              # the quoin rows beside the doorway cover at least this width from the door edge (m)
TIGHT_JOINT = 0.12            # a joint nearer than this to a joint of the stone below is avoided where the run allows
CELL = 0.05                   # skyline resolution (m)
SINK = 0.0                   # a bed is laid this far INTO the highest cell under it. 0.03 was tried (no hollow at all) and reverted: the beds then overlap the stones below and the round-1 ray test calls 94 of them floating
TOP_CHIP = 0.03               # corner chips on the TOP of a stone that carries another stone are at most this big (a notch under a bridging stone is a hollow: 0.05 left 2 of 353 stones with a hollow)
TOL = 0.06                    # a run = neighbouring cells whose tops lie within 6 cm of the lowest one (the hollow under a bed is <= 6 cm)
UV_K_TOP = 0.26
UV_K = (0.30, 1.50)           # per-face UV density as a factor of the contract density (1 / 4 m); verify allows 1/3 .. 3 on the mean and 1/4 .. 4 per edge
MAS_ROW = dict(y0=31.0, period=64.0, pad=9.0, h=46.0, size=512.0)   # px of the brick rows of Masonry_C.png (mortar line centres at y = 31 + 64 k from the bottom)
BRICK_PAD_PX = 6              # a window keeps this far from a mortar column (px)
MIN_SEG_PX = 30               # a brick interior narrower than this is not used

# box corner loops (ix, iy, iz): the faces that get a pillow apex
_FACES = {
    "front": [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],
    "back": [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)],
    "top": [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
    "left": [(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)],
    "right": [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)],
}


# --------------------------------------------------------------------------------------------- brick interiors of Masonry_C.png
_SEGS = None


def _generator_joints(seed=1001, courses=8):
    """u of the vertical mortar joints of every course of Masonry_C.png, re-derived from the texture generator's own random tables (golf_look_textures.mat_masonry draws, per course,
    nb = integers(4, 8), the brick widths uniform(0.6, 1.4, nb) and a phase, from default_rng([seed, 1])). Generator course j is centred on v = j / courses."""
    rng_ = np.random.default_rng([seed, 1])
    out = []
    for _k in range(courses):
        nb = int(rng_.integers(4, 8))
        w = rng_.uniform(0.6, 1.4, nb)
        cb = np.concatenate([[0.0], np.cumsum(w) / w.sum()])
        ph = float(rng_.random())
        out.append(sorted(((cb[i] - ph) % 1.0) for i in range(nb)))
    return out


def brick_segments():
    """Brick interiors of Masonry_C.png as [(u0, u1, v0, v1)] (uv units; v1 may exceed 1 for the top row: the texture tiles). Two independent sources are intersected: (a) the pixels: the 8 brick
    rows (MAS_ROW) are scanned for vertical mortar columns (darker than the row median by 0.07), each widened by BRICK_PAD_PX; (b) the generator's own joint table (_generator_joints), each joint
    widened by BRICK_PAD_PX + 1 px. A run between joints that is wider than MIN_SEG_PX in both is a brick interior (the pixel scan alone missed 5 of the 46 joints)."""
    global _SEGS
    if _SEGS is not None:
        return _SEGS
    import os
    path = os.path.join(L.LOOK_DIR, "Masonry_C.png")
    had = bpy.data.images.get("Masonry_C.png")
    img = bpy.data.images.load(path, check_existing=True)
    W, H = img.size
    a = np.empty(W * H * 4, np.float32)
    img.pixels.foreach_get(a)
    lum = a.reshape(H, W, 4)[..., :3].mean(-1)                       # row 0 = bottom of the image
    if had is None:
        bpy.data.images.remove(img)
    joints = _generator_joints()
    segs = []
    h_px = int(MAS_ROW["h"])
    for k in range(8):
        y0 = int(MAS_ROW["y0"] + MAS_ROW["period"] * k + MAS_ROW["pad"])
        prof = lum[[(y0 + j) % H for j in range(h_px)]].mean(0)
        sm = np.convolve(np.r_[prof[-2:], prof, prof[:2]], np.ones(5) / 5.0, mode="valid")
        mort = sm < (np.median(sm) - 0.07)
        for jb in joints[(k + 1) % 8]:                               # my row k (bed + 9 .. bed + 55 px) is generator course k + 1
            c = int(round(jb * W)) % W
            for d_ in range(-2, 3):
                mort[(c + d_) % W] = True
        wide = mort.copy()
        for sft in range(1, BRICK_PAD_PX + 2):
            wide |= np.roll(mort, sft) | np.roll(mort, -sft)
        j = 0
        while j < W:
            if wide[j]:
                j += 1
                continue
            e = j
            while e < W and not wide[e]:
                e += 1
            if e - j >= MIN_SEG_PX and j > 0 and e < W:                  # runs that touch the tile edge wrap around: skipped
                segs.append((j / float(W), e / float(W), y0 / float(H), (y0 + h_px) / float(H)))
            j = e
    _SEGS = segs
    return segs


def uv_window(rng, w, h, kmin, kmax, widest=False, pref=None):
    """(u0, v0, k): a window of size (k*w, k*h) uv inside one brick interior, kmin <= k <= kmax (uv per metre). pref = index of the brick the stone prefers (every face of a stone takes
    a window of the SAME brick when it fits, so a stone keeps one tone and neighbouring stones differ); widest: the lintel's long faces take the widest interior at kmin."""
    segs = brick_segments()
    if widest:
        s = max(segs, key=lambda q: (q[1] - q[0]))
        k = kmin
        return rng.uniform(s[0], max(s[0], s[1] - k * w)), rng.uniform(s[2], max(s[2], s[3] - k * h)), k
    order = ([pref] if pref is not None else []) + [rng.randrange(len(segs)) for _ in range(60)]
    for idx in order:
        s = segs[idx]
        k = min((s[1] - s[0]) / max(w, 1e-3), (s[3] - s[2]) / max(h, 1e-3), kmax)
        if k < kmin:
            continue
        k = rng.uniform(max(kmin, 0.75 * k), k)
        return rng.uniform(s[0], s[1] - k * w), rng.uniform(s[2], s[3] - k * h), k
    s = max(segs, key=lambda q: (q[1] - q[0]) * (q[3] - q[2]))
    return s[0], s[2], kmin


def _face_uv(rng, pts, widest=False, pref=None):
    """UV of one polygon (list of Vector / xyz): a brick-interior window in the polygon's own plane axes (a standing face: u along the face, v up; a top / bottom face: a random 90-degree turn)."""
    p = np.array([tuple(q) for q in pts], float)
    n = np.zeros(3)
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        n += np.array([(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])])
    ln = float(np.linalg.norm(n))
    n = n / ln if ln > 1e-12 else np.array([0.0, 0.0, 1.0])
    kd = 1.0 / L.LOOK["LK_MASONRY"][2]
    if abs(n[2]) < 0.75:
        up = np.array([0.0, 0.0, 1.0])
        vax = up - n * float(up @ n)
        vax /= max(float(np.linalg.norm(vax)), 1e-9)
        uax = np.cross(vax, n)
        a, b = p @ uax, p @ vax
        flip = rng.random() < 0.5
    else:
        ang = rng.choice((0.0, 0.5 * math.pi, math.pi, 1.5 * math.pi)) + rng.uniform(-0.25, 0.25)
        c, s = math.cos(ang), math.sin(ang)
        a, b = c * p[:, 0] - s * p[:, 1], s * p[:, 0] + c * p[:, 1]
        flip = rng.random() < 0.5
    w, h = float(a.max() - a.min()), float(b.max() - b.min())
    kmin = (UV_K[0] if abs(n[2]) < 0.75 else UV_K_TOP) * kd                 # a top face may be up to 1.7 m across: it gets a slightly lower density (UV_DENSITY: per-edge floor is 1/4)
    u0, v0, k = uv_window(rng, max(w, 0.04), max(h, 0.04), kmin, UV_K[1] * kd, widest=widest, pref=pref)
    if flip:
        return [(u0 + k * float(a.max() - a[i]), v0 + k * float(b[i] - b.min())) for i in range(len(p))]
    return [(u0 + k * float(a[i] - a.min()), v0 + k * float(b[i] - b.min())) for i in range(len(p))]


# --------------------------------------------------------------------------------------------- stone shapes
def _box_corners(rng, sx, sy, sz, top_rag=0.0):
    """8 corners (ix, iy, iz in {0, 1}) of a hand-hewn block: origin = centre of the bottom face, x along the wall, y thickness, z up. A box pushed through a random taper + shear (no two faces
    parallel) with a tilted top plane; top_rag lowers and slopes the top steeply (a broken top: up to ~40 % of the height at one corner)."""
    tx, ty = rng.uniform(-0.04, 0.05), rng.uniform(-0.05, 0.05)
    shx, shy = rng.uniform(-0.05, 0.05) * sz, rng.uniform(-0.05, 0.05) * sz
    twist = rng.uniform(-0.03, 0.03)
    sl_x, sl_y = rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06)
    drop = rng.uniform(0.0, 0.04) + top_rag * rng.uniform(0.15, 0.45)
    rag_x, rag_y = top_rag * rng.uniform(-1.1, 1.1), top_rag * rng.uniform(-0.8, 0.8)
    C = {}
    for ix in (0, 1):
        for iy in (0, 1):
            for iz in (0, 1):
                u, v = (ix - 0.5), (iy - 0.5)
                x, y = u * sx * (1.0 + tx * (iz * 2 - 1)), v * sy * (1.0 + ty * (iz * 2 - 1))
                if iz:
                    c, sn = math.cos(twist), math.sin(twist)
                    x, y = c * x - sn * y, sn * x + c * y
                    x, y = x + shx, y + shy
                    z = sz * (1.0 - drop - (sl_x + rag_x) * u - (sl_y + rag_y) * v)
                    z = max(z, 0.18 * sz)
                else:
                    z = sz * 0.012 * (u + v)                       # the bed is almost flat
                C[(ix, iy, iz)] = np.array([x, y, z])
    return C


def rough_points(rng, C, loops=None, bulge_faces=("front", "back", "top"), chamfer=0.35, chip=(0.04, 0.13), bulge=(0.008, 0.016), p_bulge=0.0, top_chip=None):
    """Points of a chipped stone: every corner of C is kept or replaced by its 3 chamfer points (an edge fraction capped at 40 %, chip[0]..chip[1] m: a chipped corner; top_chip caps the chips of the
    top corners); with p_bulge > 0 a face in `bulge_faces` may get one apex pushed out (a pillow: the hull makes a pyramid of facets; OFF by default, see the module docstring). Convex hull = planar facets."""
    loops = loops or _FACES
    ctr = np.mean([v for v in C.values()], axis=0)
    pts = []
    for key, p in C.items():
        if rng.random() < chamfer:
            for ax in range(3):
                nb = list(key)
                nb[ax] ^= 1
                q = C[tuple(nb)]
                e = q - p
                ln = float(np.linalg.norm(e))
                cap = chip[1] if (top_chip is None or key[2] == 0) else min(chip[1], top_chip)     # a stone that carries another one keeps its top corners (a notch under a bridging stone is a hollow)
                pts.append(p + e / max(ln, 1e-9) * min(rng.uniform(chip[0], max(chip[0], cap)), 0.4 * ln))
        else:
            pts.append(p)
    for name in bulge_faces:
        if rng.random() > p_bulge:
            continue
        loop = [C[k] for k in loops[name]]
        e1, e2 = loop[1] - loop[0], loop[3] - loop[0]
        dims = (float(np.linalg.norm(e1)), float(np.linalg.norm(e2)))
        if min(dims) < 0.22:
            continue
        nrm = np.cross(e1, e2)
        nrm /= max(float(np.linalg.norm(nrm)), 1e-9)
        fc = np.mean(loop, axis=0)
        if float(nrm @ (fc - ctr)) < 0:
            nrm = -nrm
        b = min(rng.uniform(*bulge), 0.10 * min(dims))
        pts.append(fc + e1 * rng.uniform(-0.18, 0.18) + e2 * rng.uniform(-0.18, 0.18) + nrm * b)
    return pts


class StoneSet:
    """Collects stones into DRESS_<kind>_<nn>_<pp> meshes of <= max_faces faces (LK_MASONRY, per-face brick-interior UV windows, FLAT shading)."""

    def __init__(self, D, prefix, seed, clip=None, max_faces=420):
        self.D, self.prefix = D, prefix
        self.rng = random.Random(seed)
        self.clip = clip                       # clip(X, Y) -> bool array: every vertex of a stone must pass
        self.base = L._next_name(D, prefix)
        self.mat = L.look_material("LK_MASONRY", D)
        self.max_faces = max_faces
        self.part = 0
        self.objs = []
        self.n_blocks = 0
        self.n_refused = 0
        self.refused = []                      # (x, y) of every refused stone
        self.records = []                      # (kind, bottom z, centre x, y) of every stone (for the report)
        self.tris = 0
        self._reset()

    def _reset(self):
        self.V, self.F, self.UV = [], [], []

    def flush(self):
        if not self.F:
            return
        name = f"{self.base}_{self.part:02d}"
        ob = L._new_piece(self.D, name, self.V, self.F, self.UV, [0] * len(self.F), [self.mat], col="STRUCTURES", sharp_deg=32.0)
        ob.data.shade_flat()                   # loop normal == face normal: no diagonal shading steps inside a face
        ob.data.update()
        ob["h9_class"] = "masonry"
        self.objs.append(ob)
        self.part += 1
        self._reset()

    def add(self, local_pts, origin, R, kind="block", widest_uv=False):
        """Add one stone: hull of local_pts, placed at origin (world, m) with the 3x3 rotation R. Returns True when it was kept (every vertex passes the clip)."""
        verts, faces = PL._hull(local_pts, merge=0.012, dissolve_deg=0.8)
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
        pref = self.rng.randrange(len(brick_segments()))
        for f in faces:
            self.F.append(tuple(base + i for i in f))
            self.UV.append(_face_uv(self.rng, [W[i] for i in f], widest=widest_uv, pref=pref))
            self.tris += max(1, len(f) - 2)
        self.n_blocks += 1
        self.records.append((kind, float(min(w.z for w in W)), float(origin[0]), float(origin[1])))
        return True

    def stone(self, origin, yaw, sx, sy, sz, top_rag=0.0, chamfer=0.35, tilt=0.015, kind="block", bulge_faces=("front", "back", "top"), widest_uv=False, top_chip=None):
        rng = self.rng
        R = Matrix.Rotation(yaw, 3, 'Z') @ Matrix.Rotation(rng.uniform(-tilt, tilt), 3, 'X') @ Matrix.Rotation(rng.uniform(-tilt, tilt), 3, 'Y')
        return self.add(rough_points(rng, _box_corners(rng, sx, sy, sz, top_rag), None, bulge_faces, chamfer, top_chip=top_chip), origin, R, kind, widest_uv)


# --------------------------------------------------------------------------------------------- walls (skyline rubble)
def make_profile(rng, total, hmax_of_s, door=None):
    """Broken height profile h(s) (m above the ground) along the path of length `total`: random control points every ~1.9 m (full stretches, stubs, collapsed gaps),
    low at both free ends, never lower than `door[2]` within door[1]/2 + 0.6 m of the doorway axis door[0] (then stepping down over 2.4 m)."""
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
        if door is not None:
            k = min(1.0, max(0.0, 1.0 - (abs(s - door[0]) - (door[1] / 2 + 0.6)) / 2.4))
            out = max(out, door[2] * k)
        return out
    return h


def _draw_len(rng, block_l):
    r = rng.random()
    if r < 0.16:
        return rng.uniform(*LONG_L)
    if r < 0.40:
        return rng.uniform(*SHORT_L)
    return rng.uniform(*block_l)


def lay_wall(ss, rng, a, d, ln, T, ground, prof, s_lo, s_hi, door=None, block_l=BLOCK_L, end_jitter=0.0, tag=0):
    """Skyline-laid rubble wall along the segment a + d*s (s in [s_lo, s_hi], a = start point (world m), d = unit direction, ln = segment length). prof(s) = broken profile (m above the ground,
    s from a). door = (s_door, width, top z (world, m)) or None. Stones are laid on the LOWEST open run of the wall: its bed rests on the highest cell under it (hollow <= TOL), its height is drawn
    per stone (so beds are not ruled courses), the last stone of a column is cut to the profile with a steep sloped top. Returns dict(stones=[(s0, s1, zbot, ztop)], lintel, jamb, drops, ...)."""
    nrm = np.array([-d[1], d[0]])
    yaw0 = math.atan2(d[1], d[0])
    n = max(2, int(round((s_hi - s_lo) / CELL)))
    sc = s_lo + (np.arange(n) + 0.5) * CELL
    gx, gy = a[0] + d[0] * sc, a[1] + d[1] * sc
    g = np.asarray(ground(gx, gy), float)
    if not np.isfinite(g).all():
        g = np.where(np.isfinite(g), g, float(np.nanmean(g)))
    target = g + np.array([prof(float(min(max(s, 0.0), ln))) for s in sc])
    sky = g.copy()
    is_gr = np.ones(n, bool)
    closed = np.zeros(n, bool)
    joint = np.zeros(n, bool)
    stones, drops = [], []
    out = dict(stones=stones, drops=drops, lintel=0, jamb=None)

    def cells(s0, s1):
        return max(0, int(round((s0 - s_lo) / CELL))), min(n, int(round((s1 - s_lo) / CELL)))

    def put(s0, s1, zb, h, depth, dy, rag, kind="wall", chamfer=0.35, tilt=0.015, yaw_j=0.025):
        """One stone over [s0, s1] (along the wall, joints included): returns True when it was made."""
        sm = 0.5 * (s0 + s1)
        cpos = np.array(a) + d * sm + nrm * dy
        ok = ss.stone((cpos[0], cpos[1], zb), yaw0 + rng.uniform(-yaw_j, yaw_j), (s1 - s0) - 2 * GAP, depth, max(MIN_STONE_H, h), top_rag=rag, chamfer=chamfer, tilt=tilt, kind=kind,
                      widest_uv=(kind == "lintel"), top_chip=(None if rag > 0.0 else TOP_CHIP))
        if ok:
            c0, c1 = cells(s0, s1)
            sky[c0:c1] = zb + max(MIN_STONE_H, h) * 0.97          # a little below the nominal top: the next bed interpenetrates the real (tilted, chipped) top instead of floating over it
            is_gr[c0:c1] = False
            joint[c0:c1] = False
            joint[c0] = True
            joint[max(c0, c1 - 1)] = True
            stones.append((s0, s1, zb, zb + h))
        return ok

    # ---------------------------------------------------------------- phase 1: the doorway (quoin rows beside the opening, then ONE lintel stone)
    if door is not None:
        sd, w, z_door = door
        e_l, e_r = sd - w / 2, sd + w / 2
        c0, c1 = cells(e_l, e_r)
        closed[c0:c1] = True                                           # the opening stays clear below the lintel
        sky[c0:c1] = z_door
        is_gr[c0:c1] = False
        rows_zb = None
        covered = {-1: e_l, 1: e_r}
        for side in (-1, 1):
            edge = e_l if side < 0 else e_r
            far = edge + side * 1.9
            ca, cb = cells(min(edge, far), max(edge, far))
            gmax = float(g[ca:cb].max()) if cb > ca else float(g[min(max(c0, 0), n - 1)])
            top0 = gmax + rng.uniform(*FOUND_ABOVE)
            nrow = max(3, int(round((z_door - top0) / 0.47)))
            wts = [rng.uniform(0.85, 1.15) for _ in range(nrow)]
            span = z_door - top0
            bounds = [top0]
            for x_ in wts:
                bounds.append(bounds[-1] + span * x_ / sum(wts))
            bounds[-1] = z_door
            x_prev = None
            for k in range(-1, nrow):                                  # row -1 = the foundation row (buried), row k >= 0 = bounds[k] .. bounds[k + 1]
                # every row ends at or before the end of the row below (its last stone always rests on it: no cantilevered stone) and at least JAMB_ZONE from the door edge; the outer ends differ row to row (no ruler joint line)
                X = rng.uniform(1.5, 2.1) if x_prev is None else min(max(rng.uniform(x_prev - 0.6, x_prev), JAMB_ZONE), x_prev)
                first = min(rng.uniform(1.0, 1.3) if (k % 2 == 0) else rng.uniform(0.8, 1.0), X)
                lens, x_ = [first], first
                while x_ < X - 0.45:
                    ln_ = min(rng.uniform(*block_l), X - x_)
                    if X - x_ - ln_ < 0.45:
                        ln_ = X - x_
                    lens.append(ln_)
                    x_ += ln_
                x_prev = x_
                pos = edge
                for ln_ in lens:
                    s_a, s_b = (pos, pos + side * ln_) if side > 0 else (pos - ln_, pos)
                    s_a, s_b = max(s_a, s_lo), min(s_b, s_hi)
                    pos += side * ln_
                    if s_b - s_a < 0.3:
                        continue
                    ia, ib = cells(s_a, s_b)
                    if k < 0:
                        gmin_ = float(g[ia:ib].min())
                        zb = gmin_ - rng.uniform(*BURY)
                        top = bounds[0] - rng.uniform(0.0, 0.03)
                    else:
                        zb = bounds[k] - 0.02
                        top = bounds[k + 1] - rng.uniform(0.0, 0.02)
                    ok = put(s_a, s_b, zb, top - zb, T * rng.uniform(0.95, 1.0), rng.uniform(-0.02, 0.02), 0.0, kind="jamb", chamfer=0.30, tilt=0.008, yaw_j=0.012)
                    if side > 0 and ok:
                        covered[1] = max(covered[1], s_b)
                    if side < 0 and ok:
                        covered[-1] = min(covered[-1], s_a)
        l0, l1 = max(s_lo, e_l - LINTEL_BEARING), min(s_hi, e_r + LINTEL_BEARING)
        ia, ib = cells(l0 + 0.25, e_l)
        ja, jb = cells(e_r, l1 - 0.25)
        jam_ok = bool(ib > ia and jb > ja and (sky[ia:ib] >= z_door - 0.04).all() and (sky[ja:jb] >= z_door - 0.04).all())
        out["jamb"] = (jam_ok, round(l0, 2), round(l1, 2), [round(covered[-1], 2), round(covered[1], 2)])
        if jam_ok:
            lh = rng.uniform(*LINTEL_H)
            if put(l0, l1, z_door + 0.006, lh, T * rng.uniform(0.96, 1.0), 0.0, 0.0, kind="lintel", chamfer=0.25, tilt=0.006, yaw_j=0.01):
                out["lintel"] = 1
                ia, ib = cells(l0, l1)
                sky[ia:ib] = z_door + lh
                closed[c0:c1] = False                                   # the wall continues over the lintel
        out["door_s"] = sd

    # ---------------------------------------------------------------- phase 2: skyline fill up to the broken profile
    # bed levels of this wall: level k is a WAVY line (amplitude 2-6 cm, wavelength 5-11 m) with one JOG (7-12 cm step) at a random place for 70 % of the levels, spaced 27-44 cm apart.
    # A stone's top lands on one of them (+-1.5 cm) and a stone may span 2 or 3 levels, so neighbouring stones of a course share a bed line within the run tolerance (a running bond is possible)
    # but no bed is a ruler line and no two courses are alike.
    gref = float(np.median(g))
    lev = []
    Bk = gref + rng.uniform(0.16, 0.30)
    for _ in range(16):
        lev.append(dict(B=Bk, amp=rng.uniform(*LEVEL_WAVE), lam=rng.uniform(7.0, 14.0), ph=rng.uniform(0.0, 2 * math.pi), sp=rng.uniform(s_lo, s_hi),
                        sa=(rng.choice((-1.0, 1.0)) * rng.uniform(*LEVEL_JOG)) if rng.random() < 0.7 else 0.0))
        Bk += rng.uniform(*LEVEL_STEP)

    def level(k, s):
        q = lev[k]
        return q["B"] + q["amp"] * math.sin(2 * math.pi * s / q["lam"] + q["ph"]) + (q["sa"] if s > q["sp"] else 0.0)
    open_ = (~closed) & ((target - sky) >= MIN_STACK)
    guard = 0
    while open_.any() and guard < 6000:
        guard += 1
        idx = np.flatnonzero(open_)
        m = float(sky[idx].min())
        i = int(idx[np.flatnonzero(sky[idx] <= m + 0.03)[0]])
        gr = bool(is_gr[i])
        j0 = j1 = i
        while j0 > 0 and open_[j0 - 1] and bool(is_gr[j0 - 1]) == gr and (gr or sky[j0 - 1] <= m + TOL + 0.03):
            j0 -= 1
        while j1 < n - 1 and open_[j1 + 1] and bool(is_gr[j1 + 1]) == gr and (gr or sky[j1 + 1] <= m + TOL + 0.03):
            j1 += 1
        wr = (j1 - j0 + 1) * CELL
        if wr < 0.2:                                                    # a crack between two stones: left open (nothing fits)
            closed[j0:j1 + 1] = True
            open_[j0:j1 + 1] = False
            drops.append(("crack", round(s_lo + j0 * CELL, 2), round(wr, 2)))
            continue
        best = None
        for _ in range(8):
            wl = _draw_len(rng, block_l)
            if wr - wl < 0.45 or wl > wr:
                wl = wr
            elif wr > 2.4 and wl > wr - 0.45:
                wl = wr - 0.45
            side_left = (j0 == 0) or (j1 < n - 1 and rng.random() < 0.5)
            x0 = (s_lo + j0 * CELL) if side_left else (s_lo + (j1 + 1) * CELL - wl)
            c_a, c_b = cells(x0, x0 + wl)
            pen = 0
            if not gr:
                for cj in (c_a, c_b - 1):
                    lo_, hi_ = max(0, cj - int(TIGHT_JOINT / CELL)), min(n, cj + int(TIGHT_JOINT / CELL) + 1)
                    pen += int(joint[lo_:hi_].any())
            cand = (pen, rng.random(), x0, wl)
            if best is None or cand[:2] < best[:2]:
                best = cand
        _, _, x0, wl = best
        c_a, c_b = cells(x0, x0 + wl)
        c_b = max(c_b, c_a + 1)
        s_mid = x0 + 0.5 * wl
        rag = 0.0
        if gr:
            gmin, gmax = float(g[c_a:c_b].min()), float(g[c_a:c_b].max())
            zb = gmin - rng.uniform(*BURY)
            top = max(level(0, s_mid) + rng.uniform(-0.015, 0.015), gmax + 0.12)
            rem = float(target[c_a:c_b].mean()) - gmax
            if rem < top - gmax:                                       # the broken profile ends inside the foundation row
                top = gmax + max(0.12, rem * rng.uniform(0.9, 1.1))
            h = top - zb
        else:
            zb = float(sky[c_a:c_b].max()) - SINK
            rem = float(target[c_a:c_b].mean()) - zb
            if rem < MIN_STACK:
                closed[c_a:c_b] = True
                open_[c_a:c_b] = False
                drops.append(("profile", round(x0, 2), round(wl, 2)))
                continue
            k_ = 1
            while k_ < len(lev) - 1 and level(k_, s_mid) - zb < 0.26:
                k_ += 1
            r_ = rng.random()
            span_ = 1 if r_ < 0.72 else 2 if r_ < 0.96 else 3
            kk_ = min(len(lev) - 1, k_ + span_ - 1)
            while kk_ > k_ and level(kk_, s_mid) - zb > 0.85:
                kk_ -= 1
            h = level(kk_, s_mid) + rng.uniform(-0.015, 0.015) - zb
            if h > rem - 0.02 or rem - h < MIN_STACK:                  # the top of the column: cut to the broken profile (a steeply sloped, chipped top)
                h = min(0.80, max(0.25, rem * rng.uniform(0.80, 1.10)))
                rag = rng.uniform(0.30, 0.70)
        x1 = x0 + wl
        ej = end_jitter
        if ej > 0.0:                                                    # ragged wall / pier ends: the end stones stick out or stand back
            if j0 == 0 and x0 <= s_lo + 1e-6:
                x0 -= rng.uniform(-ej, ej)
            if j1 == n - 1 and x1 >= s_hi - 1e-6:
                x1 += rng.uniform(-ej, ej)
        depth = T * rng.uniform(0.86, 1.0)                              # >= 0.86 of the wall: two stones on top of each other always share >= 72 % of their depth (a thinner stone could overhang the one below)
        dy = rng.uniform(-1.0, 1.0) * (T - depth) * 0.5 + rng.uniform(-0.03, 0.03)
        if not put(x0, x1, zb, h, depth, dy, rag):
            closed[c_a:c_b] = True
            open_[c_a:c_b] = False
            drops.append(("clip", round(x0, 2), round(wl, 2)))
            continue
        if rag > 0.0:                                                   # a broken top: nothing is ever laid on it (its real top is tilted / chipped far below the nominal one)
            closed[c_a:c_b] = True
        open_[c_a:c_b] = (~closed[c_a:c_b]) & ((target[c_a:c_b] - sky[c_a:c_b]) >= MIN_STACK)
    out["guard"] = guard
    out["levels"] = len(lev)
    return out


def build_wall_path(ss, pts, seg_h, T, door, seed, ground, G0, block_l=BLOCK_L, end_jitter=0.05):
    """Rubble wall along the polyline pts (world metres): segment i = pts[i] -> pts[i + 1], seg_h[i] = max height of the segment (m above the ground), T = wall thickness, door = (segment index,
    centre s along that segment, clear width, clear height above G0) or None. The corners are butt joints: the earlier segment runs T/2 past the corner point, the next one starts T/2 after it.
    Returns dict(blocks, joints, tight, lintels, jamb, door_world, per_course, drops)."""
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
    prof = make_profile(rng, tot, hmax_of_s, door=door_g)
    stat = dict(blocks=0, joints=0, tight=0, lintels=0, per_course={}, drops=[])
    all_st = []
    for i, (a, b, ln, d) in enumerate(segs):
        s_lo = 0.0 if i == 0 else 0.5 * T
        s_hi = ln + 0.5 * T if i < len(segs) - 1 else ln
        dr = None if (door is None or door[0] != i) else (door[1], door[2], G0 + door[3])
        r = lay_wall(ss, rng, a, d, ln, T, ground, lambda s, i=i: prof(s0g[i] + min(max(s, 0.0), ln)), s_lo, s_hi, door=dr, block_l=block_l, end_jitter=end_jitter if i in (0, len(segs) - 1) else 0.0)
        st = r["stones"]
        stat["blocks"] += len(st)
        stat["lintels"] += r["lintel"]
        stat["per_course"][i] = len(st)
        stat["drops"] += [(i,) + tuple(x_) for x_ in r["drops"]]
        if r["jamb"] is not None:
            stat["jamb"] = r["jamb"]
        all_st.append(st)
        for k, (s0, s1, zb, zt) in enumerate(st):                       # joints within TIGHT_JOINT of a joint of a stone directly below
            for (c0, c1, zb2, zt2) in st:
                if abs(zt2 - zb) < 0.08 and c0 < s1 and c1 > s0:
                    for x in (s0, s1):
                        if c0 + 0.0 < x < c1 - 0.0:
                            stat["tight"] += int(abs(x - c0) < TIGHT_JOINT or abs(x - c1) < TIGHT_JOINT)
            stat["joints"] += 2
    if door is not None:
        a, b, ln, d = segs[door[0]]
        stat["door_world"] = tuple(a + d * door[1])
    stat["segments"] = len(segs)
    return stat


# --------------------------------------------------------------------------------------------- arch
def build_arch(ss, center, phi_deg, ground, G0, r=2.0, t=0.75, depth=1.3, pier_w=1.7, spring=2.7, left_top=6.2, right_top=4.4, seed=0, missing=(6,)):
    """Broken masonry arch: two rubble piers + a ring of 11 wedge voussoirs. center = (x, y) midway between the piers (world, m); phi_deg = the direction you look THROUGH the opening (clockwise
    from +Y, the postcard_lib build_arch convention). The wedges in `missing` (the crown, 6 and 7 of 0..10) lie in a rubble heap under the gap; the left ring (0..5) rings up to the crown from the
    tall left pier, the right springers (8, 9, 10) are seated IN the right pier (its top is above the highest right wedge, so no stone pokes out of it). Returns dict(missing, height, centre, heap)."""
    rng = random.Random(seed)
    phi = math.radians(phi_deg)
    xl = np.array([math.cos(phi), -math.sin(phi)])            # across the opening (local x)
    yl = np.array([math.sin(phi), math.cos(phi)])             # through the opening (local y)
    c0 = np.array(center, float)
    st_piers = []
    for side, top in ((-1, left_top), (1, right_top)):
        a = c0 + xl * side * (r + pier_w)
        b = c0 + xl * side * r
        p0, p1 = (a, b) if side < 0 else (b, a)
        dd = (p1 - p0) / np.hypot(*(p1 - p0))
        ph = rng.uniform(0, 6.0)
        # the pier is a short wall across the opening, `depth` thick; its broken top swings +-18 % (never below the springer on the opening side)
        prof = (lambda s_, top=top, ph=ph: top * (0.82 + 0.18 * math.sin(2.1 * s_ + ph)))
        rr = lay_wall(ss, rng, p0, dd, pier_w, depth, ground, prof, 0.0, pier_w, door=None, block_l=(0.45, 1.0), end_jitter=0.07)
        st_piers.append(len(rr["stones"]))
    n = 11
    Rl = Matrix.Rotation(-phi, 3, 'Z')
    fallen = []
    for i in range(n):
        th0 = i * math.pi / n + 0.006
        th1 = (i + 1) * math.pi / n - 0.006
        corners = {}
        dy = depth * rng.uniform(0.9, 1.0)
        for ia, th in ((0, th0), (1, th1)):
            for iy in (0, 1):
                for ir, rad in ((0, r - 0.03), (1, r + t)):
                    rr_ = rad + rng.uniform(-0.02, 0.02)
                    th_j = th + rng.uniform(-0.005, 0.005)
                    # key (ia, iy, ir) with ir in the z slot of the loops below: loops map (ix = ia, iy, iz = ir)
                    corners[(ia, iy, ir)] = np.array([-rr_ * math.cos(th_j), (iy - 0.5) * dy * (1.0 + rng.uniform(-0.04, 0.04)), spring + rr_ * math.sin(th_j)])
        # faces of a wedge by corner keys (ia, iy, ir): intrados ir = 0, extrados ir = 1, front / back iy = 1 / 0
        wl = {"intrados": [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], "extrados": [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
              "front": [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)], "back": [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]}
        pts_ = rough_points(rng, corners, wl, (), chamfer=0.15, chip=(0.03, 0.08))
        origin = (c0[0], c0[1], G0)
        if i in missing:
            fallen.append((i, pts_))
        else:
            ss.add([tuple(p) for p in pts_], origin, Rl, kind="voussoir")
    # the fallen crown wedges: lie in the heap under the gap, tilted, half buried
    heap, first = [], []
    for k, (i, pts_) in enumerate(fallen):
        mid = np.mean([np.array(p) for p in pts_], axis=0)
        loc = [tuple(np.array(p) - mid) for p in pts_]
        rel = np.array([rng.uniform(-0.55, 0.55), rng.uniform(-0.7, -0.2) if k == 0 else rng.uniform(0.2, 0.7)])
        posx = c0 + xl * rel[0] + yl * rel[1]
        Rf = Matrix.Rotation(rng.uniform(0, math.tau), 3, 'Z') @ Matrix.Rotation(rng.uniform(-0.45, 0.45), 3, 'X') @ Matrix.Rotation(rng.uniform(-0.45, 0.45), 3, 'Y')
        gz = float(ground(np.array([posx[0]]), np.array([posx[1]]))[0])
        ss.add(loc, (posx[0], posx[1], gz + 0.16), Rf, kind="fallen")
    # a heap of small stones round the fallen wedges (under the broken crown): a half-buried first layer, then a few stones resting on it
    for k in range(9):
        sx = rng.uniform(0.45, 0.85)
        ang = rng.uniform(0, math.tau)
        rad_ = rng.uniform(0.2, 1.5)
        rel = np.array([math.cos(ang) * rad_ * 1.1, math.sin(ang) * rad_ * 0.5])
        p = c0 + xl * rel[0] + yl * rel[1]
        gz = float(ground(np.array([p[0]]), np.array([p[1]]))[0])
        sz_h = sx * rng.uniform(0.55, 0.8)
        if ss.stone((p[0], p[1], gz - 0.14), rng.uniform(0, math.tau), sx, sx * rng.uniform(0.6, 1.0), sz_h, top_rag=0.0, chamfer=0.6, tilt=0.06, kind="rubble", bulge_faces=("top",)):
            first.append((float(p[0]), float(p[1]), gz - 0.14 + sz_h * 0.95))
            heap.append((float(p[0]), float(p[1])))
    for (px, py, tz) in first[:4]:
        sx = rng.uniform(0.32, 0.5)
        ss.stone((px + rng.uniform(-0.1, 0.1), py + rng.uniform(-0.1, 0.1), tz - 0.05), rng.uniform(0, math.tau), sx, sx * rng.uniform(0.6, 1.0), sx * rng.uniform(0.5, 0.75),
                 top_rag=0.0, chamfer=0.6, tilt=0.06, kind="rubble", bulge_faces=())
    return dict(missing=len(fallen), height=max(left_top, right_top), center=tuple(c0), phi=phi_deg, heap=heap, pier_stones=st_piers)


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
            if ss.stone((p[0], p[1], gz - 0.10), rng.uniform(0, math.tau), sx, sx * rng.uniform(0.6, 1.0), sx * rng.uniform(0.45, 0.8), top_rag=0.1, chamfer=0.6, tilt=0.12, kind="rubble",
                        bulge_faces=("top",) if sx > 0.4 else ()):
                n_made += 1
    return n_made


# --------------------------------------------------------------------------------------------- DRESS_BLOCK variants (fallen blocks)
def make_block_variant(name, seed, dims=(1.1, 0.6, 0.5), grid=(3, 2, 2), p_norm=5.0):
    """A fallen cut block as a mesh: a rounded (superellipsoid-ish), subdivided, noise-displaced box (>= 64 welded vertices), flat shaded, per-face brick-interior UVs (LK_MASONRY). The mesh
    stands on z = 0 (origin at the centre of the bottom, like the library DRESS_BLOCK_x). Returns the bpy mesh (no object)."""
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=max(grid), use_grid_fill=True)
    sx, sy, sz = dims
    # rounded cube: pull the corners / edges in along the diagonal (p-norm), then non-uniform scale, taper, shear, noise
    tx, ty = rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05)
    shx, shy = rng.uniform(-0.04, 0.04) * sz, rng.uniform(-0.04, 0.04) * sz
    for v in bm.verts:
        x, y, z = v.co
        nrm = (abs(x) ** p_norm + abs(y) ** p_norm + abs(z) ** p_norm) ** (1.0 / p_norm)
        k = 1.0 / max(nrm, 1e-6)
        x, y, z = x * k, y * k, z * k
        zt = (z + 1.0) * 0.5
        X = x * 0.5 * sx * (1.0 + tx * (zt * 2 - 1)) + shx * zt
        Y = y * 0.5 * sy * (1.0 + ty * (zt * 2 - 1)) + shy * zt
        Z = zt * sz
        v.co = Vector((X, Y, Z))
    bm.normal_update()
    for v in bm.verts:
        v.co += v.normal * rng.uniform(-0.010, 0.010)
    bm.verts.ensure_lookup_table()
    # flat bed: the lowest ring is flattened onto z = 0
    for v in bm.verts:
        if v.co.z < 0.04 * sz:
            v.co.z = 0.0
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    uv_layer = bm.loops.layers.uv.verify()
    pref = rng.randrange(len(brick_segments()))
    for f in bm.faces:
        uvs = _face_uv(rng, [v.co for v in f.verts], pref=pref)
        for lp, uv in zip(f.loops, uvs):
            lp[uv_layer].uv = uv
        f.smooth = False
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return me
