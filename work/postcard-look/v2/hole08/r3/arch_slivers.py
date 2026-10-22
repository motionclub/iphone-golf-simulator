import sys, math
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
import bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--") + 1])
ob = [o for o in bpy.data.objects if o.name.startswith("DRESS_ARCH")][0]
me = ob.data; me.calc_loop_triangles()
mw = np.array(ob.matrix_world)
V = np.array([v.co[:] for v in me.vertices]) @ mw[:3,:3].T + mw[:3,3]
print("arch verts", len(V), "tris", len(me.loop_triangles), "faces", len(me.polygons))
thin = []
for t in me.loop_triangles:
    a, b, c = V[list(t.vertices)]
    e = [np.linalg.norm(b-a), np.linalg.norm(c-b), np.linalg.norm(a-c)]
    area = 0.5*np.linalg.norm(np.cross(b-a, c-a))
    ar = max(e)**2 / max(area, 1e-12)
    if ar > 40 or area < 1e-6: thin.append((round(float(ar),1), round(float(area),6), round(max(e),3)))
print("thin tris (ar>40 or area<1e-6):", len(thin), sorted(thin, reverse=True)[:10])
# UV stretch: UV area / world area per tri
lay = me.uv_layers.active.data
bad = 0; worst = []
for t in me.loop_triangles:
    a, b, c = V[list(t.vertices)]
    area = 0.5*np.linalg.norm(np.cross(b-a, c-a))
    uv = [np.array(lay[l].uv) for l in t.loops]
    au = 0.5*abs((uv[1][0]-uv[0][0])*(uv[2][1]-uv[0][1])-(uv[2][0]-uv[0][0])*(uv[1][1]-uv[0][1]))
    if area > 1e-4:
        d = math.sqrt(au/area) * 10.0   # UV per metre * tile(10 m?) unknown; just ratio
        worst.append(d)
w = np.array(worst)
print("uv density ratio (sqrt(uvarea/area)) min/median/max", w.min(), np.median(w), w.max(), " >2x median:", int((w > 2*np.median(w)).sum()), "<0.5x:", int((w < 0.5*np.median(w)).sum()))
print("materials", [m.name for m in me.materials])
