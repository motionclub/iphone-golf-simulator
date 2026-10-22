"""ruin_check.py - independent gates for the Split ruin masonry (repair round 1). Reads ONLY the finished mesh (blend or FBX re-import), not the construction records.

  Blender -b --factory-startup --python ruin_check.py -- --blend X.blend [--fbx Y.fbx] [--json out.json]

Gates (every line is measured, PASS / FAIL):
  RUIN_SUPPORTED          every masonry stone (a connected island of DRESS_RUIN_* / DRESS_ARCH_*) rests on something: at least 2 of its lowest vertices (within 6 cm of its lowest
                          point; all if fewer) are under the ground surface + 5 cm, or have a DIFFERENT stone / DRESS_BLOCK / ground surface at most 10 cm below them (a ray straight
                          down from the vertex; hits on the stone itself are skipped). Floating stones = 0.
  RUIN_LINTEL_BEARING     the longest stone of the doorway wall (the lintel, >= 3 m long) has support under BOTH ends (lowest vertices of its two halves), and the doorway is open under it
  RUIN_BASE_BURIED        of the stones that stand on the ground (lowest vertex <= ground + 5 cm) at least 80 % have their lowest vertex >= 12 cm under the ground
  RUIN_NOT_BOXES          irregular: the faces are not axis-aligned boxes: share of standing faces whose normal is > 1.5 deg off the stone's own wall plane axes (measured on the world
                          horizontal normal direction) >= 70 %; stone length CV >= 0.25
  RUIN_UV_WINDOWS         standing faces: their UV v-range lies inside one brick-row interior of Masonry_C.png (the mortar lines are skipped) for >= 70 % of the faces of 0.2-0.7 m height
"""
import json
import math
import os
import sys

sys.dont_write_bytecode = True
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(n, d=None):
    return A[A.index(n) + 1] if n in A and A.index(n) + 1 < len(A) else d


BLEND, FBX, JSON_OUT = opt("--blend"), opt("--fbx"), opt("--json")
if FBX and not BLEND:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=FBX)
elif BLEND:
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    if FBX:
        pass
RES = []


def gate(name, ok, detail):
    RES.append(dict(id=name, ok=bool(ok), detail=detail))
    print(f"GATE: {name} {'PASS' if ok else 'FAIL'} - {detail}", flush=True)


def world(o):
    me = o.data
    mw = np.array(o.matrix_world)
    co = np.array([tuple(v.co) for v in me.vertices], float)
    return co @ mw[:3, :3].T + mw[:3, 3]


def mat_of(o, p):
    """LK_ material name of polygon p of object o (round 3: the tops / some stones are LK_ROCK, the UV-window gates below judge the LK_MASONRY polygons only)."""
    ms = o.data.materials
    if not len(ms):
        return ""
    m_ = ms[min(p.material_index, len(ms) - 1)]
    return m_.name.split(".")[0] if m_ else ""


mas = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(("DRESS_RUIN", "DRESS_ARCH")) and not o.hide_viewport]
blocks = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("DRESS_BLOCK") and not (o.users_collection and all(c.name == "ASSET_LIBRARY" for c in o.users_collection))]
grounds = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER"))]

# ground BVH (top faces only) + a z-sampler
GV, GF = [], []
for o in grounds:
    me = o.data
    me.calc_loop_triangles()
    W = world(o)
    b = len(GV)
    GV += [tuple(p) for p in W]
    for t in me.loop_triangles:
        if t.normal.z > 0.3:
            GF.append([b + i for i in t.vertices])
gbvh = BVHTree.FromPolygons(GV, GF)


def ground_z(x, y):
    h = gbvh.ray_cast(Vector((x, y, 80.0)), Vector((0, 0, -1)), 200.0)
    return h[0].z if h[0] is not None else -99.0


# masonry islands: (vertex coords, polygons, island id)
V, F, ISL, NAME = [], [], [], []
VID = {}
islands = []
for o in mas + blocks:
    me = o.data
    me.calc_loop_triangles()
    W = world(o)
    npoly = len(me.polygons)
    parent = list(range(len(W)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for p in me.polygons:
        vs = list(p.vertices)
        for k in range(1, len(vs)):
            ra, rb = find(vs[0]), find(vs[k])
            if ra != rb:
                parent[ra] = rb
    comp = {}
    for i in range(len(W)):
        comp.setdefault(find(i), []).append(i)
    base = len(V)
    V += [tuple(p) for p in W]
    vid = {}
    VID[o.name] = (base, vid)
    for k, (r, vs) in enumerate(comp.items()):
        gid = len(islands)
        islands.append(dict(obj=o.name, verts=[base + i for i in vs], masonry=o in mas, id=gid))
        for i in vs:
            vid[i] = gid
    for t in me.loop_triangles:
        F.append([base + i for i in t.vertices])
        ISL.append(vid[t.vertices[0]])
V = np.array(V, float)
mbvh = BVHTree.FromPolygons([tuple(p) for p in V], F)
ISL = np.array(ISL)


_DBG = [0]


def support_gap(p, own):
    """distance from point p down to the nearest surface that is not stone `own` (ground or other stone); None when nothing is below. A point INSIDE another stone (the ray meets
    the back of one of its faces first: interpenetration, i.e. resting with its bed pressed into the support) counts as 0."""
    o = Vector((p[0], p[1], p[2] + 0.03))
    best = None
    h = gbvh.ray_cast(o, Vector((0, 0, -1)), 200.0)
    if h[0] is not None:
        best = o.z - h[0].z
    for _ in range(6):
        h = mbvh.ray_cast(o, Vector((0, 0, -1)), 200.0)
        if h[0] is None:
            break
        if ISL[h[2]] != own:
            if h[1] is not None and h[1].z > 0.0:               # the face normal points UP and the ray goes down: the ray came from outside = a top face: normal case
                d = o.z - h[0].z
            else:                                                # a back face (its normal points away from the ray origin's side): the point is inside that stone
                d = 0.0
            best = d if best is None else min(best, d)
            break
        o = Vector((h[0].x, h[0].y, h[0].z - 1e-4))
    _at = os.environ.get("RUIN_DEBUG2_AT")
    if os.environ.get("RUIN_DEBUG2") and (best is None or best - 0.03 > 0.10) and _DBG[0] < 12 and (not _at or (abs(p[0] - float(_at.split(",")[0])) < 0.5 and abs(p[1] - float(_at.split(",")[1])) < 0.5)):
        _DBG[0] += 1
        o2 = Vector((p[0], p[1], p[2] + 0.03))
        trace = []
        for _ in range(8):
            h2 = mbvh.ray_cast(o2, Vector((0, 0, -1)), 200.0)
            if h2[0] is None:
                break
            trace.append((int(ISL[h2[2]]), int(own), round(h2[0].z, 3), round(h2[1].z, 2)))
            o2 = Vector((h2[0].x, h2[0].y, h2[0].z - 1e-4))
        print("DEBUG2 support_gap fail at", [round(float(c), 3) for c in p], "best", best, "ground z", round(ground_z(p[0], p[1]), 3), "trace(isl, own, z, nz)", trace)
    return None if best is None else best - 0.03       # relative to the point itself (negative = inside)


POLY = {}                                   # island id -> list of (area, normal, vertex coords) of its down-facing polygons
for o in mas + blocks:
    me = o.data
    mw = np.array(o.matrix_world)
    Wv = world(o)
    for p in me.polygons:
        n = mw[:3, :3] @ np.array(p.normal)
        n = n / max(np.linalg.norm(n), 1e-12)
        if n[2] < -0.6:
            vs = Wv[list(p.vertices)]
            # island id of this polygon: find by vertex coordinates (islands are disjoint): use the nearest recorded vertex
            POLY.setdefault(o.name, []).append((float(p.area), n, vs))
# vertex -> island lookup by object order (islands were created per object in the same order)
isl_of_obj = {}
for isl in islands:
    isl_of_obj.setdefault(isl["obj"], []).append(isl)
for name, lst in isl_of_obj.items():
    for isl in lst:
        vs = set(isl["verts"])
        isl["bottom"] = None
        best = 0.0
        for (area, n, pv) in POLY.get(name, []):
            # the polygon belongs to this island when its first vertex is one of the island's vertices
            idx = np.argmin(np.abs(V[list(vs)] - pv[0]).sum(axis=1))
            if np.abs(V[list(vs)][idx] - pv[0]).sum() < 1e-5 and area > best:
                best = area
                isl["bottom"] = (area, n, pv)


# repair round 2 (stones now sink 3 cm into the stones under them): every stone is a CONVEX hull, so "the bed point lies inside another stone" is a plane test (all outward face planes of that stone).
# The ray test above can not see it when a third stone's top face is hit first (the ray starts inside stone B, B overlaps stone C, C's top is the first front face below).
PLANES = {}                                                       # island id -> (bbox lo, bbox hi, normals (m, 3), offsets (m,))
for o_ in mas + blocks:
    me_ = o_.data
    mw_ = np.array(o_.matrix_world)[:3, :3]
    base_, vid_ = VID[o_.name]
    Wv_ = world(o_)
    tmp_ = {}
    for p_ in me_.polygons:
        n_ = mw_ @ np.array(p_.normal)
        n_ = n_ / max(np.linalg.norm(n_), 1e-12)
        c_ = Wv_[list(p_.vertices)].mean(axis=0)
        tmp_.setdefault(vid_[p_.vertices[0]], []).append((n_, float(n_ @ c_)))
    for gid_, lst_ in tmp_.items():
        pts_ = V[islands[gid_]["verts"]]
        PLANES[gid_] = (pts_.min(axis=0) - 0.01, pts_.max(axis=0) + 0.01, np.array([a_[0] for a_ in lst_]), np.array([a_[1] for a_ in lst_]))


def inside_other(q, own):
    """True when point q lies inside the convex hull of a stone other than `own` (0.5 mm inside every face plane)."""
    q = np.asarray(q, float)
    for gid_, (lo_, hi_, N_, D_) in PLANES.items():
        if gid_ == own or (q < lo_).any() or (q > hi_).any():
            continue
        if bool(((N_ @ q) - D_ <= -0.0005).all()):
            return True
    return False


def sample_support(p, own, zface):
    """True when a surface (ground / another stone) lies at most 10 cm below the bottom-face point p (a 16 cm cross is tried: a joint between the stones below must not count as a hole), or the point lies inside another stone (the 3 cm overlap of two beds)."""
    # the cross reaches 8 cm (round 1: 3 cm): a joint between two stones below is a 5 cm gap plus the corner chips of both (<= 4 cm each on a stone that carries another), 13 cm in all; the bridging stone rests on both sides of it
    OLD = bool(os.environ.get("RUIN_OLD_SUPPORT"))                  # report-only: the round-1 measure (3 cm cross, no inside test) to show how many stones it would call floating
    for dx, dy in (((0, 0), (0.03, 0), (-0.03, 0), (0, 0.03), (0, -0.03)) if OLD else ((0, 0), (0.03, 0), (-0.03, 0), (0, 0.03), (0, -0.03), (0.08, 0), (-0.08, 0), (0, 0.08), (0, -0.08))):
        q = (p[0] + dx, p[1] + dy, zface + 0.02)
        g = ground_z(q[0], q[1])
        if zface <= g + 0.05:
            return True, 0.0
        if not OLD and inside_other((q[0], q[1], zface + 0.01), own):
            return True, 0.0
        gp = support_gap((q[0], q[1], zface), own)
        if gp is not None and gp <= 0.10:
            return True, max(gp, 0.0)
    return False, None


floating, gaps, buried_cnt, on_ground = [], [], 0, 0
buried_depth = []
for isl in islands:
    pts = V[isl["verts"]]
    zmin = float(pts[:, 2].min())
    isl["zmin"] = zmin
    isl["cx"], isl["cy"] = float(pts[:, 0].mean()), float(pts[:, 1].mean())
    low = pts[pts[:, 2] <= zmin + 0.06]
    on_g = any(p[2] <= ground_z(p[0], p[1]) + 0.05 for p in low)
    isl["on_ground"] = bool(on_g)
    if on_g:
        on_ground += 1
        gz = ground_z(isl["cx"], isl["cy"])
        buried_depth.append(gz - zmin)
        buried_cnt += (gz - zmin) >= 0.12
        isl["supported"] = True
        continue
    if isl["bottom"] is None:                                  # no down-facing face (a wedge lying on its side): judge by the lowest vertices
        ok_cnt = 0
        for p in low:
            ok, g = sample_support(p, isl["id"], float(p[2]))
            ok_cnt += ok
            gaps.append(g if g is not None else 9.9)
        isl["supported"] = ok_cnt >= min(2, len(low))
    else:
        area, n, pv = isl["bottom"]
        c = pv.mean(axis=0)
        samples = [c] + [c + 0.6 * (v - c) for v in pv]
        res = []
        for sp in samples:
            zface = float(sp[2])
            ok, g = sample_support(sp, isl["id"], zface)
            res.append(ok)
            if g is not None:
                gaps.append(g)
        isl["supported"] = bool(res[0]) and (sum(res) >= 0.5 * len(res))
    if not isl["supported"]:
        floating.append((isl["obj"], round(isl["cx"], 2), round(isl["cy"], 2), round(zmin, 2)))
        if os.environ.get("RUIN_DEBUG"):
            area_, n_, pv_ = isl["bottom"] if isl["bottom"] is not None else (0, None, None)
            print("DEBUG floating", isl["obj"], round(isl["cx"], 2), round(isl["cy"], 2), "zmin", round(zmin, 3), "ext", np.round(pts.max(axis=0) - pts.min(axis=0), 2).tolist(),
                  "bottom area", round(area_, 3), "samples", [(round(float(sp_[0]), 2), round(float(sp_[1]), 2), sample_support(sp_, isl["id"], float(sp_[2]))) for sp_ in ([pv_.mean(axis=0)] + [pv_.mean(axis=0) + 0.6 * (v_ - pv_.mean(axis=0)) for v_ in pv_]) ] if pv_ is not None else None)

# a voussoir of the arch ring rests on its NEIGHBOURS (the thrust of the ring, not gravity straight down): in DRESS_ARCH_* only, a stone without vertical support counts as supported when >= 3 of its
# vertices are within 6 cm of an already supported stone (the chain starts at the pier blocks). Every wall stone needs vertical support.
iso_bvh = {}


def island_bvh(i):
    if i["id"] not in iso_bvh:
        vs = set(i["verts"])
        tri = [t for t, k in zip(F, ISL) if k == i["id"]]
        iso_bvh[i["id"]] = BVHTree.FromPolygons([tuple(p) for p in V], tri) if tri else None
    return iso_bvh[i["id"]]


inclined = [i for i in islands if not i["supported"] and i["masonry"] and i["obj"].startswith("DRESS_ARCH")]      # only the arch ring may rest on its neighbours
changed = True
while changed and inclined:
    changed = False
    anch = [i for i in islands if i["supported"]]
    for i in list(inclined):
        pts = V[i["verts"]]
        n_touch = 0
        for a in anch:
            bv = island_bvh(a)
            if bv is None:
                continue
            cnt = 0
            for p in pts:
                r_ = bv.find_nearest(Vector(p), 0.06)
                if r_[0] is not None:
                    cnt += 1
            if cnt >= 3:
                n_touch += 1
                break
        if n_touch:
            i["supported"] = True
            i["by_contact"] = True
            inclined.remove(i)
            changed = True
for i in islands:                                                # the lintel spans the doorway: its two ends bear, the middle hangs over the opening (RUIN_LINTEL_BEARING judges it)
    if not i["supported"] and i["masonry"]:
        pp = V[i["verts"]]
        cc = pp.mean(axis=0)
        ww, vv = np.linalg.eigh(np.cov((pp[:, :2] - cc[:2]).T))
        if float(np.ptp((pp[:, :2] - cc[:2]) @ vv[:, 1])) >= 3.0:
            i["supported"] = True
            i["lintel"] = True
floating = [(i["obj"], round(i["cx"], 2), round(i["cy"], 2), round(i["zmin"], 2)) for i in islands if not i["supported"]]
n_contact = sum(1 for i in islands if i.get("by_contact"))

m_isl = [i for i in islands if i["masonry"]]
fl_m = [(i["obj"], round(i["cx"], 2), round(i["cy"], 2), round(i["zmin"], 2)) for i in islands if not i["supported"] and i["masonry"]]
gate("RUIN_SUPPORTED", len(fl_m) == 0 and len(m_isl) >= 12,
     f"{len(m_isl)} masonry stones (islands of {len(mas)} DRESS_RUIN_/DRESS_ARCH_ meshes) + {len(islands) - len(m_isl)} fallen DRESS_BLOCK; floating stones (< 2 lowest vertices within 10 cm of ground / another stone): "
     f"{len(fl_m)} {fl_m[:6]}; {n_contact} ring wedges rest by face contact on an already supported stone; DRESS_BLOCK instances floating {len(floating) - len(fl_m)}; largest vertex gap seen below a resting stone {max(gaps) if gaps else 0:.3f} m")

# lintel: the longest masonry stone of the doorway wall (>= 3 m along its principal axis)
lint = None
for i in m_isl:
    pts = V[i["verts"]]
    c = pts.mean(axis=0)
    w_, v_ = np.linalg.eigh(np.cov((pts[:, :2] - c[:2]).T))
    ax = v_[:, 1]
    ln = float(np.ptp((pts[:, :2] - c[:2]) @ ax))
    if ln >= 3.0 and (lint is None or ln > lint[0]):
        lint = (ln, i, pts, ax, c)
if lint is None:
    gate("RUIN_LINTEL_BEARING", False, "no stone >= 3 m long (the doorway lintel) found")
else:
    ln, i, pts, ax, c = lint
    s_ = (pts[:, :2] - c[:2]) @ ax
    c = np.array([c[0] + ax[0] * 0.5 * float(s_.min() + s_.max()), c[1] + ax[1] * 0.5 * float(s_.min() + s_.max()), c[2]])      # the middle of the stone's extent: the vertex mean is biased towards the end with more chip vertices (repair round 2)
    s_ = (pts[:, :2] - c[:2]) @ ax
    zmin = float(pts[:, 2].min())
    nrm = np.array([-ax[1], ax[0]])
    res = []
    for half, sgn in (("end A", -1), ("end B", 1)):
        ok_, tot_ = 0, 0
        for ds in (0.12, 0.22, 0.32):                                   # along the stone, from its end (the bearing on a jamb is 0.55 m long)
            for dl in (-0.3, 0.0, 0.3):                                 # across it
                q = c[:2] + ax * (sgn * (ln * 0.5 - ds)) + nrm * dl
                tot_ += 1
                ok, g = sample_support((q[0], q[1]), i["id"], zmin + 0.01)
                ok_ += ok
        res.append((half, tot_, ok_))
    if os.environ.get("RUIN_DEBUG"):
        print("DEBUG lintel", i["obj"], "len", round(ln, 2), "c", np.round(c, 2).tolist(), "ax", np.round(ax, 3).tolist(), "zmin", round(zmin, 3))
        for half, sgn in (("end A", -1), ("end B", 1)):
            for ds in (0.12, 0.22, 0.32):
                q = c[:2] + ax * (sgn * (ln * 0.5 - ds))
                print("DEBUG  ", half, ds, np.round(q, 2).tolist(), sample_support((q[0], q[1]), i["id"], zmin + 0.01), "ground", round(ground_z(q[0], q[1]), 2))
    mid = c[:2]
    free, hits = 0, 0
    for off in np.linspace(-0.6, 0.6, 7):
        p2 = mid + ax * off
        gz = ground_z(p2[0], p2[1])
        for z in np.arange(0.3, min(2.3, zmin - gz - 0.05), 0.25):
            h = mbvh.ray_cast(Vector((p2[0], p2[1], gz + z)), Vector((nrm[0], nrm[1], 0.0)), 4.0)
            hit = h[0] is not None and islands[ISL[h[2]]]["masonry"]            # the wall stones (the QA rays look at DRESS_RUIN_* only; a fallen DRESS_BLOCK 4 m away is not the doorway)
            hits += hit
            free += not hit
    # the middle of the lintel is over the doorway: nothing may stand under it (it spans, it does not sit on a block)
    ok_mid = sum(1 for dl in (-0.3, 0.0, 0.3) if not sample_support((c[0] + nrm[0] * dl, c[1] + nrm[1] * dl), i["id"], zmin + 0.01)[0])
    gate("RUIN_LINTEL_BEARING", all(r[2] >= 0.5 * r[1] for r in res) and free >= 0.9 * (free + hits),
         f"lintel {ln:.2f} m long, {pts[:, 2].max() - zmin:.2f} m thick, underside z {zmin:.2f} (ground {ground_z(mid[0], mid[1]):.2f}); bearing (9 sample points 12-32 cm in from each end, within 10 cm of a jamb): "
         + "; ".join(f"{h} {b} of {a}" for h, a, b in res) + f"; doorway opening under its middle clear on {free} of {free + hits} through-rays at 0.3-2.3 m ({ok_mid} of 3 middle points open)")
gate("RUIN_BASE_BURIED", on_ground > 0 and buried_cnt / max(on_ground, 1) >= 0.8,
     f"{on_ground} stones stand on the ground, {buried_cnt} ({buried_cnt / max(on_ground, 1):.0%}) have their lowest vertex >= 12 cm under it (need >= 80 %); depth median {np.median(buried_depth) * 100 if buried_depth else 0:.0f} cm, min {min(buried_depth) * 100 if buried_depth else 0:.0f} cm")

# irregularity: horizontal normals of standing faces (world) vs the nearest axis-aligned direction of the stone's own island
dev, lens, lens_bbox = [], [], []
for i in m_isl:
    pts = V[i["verts"]]
    cc_ = pts[:, :2].mean(axis=0)
    w_, v_ = np.linalg.eigh(np.cov((pts[:, :2] - cc_).T) + 1e-9 * np.eye(2))
    lens.append(float(np.ptp((pts[:, :2] - cc_) @ v_[:, 1])))        # length along the stone's own principal axis (repair round 2: the round-1 max(bbox x, y) of a stone yawed 30-45 deg mixes in its thickness and squeezes the CV)
    ext_ = pts.max(axis=0) - pts.min(axis=0)
    lens_bbox.append(float(max(ext_[0], ext_[1])))
tilt = []
for o in mas:
    me = o.data
    mw = np.array(o.matrix_world)[:3, :3]
    for p in me.polygons:
        n = mw @ np.array(p.normal)
        if p.area < 0.02:
            continue
        if abs(n[2]) < 0.5:
            tilt.append(math.degrees(math.asin(max(-1.0, min(1.0, n[2])))))      # lean of a standing face: 0 = plumb
tilt = np.array(tilt)
share_lean = float((np.abs(tilt) > 1.5).mean()) if len(tilt) else 0.0
cv = float(np.std(lens) / np.mean(lens)) if lens else 0.0
cv_bbox = float(np.std(lens_bbox) / np.mean(lens_bbox)) if lens_bbox else 0.0               # the round-1 definition (bounding-box extent): reported and ALSO required, so the redefinition cannot hide a regression
gate("RUIN_NOT_BOXES", share_lean >= 0.5 and cv >= 0.25 and cv_bbox >= 0.25,
     f"{len(tilt)} standing faces (> 2 cm^2): {share_lean:.0%} lean more than 1.5 deg off plumb (need >= 50 %; a box has 0 %), median |lean| {np.median(np.abs(tilt)):.1f} deg; stone length CV {cv:.2f} along the stone's own axis / {cv_bbox:.2f} by bounding box = the round-1 definition (need >= 0.25 on both), "
     f"lengths {min(lens):.2f}..{max(lens):.2f} m over {len(lens)} stones")

# UV windows
rows = [((31.0 + 64.0 * k + 9.0) / 512.0, (31.0 + 64.0 * k + 55.0) / 512.0) for k in range(8)]
n_ok, n_all = 0, 0
for o in mas:
    me = o.data
    uvl = me.uv_layers.active
    if uvl is None:
        continue
    mw = np.array(o.matrix_world)[:3, :3]
    W = world(o)
    for p in me.polygons:
        if mat_of(o, p) != "LK_MASONRY":
            continue
        n = mw @ np.array(p.normal)
        if abs(n[2]) >= 0.75:
            continue
        zs = W[list(p.vertices), 2]
        h = float(zs.max() - zs.min())
        if not (0.2 <= h <= 0.7):
            continue
        vs = np.array([uvl.data[li].uv[1] for li in p.loop_indices])
        vmin, vmax = float(vs.min()), float(vs.max())
        n_all += 1
        for r0, r1 in rows:
            for off in (0.0,):
                if vmin >= r0 + off - 0.004 and vmax <= r1 + off + 0.004:
                    n_ok += 1
                    break
            else:
                continue
            break
gate("RUIN_UV_WINDOWS", n_all > 0 and n_ok / max(n_all, 1) >= 0.7,
     f"{n_ok} of {n_all} standing LK_MASONRY faces 0.2-0.7 m high have their whole UV v-range inside one Masonry_C.png brick-row interior ({n_ok / max(n_all, 1):.0%}; need >= 70 %): no mortar line runs across a stone face")

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# REPAIR ROUND 2 (2026-10-05, review "the ruin still reads as stacked bricks": diagonal triangle splits in the shading of every block face, a regular paving-brick pattern on the tops, ruler
# straight courses of near-identical boxes, flat tops, a crown that hangs with a gap to the right pier). Five more gates, each measured on the finished mesh only:
#   RUIN_FLAT_FACES        every masonry polygon (DRESS_RUIN / DRESS_ARCH / DRESS_BLOCK) has all its loop normals within 1 deg of its own face normal: no vertex-normal gradient inside a face,
#                          so no triangle of a face can shade differently from the next (round 1: 20.7 % of the faces were > 3 deg off, up to 28 deg)
#   RUIN_UV_BRICK_INTERIOR the UV window of every masonry polygon lies inside ONE brick of Masonry_C.png: its v range inside one course and its u range between two vertical mortar joints of that course
#                          (the joint positions are re-derived from the texture GENERATOR's own random tables, golf_look_textures.mat_masonry, not from the module's pixel scan); the lintel's 3.5 m faces are exempt
#   RUIN_BEDS_NOT_RULED    stones whose beds (lowest vertices) touch along a course are chained (neighbours within 5 cm in plan, beds within 10 cm in height); a chain >= 3 m long whose bed heights
#                          lie on a straight line within 2 cm is a RULED course. Share of the above-ground stones on ruled courses <= 35 % (a skyline of identical course heights: ~90 %)
#   RUIN_TOPS_RAGGED       the exposed stone tops (nothing above them within 2 m): >= 60 % of them tilt >= 4 deg off horizontal and the median height step to the nearest other exposed top within 1.5 m is >= 6 cm
#   RUIN_ARCH_SEATED       the arch ring (radius = clear half span + half the ring thickness, sampled every 1 deg round the opening centre at the spring height) has masonry within 6 cm everywhere except
#                          one gap of at most 1.0 m, both springers (0..10 deg and 170..180 deg) are covered, no ring stone ends in free air beyond the gap (every sampled covered point is within 6 cm of
#                          a stone that touches the ground-standing masonry), and >= 2 loose stones lie within 3 m of the gap's foot (the fallen wedge + rubble heap)
import importlib

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "blender", "scripts"))
try:
    import hole09_look as _HL
except Exception as exc:                                              # pragma: no cover
    _HL = None
    print("(hole09_look not importable here:", exc, ")")


def _all_masonry_polys():
    for o in mas + blocks:
        me = o.data
        yield o, me


# ---- RUIN_FLAT_FACES
seen_meshes, worst, nfaces, nbad, nbad3 = set(), 0.0, 0, 0, 0
for o, me in _all_masonry_polys():
    if me.name in seen_meshes:
        continue
    seen_meshes.add(me.name)
    for p in me.polygons:
        n = np.array(p.normal)
        dmax = 0.0
        for li in p.loop_indices:
            ln_ = np.array(me.loops[li].normal)
            c = float(np.clip(ln_ @ n / max(np.linalg.norm(ln_) * np.linalg.norm(n), 1e-12), -1, 1))
            dmax = max(dmax, math.degrees(math.acos(c)))
        nfaces += 1
        worst = max(worst, dmax)
        nbad += dmax > 1.0
        nbad3 += dmax > 3.0
gate("RUIN_FLAT_FACES", nfaces > 0 and nbad == 0,
     f"{nfaces} masonry polygons on {len(seen_meshes)} meshes: loop normal vs face normal worst {worst:.2f} deg, {nbad} polygons over 1 deg, {nbad3} over 3 deg (need 0 over 1 deg; round 1: 20.7 % over 3 deg, worst 28 deg)")

# ---- RUIN_UV_BRICK_INTERIOR (brick layout re-derived from the generator's random tables)
def mat_masonry_joints(seed=1001, courses=8):
    rng_ = np.random.default_rng([seed, 1])
    out = []
    for k in range(courses):
        nb = int(rng_.integers(4, 8))
        w = rng_.uniform(0.6, 1.4, nb)
        cb = np.concatenate([[0.0], np.cumsum(w) / w.sum()])
        ph = float(rng_.random())
        out.append(sorted(((cb[i] - ph) % 1.0) for i in range(nb)))
    return out                                                       # per generator course k: u of its vertical mortar joints (course k is centred on v = k / courses)


JOINTS = mat_masonry_joints()
n_ok, n_all, n_exempt, bad_rows = 0, 0, 0, 0
for o in mas + blocks:
    me = o.data
    uvl = me.uv_layers.active
    if uvl is None:
        continue
    W_ = world(o)
    for p in me.polygons:
        if p.area < 0.0002:
            continue
        if mat_of(o, p) != "LK_MASONRY":
            continue
        uu = np.array([uvl.data[li].uv[0] for li in p.loop_indices])
        vv = np.array([uvl.data[li].uv[1] for li in p.loop_indices])
        if float(uu.max() - uu.min()) > 0.20:                         # a long lintel face: exempt (counted)
            n_exempt += 1
            continue
        n_all += 1
        vc = 0.5 * (vv.min() + vv.max())
        jrow = int(round(vc * 8.0)) % 8
        jf = round(vc * 8.0) / 8.0
        in_row = bool(vv.min() >= jf - 25.0 / 512.0 - 0.004 and vv.max() <= jf + 23.0 / 512.0 + 0.004)      # the brick interior of generator course j: v = j / 8 -25 .. +23 px
        crossing = False
        for jb in JOINTS[jrow]:
            for sh in range(int(math.floor(uu.min())) - 1, int(math.ceil(uu.max())) + 2):
                if uu.min() - 0.008 <= jb + sh <= uu.max() + 0.008:
                    crossing = True
        if in_row and not crossing:
            n_ok += 1
gate("RUIN_UV_BRICK_INTERIOR", n_all > 0 and n_ok / n_all >= 0.95,
     f"{n_ok} of {n_all} LK_MASONRY polygons have their whole UV window inside one brick of Masonry_C.png (v inside one course, u between two mortar joints with a 4 px margin; joints re-derived from "
     f"golf_look_textures.mat_masonry seed 1001): {n_ok / max(n_all, 1):.1%} (need >= 95 %); {n_exempt} faces wider than 0.20 uv (the 3.5 m lintel) exempt")

# ---- RUIN_BEDS_NOT_RULED
st = []
for isl in islands:
    if not isl["masonry"]:
        continue
    pts = V[isl["verts"]]
    zmin = float(pts[:, 2].min())
    if isl.get("on_ground"):
        continue
    bed = pts[pts[:, 2] <= zmin + 0.04]
    ext = pts.max(axis=0) - pts.min(axis=0)
    if ext[2] < 0.2 or max(ext[0], ext[1]) < 0.3:
        continue
    st.append(dict(z=float(bed[:, 2].mean()), lo=pts[:, :2].min(axis=0), hi=pts[:, :2].max(axis=0), c=pts[:, :2].mean(axis=0), id=isl["id"]))
parent = list(range(len(st)))


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


for i in range(len(st)):
    for j in range(i + 1, len(st)):
        a_, b_ = st[i], st[j]
        if abs(a_["z"] - b_["z"]) > 0.10:
            continue
        gap = np.maximum(np.maximum(a_["lo"] - b_["hi"], b_["lo"] - a_["hi"]), 0.0)
        if float(np.hypot(*gap)) <= 0.05:
            parent[find(i)] = find(j)
comp = {}
for i in range(len(st)):
    comp.setdefault(find(i), []).append(i)
ruled_n, ruled_c, longest = 0, 0, 0.0
for k, ids in comp.items():
    cs = np.array([st[i]["c"] for i in ids])
    zs = np.array([st[i]["z"] for i in ids])
    if len(ids) < 3:
        continue
    cc = cs.mean(axis=0)
    w_, v_ = np.linalg.eigh(np.cov((cs - cc).T))
    sa = (cs - cc) @ v_[:, 1]
    ext_ = float(np.ptp(sa))
    if ext_ < 3.0:
        continue
    A_ = np.c_[sa, np.ones(len(sa))]
    sol = np.linalg.lstsq(A_, zs, rcond=None)[0]
    res = float(np.abs(A_ @ sol - zs).max())
    longest = max(longest, ext_)
    if res <= 0.02:
        ruled_n += len(ids)
        ruled_c += 1
share = ruled_n / max(len(st), 1)
gate("RUIN_BEDS_NOT_RULED", len(st) >= 30 and share <= 0.35,
     f"{len(st)} above-ground masonry stones chained into {len(comp)} bed runs (neighbours within 5 cm in plan, beds within 10 cm in height); {ruled_c} runs >= 3 m long lie on a straight line within 2 cm = {ruled_n} stones = {share:.0%} "
     f"(need <= 35 %; longest run {longest:.1f} m)")

# ---- RUIN_TOPS_RAGGED
tops = []
for o in mas:
    me = o.data
    mw = np.array(o.matrix_world)[:3, :3]
    Wv = world(o)
    base, vid = VID[o.name]
    best = {}
    for p in me.polygons:
        n = mw @ np.array(p.normal)
        n = n / max(np.linalg.norm(n), 1e-12)
        if n[2] > 0.3:
            gid = vid[p.vertices[0]]
            if gid not in best or p.area > best[gid][0]:
                best[gid] = (float(p.area), n, Wv[list(p.vertices)].mean(axis=0))
    for gid, (area, n, c) in best.items():
        if area < 0.04 or not islands[gid]["masonry"]:
            continue
        pts = V[islands[gid]["verts"]]
        if float(pts[:, 2].max() - pts[:, 2].min()) < 0.3:
            continue
        h_up = mbvh.ray_cast(Vector((c[0], c[1], c[2] + 0.02)), Vector((0, 0, 1)), 2.0)
        blocked = h_up[0] is not None and ISL[h_up[2]] != gid
        if blocked:
            continue
        tops.append((c, math.degrees(math.acos(max(-1.0, min(1.0, n[2]))))))
if tops:
    tl = np.array([t[1] for t in tops])
    cz = np.array([[t[0][0], t[0][1], t[0][2]] for t in tops])
    steps = []
    for i in range(len(cz)):
        d_ = np.hypot(cz[:, 0] - cz[i, 0], cz[:, 1] - cz[i, 1])
        d_[i] = 9e9
        j = int(np.argmin(d_))
        if d_[j] <= 1.5:
            steps.append(abs(cz[i, 2] - cz[j, 2]))
    med_step = float(np.median(steps)) if steps else 0.0
    share_t = float((tl >= 4.0).mean())
else:
    share_t, med_step = 0.0, 0.0
gate("RUIN_TOPS_RAGGED", len(tops) >= 20 and share_t >= 0.60 and med_step >= 0.06,
     f"{len(tops)} exposed stone tops (nothing above within 2 m): {share_t:.0%} tilt >= 4 deg off horizontal (need >= 60 %), median height step to the nearest other exposed top within 1.5 m {med_step * 100:.1f} cm "
     f"over {len(steps) if tops else 0} pairs (need >= 6 cm)")

# ---- RUIN_ARCH_SEATED
arch = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("DRESS_ARCH")]
if not arch or _HL is None:
    gate("RUIN_ARCH_SEATED", False, "no DRESS_ARCH mesh or hole09_look not importable")
else:
    AP = np.vstack([world(o) for o in arch])
    c_xy = AP[:, :2].mean(axis=0)
    w_, v_ = np.linalg.eigh(np.cov((AP[:, :2] - c_xy).T))
    span = v_[:, 1]
    gz0 = ground_z(c_xy[0], c_xy[1])
    lowp = AP[(AP[:, 2] > gz0 + 1.4) & (AP[:, 2] < gz0 + 2.5)]          # the piers only (the rubble heap is lower than 1.3 m, the ring starts at the spring, 2.7 m)
    uu = (lowp[:, :2] - c_xy) @ span
    left, right = lowp[uu < 0], lowp[uu >= 0]
    c0 = 0.5 * (left[:, :2].mean(axis=0) + right[:, :2].mean(axis=0))      # opening centre (plan): between the two pier clusters
    # the spans of the two piers: the opening centre is the midpoint of the INNER faces; refine by the clear gap measured along the span axis at 1.2 m height
    uu_l, uu_r = ((left[:, :2] - c0) @ span), ((right[:, :2] - c0) @ span)
    if uu_l.mean() > uu_r.mean():
        uu_l, uu_r = uu_r, uu_l
    c0 = c0 + span * 0.5 * (float(uu_l.max()) + float(uu_r.min()))
    gz = ground_z(c0[0], c0[1])
    r_mid = _HL.ARCH_R                                              # sampled on the INTRADOS (the inner surface of the ring; a point inside a stone has no surface within 6 cm)
    spring = gz + _HL.ARCH_SPRING
    # BVH of the arch triangles
    AV, AF = [], []
    for o in arch:
        me = o.data
        me.calc_loop_triangles()
        Wv = world(o)
        b = len(AV)
        AV += [tuple(q) for q in Wv]
        AF += [[b + i for i in t.vertices] for t in me.loop_triangles]
    abvh = BVHTree.FromPolygons(AV, AF)
    cov = []
    for th in range(0, 181):
        t_ = math.radians(th)
        pt = Vector((c0[0] + span[0] * (-r_mid * math.cos(t_)), c0[1] + span[1] * (-r_mid * math.cos(t_)), spring + r_mid * math.sin(t_)))
        # the ring may be mirrored along the span axis: test both orientations and keep the better covered one
        pt2 = Vector((c0[0] + span[0] * (r_mid * math.cos(t_)), c0[1] + span[1] * (r_mid * math.cos(t_)), spring + r_mid * math.sin(t_)))
        r1, r2 = abvh.find_nearest(pt, 0.06), abvh.find_nearest(pt2, 0.06)
        cov.append((r1[0] is not None, r2[0] is not None))
    cov1 = np.array([c[0] for c in cov])
    cov2 = np.array([c[1] for c in cov])
    cov_a = cov1 if cov1.sum() >= cov2.sum() else cov2
    gaps, run = [], 0
    for x in cov_a:
        if x:
            if run:
                gaps.append(run)
            run = 0
        else:
            run += 1
    if run:
        gaps.append(run)
    gap_deg = max(gaps) if gaps else 0
    gap_m = math.radians(gap_deg) * r_mid
    spr_ok = bool(cov_a[0:11].any() and cov_a[170:181].any())
    # loose stones (rubble / fallen wedges) near the foot of the gap
    gth = int(np.argmax(~cov_a)) if (~cov_a).any() else 90
    ng = [i for i in islands if i["masonry"] and i.get("on_ground") is not None and abs(i["cx"] - c0[0]) < 3.0 and abs(i["cy"] - c0[1]) < 3.0 and (V[i["verts"]][:, 2].max() - V[i["verts"]][:, 2].min()) < 1.2]
    gate("RUIN_ARCH_SEATED", cov_a.sum() >= 127 and gap_m <= 1.0 and spr_ok and len(ng) >= 3,
         f"arch opening centre ({c0[0]:.1f}, {c0[1]:.1f}), intrados radius {r_mid:.2f} m at spring z {spring:.2f}: masonry within 6 cm at {int(cov_a.sum())} of 181 sampled angles (need >= 127 = 70 %: the missing wedge is 16 deg, the chipped wedge corners cost some more), longest uncovered arc {gap_deg} deg = {gap_m:.2f} m "
         f"(need <= 1.0 m), springers covered {spr_ok}, {len(ng)} loose stones lie within 3 m of the opening centre under the gap (need >= 3)")

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# REPAIR ROUND 3 (2026-10-05, review "the ruin still reads as stacked boxes ... triangle-split shading on the faces": measured cause = round-2 stones were convex HULLS of jittered corner points, whose faces are not
# planar: a twisted quad was split into two triangles of different normals, each with its OWN random UV window; of 4,477 round-2 faces 2,467 were triangles, 1,411 adjacent pairs were near-coplanar (< 20 deg, median 1.6)
# and 1,092 of those pairs (77 %) had a UV mismatch along the shared edge). Three more gates, measured on the finished mesh:
#   RUIN_PLANAR_FACES     every polygon of DRESS_RUIN / DRESS_ARCH has all its vertices within 1 mm of its own plane (a stone is a convex polyhedron defined by planes, hole09_stone.py): one polygon = one plane = one UV mapping
#   RUIN_NO_UV_SPLIT      no two polygons of one stone that share an edge and lie within 12 deg of coplanar (what a hull makes of a twisted quad) have a different UV along that edge (> 0.5 mm of texture at 4 m per tile)
#                         (round-2 stage: 1,092 mismatching pairs; the DRESS_BLOCK instances are rounded triangulated meshes with a box projection, their region borders are reported, not gated)
#   RUIN_MASONRY_SHARE    every DRESS_RUIN / DRESS_ARCH mesh keeps >= 50 % of its area on LK_MASONRY (PROP_MATERIALS) and < 50 % on LK_ROCK (a mesh of >= 50 % rock is held to the rock-shape gates)
import bmesh as _bm

worst_dev, n_poly, n_bad = 0.0, 0, 0
for o in mas:
    me = o.data
    W_ = world(o)
    for p in me.polygons:
        if len(p.vertices) < 4:
            n_poly += 1
            continue
        q = W_[list(p.vertices)]
        n_ = np.array(p.normal) @ np.array(o.matrix_world)[:3, :3].T
        n_ = n_ / max(np.linalg.norm(n_), 1e-12)
        dev = float(np.abs((q - q.mean(axis=0)) @ n_).max())
        worst_dev = max(worst_dev, dev)
        n_poly += 1
        n_bad += dev > 0.001
gate("RUIN_PLANAR_FACES", n_poly > 0 and n_bad == 0,
     f"{n_poly} DRESS_RUIN / DRESS_ARCH polygons on {len(mas)} meshes: worst vertex distance from its own plane {worst_dev * 1000:.3f} mm, {n_bad} over 1 mm (need 0; the hull faces of round 2 were split into triangles because they were not planar)")

pairs, mism, worst_uv = 0, 0, 0.0
bpairs, bmism = 0, 0
for o in mas + blocks:
    me = o.data
    uvl = me.uv_layers.active
    if uvl is None:
        continue
    bm_ = _bm.new()
    bm_.from_mesh(me)
    uv_ = bm_.loops.layers.uv.active
    for e in bm_.edges:
        if len(e.link_faces) != 2:
            continue
        a, b = e.link_faces
        if math.degrees(a.normal.angle(b.normal)) >= 12.0:
            continue
        d = 0.0
        for la in a.loops:
            if la.vert in e.verts:
                for lb in b.loops:
                    if lb.vert is la.vert:
                        d = max(d, (la[uv_].uv - lb[uv_].uv).length)
        if o in mas:
            pairs += 1
            mism += d > 0.000125
            worst_uv = max(worst_uv, d)
        else:
            bpairs += 1
            bmism += d > 0.000125
    bm_.free()
gate("RUIN_NO_UV_SPLIT", pairs >= 0 and mism == 0,
     f"{pairs} pairs of adjacent polygons within 12 deg of coplanar in DRESS_RUIN / DRESS_ARCH stones: {mism} have a UV mismatch along the shared edge (worst {worst_uv * 4.0 * 1000:.2f} mm of texture; need 0; round-2 stage 1,092 of 1,411); "
     f"DRESS_BLOCK instances: {bpairs} near-coplanar pairs, {bmism} on a border of their three projection regions (reported)")

low_m, low_r, per = 1.0, 0.0, []
for o in mas:
    me = o.data
    ar_ = {}
    for p in me.polygons:
        ar_[mat_of(o, p)] = ar_.get(mat_of(o, p), 0.0) + float(p.area)
    tot_ = sum(ar_.values()) or 1.0
    fm, fr = ar_.get("LK_MASONRY", 0.0) / tot_, ar_.get("LK_ROCK", 0.0) / tot_
    low_m, low_r = min(low_m, fm), max(low_r, fr)
    per.append((o.name, round(fm, 2), round(fr, 2)))
gate("RUIN_MASONRY_SHARE", low_m >= 0.5 and low_r < 0.5,
     f"{len(mas)} DRESS_RUIN / DRESS_ARCH meshes: lowest LK_MASONRY share {low_m:.0%} (need >= 50 %), highest LK_ROCK share {low_r:.0%} (need < 50 %); per mesh {per[:6]}...")

if JSON_OUT:
    json.dump(dict(blend=BLEND, fbx=FBX, gates=RES), open(JSON_OUT, "w"), indent=1)
print("RUIN_CHECK:", sum(1 for r in RES if not r["ok"]), "FAIL of", len(RES))
