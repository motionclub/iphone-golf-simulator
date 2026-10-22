"""Hole 8 NEEDLE: scene build (three flat 6 m pads standing in the sea, two water gaps, a ruined sea arch).

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/hole08_build.py
    ... -- --out DIR    (optional: write the .blend / overview / FBX into DIR instead of the repo, for experiments)

Writes blender/hole_08.blend, blender/previews/hole_08_overview.png and Unity/Assets/Resources/Course/hole_08.fbx (+ .meta),
prints its own GATE lines (mesh quality, needles, arch, rocks, lines of play) and exits 1 when one fails. main() below is the
whole build: postcard_lib calls plus this hole's scenery (the SCENERY dict of hole08_design.py). The helpers under it do what
the library does not:
  * weld_terrain      the shore meets each water ellipse at four pad corners and the library leaves sub-yard edges there
                      (a shore vertex 0.1-0.4 yd from the crossing, an ellipse vertex 0.05 yd from it). Edges shorter than
                      WELD_M are merged, together with the same edge on every ring of the cliff wall below, so there is no
                      needle triangle or zero-area face; nothing on the boundary moves more than WELD_M / 2 (0.28 yd measured).
  * fix_overhangs     a weld can twist a wall triangle out by a degree or two: pushed back in (walls stay vertical or undercut).
  * split_deep_band   the underwater wall band (z 0 to -6) is cut in two, so no wall triangle is a 6 m sliver.
  * tidy_flat         play-surface and water-band meshes are re-triangulated (constrained Delaunay on a welded, simplified
                      boundary, boundary slivers peeled): a flat surface has no needle triangles either.
  * scenery           arch + outcrop, needles (capped at 18 m), cliff-foot boulders; overview framing; qa_gates.
  * rubble_on_outcrop the library's arch rubble is placed for flat ground at the play height and so hangs 1-2 m in the air over the
                      outcrop: it is deleted and replaced by fallen blocks that are dropped (settle_rock) onto the outcrop and kept
                      only when they pass the same rests() test as the gate below.
  * RockField         world-space rock set + merged BVH: gates ROCKS_CONTACT_CHAIN (every rock instance in the scene is chained by
                      touching surfaces to a rock that stands in the sea) and ROCKS_REST (every rock that is not hung from its
                      neighbours, i.e. not an arch ring piece, rests on rock below it and does not overhang open air).
"""
import sys
import os
import math
import random
import hashlib

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector, Matrix  # noqa: E402
from mathutils import geometry as G  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402
from mathutils.kdtree import KDTree  # noqa: E402

import postcard_lib as P  # noqa: E402

YD = P.YD
WELD_M = 0.8                # terrain boundary edges shorter than this are welded (0.875 yd)
STACK_CAP_M = 18.0          # brief: needles may rise above the pads but never above 18 m, the tee camera must see the next pad
STACK_TIP_M = 17.6          # the tallest needle's design tip (tilt jitter stays under the cap)
STACK_FLOOR_M = 9.0         # the shortest needle is still well above the 6 m pads
OVERVIEW_ROT = (50.0, 0.0, 4.0)   # camera tilt, roll, yaw: the hole runs almost straight up the frame (tee at the bottom)
OVERVIEW_RES = (900, 1800)
ARCH_MOVE_X_YD = -1.2       # the arch stands 1.2 yd further out than SCENERY['arch'].x so its right pillar clears the pad edge
ARCH_SCALE = 1.25           # the arch is built 25 percent larger than span_yd/height_yd so it reads from the overview camera
CHAIN_TOL_M = 0.05          # rocks count as touching when their surfaces cross or come this close (gate ROCKS_CONTACT_CHAIN)
REST_CONTACT_M = 0.25       # gate ROCKS_REST: the underside of a rock that is not in the sea touches or sinks into a rock within this
REST_OVERHANG_MAX = 0.5     # ... and at most this share of its lower half hangs over open air (hovering rubble measured 57-80 percent)
# Needle positions that differ from SCENERY['stacks'] (x, d in yards, key = the stack's seed): from the middle pad and from the
# tee the design's needle 7 stands exactly behind the arch opening and needle 9 exactly behind the flag, so they move 12 yd
# left and 30 yd right. Still outside the water ellipses and far from every line of play.
STACK_MOVE = {7: (-52.0, 345.0), 9: (16.0, 398.0)}
# mesh name -> (boundary edge length h in metres, boundary sliver peel angle in degrees, weld distance, simplify tolerance);
# the water bands are soft decoration (a 0.35 m simplification is invisible), the play surfaces keep their scoring edges (0.05 m)
FLAT_MESHES = {"FAIRWAY": (2.4, 5.0, 0.25, 0.05), "FAIRWAY_FIRSTCUT": (2.4, 5.0, 0.25, 0.05), "GREEN": (2.4, 5.0, 0.25, 0.05),
               "GREEN_APRON": (2.4, 5.0, 0.25, 0.05), "TEE_BOX": (1.6, 5.0, 0.25, 0.05), "BUNKER_01": (2.0, 5.0, 0.25, 0.05),
               "WATER_SHALLOW": (5.0, 0.0, 0.6, 0.35), "WATER_FOAM": (3.0, 0.0, 0.6, 0.30), "WATER_FOAM_CREST": (1.6, 0.0, 0.3, 0.08)}


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = os.path.abspath(args[args.index("--out") + 1]) if "--out" in args else None
    D = P.start("hole08_design", out_dir=out)
    SC = D.scenery
    P.build_terrain(D)                                      # flat top at 6 m, both ellipses cut out, undercut cliffs
    welds, move = weld_terrain(D)                           # no sub-metre edges at the four pad corners
    fix_overhangs(D)
    split_deep_band(D)
    P.build_play_surfaces(D)                                # fairway, first cut, green, apron, tee box, bunker + lip
    P.build_water(D)                                        # sea, shallow and foam bands round every pad and gap
    tidy_all_flat(D)                                        # clean triangles on every flat mesh
    trim_lip_off_green(D)
    P.import_rocks(D)
    outcrop, arch, ring = arch_with_outcrop(D, SC["arch"])  # SCENERY['arch']
    stacks = [sea_stack(D, st) for st in SC["stacks"]]      # SCENERY['stacks']
    boulders = cliff_foot_boulders(D)
    P.build_gameplay(D)
    P.build_cameras_and_light(D, overview_rot_deg=OVERVIEW_ROT)
    frame_overview(D, OVERVIEW_RES)
    P.render_overview(D, res=OVERVIEW_RES)
    ok = qa_gates(D, move, stacks, outcrop, arch, ring, boulders)
    P.save(D)
    P.export_fbx(D)
    st = P.stats(D)
    print(f"stats: {st['objects']} objects, {st['meshes']} meshes, {st['tris']} triangles ({st['ground_tris']} ground), "
          f"{welds} terrain welds; geometry fingerprint {fingerprint()}")
    if not ok:
        sys.exit(1)


def fingerprint():
    """sha256 of every mesh object's name and 0.1 mm rounded vertex coordinates: two builds must print the same."""
    h = hashlib.sha256()
    for ob in sorted((o for o in bpy.data.objects if o.type == 'MESH'), key=lambda o: o.name):
        mw = np.array(ob.matrix_world)
        co = np.array([v.co[:] for v in ob.data.vertices]).reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
        h.update(ob.name.encode())
        h.update(np.round(co, 4).tobytes())
    return h.hexdigest()[:16]


# ----------------------------------------------------------------------------- terrain hygiene
def weld_terrain(D, weld_m=WELD_M):
    """Merge the two ends of every terrain top-boundary edge shorter than weld_m (and the same edge on every ring of the
    wall below it) at their midpoint, then re-trace D.loops. Returns (welds, largest vertex move in metres)."""
    ob, pz = D.terrain, D.play_z
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    n_weld, max_move = 0, 0.0
    for _ in range(200):
        bm.edges.ensure_lookup_table()
        best = None
        for e in bm.edges:
            L = e.calc_length()
            if L >= weld_m or (best is not None and L >= best[0]):
                continue
            if all(abs(v.co.z - pz) < 1e-6 for v in e.verts) and any(len(f.verts) == 4 for f in e.link_faces):
                best = (L, e)
        if best is None:
            break
        e = best[1]
        pairs = [(e.verts[0], e.verts[1])]
        cur, ca = e, e.verts[0]
        seen = set()
        while True:                                   # walk down the wall: the same edge on every ring
            q = next((f for f in cur.link_faces if len(f.verts) == 4 and f not in seen), None)
            if q is None:
                break
            seen.add(q)
            bot = next((x for x in q.edges if not (set(x.verts) & set(cur.verts))), None)
            na = next((x.other_vert(ca) for x in q.edges if bot is not None and ca in x.verts and x is not cur
                       and x.other_vert(ca) in bot.verts), None)
            if bot is None or na is None:
                break
            pairs.append((na, bot.other_vert(na)))
            cur, ca = bot, na
        tmap = {}
        for a, b in pairs:
            mid = (a.co + b.co) * 0.5
            max_move = max(max_move, (a.co - mid).length)
            a.co = mid
            b.co = mid
            tmap[b] = a
        bmesh.ops.weld_verts(bm, targetmap=tmap)
        n_weld += 1
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges[:])
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    me = ob.data
    me.calc_loop_triangles()
    co = np.array([v.co[:] for v in me.vertices])
    T = np.array([t.vertices[:] for t in me.loop_triangles])
    Tt = T[np.abs(co[T][:, :, 2] - pz).max(1) < 1e-6]
    loops = _boundary_loops(Tt)                                 # land on the left of every loop
    D.loops = [[(float(co[i][0]), float(co[i][1])) for i in lp] for lp in loops]
    D.loop_kinds = ["outer" if P.signed_area(np.array(L)) > 0 else "hole" for L in D.loops]
    D._distfield = None
    return n_weld, max_move


def _boundary_loops(T):
    """Closed boundary loops (vertex index lists) of a counter-clockwise triangle set; the land is on the left."""
    directed = {(a, b) for t in T.tolist() for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0]))}
    nxt = {a: b for (a, b) in directed if (b, a) not in directed}
    assert len(nxt) == sum(1 for (a, b) in directed if (b, a) not in directed), "pinched terrain boundary"
    loops, seen = [], set()
    for s0 in sorted(nxt):
        if s0 in seen:
            continue
        loop, cur = [], s0
        while cur not in seen:
            seen.add(cur)
            loop.append(cur)
            cur = nxt[cur]
        loops.append(loop)
    return loops


def fix_overhangs(D, step=0.03):
    """Welding twists the wall where two columns with different insets merge (a pad corner): a triangle may then lean out by a
    degree or two. Move the lower vertices of any wall triangle whose normal points up inward until none does (walls stay
    vertical or undercut). Returns the number of vertex moves."""
    me, pz = D.terrain.data, D.play_z
    co = np.array([v.co[:] for v in me.vertices])
    me.calc_loop_triangles()
    T = np.array([t.vertices[:] for t in me.loop_triangles])
    moves = 0
    for _ in range(60):
        a, b, c = co[T[:, 0]], co[T[:, 1]], co[T[:, 2]]
        n = np.cross(b - a, c - a)
        n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
        wall = np.abs(co[T][:, :, 2] - pz).max(1) > 1e-6
        bad = np.nonzero(wall & (n[:, 2] > 0.004))[0]
        if len(bad) == 0:
            break
        push = {}
        for i in bad:
            h = np.hypot(n[i, 0], n[i, 1])
            if h < 1e-9:
                continue
            zmin = co[T[i]][:, 2].min()
            for v in T[i]:
                if co[v][2] <= zmin + 1e-6:
                    push.setdefault(int(v), []).append(-n[i, :2] / h)
        for v, ds in push.items():
            co[v][:2] += np.mean(ds, axis=0) * step
            moves += 1
    for v, p in zip(me.vertices, co):
        v.co = p
    me.update()
    return moves


def split_deep_band(D):
    """Cut the lowest wall band (waterline z 0 down to z -6, never visible) at z -3: two 3 m quads instead of one 6 m one."""
    bm = bmesh.new()
    bm.from_mesh(D.terrain.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0.0, 0.0, -3.0),
                           plane_no=(0.0, 0.0, 1.0), dist=1e-6)
    bm.to_mesh(D.terrain.data)
    bm.free()
    D.terrain.data.update()


def _evenodd(Pt, A, B):
    out = np.zeros(len(Pt), bool)
    ax, ay, bx, by = A[:, 0][None], A[:, 1][None], B[:, 0][None], B[:, 1][None]
    with np.errstate(divide='ignore', invalid='ignore'):
        for s in range(0, len(Pt), 512):
            px, py = Pt[s:s + 512, 0:1], Pt[s:s + 512, 1:2]
            cond = (ay > py) != (by > py)
            xint = (bx - ax) * (py - ay) / (by - ay) + ax
            out[s:s + 512] = ((cond & (px < xint)).sum(axis=1) & 1).astype(bool)
    return out


def _tri_min_angle(V, T):
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]

    def ang(p, q, r):
        u, v = q - p, r - p
        cs = (u * v).sum(1) / np.maximum(np.hypot(u[:, 0], u[:, 1]) * np.hypot(v[:, 0], v[:, 1]), 1e-12)
        return np.degrees(np.arccos(np.clip(cs, -1, 1)))
    return np.minimum(np.minimum(ang(a, b, c), ang(b, c, a)), ang(c, a, b))


def tidy_flat(ob, h, peel=6.0, weld=0.25, simp=0.05, grid=1.7, margin=0.9):
    """Re-triangulate a flat (constant z) triangle mesh. Constraints = the region boundary and the material interfaces; their
    vertices closer than `weld` merge, chains are simplified (RDP `simp`) and cut to edges <= h; interior points sit on a
    grid of grid*h kept margin*h from every constraint; constrained Delaunay; boundary triangles with an angle under `peel`
    degrees are dropped (repeatedly). Face materials are carried over. Returns False when the mesh is not flat."""
    me = ob.data
    me.calc_loop_triangles()
    co = np.array([v.co[:] for v in me.vertices])
    if co[:, 2].max() - co[:, 2].min() > 1e-6:
        return False
    z0 = float(co[0, 2])
    T = np.array([t.vertices[:] for t in me.loop_triangles])
    mat = np.array([me.polygons[t.polygon_index].material_index for t in me.loop_triangles])
    emap = {}
    for k, (a, b, c) in enumerate(T.tolist()):
        for u, v in ((a, b), (b, c), (c, a)):
            emap.setdefault((min(u, v), max(u, v)), []).append(k)
    kind = {}                                         # edge -> 'B' region boundary | 'M' material interface
    for e, ks in emap.items():
        if len(ks) != 2:
            kind[e] = 'B'
        elif mat[ks[0]] != mat[ks[1]]:
            kind[e] = 'M'
    cv = sorted({v for e in kind for v in e})
    kd = KDTree(len(cv))
    for i, v in enumerate(cv):
        kd.insert((co[v][0], co[v][1], 0.0), i)
    kd.balance()
    par = list(range(len(cv)))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for i, v in enumerate(cv):
        for (_p, j, _d) in kd.find_range((co[v][0], co[v][1], 0.0), weld):
            ri, rj = find(i), find(j)
            if ri != rj:
                par[rj] = ri
    groups = {}
    for i, v in enumerate(cv):
        groups.setdefault(find(i), []).append(v)
    rep, pts = {}, []
    for g in groups.values():
        p = co[g][:, :2].mean(axis=0)
        for v in g:
            rep[v] = len(pts)
        pts.append(p)
    edges = {}
    for (u, v), k_ in kind.items():
        a, b = rep[u], rep[v]
        if a != b:
            e = (min(a, b), max(a, b))
            if edges.get(e) != 'B':
                edges[e] = k_
    adj = {}
    for a, b in edges:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    junction = {n for n, nb in adj.items() if len(nb) != 2}
    seen_e, chains = set(), []

    def walk(start, nxt):
        ch = [start, nxt]
        seen_e.add((min(start, nxt), max(start, nxt)))
        prev, cur = start, nxt
        while cur not in junction and cur != start:
            n2 = [x for x in adj[cur] if x != prev]
            if not n2:
                break
            prev, cur = cur, n2[0]
            e = (min(prev, cur), max(prev, cur))
            if e in seen_e:
                break
            seen_e.add(e)
            ch.append(cur)
        return ch
    for j in sorted(junction):
        for nb in sorted(adj[j]):
            if (min(j, nb), max(j, nb)) not in seen_e:
                chains.append(walk(j, nb))
    for n in sorted(adj):
        for nb in sorted(adj[n]):
            if (min(n, nb), max(n, nb)) not in seen_e:
                chains.append(walk(n, nb))

    def rdp(idx, tol):
        keep = {0, len(idx) - 1}
        stack = [(0, len(idx) - 1)]
        while stack:
            i, j = stack.pop()
            if j <= i + 1:
                continue
            a, b = pts[idx[i]], pts[idx[j]]
            seg = b - a
            L = float(np.hypot(*seg))
            best, bk = -1.0, -1
            for k in range(i + 1, j):
                p = pts[idx[k]]
                d = abs(seg[0] * (p[1] - a[1]) - seg[1] * (p[0] - a[0])) / L if L > 1e-12 else float(np.hypot(*(p - a)))
                if d > best:
                    best, bk = d, k
            if best > tol:
                keep.add(bk)
                stack.append((i, bk))
                stack.append((bk, j))
        return [idx[k] for k in sorted(keep)]
    sub, bnd_edges = set(), []
    for ch in chains:
        k0 = edges[(min(ch[0], ch[1]), max(ch[0], ch[1]))]
        if ch[0] == ch[-1] and len(ch) > 6:
            far = max(range(len(ch)), key=lambda k: float(np.hypot(*(pts[ch[k]] - pts[ch[0]]))))
            ch2 = rdp(ch[:far + 1], simp)[:-1] + rdp(ch[far:], simp)
        else:
            ch2 = rdp(ch, simp) if len(ch) > 2 else ch
        for a, b in zip(ch2[:-1], ch2[1:]):
            k = int(math.ceil(float(np.hypot(*(pts[b] - pts[a]))) / h))
            prev = a
            for j in range(1, k):
                pts.append(pts[a] + (pts[b] - pts[a]) * j / k)
                e = (min(prev, len(pts) - 1), max(prev, len(pts) - 1))
                sub.add(e)
                if k0 == 'B':
                    bnd_edges.append(e)
                prev = len(pts) - 1
            e = (min(prev, b), max(prev, b))
            sub.add(e)
            if k0 == 'B':
                bnd_edges.append(e)
    live = sorted({n for e in sub for n in e})                     # only the vertices a constraint still uses (RDP dropped the rest)
    renum = {n: i for i, n in enumerate(live)}
    Pp = np.array([pts[n] for n in live])
    E = np.array(sorted((renum[a], renum[b]) for a, b in sub))
    Bn = np.array(sorted({(renum[a], renum[b]) for a, b in bnd_edges}))
    BA, BB = Pp[Bn[:, 0]], Pp[Bn[:, 1]]
    bvh = BVHTree.FromPolygons([tuple(c) for c in co.tolist()], [tuple(t) for t in T.tolist()], all_triangles=True)
    sp = grid * h
    x0, y0 = Pp.min(0)
    x1, y1 = Pp.max(0)
    GX, GY = np.meshgrid(np.arange(x0 + sp * 0.37, x1, sp), np.arange(y0 + sp * 0.61, y1, sp), indexing='ij')
    C = np.stack([GX.ravel(), GY.ravel()], 1)
    C = C[_evenodd(C, BA, BB)]
    A_, B_ = Pp[E[:, 0]], Pp[E[:, 1]]
    ab = B_ - A_
    l2 = np.maximum((ab ** 2).sum(1), 1e-12)
    keep = np.zeros(len(C), bool)
    for s in range(0, len(C), 256):
        c = C[s:s + 256]
        t = np.clip(((c[:, None, 0] - A_[None, :, 0]) * ab[None, :, 0] + (c[:, None, 1] - A_[None, :, 1]) * ab[None, :, 1]) / l2[None], 0, 1)
        dx = c[:, None, 0] - (A_[None, :, 0] + ab[None, :, 0] * t)
        dy = c[:, None, 1] - (A_[None, :, 1] + ab[None, :, 1] * t)
        keep[s:s + 256] = np.sqrt(dx * dx + dy * dy).min(1) >= margin * h
    C = C[keep]
    allp = np.vstack([Pp, C]) if len(C) else Pp
    vo, _eo, fo, _a, _b, _c = G.delaunay_2d_cdt([Vector((float(x), float(y))) for x, y in allp],
                                                [(int(a), int(b)) for a, b in E], [], 0, 1e-5, False)
    V = np.array([(v.x, v.y) for v in vo])
    Tn = np.array([list(f) for f in fo], dtype=np.int64).reshape(-1, 3)
    a, b, c = V[Tn[:, 0]], V[Tn[:, 1]], V[Tn[:, 2]]
    ar = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    Tn[ar < 0] = Tn[ar < 0][:, [0, 2, 1]]                         # counter-clockwise = facing up
    Tn = Tn[np.abs(ar) > 2e-3]
    Tn = Tn[_evenodd(V[Tn].mean(axis=1), BA, BB)]
    newmat = np.array([mat[bvh.find_nearest(Vector((float(x), float(y), z0)))[2]] for x, y in V[Tn].mean(axis=1)])
    for _ in range(40):                                           # peel boundary slivers
        cnt = {}
        for t in Tn.tolist():
            for u, v in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                e = (min(u, v), max(u, v))
                cnt[e] = cnt.get(e, 0) + 1
        onb = np.array([any(cnt[(min(u, v), max(u, v))] == 1 for u, v in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])))
                        for t in Tn.tolist()])
        bad = onb & (_tri_min_angle(V, Tn) < peel)
        if not bad.any():
            break
        Tn, newmat = Tn[~bad], newmat[~bad]
    used = np.unique(Tn)
    remap = -np.ones(len(V), np.int64)
    remap[used] = np.arange(len(used))
    Vn, Tn = V[used], remap[Tn]
    mats = list(me.materials)
    smooth = any(p.use_smooth for p in me.polygons)
    me.clear_geometry()
    me.from_pydata([(float(x), float(y), z0) for x, y in Vn], [], [tuple(int(i) for i in t) for t in Tn])
    me.materials.clear()
    for m_ in mats:
        me.materials.append(m_)
    for p, mi in zip(me.polygons, newmat):
        p.material_index = int(mi)
        p.use_smooth = smooth
    me.update()
    return True


def trim_lip_off_green(D):
    """The bunker's raised grass lip may not lie on the green disc (the green is flat at +0.26 m): drop lip quads that touch it."""
    for name in [n for n in D.objects if n.endswith("_LIP")]:
        ob = bpy.data.objects[name]
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        pts = np.array([(v.co.x, v.co.y) for v in bm.verts])
        green = P.lie_codes_m(D, pts[:, 0], pts[:, 1]) == P.LIE_GREEN
        bad = [f for f in bm.faces if any(green[v.index] for v in f.verts)]
        bmesh.ops.delete(bm, geom=bad, context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.update()


def tidy_all_flat(D):
    done = []
    for name, (h, peel, weld, simp) in FLAT_MESHES.items():
        ob = bpy.data.objects.get(name)
        if ob is not None and tidy_flat(ob, h, peel=peel, weld=weld, simp=simp):
            done.append(name)
    return done


# ----------------------------------------------------------------------------- scenery (library rocks only)
def fit_rock(D, kind, center, dims, yaw=0.0, tilt=(0.0, 0.0)):
    """Instance of a library rock scaled so its bounding box is `dims` (x, y, z metres) about `center`."""
    mn, mx = D.rock_bbox["CLIFF_ROCK" if kind.startswith("CLIFF") else "ROCK_" + kind.replace("ROCK_", "")]
    size, ctr = mx - mn, (mn + mx) * 0.5
    scale = Vector((dims[0] / size.x, dims[1] / size.y, dims[2] / size.z))
    R = Matrix.Rotation(yaw, 3, 'Z') @ Matrix.Rotation(tilt[0], 3, 'X') @ Matrix.Rotation(tilt[1], 3, 'Y')
    loc = Vector(center) - R @ Vector((ctr.x * scale.x, ctr.y * scale.y, ctr.z * scale.z))
    return P.place_rock(D, kind, loc, scale=scale, rot=R.to_euler())


def sea_stack(D, st):
    """A needle: tapering library rocks stacked in the sea (base boulder, waist, tall tip) and a small satellite spire.
    The design's 12-30 yd heights are mapped onto STACK_FLOOR_M..STACK_TIP_M (9-17.6 m), keeping their order."""
    rnd = random.Random(8100 + st["seed"])
    cx, cy = P.m(*STACK_MOVE.get(st["seed"], (st["x"], st["d"])))
    R = st["radius_yd"] * YD
    t = max(0.0, min(1.0, (st["height_yd"] - 12.0) / (30.0 - 12.0)))
    H = STACK_FLOOR_M + (STACK_TIP_M - STACK_FLOOR_M) * t
    w0 = 1.15 * R                                                  # footprint stays inside the design radius
    pieces = [("CLIFF", w0, -4.5, 0.46 * H), ("LARGE", 0.74 * w0, 0.30 * H, 0.76 * H), ("MEDIUM", 0.44 * w0, 0.58 * H, H)]
    objs = []
    for kind, w, z0, z1 in pieces:
        off = Vector((rnd.uniform(-0.10, 0.10) * R, rnd.uniform(-0.10, 0.10) * R, 0.0))
        objs.append(fit_rock(D, kind, (cx + off.x, cy + off.y, (z0 + z1) / 2), (w, w * rnd.uniform(0.85, 1.0), z1 - z0),
                             yaw=rnd.uniform(0, math.tau), tilt=(rnd.uniform(-0.04, 0.04), rnd.uniform(-0.04, 0.04))))
    ang = rnd.uniform(0, math.tau)
    sx, sy = cx + math.cos(ang) * 0.95 * w0, cy + math.sin(ang) * 0.95 * w0
    objs.append(fit_rock(D, "LARGE", (sx, sy, (-4.0 + 0.55 * H) / 2), (0.42 * w0, 0.40 * w0, 0.55 * H + 4.0), yaw=rnd.uniform(0, math.tau)))
    return objs, H


def arch_with_outcrop(D, a):
    """The ruined arch on a rock outcrop beside the front bunker, in the sea off the green pad's left cliff (visual only:
    ROCK_/CLIFF_ROCK instances, no collider). SCENERY['arch'] gives the place, facing and outcrop; the arch is built a little
    bigger than span_yd/height_yd so that it reads from the overview camera (ARCH_SCALE)."""
    rnd = random.Random(8200)
    cx, cy = P.m(a["x"] + ARCH_MOVE_X_YD, a["d"])
    r = a["base_radius_yd"] * YD
    top = a["base_top_m"]
    span, height = a["span_yd"] * YD * ARCH_SCALE, min(a["height_yd"] * YD * ARCH_SCALE, STACK_CAP_M - top - 0.6)
    phi = math.radians(a["facing_deg"])
    ax, ay = math.cos(phi), -math.sin(phi)                          # the arch plane axis (pillar to pillar)
    objs = [fit_rock(D, "CLIFF", (cx, cy, (top - 6.0) / 2 - 0.8), (2.0 * r, 1.75 * r, top + 6.0), yaw=0.3)]
    for side in (-1, 1):                                            # a footing under each pillar
        px, py = cx + ax * side * span / 2, cy + ay * side * span / 2
        objs.append(fit_rock(D, "LARGE", (px, py, top - 1.1), (span * 0.55, span * 0.50, 2.8), yaw=rnd.uniform(0, math.tau)))
    for k in range(4):                                              # boulders round the plinth at the waterline
        ang = math.pi * 0.35 + k * math.pi * 0.42 + rnd.uniform(-0.2, 0.2)
        s = rnd.uniform(0.9, 1.3)
        objs.append(fit_rock(D, "LARGE", (cx + math.cos(ang) * r * 0.95, cy + math.sin(ang) * r * 0.8, 0.4 * s),
                             (4.4 * s, 4.0 * s, 4.6 * s), yaw=rnd.uniform(0, math.tau)))
    arch = P.build_arch(D, (cx, cy), a["facing_deg"], span_m=span, height_m=height)
    dz = top + 0.2 - (D.play_z - 0.25)                              # build_arch stands on the play height: onto the outcrop
    for ob in arch:
        ob.location.z += dz
    body, lib_rubble = arch[:-8], arch[-8:]                         # the library ends with 8 rubble rocks round the feet
    for ob in lib_rubble:                                           # they were placed for flat ground at the play height and hang in the
        bpy.data.objects.remove(ob, do_unlink=True)                 # air over the outcrop: replaced by rubble that is settled onto it
    ring = body[6:]                                                 # after the 6 pillar rocks: the ring pieces and the stub, held up by their neighbours
    rubble = rubble_on_outcrop(D, objs, (cx, cy), (ax, ay), span, rnd)
    return objs, body + rubble, ring


def rubble_on_outcrop(D, support, centre, axis, span, rnd, want=4, tries=80):
    """Fallen blocks round the arch's feet that really lie on the outcrop. Candidates are scattered like the library's rubble
    (rings of 0.35-1.5 half-spans round the arch centre), each is dropped straight down until its lowest point sinks 0.12 m into
    the outcrop rock under it (settle_rock) and kept only when it then passes the same rests() test as the gate, with the
    stricter 0.15 m / 25 percent limits: no hovering, no overhanging the edge. `support` = the outcrop rocks."""
    cx, cy = centre
    ax, ay = axis
    fx, fy = -ay, ax                                                # horizontal, perpendicular to the arch plane
    R = span / 2.0
    kept = []
    for _ in range(tries):
        if len(kept) >= want:
            break
        ang, rr, s = rnd.uniform(0, math.tau), R * rnd.uniform(0.35, 1.5), rnd.uniform(0.7, 1.6)
        dims = (s * rnd.uniform(1.2, 1.9), s * rnd.uniform(0.9, 1.4), s * rnd.uniform(0.7, 1.1))
        x = cx + ax * math.cos(ang) * rr + fx * math.sin(ang) * rr * 0.55
        y = cy + ay * math.cos(ang) * rr + fy * math.sin(ang) * rr * 0.55
        ob = fit_rock(D, rnd.choice(("SMALL", "SMALL", "MEDIUM")), (x, y, D.play_z), dims, yaw=rnd.uniform(0, math.tau))
        if settle_rock(ob, RockField(support + kept)):
            F = RockField(support + kept + [ob])
            if F.rests(len(F.obs) - 1, contact=0.15, unsupported_max=0.25)[0]:
                kept.append(ob)
                continue
        bpy.data.objects.remove(ob, do_unlink=True)
    return kept


def cliff_foot_boulders(D, seed=11, spacing=11.0, keep_clear=4.0):
    """Boulders hugging the cliff foot along every pad edge, none inside a water ellipse (the gaps stay clear)."""
    rnd = random.Random(seed)
    ells = [(P.m(k[1], k[2]), k[3] / 2 * YD, k[4] / 2 * YD) for k in D.hole.hazards if k[0] == "water"]

    def in_gap(x, y):
        return any(((x - c[0]) / (a + keep_clear)) ** 2 + ((y - c[1]) / (b + keep_clear)) ** 2 <= 1 for c, a, b in ells)
    objs = []
    for loop in D.loops:
        L = np.array(loop)
        e = np.roll(L, -1, 0) - L
        seg = np.hypot(e[:, 0], e[:, 1])
        cum = np.concatenate([[0.0], np.cumsum(seg)])
        s = rnd.uniform(0, spacing)
        while s < cum[-1]:
            i = int(np.searchsorted(cum, s, side='right') - 1)
            p = L[i] + e[i] * ((s - cum[i]) / max(seg[i], 1e-9))
            tg = e[i] / max(seg[i], 1e-9)
            out = np.array([tg[1], -tg[0]])                           # land is on the left, outward is the right normal
            s += spacing * rnd.uniform(0.7, 1.4)
            q = p + out * rnd.uniform(2.2, 4.2)
            if in_gap(q[0], q[1]) or rnd.random() < 0.25:
                continue
            kind = rnd.choice(("LARGE", "LARGE", "MEDIUM", "MEDIUM"))
            sc = rnd.uniform(0.55, 1.0)
            sz = sc * rnd.uniform(0.8, 1.2)
            bb = D.rock_bbox["ROCK_" + kind]
            top = rnd.uniform(0.8, min(2.6, (bb[1].z - bb[0].z) * sz - 0.4))   # shows 0.8-2.6 m above the sea, sunk at least 0.4 m
            objs.append(P.place_rock(D, kind, (q[0], q[1], top - bb[1].z * sz),
                                     (sc, sc * rnd.uniform(0.85, 1.1), sz)))
    return objs


class RockField:
    """A set of rock instances in world space plus one merged BVH: the tool behind settle_rock and the contact gates.
    The library rocks are 12-vertex, 20-triangle icosahedra, so every polygon is one triangle and a ray-cast face index is
    also the polygon index."""

    SEA_TOL = 0.15      # a rock whose lowest vertex is at or below this height stands in the sea

    def __init__(self, obs):
        bpy.context.view_layer.update()
        self.obs = list(obs)
        self.V, self.F, self.owner = [], [], []
        verts, faces, base = [], [], 0
        for i, o in enumerate(self.obs):
            mw = np.array(o.matrix_world)
            co = np.array([v.co[:] for v in o.data.vertices]).reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
            fc = [tuple(p.vertices) for p in o.data.polygons]
            assert all(len(f) == 3 for f in fc), f"{o.name}: RockField expects triangle meshes"
            self.V.append(co)
            self.F.append(fc)
            verts += [tuple(c) for c in co.tolist()]
            faces += [tuple(base + k for k in f) for f in fc]
            self.owner += [i] * len(fc)
            base += len(co)
        self.bvh = BVHTree.FromPolygons(verts, faces)
        self.zmin = [float(v[:, 2].min()) for v in self.V]

    def surface_samples(self, i):
        """Vertices, edge midpoints and face centroids of rock i (62 points on an icosahedron)."""
        V, pts = self.V[i], list(self.V[i])
        for a, b, c in self.F[i]:
            pts += [(V[a] + V[b]) / 2, (V[b] + V[c]) / 2, (V[c] + V[a]) / 2, (V[a] + V[b] + V[c]) / 3]
        return np.array(pts)

    def gap_below(self, i, p, skip_own=True):
        """Distance straight down from point p (on rock i) to the first surface of another rock; 0 when p lies inside another
        rock (the ray leaves it through a back face), inf when nothing is below."""
        o, d = Vector(p), Vector((0.0, 0.0, -1.0))
        for _ in range(12):
            hit = self.bvh.ray_cast(o, d)
            if hit[0] is None:
                return math.inf
            if skip_own and self.owner[hit[2]] == i:
                o = hit[0] + d * 1e-4
                continue
            return 0.0 if hit[1].z < 0.0 else float(p[2] - hit[0].z)
        return math.inf

    def reaches_sea(self, i):
        return self.zmin[i] <= self.SEA_TOL

    def contact_pairs(self, tol=0.15):
        """Index pairs of rocks that overlap or whose surfaces come within tol metres of each other."""
        n = len(self.obs)
        lo = [v.min(0) - tol for v in self.V]
        hi = [v.max(0) + tol for v in self.V]
        trees = [BVHTree.FromPolygons([tuple(c) for c in self.V[i].tolist()], self.F[i]) for i in range(n)]
        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                if (lo[i] > hi[j]).any() or (lo[j] > hi[i]).any():
                    continue
                if trees[i].overlap(trees[j]) or any(
                        (r := trees[j].find_nearest(Vector(p)))[0] is not None and r[3] < tol for p in self.V[i]) or any(
                        (r := trees[i].find_nearest(Vector(p)))[0] is not None and r[3] < tol for p in self.V[j]):
                    pairs.append((i, j))
        return pairs

    def floating(self, tol=0.15):
        """Indices of rocks with no chain of touching rocks down to a rock that stands in the sea."""
        adj = {i: set() for i in range(len(self.obs))}
        for i, j in self.contact_pairs(tol):
            adj[i].add(j)
            adj[j].add(i)
        seen = {i for i in adj if self.reaches_sea(i)}
        stack = list(seen)
        while stack:
            for m in adj[stack.pop()]:
                if m not in seen:
                    seen.add(m)
                    stack.append(m)
        return [i for i in adj if i not in seen]

    def rests(self, i, contact=REST_CONTACT_M, unsupported_max=REST_OVERHANG_MAX):
        """(ok, why) for a rock that is not hung from its neighbours. Unless it stands in the sea: some point of its underside
        (lower-half surface samples) touches or sinks into another rock (gap <= contact), the column under its centre has rock
        below it, and at most unsupported_max of the lower-half samples have open air under them (no rock below, or more than
        its own height of air), so it neither floats nor overhangs a gap."""
        if self.reaches_sea(i):
            return True, "stands in the sea"
        S = self.surface_samples(i)
        zmid = 0.5 * (self.zmin[i] + float(self.V[i][:, 2].max()))
        h = float(self.V[i][:, 2].max()) - self.zmin[i]
        low = S[S[:, 2] <= zmid]
        gaps = np.array([self.gap_below(i, p) for p in low])
        g0 = float(gaps.min())
        if g0 > contact:
            return False, (f"its underside is {g0:.2f} m above the rock under it" if math.isfinite(g0) else "nothing under its underside")
        ctr = self.V[i].mean(0)
        gc = self.gap_below(i, np.array([ctr[0], ctr[1], self.zmin[i] + 1e-3]))
        if not math.isfinite(gc):
            return False, "centre of mass hangs over open air"
        bad = float(np.mean(gaps > max(h, 0.5)))
        if bad > unsupported_max:
            return False, f"{bad * 100:.0f} percent of its lower half overhangs open air"
        return True, "rests on rock below"


def settle_rock(ob, support, sink=0.12):
    """Move rock `ob` straight along z so that its lowest contact sinks `sink` metres into the topmost surface of the rocks in
    `support` (a RockField) below it. Returns False when no vertex of it has any support under it."""
    bpy.context.view_layer.update()
    mw = np.array(ob.matrix_world)
    V = np.array([v.co[:] for v in ob.data.vertices]).reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
    gaps = []
    for x, y, z in V:
        hit = support.bvh.ray_cast(Vector((x, y, float(V[:, 2].max()) + 2.0)), Vector((0.0, 0.0, -1.0)))
        if hit[0] is not None:
            gaps.append(float(z - hit[0].z))
    if not gaps:
        return False
    ob.location.z -= min(gaps) + sink
    bpy.context.view_layer.update()
    return True


def frame_overview(D, res, margin=1.05):
    """CAM_HOLE_OVERVIEW framed on everything that is built (pads, needles, arch), same view direction as the library's.
    Blender's ortho_scale spans the longer image side."""
    cam = bpy.data.objects["CAM_HOLE_OVERVIEW"]
    R = cam.rotation_euler.to_matrix()
    right, up, view = R @ Vector((1, 0, 0)), R @ Vector((0, 1, 0)), R @ Vector((0, 0, -1))
    pts = []
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob.name.startswith("WATER") or ob.hide_render or ob.name in P.ROCK_NAMES:
            continue
        pts += [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    rs = [p.dot(right) for p in pts]
    us = [p.dot(up) for p in pts]
    cr, cu = (min(rs) + max(rs)) / 2, (min(us) + max(us)) / 2
    w, h = res
    span_u, span_r = max(us) - min(us), max(rs) - min(rs)
    cam.data.ortho_scale = (max(span_u, span_r * h / w) if h >= w else max(span_r, span_u * w / h)) * margin
    cam.location = right * cr + up * cu - view * 1500.0


# ----------------------------------------------------------------------------- the build's own gates
def _gate(name, ok, detail):
    print(f"GATE: {name} {'PASS' if ok else 'FAIL'} - {detail}", flush=True)
    return ok


def _world_verts(obs):
    out = []
    for ob in obs:
        mw = np.array(ob.matrix_world)
        co = np.array([v.co[:] for v in ob.data.vertices])
        out.append(co @ mw[:3, :3].T + mw[:3, 3])
    return np.vstack(out)


def qa_gates(D, weld_move, stacks, outcrop, arch, ring, boulders):
    """Mesh hygiene and scenery rules that postcard_verify does not measure."""
    h, pz = D.hole, D.play_z
    ok = True
    # 1. no needle triangles / zero-area faces on any ground or water mesh
    worst = []
    for name in ("TERRAIN_NEEDLE", "FAIRWAY", "FAIRWAY_FIRSTCUT", "GREEN", "GREEN_APRON", "TEE_BOX", "BUNKER_01", "BUNKER_01_LIP",
                 "WATER_SHALLOW", "WATER_FOAM", "WATER_FOAM_CREST"):
        me = bpy.data.objects[name].data
        me.calc_loop_triangles()
        co = np.array([v.co[:] for v in me.vertices])
        T = np.array([t.vertices[:] for t in me.loop_triangles])
        a, b, c = co[T[:, 0]], co[T[:, 1]], co[T[:, 2]]
        area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)

        def ang(p, q, r):
            u, v = q - p, r - p
            return np.degrees(np.arccos(np.clip((u * v).sum(1) / np.maximum(np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1), 1e-12), -1, 1)))
        mn = np.minimum(np.minimum(ang(a, b, c), ang(b, c, a)), ang(c, a, b))
        worst.append((name, float(mn.min()), float(area.min())))
    bad = [w for w in worst if w[1] < 5.0 or w[2] < 0.02]
    ok &= _gate("MESH_QUALITY", not bad, "min triangle angle / min area over every ground and water mesh: " +
                ", ".join(f"{n} {a_:.1f} deg {ar:.2f} m2" for n, a_, ar in worst) + (f"; BAD {bad}" if bad else " (limits 5 deg, 0.02 m2)"))
    ok &= _gate("TERRAIN_WELD", weld_move <= 0.5 * YD, f"largest boundary vertex move {weld_move:.3f} m = {weld_move / YD:.2f} yd "
                f"(<= 0.5 yd, SHORE_MATCH measures the result); loops {[len(L) for L in D.loops]}, shortest loop edge "
                f"{min(float(np.min(np.hypot(*(np.roll(np.array(L), -1, 0) - np.array(L)).T))) for L in D.loops):.2f} m")
    # 2. needles: height cap, none in a water ellipse, 25 yd from every leg of the centerline, none on land
    sv = [(_world_verts(objs), H) for objs, H in stacks]
    top = max(v[:, 2].max() for v, _ in sv)
    far = min(min(h.dist_center((x / YD, y / YD)) for x, y in v[:, :2]) for v, _ in sv)
    in_w = sum(1 for v, _ in sv for x, y in v[:, :2] if any(k[0] == "water" and h.in_ellipse(k, (x / YD, y / YD)) for k in h.hazards))
    on_l = sum(1 for v, _ in sv for x, y in v[:, :2] if h.on_land((x / YD, y / YD)))
    ok &= _gate("NEEDLES", top <= STACK_CAP_M + 1e-6 and far >= 25.0 and in_w == 0 and on_l == 0,
                f"{len(sv)} needles: highest point {top:.2f} m (cap {STACK_CAP_M}), nearest vertex {far:.1f} yd from the centerline (>= 25), "
                f"{in_w} vertices in a water ellipse, {on_l} on land")
    # 3. arch: height cap; it stands on the footings, the footings on the plinth (gates ROCKS_CONTACT_CHAIN / ROCKS_REST below)
    av = _world_verts(arch)
    plinth, foot = _world_verts(outcrop[:1]), _world_verts(outcrop[1:3])
    ok &= _gate("ARCH", av[:, 2].max() <= STACK_CAP_M + 1e-6,
                f"{len(arch)} arch rocks on {len(outcrop)} outcrop rocks, top {av[:, 2].max():.2f} m (cap {STACK_CAP_M}), "
                f"lowest arch rock {av[:, 2].min():.2f} m (plinth top {plinth[:, 2].max():.2f} m, footings top {foot[:, 2].max():.2f} m)")
    # 4. nothing pokes through a play surface: no rock vertex above the land top, inside the shore and outside the water ellipses
    allrocks = [o for objs, _ in stacks for o in objs] + outcrop + arch + boulders
    rv = _world_verts(allrocks)
    poke = sum(1 for x, y, z in rv if z > pz + 1e-6 and h.lie_at((x / YD, y / YD)) != "Water")
    in_gap = sum(1 for x, y, z in rv if any(k[0] == "water" and h.in_ellipse(k, (x / YD, y / YD)) for k in h.hazards))
    ok &= _gate("ROCKS_OFF_PLAY_SURFACES", poke == 0 and in_gap == 0,
                f"{len(allrocks)} rock instances, {len(rv)} vertices: {poke} above the land top over dry land, {in_gap} inside a water ellipse")
    # 5. nothing floats: every sea rock reaches the water
    lows = [float(_world_verts([o])[:, 2].min()) for objs, _ in stacks for o in objs[:1]] + [float(_world_verts([o])[:, 2].min()) for o in boulders + outcrop[:1]]
    ok &= _gate("ROCKS_STAND_IN_THE_SEA", max(lows) <= 0.0, f"lowest vertex of every needle base / boulder / outcrop is at or below the sea: highest of those {max(lows):.2f} m")
    # 5b. nothing hovers: over EVERY rock instance in the scene (not only the lists above) -- a chain of touching rocks leads down
    #     to a rock standing in the sea, and every rock that is not hung from its neighbours (the arch ring) rests on the rock under it
    inst = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(P.ROCK_NAMES) and o.name not in P.ROCK_NAMES]
    field = RockField(inst)
    floating = field.floating(CHAIN_TOL_M)
    ok &= _gate("ROCKS_CONTACT_CHAIN", not floating and len(inst) == len(allrocks),
                f"{len(inst)} rock instances in the scene ({len(allrocks)} built here): {sum(field.reaches_sea(i) for i in range(len(inst)))} stand in the sea, "
                f"the rest are chained to them by surfaces that cross or lie within {CHAIN_TOL_M} m; floating: "
                f"{[inst[i].name for i in floating]}")
    hung = {o.name for o in ring}
    verdict = [(inst[i].name, field.rests(i)) for i in range(len(inst)) if inst[i].name not in hung]
    loose = [(n, why) for n, (good, why) in verdict if not good]
    ok &= _gate("ROCKS_REST", not loose,
                f"{len(verdict)} rocks not hung from neighbours ({len(hung)} arch ring pieces are): "
                f"{sum(1 for _, (g, w) in verdict if w == 'stands in the sea')} stand in the sea, "
                f"{sum(1 for _, (g, w) in verdict if g and w != 'stands in the sea')} rest on rock below (underside within {REST_CONTACT_M} m of it, "
                f"at most {int(REST_OVERHANG_MAX * 100)} percent of the lower half over open air); not resting: {loose}")
    # 6. the tee, landing-pad and green stay visible from the game's address camera (CameraRig.FrameAddress: 4.5 yd behind the
    #    ball, 2.4 yd up): a ray from the camera to the next pad and to the green is never stopped by a rock
    verts, faces, base = [], [], 0
    for o in allrocks:
        mw = np.array(o.matrix_world)
        co = np.array([v.co[:] for v in o.data.vertices]) @ mw[:3, :3].T + mw[:3, 3]
        verts += [tuple(c) for c in co]
        faces += [tuple(base + i for i in p.vertices) for p in o.data.polygons]
        base += len(co)
    bvh = BVHTree.FromPolygons(verts, faces)
    pin = h.pin
    green_pts = [pin] + [(pin[0] + 10 * math.cos(t), pin[1] + 10 * math.sin(t)) for t in np.linspace(0, math.tau, 8, endpoint=False)]
    stations = [("tee", (0.0, 0.0), h.center[1], [(19.0, 150.0), (19.0, 178.0), (16.0, 200.0)] + green_pts),
                ("middle pad", h.center[1], pin, green_pts),
                ("middle pad far end", (14.0, 205.0), pin, green_pts)]
    blocked, tested = [], 0
    for nm, ball, aim, targets in stations:
        b = Vector((*P.m(*ball), pz + 0.3))
        dv = Vector((*P.m(*aim), 0.0)) - Vector((b.x, b.y, 0.0))
        dv.normalize()
        cam = b - dv * 4.5 * YD + Vector((0, 0, 2.4 * YD))
        for t in targets:
            tp = Vector((*P.m(*t), pz + 0.3))
            d = tp - cam
            hit = bvh.ray_cast(cam, d.normalized(), d.length - 0.05)
            tested += 1
            if hit[0] is not None:
                blocked.append((nm, tuple(round(c, 1) for c in t)))
    ok &= _gate("LINES_OF_PLAY_VISIBLE", not blocked,
                f"{tested} camera-to-target rays (tee, middle pad, its far end -> landing pad and green, 9 green points): {len(blocked)} stopped by a rock {blocked[:3]}")
    return ok


if __name__ == "__main__":
    main()
