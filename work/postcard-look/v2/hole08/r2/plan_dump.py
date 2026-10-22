"""Dump ground meshes (up-facing tris) per mesh name + material to npz for a plan raster; run in Blender."""
import bpy, sys, numpy as np
out = sys.argv[sys.argv.index("--")+1]
res = {}
for ob in bpy.data.objects:
    if ob.type != 'MESH': continue
    if not ob.name.startswith(("TERRAIN","FAIRWAY","GREEN","TEE_BOX","BUNKER","DRESS_PATH")): continue
    me = ob.data; me.calc_loop_triangles()
    mw = np.array(ob.matrix_world)
    V = np.array([v.co[:] for v in me.vertices]).reshape(-1,3) @ mw[:3,:3].T + mw[:3,3]
    T = np.array([t.vertices[:] for t in me.loop_triangles]).reshape(-1,3)
    mi = np.array([me.polygons[t.polygon_index].material_index for t in me.loop_triangles])
    mats = [m.name if m else "" for m in me.materials]
    a,b,c = V[T[:,0]],V[T[:,1]],V[T[:,2]]
    n = np.cross(b-a,c-a); up = n[:,2] > 0
    res[ob.name+"|V"] = V; res[ob.name+"|T"] = T[up]; res[ob.name+"|M"] = np.array([mats[i] for i in mi[up]])
np.savez(out, **res)
print("DUMPED", sorted({k.split('|')[0] for k in res}))
