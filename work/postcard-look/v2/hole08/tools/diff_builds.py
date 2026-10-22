"""Round 7: per-object diff of two hole 8 blends (the round-6 stage = what is installed vs the round-7 stage).
usage: Blender -b --factory-startup --python diff_builds.py -- OLD.blend NEW.blend OUT.json
Per mesh object: name, 0.1 mm world-vertex hash and the material names; reports added / removed / moved / re-materialled objects grouped by name prefix."""
import sys, hashlib, json, re
import bpy, numpy as np
old, new, out = sys.argv[sys.argv.index("--") + 1:][:3]
def load(path):
    bpy.ops.wm.open_mainfile(filepath=path); bpy.context.view_layer.update(); d = {}
    for ob in bpy.data.objects:
        if ob.type != 'MESH': continue
        mw = np.array(ob.matrix_world)
        co = np.array([v.co[:] for v in ob.data.vertices]).reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
        d[ob.name] = (hashlib.sha256(np.round(co, 4).tobytes()).hexdigest()[:12], len(co), [m.name if m else None for m in ob.data.materials], co.min(0).tolist() if len(co) else None, co.max(0).tolist() if len(co) else None)
    return d
A = load(old); B = load(new)
def cls(n): return re.sub(r"[._]?\d+$", "", re.sub(r"\.\d+$", "", n))
rep = {"added": sorted(set(B) - set(A)), "removed": sorted(set(A) - set(B)), "changed_geometry": [], "changed_materials": []}
for n in sorted(set(A) & set(B)):
    if A[n][0] != B[n][0]: rep["changed_geometry"].append(n)
    elif A[n][2] != B[n][2]: rep["changed_materials"].append(n)
groups = {}
for k in ("added", "removed", "changed_geometry", "changed_materials"):
    g = {}
    for n in rep[k]: g[cls(n)] = g.get(cls(n), 0) + 1
    groups[k] = g
ground = [n for n in B if n.split(".")[0].split("_")[0] in ("TERRAIN", "FAIRWAY", "GREEN", "TEE", "BUNKER", "CART")]
gc = [n for n in ground if n in A and A[n][0] != B[n][0]]
print("DIFF objects old", len(A), "new", len(B), "same", len(set(A) & set(B)) - len(rep["changed_geometry"]) - len(rep["changed_materials"]))
for k, g in groups.items(): print("DIFF", k, sum(g.values()), dict(sorted(g.items(), key=lambda kv: -kv[1])[:14]))
print("DIFF collision-named meshes changed:", gc)
json.dump({"report": rep, "groups": groups, "collision_changed": gc}, open(out, "w"), indent=1)
