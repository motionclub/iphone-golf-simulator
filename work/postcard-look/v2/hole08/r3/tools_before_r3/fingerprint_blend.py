"""H_REPRODUCIBLE helper: sha256 of every mesh object's name + 0.1 mm rounded world vertices + vertex counts of a hole blend.
usage: Blender -b --factory-startup --python fingerprint_blend.py -- A.blend [B.blend ...] ; prints FP <file> <hash16> objects N meshes M verts V tris T"""
import sys, hashlib
import bpy, numpy as np
for path in sys.argv[sys.argv.index("--") + 1:]:
    bpy.ops.wm.open_mainfile(filepath=path)
    bpy.context.view_layer.update()
    h = hashlib.sha256()
    nv = nt = nm = 0
    for ob in sorted((o for o in bpy.data.objects if o.type == 'MESH'), key=lambda o: o.name):
        mw = np.array(ob.matrix_world)
        co = np.array([v.co[:] for v in ob.data.vertices]).reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
        h.update(ob.name.encode()); h.update(np.round(co, 4).tobytes())
        ob.data.calc_loop_triangles()
        nv += len(co); nt += len(ob.data.loop_triangles); nm += 1
    print(f"FP {path} {h.hexdigest()[:16]} meshes {nm} verts {nv} tris {nt}")
