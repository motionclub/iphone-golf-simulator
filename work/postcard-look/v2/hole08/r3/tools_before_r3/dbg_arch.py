import sys, math
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.dont_write_bytecode = True
import bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath=REPO + "/work/postcard-look/v2/hole08/scratch/dev2/dev_hole_08.blend")
import hole08_look as K
for o in bpy.data.objects:
    if o.name.startswith("ROCK_OUTCROP"):
        V, T = K.world_tris(o)
        a, b, c = V[T[:,0]], V[T[:,1]], V[T[:,2]]
        n = np.cross(b-a, c-a); n /= np.linalg.norm(n, axis=1)[:,None]
        top = (n[:,2] > 0.95)
        print('upfaces z hist', np.round(np.percentile(a[top][:,2],[0,10,50,90,100]),2), top.sum())
        top = top & (a[:,2] > 4.0)
        pts = V[np.unique(T[top])]
        print(o.name, "top verts", len(pts), "z", pts[:,2].min(), pts[:,2].max(), "scale", tuple(o.scale), "loc", tuple(o.location))
        print(" top bbox x", pts[:,0].min(), pts[:,0].max(), "y", pts[:,1].min(), pts[:,1].max())
        np.save("/tmp/outcrop_top.npy", pts)
        print(" all bbox", V.min(0), V.max(0))
for o in bpy.data.objects:
    if o.name.startswith("DRESS_ARCH"):
        V = K.world_verts([o]); print(o.name, V.min(0), V.max(0), tuple(o.location), tuple(o.rotation_euler))
    if o.name.startswith("DRESS_BLOCK"):
        V = K.world_verts([o]); print(o.name, V.min(0), V.max(0))
