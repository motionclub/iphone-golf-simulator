import bpy, sys, math, json
import numpy as np
from mathutils import Vector
A = sys.argv[sys.argv.index("--")+1:]
def arg(n, d=None): return A[A.index(n)+1] if n in A else d
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=arg("--in"))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); body = bpy.data.objects[arg("--mesh", "Body")]
mw = body.matrix_world; me = body.data
vg = {g.index: g.name for g in body.vertex_groups}
bones = rig.data.bones
def head(n): return rig.matrix_world @ bones[n].head_local
def tail(n): return rig.matrix_world @ bones[n].tail_local
res = {}
for side in ("Right", "Left"):
    names = [side + s for s in ("Hand",)] + [side + f + j for f in ("Thumb", "Index", "Middle", "Ring", "Little") for j in ("Proximal", "Intermediate", "Distal")]
    verts = {}
    for v in me.vertices:
        w = {vg[g.group]: g.weight for g in v.groups if vg[g.group] in names}
        tot = sum(w.values())
        if tot > .5: verts[v.index] = (max(w, key=w.get), tot)
    P = np.array([list(mw @ me.vertices[i].co) for i in verts])
    hand = head(side + "Hand"); mid_tip = tail(side + "MiddleDistal")
    fwd = (mid_tip - hand).normalized()
    lat = (head(side + "IndexProximal") - head(side + "LittleProximal")).normalized()
    nrm = fwd.cross(lat).normalized(); lat = nrm.cross(fwd).normalized()
    R = np.array([[*fwd], [*lat], [*nrm]])
    L = (P - np.array(hand)) @ R.T
    out = {"nverts": len(verts), "length_wrist_to_tip_cm": float((L[:, 0].max()) * 100), "width_cm": float((L[:, 1].max() - L[:, 1].min()) * 100),
           "thick_cm": float((L[:, 2].max() - L[:, 2].min()) * 100)}
    # finger radii: distance of finger verts to their segment
    for f in ("Index", "Middle", "Ring", "Little", "Thumb"):
        seg = [(head(side + f + j), tail(side + f + j)) for j in ("Proximal", "Intermediate", "Distal")]
        rs = [[], [], []]
        for i, (g, t) in verts.items():
            if g.startswith(side + f):
                k = 0 if "Proximal" in g else 1 if "Intermediate" in g else 2
                a, b = seg[k]; p = mw @ me.vertices[i].co; ab = b - a
                tt = max(0, min(1, (p - a).dot(ab) / ab.length_squared)); rs[k].append(((p - (a + ab * tt)).length))
        out[f + "_radius_mm"] = [round(float(np.mean(r)) * 1000, 1) if r else None for r in rs]
        out[f + "_seglen_mm"] = [round((b - a).length * 1000, 1) for a, b in seg]
    # finger spread: angle between index and little proximal directions
    di = (tail(side + "IndexProximal") - head(side + "IndexProximal")).normalized(); dl = (tail(side + "LittleProximal") - head(side + "LittleProximal")).normalized()
    out["index_little_spread_deg"] = round(math.degrees(di.angle(dl)), 1)
    res[side] = out
print("MEASURE", json.dumps(res))
