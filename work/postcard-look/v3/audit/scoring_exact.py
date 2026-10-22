"""Read-only, zero-tolerance comparison of frozen course geometry.

Run in Blender --background --factory-startup --python this_file.py.
Writes only scoring_exact.json and scoring_exact.txt beside this script.
Material assignments, UVs and normals are deliberately excluded: the goal
allows shading edits, but freezes names, geometry, topology and markers.
"""
import json
import os
import re
import sys

sys.dont_write_bytecode = True
import bpy
import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
OUT = os.path.dirname(os.path.abspath(__file__))
STAGE_ROOT = os.path.abspath(os.path.join(REPO, os.environ.get("POSTCARD_SCORING_STAGE_ROOT", "work/postcard-look/v2")))
OUTPUT_STEM = os.environ.get("POSTCARD_SCORING_OUTPUT_STEM", "scoring_exact")
HOLES = tuple(int(h) for h in os.environ.get("POSTCARD_SCORING_HOLES", "8,9,10").split(","))
COLL_PREFIXES = ("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER", "CART_PATH", "PLAY_SURFACE_")
MARKER_PREFIXES = ("FLAG", "HOLE_CUP", "BALL_START", "MARKER_")
MARKER_NAMES = {"TEE_MARKER_1", "TEE_MARKER_2"}


def protected(ob):
    return (ob.name.startswith(COLL_PREFIXES) or
            ob.name.startswith(MARKER_PREFIXES) or ob.name in MARKER_NAMES)


def snapshot(path):
    is_fbx = path.lower().endswith(".fbx")
    if is_fbx:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        bpy.ops.wm.open_mainfile(filepath=path, load_ui=False)
    bpy.context.view_layer.update()
    snap = {}
    for ob in bpy.context.scene.objects:
        if not protected(ob):
            continue
        matrix = np.asarray(ob.matrix_world, dtype=np.float64).copy()
        rec = {"type": ob.type, "matrix": matrix, "local": None,
               "world": None, "polygons": None, "triangles": None}
        if ob.type == "MESH":
            coords = np.asarray([tuple(v.co) for v in ob.data.vertices], dtype=np.float64).reshape(-1, 3)
            rec["local"] = coords
            rec["world"] = coords @ matrix[:3, :3].T + matrix[:3, 3]
            rec["polygons"] = tuple(tuple(int(k) for k in p.vertices) for p in ob.data.polygons)
            ob.data.calc_loop_triangles()
            rec["triangles"] = np.asarray([tuple(t.vertices) for t in ob.data.loop_triangles], dtype=np.int64).reshape(-1, 3)
        snap[ob.name] = rec
    return snap


def spatial_triangle_multiset(rec):
    """Exact world-coordinate triangle multiset; cyclic corner order normalised.

    UV-induced duplicates and vertex reordering disappear. Triangle winding and
    multiplicity remain significant. There is no rounding or weld epsilon.
    """
    out = []
    for tri in rec["triangles"]:
        points = [tuple(rec["world"][v]) for v in tri]
        out.append(min(tuple(points[k:] + points[:k]) for k in range(3)))
    return sorted(out)


def point_set_delta(a, b):
    """Exact arithmetic symmetric nearest-point distance, without epsilon."""
    if np.array_equal(a, b):
        return 0.0
    if not len(a) or not len(b):
        return None
    worst = 0.0
    for source, target in ((a, b), (b, a)):
        for start in range(0, len(source), 128):
            d = np.linalg.norm(source[start:start+128, None, :] - target[None, :, :], axis=2)
            worst = max(worst, float(d.min(axis=1).max()))
    return worst


def compare(base, current, hole, stage, path):
    is_fbx = path.lower().endswith(".fbx")
    problems = []
    missing = sorted(set(base) - set(current))
    added = sorted(set(current) - set(base))
    if missing:
        problems.append("missing protected names: " + repr(missing))
    if added:
        problems.append("added protected names: " + repr(added))
    by_object = []
    max_vertex_delta = 0.0
    max_marker_delta = 0.0
    vertex_count = polygon_count = marker_count = mesh_count = 0
    for name in sorted(set(base) & set(current)):
        a, b = base[name], current[name]
        row = {"name": name, "type": b["type"], "pass": True,
               "matrix_exact": bool(np.array_equal(a["matrix"], b["matrix"]))}
        errors = []
        if a["type"] != b["type"]:
            errors.append("type changed")
        if not row["matrix_exact"]:
            errors.append("world matrix changed")
        if name.startswith(MARKER_PREFIXES) or name in MARKER_NAMES:
            marker_count += 1
            d = float(np.linalg.norm(a["matrix"][:3, 3] - b["matrix"][:3, 3]))
            max_marker_delta = max(max_marker_delta, d)
            row["marker_delta_m"] = d
        if a["type"] == "MESH" and b["type"] == "MESH":
            mesh_count += 1
            vertex_count += len(a["local"])
            polygon_count += len(a["polygons"])
            row["baseline_vertices"] = len(a["local"])
            row["current_vertices"] = len(b["local"])
            if is_fbx:
                aw, bw = np.unique(a["world"], axis=0), np.unique(b["world"], axis=0)
                row["unique_world_vertices_exact"] = bool(np.array_equal(aw, bw))
                row["spatial_triangle_multiset_exact"] = spatial_triangle_multiset(a) == spatial_triangle_multiset(b)
                row["baseline_unique_vertices"] = len(aw)
                row["current_unique_vertices"] = len(bw)
                row["baseline_triangles"] = len(a["triangles"])
                row["current_triangles"] = len(b["triangles"])
                d = point_set_delta(aw, bw)
                row["max_vertex_delta_m"] = d
                if d is not None:
                    max_vertex_delta = max(max_vertex_delta, d)
                for key in ("unique_world_vertices_exact", "spatial_triangle_multiset_exact"):
                    if not row[key]:
                        errors.append(key + " FAIL")
            else:
                row["local_vertices_exact"] = bool(np.array_equal(a["local"], b["local"]))
                row["world_vertices_exact"] = bool(np.array_equal(a["world"], b["world"]))
                row["polygon_vertex_lists_exact"] = a["polygons"] == b["polygons"]
                for key in ("local_vertices_exact", "world_vertices_exact", "polygon_vertex_lists_exact"):
                    if not row[key]:
                        errors.append(key + " FAIL")
            if not is_fbx and a["world"].shape == b["world"].shape:
                d = float(np.linalg.norm(a["world"] - b["world"], axis=1).max()) if len(a["world"]) else 0.0
                row["max_vertex_delta_m"] = d
                max_vertex_delta = max(max_vertex_delta, d)
            elif not is_fbx:
                row["max_vertex_delta_m"] = None
                errors.append("vertex count changed; positional delta unavailable")
        if errors:
            row["pass"] = False
            row["errors"] = errors
            problems.append(name + ": " + "; ".join(errors))
        by_object.append(row)
    return {"hole": hole, "stage": stage, "format": "fbx" if is_fbx else "blend", "path": path,
            "pass": not problems, "threshold_m": 0.0,
            "protected_name_count": len(base), "mesh_count": mesh_count,
            "baseline_vertex_count": vertex_count, "baseline_polygon_count": polygon_count,
            "marker_count": marker_count, "max_vertex_delta_m": max_vertex_delta,
            "max_marker_delta_m": max_marker_delta, "problems": problems,
            "objects": by_object}


results = []
for hole in HOLES:
    h = f"{hole:02d}"
    baseline = snapshot(os.path.join(REPO, "work/postcard-look/baseline/blender", f"hole_{h}.blend"))
    for stage, path in (("installed", os.path.join(REPO, "blender", f"hole_{h}.blend")),
                        ("staged", os.path.join(STAGE_ROOT, f"hole{h}", "stage", f"hole_{h}.blend"))):
        results.append(compare(baseline, snapshot(path), hole, stage, path))
for hole in HOLES:
    h = f"{hole:02d}"
    baseline = snapshot(os.path.join(REPO, "work/postcard-look/baseline/fbx", f"hole_{h}.fbx"))
    for stage, path in (("installed", os.path.join(REPO, "Unity/Assets/Resources/Course", f"hole_{h}.fbx")),
                        ("staged", os.path.join(STAGE_ROOT, f"hole{h}", "stage", f"hole_{h}.fbx"))):
        results.append(compare(baseline, snapshot(path), hole, stage, path))

payload = {"method": "Blend: exact ordered local/world vertices and polygon lists. FBX: exact unique world-position sets and canonical spatial triangle multisets, with winding/multiplicity; UV splits/reordering permitted. Both: exact protected names/types and matrices; zero tolerance; shader data excluded",
           "pass": all(r["pass"] for r in results), "results": results}
with open(os.path.join(OUT, OUTPUT_STEM + ".json"), "w") as f:
    json.dump(payload, f, indent=2)
lines = []
for r in results:
    line = (f"GATE: SCORING_EXACT_H{r['hole']:02d}_{r['stage'].upper()}_{r['format'].upper()} {'PASS' if r['pass'] else 'FAIL'} - "
            f"{r['mesh_count']} protected meshes, {r['baseline_vertex_count']} vertices, "
            f"{r['baseline_polygon_count']} polygons, {r['marker_count']} markers; "
            f"max vertex delta {r['max_vertex_delta_m']:.17g} m, marker delta {r['max_marker_delta_m']:.17g} m; "
            f"threshold 0 m; names/topology/matrices exact {r['pass']}")
    lines.append(line)
    lines.extend("FAIL_DETAIL: " + p for p in r["problems"])
lines.append("RESULT: " + ("ALL PASS" if payload["pass"] else "FAIL"))
with open(os.path.join(OUT, OUTPUT_STEM + ".txt"), "w") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines), flush=True)
sys.exit(0 if payload["pass"] else 1)
