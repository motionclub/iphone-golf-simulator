"""hole09_build.py - Hole 9 "Split" (par 5, 494 yd): a C-shaped ring island at ONE height (6 m).

Run from a clean Blender (re-runnable, deterministic: every random draw is seeded):

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/hole09_build.py

Writes blender/hole_09.blend, blender/previews/hole_09_overview.png and Unity/Assets/Resources/Course/hole_09.fbx (+ .meta).
Gate it with   Blender -b blender/hole_09.blend --python blender/scripts/postcard_verify.py -- hole09_design

It is the hole 7 pattern as a short sequence of postcard_lib calls plus this hole's scenery, which is read from
hole09_design.SCENERY (yards in course space, heights in metres):

    shore_stretches   cliff styling per stretch KIND (STYLE below): outer_cliff, channel_inner_wall, gap_face, channel_tip
                      -> boulders at the cliff foot, boulders wedged into the face, rim outcrops on the land top
    surf_stretches    foam: the full white surf band + broken crest dashes on those stretches only, tapering out along the
                      shore; a thin lapping line on every other stretch (see surf())
    gap, channel      the two gap faces are the ends of the ribbon: the biggest foot boulders + scree, plus the sea stack
                      standing in the mouth
    ridge             the dry safe route: no scenery rock is placed within ROUTE_CLEAR_YD of it
    ruin              broken rock walls, the fallen arch and the rubble piles on the ridge's quiet north end
    sea_stacks        ROCK_STACK_nn: faceted columns (flared foot, ledge, grassy top) with library-rock skirts round the foot
    tee_box, green_bulb  the lib builds TEE_BOX / GREEN / GREEN_APRON from the scoring lies; the tee box rectangle is sized
                      to the design and kept inside the fairway round end (see TEE_BOX_M); the apron keeps the lib's 3 yd

Everything that is not a play surface is an instance of a library rock (ROCK_*/CLIFF_ROCK.nnn), a sea stack column
(ROCK_STACK_nn) or a water band: visual only, no collider. Nothing is built with a ground prefix except the play surfaces the
lib writes. One SCENERY edit was needed in hole09_design.py (the sea stack in the channel mouth moved out of the sight lines,
see its docstring); no scoring number changed.
"""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np                                   # noqa: E402
import bpy                                           # noqa: E402
from mathutils import Matrix, Vector                 # noqa: E402
from mathutils.bvhtree import BVHTree                # noqa: E402

import postcard_lib as P                             # noqa: E402

YD = P.YD
TAU = math.tau
ROUTE_CLEAR_YD = 8.0          # design asks >= 4 yd; the build keeps twice that between any scenery rock and the safe route
TEE_BOX_M = (10.4, 13.2)      # design 12 x 16 yd; the largest rounded rectangle that stays inside the 9 yd fairway round end

# cliff styling per stretch kind. foot = boulders in the water at the cliff base; face = boulders wedged into the wall;
# rim = outcrops on the land top (only where the land is plain rough and far from every play line).
# step_m = mean spacing along the stretch, scale = rock width range (m), out_m = distance from the cliff foot.
STYLE = {
    "outer_cliff": dict(foot=dict(step_m=15.0, out_m=(5.5, 11.0), width_m=(3.2, 6.5), companion=0.5),
                        face=dict(step_m=15.0, width_m=(2.6, 5.0)), rim=dict(step_m=30.0, width_m=(2.4, 4.8))),
    "channel_inner_wall": dict(foot=dict(step_m=30.0, out_m=(3.0, 6.0), width_m=(2.0, 3.6), companion=0.25),
                               face=dict(step_m=44.0, width_m=(2.0, 3.4)), rim=None),
    "gap_face": dict(foot=dict(step_m=8.5, out_m=(2.2, 6.5), width_m=(3.4, 7.5), companion=0.7),
                     face=dict(step_m=8.0, width_m=(3.0, 5.2)), rim=None),
    "channel_tip": dict(foot=dict(step_m=10.0, out_m=(2.2, 4.5), width_m=(2.0, 3.6), companion=0.3),
                        face=dict(step_m=22.0, width_m=(2.0, 3.2)), rim=None),
}
RIM_STRETCHES = ("ridge_west_shore", "north_shore", "south_shore")     # rim outcrops only on these: never beside the ribbon, never on the
#                                                                       ridge lip that faces the channel (the aim-assist sight lines cross it)

rng = random.Random(909)


# ----------------------------------------------------------------------------------------------- geometry helpers
class Coast:
    """The SHORE polygon in metres with the SCENERY stretches on it; walk() gives points and outward normals."""

    def __init__(self, D):
        self.shore = np.array([P.m(x, d) for x, d in D.SHORE])
        self.sign = 1.0 if P.signed_area(self.shore) > 0 else -1.0
        self.stretches = list(D.SCENERY["shore_stretches"])

    def polyline(self, st):
        n = len(self.shore)
        return np.array([self.shore[i % n] for i in range(st["first"], st["last"] + 2)])      # + first point of the next stretch

    def walk(self, st, step, jitter=0.35):
        """[(x, y, nx, ny)] about every `step` metres along a stretch; (nx, ny) is the unit normal pointing OUT to the water."""
        pl = self.polyline(st)
        seg = pl[1:] - pl[:-1]
        L = np.maximum(np.hypot(seg[:, 0], seg[:, 1]), 1e-9)
        cum = np.concatenate([[0.0], np.cumsum(L)])
        out, s = [], step * rng.uniform(0.25, 0.75)
        while s < cum[-1] - step * 0.15:
            k = int(np.searchsorted(cum, s, side="right")) - 1
            k = min(max(k, 0), len(seg) - 1)
            p = pl[k] + seg[k] * ((s - cum[k]) / L[k])
            tg = seg[k] / L[k]
            out.append((float(p[0]), float(p[1]), float(tg[1] * self.sign), float(-tg[0] * self.sign)))
            s += step * rng.uniform(1.0 - jitter, 1.0 + jitter)
        return out


def route_segments(D):
    r = [P.m(x, d) for x, d in D.SCENERY["ridge"]["route"]]
    A = np.array(r[:-1], float)
    B = np.array(r[1:], float)
    return A, B


def rock(D, kind, center, dims, yaw=None, tilt=0.07, role=""):
    """A library rock whose bounding box is `dims` (x, y, z metres) and centred on `center`; random yaw + a little tilt.
    `role` is stored as a custom property (foot, face, rim, ruin, skirt ...) for the QA audits; it is not exported."""
    yaw = rng.uniform(0.0, TAU) if yaw is None else yaw
    R = (Matrix.Rotation(yaw, 3, 'Z') @ Matrix.Rotation(rng.uniform(-tilt, tilt), 3, 'X')
         @ Matrix.Rotation(rng.uniform(-tilt, tilt), 3, 'Y'))
    ob = P._place_fit(D, kind, center, dims, R)
    ob["role"] = role
    return ob


def terrain_bvh(D):
    """BVH of the TERRAIN mesh (the terrain object has an identity transform under the identity root, so object space = world)."""
    me = D.terrain.data
    me.calc_loop_triangles()
    return BVHTree.FromPolygons([tuple(v.co) for v in me.vertices], [tuple(t.vertices) for t in me.loop_triangles], all_triangles=True)


# ----------------------------------------------------------------------------------------------- surf (foam) on the listed stretches
def surf(D, coast, thin_m=1.3, foam_m=3.4, reach_m=5.0, fade_m=16.0, cell=1.0):
    """WATER_FOAM + WATER_FOAM_CREST like the lib's build_water, but the full band (foam_m wide, with crest dashes) only sits
    on the SCENERY surf_stretches and tapers out over fade_m along the shore; every other stretch gets a thin lapping line
    (thin_m) so no cliff foot is left bone dry. Same z levels as the lib (foam 0.08, crest 0.09)."""
    names = set(D.SCENERY["surf_stretches"])
    A, B = [], []
    for st in coast.stretches:
        if st["name"] in names:
            pl = coast.polyline(st)
            A.append(pl[:-1])
            B.append(pl[1:])
    A, B = np.vstack(A), np.vstack(B)
    ext = 20.0
    bx0, by0, bx1, by1 = P._shore_bbox_m(D)
    grid = P._Grid((bx0 - ext, by0 - ext, bx1 + ext, by1 + ext), cell, pad=2)
    sd = P.signed_dist_m(D, grid.X, grid.Y)
    near = sd < 12.0
    dsurf = np.full(grid.X.shape, 1e3)
    dsurf[near] = P._dist_pts_segs(np.stack([grid.X[near], grid.Y[near]], 1), A, B)
    taper = np.clip((reach_m + fade_m - dsurf) / fade_m, 0.0, 1.0)
    width = thin_m + (foam_m - thin_m) * taper
    wob = P._wobble(grid.X, grid.Y, 2.2, 5.0) * (width / foam_m)
    F = np.minimum(width + wob - sd, sd + 5.0)
    made = []
    loops = P._contours(grid, F > 0, F=F, simplify=0.05, min_area=10.0)
    ob = P._region_object(D, "WATER_FOAM", loops, 0.08, D.mats["MAT_FOAM"], 5.0)
    made.append(ob)
    lo, hi = 16.0 * 0.62, 16.0 * 0.62 + 1.6
    dash = (np.sin(0.23 * grid.X + 0.15 * grid.Y) + np.sin(0.09 * grid.X - 0.13 * grid.Y + 1.7)) > 0.35
    Fc = np.where(dash & (taper > 0.55), np.minimum(sd - lo, hi - sd), -1.0)
    made.append(P._region_object(D, "WATER_FOAM_CREST", P._contours(grid, Fc > 0, F=Fc, simplify=0.05, min_area=10.0), 0.09,
                                 D.mats["MAT_FOAM"], 3.0))
    for o in made:
        if o:
            o.parent = P.get_root()
            P.link_to(o, "ENVIRONMENT")
    return [o for o in made if o]


# ----------------------------------------------------------------------------------------------- wall materials per stretch
def style_walls(D, coast):
    """The two gap faces are the ends of the ribbon: their grassy lip band (the top metre of the wall, MAT_ROUGH) is broken up
    into patches of bare cliff (MAT_CLIFF), so those faces read as sheared-off rock rather than as an edge of the lawn. Same
    three material slots as the lib builds (the TERRAIN gate wants exactly MAT_ROUGH / MAT_CLIFF / MAT_CLIFF_DARK); only the
    per-face slot of some top-band wall quads changes. Returns the number of quads switched."""
    me = D.terrain.data
    pz = D.play_z
    segs = {}
    for st in coast.stretches:
        if st["kind"] in ("gap_face", "channel_tip"):
            pl = coast.polyline(st)
            segs.setdefault(st["kind"], []).append((pl[:-1], pl[1:]))
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    n = 0
    for poly in me.polygons:
        if poly.material_index != 0:
            continue
        z = co[list(poly.vertices)][:, 2]
        if not (z.max() <= pz + 1e-4 and z.min() >= pz - 1.05 and z.max() - z.min() > 0.5):      # a top-band wall quad, not a top triangle
            continue
        c = co[list(poly.vertices)].mean(0)[:2]
        for kind, lst in segs.items():
            A = np.vstack([a for a, b in lst])
            B = np.vstack([b for a, b in lst])
            if float(P._dist_pts_segs(c[None, :], A, B)[0]) < 0.6:
                phase = math.sin(c[0] * 0.47 + c[1] * 0.31) + math.sin(c[1] * 0.83 - c[0] * 0.21 + 1.3)
                if phase > (-0.4 if kind == "gap_face" else 0.9):
                    poly.material_index = 1
                    n += 1
                break
    me.update()
    return n


# ----------------------------------------------------------------------------------------------- cliff styling per stretch
def style_cliffs(D, coast, route_A, route_B, bvh):
    """Foot boulders, face boulders and rim outcrops, each stretch by its KIND (STYLE). Returns counters per kind."""
    pz = D.play_z
    counts = {}
    ruin_xy = [P.m(w["p0"][0], w["p0"][1]) for w in D.SCENERY["ruin"]["walls"]]
    for st in coast.stretches:
        sty = STYLE[st["kind"]]
        c = counts.setdefault(st["kind"], dict(foot=0, face=0, rim=0))
        # --- boulders standing in the water at the cliff foot (CLIFF_ROCK + a LARGE companion), tops just above the surf
        f = sty["foot"]
        for x, y, nx, ny in coast.walk(st, f["step_m"]):
            out = rng.uniform(*f["out_m"])
            w = rng.uniform(*f["width_m"])
            h = w * rng.uniform(0.75, 1.1)
            top = rng.uniform(0.6, 2.4)                                   # metres above the sea
            h = max(h, top + 0.7)                                         # bottom always >= 0.7 m under the water
            zc = top - h / 2
            rock(D, "CLIFF" if rng.random() < 0.6 else "LARGE", (x + nx * out, y + ny * out, zc), (w, w * rng.uniform(0.8, 1.1), h), role="foot")
            c["foot"] += 1
            if rng.random() < f["companion"]:
                ang = rng.uniform(0, TAU)
                w2 = w * rng.uniform(0.45, 0.8)
                top2 = rng.uniform(0.3, 1.3)
                h2 = max(w2 * 0.8, top2 + 0.5)                                       # bottom always >= 0.5 m under the sea
                q = (x + nx * out * 1.5 + math.cos(ang) * w * 0.7, y + ny * out * 1.5 + math.sin(ang) * w * 0.7)
                rock(D, "LARGE", (q[0], q[1], top2 - h2 / 2), (w2, w2 * 0.9, h2), role="foot")
                c["foot"] += 1
        # --- boulders wedged into the wall: they break the horizontal banding. Centre on the wall, top below the play surface
        f = sty["face"]
        for x, y, nx, ny in coast.walk(st, f["step_m"]):
            w = rng.uniform(*f["width_m"])
            h = min(w * rng.uniform(0.6, 0.9), pz - 0.45 - 1.8 - 0.1)       # fits between the surf line (1.8 m) and 0.45 m under the lip
            zc = rng.uniform(1.8 + h / 2, pz - 0.45 - h / 2)
            hit = bvh.ray_cast((x + nx * 4.0, y + ny * 4.0, zc), (-nx, -ny, 0.0), 9.0)      # where the wall really is at this height
            if hit[0] is None:
                continue
            q = (hit[0].x - nx * w * 0.12, hit[0].y - ny * w * 0.12)                         # centre a little behind the wall face: half buried
            rock(D, "CLIFF" if rng.random() < 0.5 else "LARGE", (q[0], q[1], zc), (w, w * 0.9, h), role="face")
            c["face"] += 1
    # --- rim outcrops on the land top of the big outer stretches only, never near a play line: one bigger boulder with satellites
    tee = P.m(*D.CENTERLINE[0])
    pin = P.m(*D.CENTERLINE[-1])
    placed = []
    for st in coast.stretches:
        if st["name"] not in RIM_STRETCHES:
            continue
        r = STYLE[st["kind"]]["rim"]
        for x, y, nx, ny in coast.walk(st, r["step_m"]):
            inset = rng.uniform(3.6, 6.0)
            px_, py_ = x - nx * inset, y - ny * inset
            lie = int(P.lie_codes_m(D, np.array([px_]), np.array([py_]))[0])
            if lie not in (P.LIE_ROUGH, P.LIE_OOB):
                continue
            d_route = float(P._dist_pts_segs(np.array([[px_, py_]]), route_A, route_B)[0])
            if d_route < ROUTE_CLEAR_YD * YD + 2.0:
                continue
            if math.hypot(px_ - tee[0], py_ - tee[1]) < 24 * YD or math.hypot(px_ - pin[0], py_ - pin[1]) < (D.GREEN_RADIUS + 9) * YD:
                continue
            if any(math.hypot(px_ - qx, py_ - qy) < 9.0 for qx, qy in placed + ruin_xy):
                continue
            w = rng.uniform(*r["width_m"])
            h = w * rng.uniform(0.5, 0.8)
            rock(D, "LARGE" if w > 3.0 else "MEDIUM", (px_, py_, pz - 0.3 + h / 2), (w, w * rng.uniform(0.75, 1.0), h), role="rim")
            for _ in range(rng.randint(2, 4)):                       # satellites kept on the cliff side of the main boulder
                ang = rng.uniform(0, TAU)
                dist = w * rng.uniform(0.7, 1.1)
                sw = w * rng.uniform(0.28, 0.55)
                qx_, qy_ = px_ + math.cos(ang) * dist, py_ + math.sin(ang) * dist
                if float(P._dist_pts_segs(np.array([[qx_, qy_]]), route_A, route_B)[0]) < ROUTE_CLEAR_YD * YD:
                    continue
                if (P.signed_dist_m(D, np.array([qx_]), np.array([qy_]))[0] > -2.0):
                    continue
                rock(D, "SMALL", (qx_, qy_, pz - 0.25 + sw * 0.3), (sw * 1.3, sw, sw * 0.75), role="rim")
            placed.append((px_, py_))
            counts[st["kind"]]["rim"] += 1
    return counts


# ----------------------------------------------------------------------------------------------- sea stacks
def sea_stack(D, idx, x_yd, d_yd, r_yd, h_m):
    """One sea stack ROCK_STACK_nn: a faceted, slightly leaning column (flat shaded like the cliff walls: dark foot, cliff
    bands, a lighter top band, a grassy lip band and a flat turf top) standing in the sea. Its base is 4 m under the water, its
    top h_m above it, its foot radius about 1.3 x radius_yd. Three or four low library-rock skirt boulders ring the foot.
    Visual only (name starts with ROCK_, no collider). Returns the number of objects."""
    cx, cy = P.m(x_yd, d_yd)
    R = r_yd * YD
    nside = rng.choice((8, 9, 10))
    z_bot, cap_h = -4.0, 0.9
    # (z, radius x R): a flared foot, sheer shoulders with one ledge, a slightly overhanging grassy top
    levels = [(z_bot, 1.85), (0.0, 1.55), (0.22 * h_m, 1.12), (0.52 * h_m, 0.92), (0.54 * h_m, 1.00), (0.80 * h_m, 0.84),
              (h_m - cap_h, 0.88), (h_m, 0.97)]
    mat_of_band = [2, 2, 1, 1, 1, 3, 0]                               # MAT_ROUGH 0, MAT_CLIFF 1, MAT_CLIFF_DARK 2, MAT_ROCK 3
    lean = (rng.uniform(-0.28, 0.28) * R, rng.uniform(-0.28, 0.28) * R)
    verts, rings = [], []
    for k, (z, mult) in enumerate(levels):
        t = (z - z_bot) / (h_m - z_bot)
        ring = []
        rot = rng.uniform(-0.2, 0.2)
        for i in range(nside):
            ang = TAU * (i + rng.uniform(-0.22, 0.22)) / nside + rot
            r = R * mult * rng.uniform(0.80, 1.20)
            zz = z + (rng.uniform(-0.35, 0.35) if k == len(levels) - 1 else 0.0)        # ragged top edge
            ring.append(len(verts))
            verts.append((cx + lean[0] * t + math.cos(ang) * r, cy + lean[1] * t + math.sin(ang) * r, zz))
        rings.append(ring)
    faces, mats = [], []
    for k in range(len(levels) - 1):
        for i in range(nside):
            j = (i + 1) % nside
            faces.append((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]))
            mats.append(mat_of_band[k])
    faces.append(tuple(rings[-1]))                                    # turf top (counter-clockwise seen from above)
    mats.append(0)
    ob = P.new_mesh_object(f"ROCK_STACK_{idx:02d}", "ENVIRONMENT")
    P.build_mesh(ob, verts, faces, smooth=False, material_index=mats,
                 materials=[D.mats[mn] for mn in ("MAT_ROUGH", "MAT_CLIFF", "MAT_CLIFF_DARK", "MAT_ROCK")])
    n = 1
    for _ in range(3 + int(R > 3.5)):
        ang = rng.uniform(0, TAU)
        dist = R * rng.uniform(1.9, 2.8)
        w = R * rng.uniform(0.9, 1.5)
        top = rng.uniform(0.6, 1.5)
        h = max(w * 0.75, top + 0.6)
        rock(D, "LARGE", (cx + math.cos(ang) * dist, cy + math.sin(ang) * dist, top - h / 2), (w, w * 0.9, h), role="skirt")
        n += 1
    return n


# ----------------------------------------------------------------------------------------------- the ruin
def ruin_wall(D, p0, p1, height_m, thick_m, room):
    """A broken rock wall from p0 to p1 (metres) in courses of staggered library-rock blocks: the top edge is ragged (the wall
    stands higher in some stretches than in others), some blocks are missing and fallen stones lie at the foot and the ends.
    Same job as postcard_lib.build_ruin_wall, but real courses so it reads as masonry instead of a row of boulders. `room` is the
    centre of the ruin (metres): fallen stones only lie on the wall side that faces it, never out towards the ridge route."""
    a, b = np.array(p0, float), np.array(p1, float)
    L = float(np.hypot(*(b - a)))
    d = (b - a) / L
    nrm = np.array([-d[1], d[0]])
    yaw = math.atan2(d[1], d[0])
    nc = max(1, int(round(height_m / 1.0)))
    ch = height_m / nc
    base = D.play_z - 0.25
    ph = rng.uniform(0, TAU)
    flip = height_m < 4.0 and rng.random() < 0.5                      # the tall walls stand highest at their p1 end
    n = 0
    for c in range(nc):
        s = -rng.uniform(0.0, 1.4)
        while s < L - 0.3:
            blen = rng.uniform(2.1, 3.1)
            sm = s + blen / 2
            s += blen * 0.78
            if sm < 0.4 or sm > L - 0.4:
                continue
            u = sm / L
            u = 1.0 - u if flip else u
            prof = min(1.0, 0.50 + 0.50 * u + 0.10 * math.sin(TAU * sm / (L * 0.55) + ph))     # standing height fraction here
            if (c + 1) * ch > prof * height_m + 0.45 * ch or (c > 0 and rng.random() < 0.06):
                continue
            q = a + d * sm + nrm * rng.uniform(-0.12, 0.12) * thick_m
            if not P._on_land_margin(D, q[0], q[1], 1.0):
                continue
            rock(D, "MEDIUM" if (c == 0 or rng.random() < 0.6) else "SMALL", (q[0], q[1], base + c * ch + ch / 2),
                 (blen * rng.uniform(1.0, 1.18), thick_m * rng.uniform(0.92, 1.12), ch * rng.uniform(1.0, 1.2)),
                 yaw=yaw + rng.uniform(-0.09, 0.09), tilt=0.04, role="ruin")
            n += 1
    inward = 1.0 if float(np.dot(nrm, np.array(room) - (a + b) / 2)) > 0 else -1.0     # the side of the wall that faces the ruin's room
    for k in range(max(3, int(L / 2.8))):                                                     # fallen stones along the foot, room side only
        sm = rng.uniform(-0.8, L + 0.8)
        side = inward * rng.uniform(0.9, 2.1)
        q = a + d * sm + nrm * side
        if not P._on_land_margin(D, q[0], q[1], 1.0):
            continue
        w = rng.uniform(0.7, 1.5)
        rock(D, "SMALL", (q[0], q[1], base + w * 0.28), (w * 1.35, w, w * 0.75), tilt=0.12, role="ruin")
        n += 1
    return n


def fallen_arch(D, a):
    """The fallen arch of SCENERY['ruin']: two pillar stumps and an elliptical ring of library-rock voussoirs that only stands
    over three quarters of its span; the stones of the missing quarter lie at its foot. Unlike postcard_lib.build_arch (pillars of at
    least 2.5 m under a semicircle, so a 7.3 m span is 7 m tall) it honours the design's span AND height: the ring is as wide as
    span_yd and the whole thing is height_m tall. yaw_deg 0 = the span runs along +D, positive clockwise seen from above."""
    cx, cy = P.m(a["x"], a["d"])
    span, H = a["span_yd"] * YD, a["height_m"]
    phi = math.radians(a["yaw_deg"])
    sdir = np.array([math.sin(phi), math.cos(phi)])                # horizontal span direction in the world
    pdir = np.array([-sdir[1], sdir[0]])                           # horizontal direction across the opening
    Rz = Matrix.Rotation(math.atan2(sdir[1], sdir[0]), 3, 'Z')     # local x -> span axis, local y -> depth axis
    base = D.play_z - 0.25
    R, thick, depth = span / 2.0, 1.9, 2.6
    pillar_h = 1.0
    ry = max(1.2, H - pillar_h - thick / 2.0)                      # vertical semi-axis of the ring centre line
    zc = base + pillar_h
    n = 0
    for side in (-1, 1):                                           # pillar stumps under the two ends of the ring
        nblk = 2
        hseg = pillar_h / 1.6
        for k in range(nblk):
            q = np.array([cx, cy]) + sdir * (side * R + rng.uniform(-0.12, 0.12)) + pdir * rng.uniform(-0.1, 0.1)
            rock(D, "LARGE" if k == 0 else "MEDIUM", (q[0], q[1], base + hseg * 0.5 + hseg * 0.7 * k),
                 (thick * 1.7 * (1.1 - 0.1 * k), depth * (1.0 - 0.08 * k), hseg * 1.35), yaw=math.atan2(sdir[1], sdir[0]) + rng.uniform(-0.2, 0.2), tilt=0.05, role="ruin")
            n += 1
    nseg = 8
    arc = math.pi * (R + ry) / 2.0 / nseg * 1.75
    for i in range(nseg):
        th = math.pi * (i + 0.5) / nseg
        px, pz = R * math.cos(th), ry * math.sin(th)
        psi = math.atan2(ry * math.cos(th), -R * math.sin(th))     # direction of the ring tangent in the (span, up) plane
        rot = Rz @ Matrix.Rotation(-psi, 3, 'Y')
        if i >= nseg - 2:                                          # the fallen side: these stones lie on the ground by the pillar
            q = np.array([cx, cy]) + sdir * (R * (0.6 + 0.5 * (i - nseg + 2))) + pdir * ((-1) ** i * rng.uniform(1.7, 2.6))
            rock(D, "MEDIUM", (q[0], q[1], base + thick * 0.5), (arc, depth * 0.85, thick), yaw=math.atan2(sdir[1], sdir[0]) + rng.uniform(-1.0, 1.0), tilt=0.16, role="ruin")
            n += 1
            continue
        q = np.array([cx, cy]) + sdir * px
        P._place_fit(D, "MEDIUM", (q[0], q[1], zc + pz), (arc, depth * 0.9, thick * rng.uniform(0.95, 1.15)), rot)["role"] = "ruin"
        n += 1
    for _ in range(7):                                              # rubble around the feet
        ang = rng.uniform(0, TAU)
        rr = R * rng.uniform(0.35, 1.45)
        q = np.array([cx, cy]) + sdir * (math.cos(ang) * rr) + pdir * (math.sin(ang) * rr * 0.55)
        w = rng.uniform(0.7, 1.6)
        rock(D, "SMALL", (q[0], q[1], base + w * 0.3), (w * rng.uniform(1.2, 1.9), w * rng.uniform(0.9, 1.4), w * 0.8), role="ruin")
        n += 1
    return n


def ruin(D):
    """Broken rock walls, the fallen arch and the rubble piles of SCENERY['ruin'], all library rocks, all on the ridge."""
    R = D.SCENERY["ruin"]
    n = 0
    pts = [w[k] for w in R["walls"] for k in ("p0", "p1")]
    room = P.m(sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    for w in R["walls"]:
        n += ruin_wall(D, P.m(*w["p0"]), P.m(*w["p1"]), w["height_m"], w["thick_yd"] * YD, room)
    n += fallen_arch(D, R["fallen_arch"])
    for pile in R["rubble"]:
        px_, py_ = P.m(pile["x"], pile["d"])
        rr = pile["radius_yd"] * YD
        for _ in range(int(3 + rr * 1.5)):
            ang, dist = rng.uniform(0, TAU), rr * math.sqrt(rng.random())
            s = rng.uniform(0.7, 1.5)
            rock(D, "SMALL", (px_ + math.cos(ang) * dist, py_ + math.sin(ang) * dist, D.play_z - 0.25 + s * 0.3),
                 (s * 1.3, s, s * 0.75), role="ruin")
            n += 1
    return n


# ----------------------------------------------------------------------------------------------- overview framing
def frame_overview(D, rot_deg=(50.0, 0.0, 20.0), margin=1.06, height_px=1700):
    """CAM_HOLE_OVERVIEW like the lib (orthographic, same angle as hole 7) but framed for a tall thin island: the image is
    as wide as the island's projection needs instead of the lib's square 1:1 frame. Returns the (width, height) in pixels."""
    cam = bpy.data.objects["CAM_HOLE_OVERVIEW"]
    rot = Matrix.Rotation(math.radians(rot_deg[2]), 3, 'Z') @ Matrix.Rotation(math.radians(rot_deg[0]), 3, 'X')
    right, up, view = rot @ Vector((1, 0, 0)), rot @ Vector((0, 1, 0)), rot @ Vector((0, 0, -1))
    corners = [Vector((x, y, z)) for x, y in (P.m(a, b) for a, b in D.SHORE) for z in (D.play_z + 10.0, -6.0)]
    rs = [c.dot(right) for c in corners]
    us = [c.dot(up) for c in corners]
    wr, hu = (max(rs) - min(rs)) * margin, (max(us) - min(us)) * margin
    cam.rotation_euler = rot.to_euler()
    cam.location = right * ((min(rs) + max(rs)) / 2) + up * ((min(us) + max(us)) / 2) - view * 1500.0
    res = (int(round(height_px * wr / hu / 2) * 2), height_px)
    cam.data.ortho_scale = max(wr, hu * res[0] / res[1]) if res[0] >= res[1] else hu
    return res


# ----------------------------------------------------------------------------------------------- build
D = P.start("hole09_design")
D.mod.SCENERY["tee_box_m"] = TEE_BOX_M                       # lib key: tee box width x depth in metres (set at runtime, not in the design file)
coast = Coast(D)
route_A, route_B = route_segments(D)

P.build_terrain(D)                                           # flat top at PLAY_Z, banded vertical/undercut cliffs on every loop
P.build_play_surfaces(D)                                     # fairway + first cut, green + apron, tee box, 3 bunkers (+lips)
P.build_water(D, shallow_m=20.0, foam_material=None)         # ocean plane + shallow band (20 m: the 33 m lagoon has no dark patch); foam: surf() below
surf(D, coast)
P.import_rocks(D)

n_walls = style_walls(D, coast)
n_cliff = style_cliffs(D, coast, route_A, route_B, terrain_bvh(D))
n_ruin = ruin(D)
n_stack = sum(sea_stack(D, i + 1, s["x"], s["d"], s["radius_yd"], s["height_m"]) for i, s in enumerate(D.SCENERY["sea_stacks"]))

P.build_gameplay(D)
P.build_cameras_and_light(D)
P.render_overview(D, res=frame_overview(D))
P.save(D)
P.export_fbx(D)
st = P.stats(D)
print("HOLE09 cliff styling per kind:", n_cliff, "| bare-rock lip quads:", n_walls)
print(f"HOLE09 ruin rocks {n_ruin}, sea-stack rocks {n_stack}, rocks total {sum(D.rock_count.values())}")
print(f"HOLE09 stats: {st['objects']} objects, {st['meshes']} meshes, {st['tris']} tris ({st['ground_tris']} ground)")
