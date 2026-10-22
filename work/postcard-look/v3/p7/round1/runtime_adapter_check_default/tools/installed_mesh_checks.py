"""POSTCARD_LOOK area I: independent mesh-level measurements on the INSTALLED hole FBXs (Unity/Assets/Resources/Course/hole_NN.fbx), imported into Blender.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python installed_mesh_checks.py -- <out.json> [8 9 10]

Per hole (names / materials as the FBX carries them):
  * objects by prefix, triangle count, materials used, any FOAM name / material
  * PLANT_*: the first surface under each plant's base (ray down from base + 0.5 m through every non-plant mesh): water (WATER_*) = a plant on the sea; nothing within 1 m = floating
  * path overlays (DRESS_PATH_* / CART_PATH*): height of every up-facing path vertex above the play-surface mesh under it (cm), and the game ball radius it must stay under
  * shelf (WATER_SHELF*): mean / p95 width in metres (2 x distance to the nearest boundary edge, area-weighted over the face centroids)
  * rocks: object-space scale / shear leftovers of every ROCK_* object (an FBX bakes its transforms: a non-unit matrix or a 3-axis extent ratio is reported, the stretch-vs-library gate itself is postcard_look_verify NO_ROCK_STRETCH_2X)
Everything is read from the FBX only (no .blend), z is up after the import (the script checks that the ocean is the flat one).
"""
import sys, os, json, math
import bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
HOLES = [int(a) for a in argv[1:]] or [8, 9, 10]
PLAY = ("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER")
BALL_RADIUS_M = 0.0600 * 0.9144          # the game ball as the Game view draws it: 0.060 yd (measured from the projected radius in the stills: 16.4 px at 5.07 yd, fov 60, 1600 px)
res = {}


def world_tris(ob):
    me = ob.data
    M = np.array(ob.matrix_world)
    V = np.array([v.co[:] for v in me.vertices], dtype=float)
    V = (np.c_[V, np.ones(len(V))] @ M.T)[:, :3]
    return V, me


def bvh_of(objs):
    verts, tris = [], []
    off = 0
    for ob in objs:
        V, me = world_tris(ob)
        me.calc_loop_triangles()
        T = np.array([t.vertices[:] for t in me.loop_triangles], dtype=int).reshape(-1, 3)
        verts.append(V); tris.append(T + off); off += len(V)
    if not verts:
        return None
    return BVHTree.FromPolygons([tuple(v) for v in np.vstack(verts)], [tuple(t) for t in np.vstack(tris)], epsilon=0.0)


for hole in HOLES:
    n = f"{hole:02d}"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    fbx = f"{R}/Unity/Assets/Resources/Course/hole_{n}.fbx"
    bpy.ops.import_scene.fbx(filepath=fbx)
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    info = dict(fbx=os.path.relpath(fbx, R), objects=len(meshes))
    prefixes = {}
    for o in meshes:
        pre = o.name.split("_")[0] + "_" if "_" in o.name else o.name
        prefixes[pre] = prefixes.get(pre, 0) + 1
    info["prefixes"] = prefixes
    mats = {}
    for o in meshes:
        for s in o.material_slots:
            if s.material:
                mats[s.material.name] = mats.get(s.material.name, 0) + 1
    info["materials"] = mats
    info["triangles"] = int(sum(len(o.data.polygons) for o in meshes))  # polygons; exact tris below
    info["foam_named_objects"] = [o.name for o in meshes if "FOAM" in o.name.upper()]
    info["foam_materials"] = [m for m in mats if "FOAM" in m.upper()]
    info["legacy_materials"] = [m for m in mats if m.startswith("MAT_") and m not in ("MAT_FLAG", "MAT_POLE", "MAT_CUP", "MAT_BALL")]
    # which axis is up: the ocean grid is flat
    ocean = next((o for o in meshes if o.name.startswith("WATER_OCEAN")), None)
    if ocean is not None:
        d = ocean.dimensions
        info["ocean_dimensions"] = [round(d.x, 1), round(d.y, 1), round(d.z, 3)]
        info["z_is_up"] = bool(d.z < 0.1 * max(d.x, d.y))
    else:
        info["z_is_up"] = True
    # ---------------- plants vs water
    plants = [o for o in meshes if o.name.startswith("PLANT_")]
    solid = [o for o in meshes if not o.name.startswith("PLANT_") and not o.name.startswith("MARKER") and not o.name.startswith("FLAG") and not o.name.startswith("HOLE_CUP")
             and not o.name.startswith("BALL") and not o.name.startswith("POLE") and not o.name.startswith("DRESS_SMOKE")]
    tree = bvh_of(solid)
    owner = []           # which object each BVH polygon belongs to (index by polygon order across objects)
    counts = dict(plants=len(plants), vine_objects_judged_by_root=0, on_sea=0, floating_no_surface_1m=0, on_ground_or_rock=0, no_hit_at_all=0)
    sea_names, float_names = [], []
    hits_by = {}
    # per-object polygon ranges for ownership lookup
    ranges = []
    off = 0
    for ob in solid:
        ob.data.calc_loop_triangles()
        k = len(ob.data.loop_triangles)
        ranges.append((off, off + k, ob.name)); off += k
    starts = np.array([r[0] for r in ranges])
    tree_land = bvh_of([o for o in solid if not o.name.startswith("WATER_")])
    vines = dict(count=0, attached=0, unattached=0, root_gap_max_m=0.0, bottom_above_sea_min_m=1e9, unattached_names=[])
    for p in plants:
        V, me = world_tris(p)
        if len(V) == 0:
            continue
        if "VINE" in p.name.upper():
            # a vine hangs DOWN a cliff face from a root: judge the root (the highest vertices), not the hanging tip
            vines["count"] += 1
            zmax = V[:, 2].max()
            top = V[V[:, 2] >= zmax - 0.05]
            root = Vector((float(top[:, 0].mean()), float(top[:, 1].mean()), float(zmax)))
            loc, nor, idx, dist = tree_land.find_nearest(root)
            gap = float(dist) if loc is not None else 1e9
            vines["root_gap_max_m"] = max(vines["root_gap_max_m"], gap)
            vines["bottom_above_sea_min_m"] = min(vines["bottom_above_sea_min_m"], float(V[:, 2].min()))
            if gap <= 0.6:
                vines["attached"] += 1
            else:
                vines["unattached"] += 1; vines["unattached_names"].append(p.name)
            continue
        zmin = V[:, 2].min()
        low = V[V[:, 2] <= zmin + 0.03]
        base = Vector((float(low[:, 0].mean()), float(low[:, 1].mean()), float(zmin)))
        o = base + Vector((0, 0, 0.5))
        loc, nor, idx, dist = tree.ray_cast(o, Vector((0, 0, -1)), 1.5)
        if loc is None:
            loc2, nor2, idx2, dist2 = tree.ray_cast(o, Vector((0, 0, -1)), 1e4)
            if loc2 is None:
                counts["no_hit_at_all"] += 1; float_names.append(p.name)
            else:
                nm = ranges[int(np.searchsorted(starts, idx2, side="right")) - 1][2]
                if nm.startswith("WATER_"):
                    counts["on_sea"] += 1; sea_names.append(p.name)
                else:
                    counts["floating_no_surface_1m"] += 1; float_names.append(p.name)
            continue
        nm = ranges[int(np.searchsorted(starts, idx, side="right")) - 1][2]
        pre = nm.split("_")[0] + "_" + (nm.split("_")[1] if nm.startswith(("WATER", "ROCK", "DRESS")) and "_" in nm else "")
        hits_by[pre] = hits_by.get(pre, 0) + 1
        if nm.startswith("WATER_"):
            counts["on_sea"] += 1; sea_names.append(p.name)
        else:
            counts["on_ground_or_rock"] += 1
    if vines["bottom_above_sea_min_m"] == 1e9:
        vines["bottom_above_sea_min_m"] = None
    info["vines"] = vines
    info["plants"] = counts
    info["plants_support_by_surface"] = hits_by
    info["plants_on_sea_names"] = sea_names[:20]
    info["plants_floating_names"] = float_names[:20]
    # ---------------- path height above the play surface
    paths = [o for o in meshes if o.name.startswith(("DRESS_PATH", "CART_PATH"))]
    play = [o for o in meshes if o.name.startswith(PLAY)]
    ptree = bvh_of(play)
    ph = []
    for o in paths:
        V, me = world_tris(o)
        me.calc_normals_split() if hasattr(me, "calc_normals_split") else None
        up = set()
        for poly in me.polygons:
            nz = (np.array(o.matrix_world.to_3x3()) @ np.array(poly.normal))[2]
            if nz > 0.5:
                up.update(poly.vertices)
        for vi in up:
            v = Vector(V[vi])
            loc, nor, idx, dist = ptree.ray_cast(v + Vector((0, 0, 0.5)), Vector((0, 0, -1)), 2.0)
            if loc is not None:
                ph.append(float(v.z - loc.z))
    ph = np.array(ph)
    info["path"] = dict(objects=len(paths), samples=int(len(ph)), max_cm=round(float(ph.max() * 100), 2) if len(ph) else None, p99_cm=round(float(np.percentile(ph, 99) * 100), 2) if len(ph) else None,
                        mean_cm=round(float(ph.mean() * 100), 2) if len(ph) else None, min_cm=round(float(ph.min() * 100), 2) if len(ph) else None,
                        ball_radius_cm=round(BALL_RADIUS_M * 100, 2), above_1p5cm=int((ph > 0.015).sum()) if len(ph) else 0)
    # ---------------- shelf width
    shelf = [o for o in meshes if o.name.startswith("WATER_SHELF")]
    sw = dict(objects=len(shelf))
    if shelf:
        P2, A, bpts = [], [], []
        for o in shelf:
            V, me = world_tris(o)
            bm = bmesh.new(); bm.from_mesh(me)
            M = np.array(o.matrix_world)
            for f in bm.faces:
                c = np.array(f.calc_center_median()[:]); c = (M @ np.r_[c, 1])[:3]
                P2.append(c[:2]); A.append(f.calc_area())
            for e in bm.edges:
                if e.is_boundary:
                    a = (M @ np.r_[np.array(e.verts[0].co[:]), 1])[:3]; b = (M @ np.r_[np.array(e.verts[1].co[:]), 1])[:3]
                    L = float(np.linalg.norm(b[:2] - a[:2]))
                    for t in np.linspace(0, 1, max(2, int(L / 0.5) + 1)):
                        bpts.append((a[:2] * (1 - t) + b[:2] * t))
            bm.free()
        P2 = np.array(P2); A = np.array(A); bpts = np.array(bpts)
        d = np.empty(len(P2))
        for i in range(0, len(P2), 2000):
            dd = np.linalg.norm(P2[i:i + 2000, None, :] - bpts[None, :, :], axis=2)
            d[i:i + 2000] = dd.min(axis=1)
        w = 2 * d
        order = np.argsort(w); cw = np.cumsum(A[order]) / A.sum()
        sw.update(faces=int(len(P2)), area_m2=round(float(A.sum()), 1), width_mean_m=round(float((w * A).sum() / A.sum()), 2),
                  width_p95_m=round(float(w[order][np.searchsorted(cw, 0.95)]), 2), width_max_m=round(float(w.max()), 2), boundary_samples=int(len(bpts)))
    info["shelf"] = sw
    # ---------------- rocks: baked transforms
    rocks = [o for o in meshes if o.name.startswith("ROCK_")]
    nonunit, an, smax, smin = [], [], [], []
    for o in rocks:
        sc = o.matrix_world.to_scale()
        a = [abs(sc.x), abs(sc.y), abs(sc.z)]
        an.append((max(a) / max(min(a), 1e-9), o.name, [round(c, 3) for c in a])); smax.append(max(a)); smin.append(min(a))
        if max(abs(a[0] - 1), abs(a[1] - 1), abs(a[2] - 1)) > 1e-3:
            nonunit.append((o.name, [round(c, 3) for c in a]))
    an.sort(reverse=True)
    info["rocks"] = dict(objects=len(rocks), non_unit_object_scale=len(nonunit), anisotropy_max=round(an[0][0], 3) if an else None, anisotropy_worst=[(round(a, 3), n, sc) for a, n, sc in an[:5]],
                         count_anisotropy_gt_2=int(sum(1 for a in an if a[0] > 2.0)), scale_max=round(max(smax), 3) if smax else None, scale_min=round(min(smin), 3) if smin else None,
                         count_scale_gt_2=int(sum(1 for v in smax if v > 2.0)), count_scale_lt_0p4=int(sum(1 for v in smin if v < 0.4)))
    res[f"hole{hole}"] = info
    print(f"hole {hole}: {len(meshes)} meshes; plants {counts}; vines {info['vines']}; support {hits_by}; path {info['path']}; shelf {sw}; foam {info['foam_named_objects']} {info['foam_materials']}; legacy mats {info['legacy_materials']}; z_is_up {info['z_is_up']}")

with open(OUT, "w") as f:
    json.dump(res, f, indent=1)
print("wrote", OUT)
