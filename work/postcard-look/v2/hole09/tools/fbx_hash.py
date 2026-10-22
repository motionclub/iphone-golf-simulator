"""fbx_hash.py - geometry hash of an FBX re-import (names, world matrices, vertex positions rounded 1e-4, material names). Blender -b --python fbx_hash.py -- a.fbx [b.fbx ...]"""
import bpy, sys, hashlib, numpy as np
for path in sys.argv[sys.argv.index("--") + 1:]:
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes): bpy.data.meshes.remove(m)
    for m in list(bpy.data.materials): bpy.data.materials.remove(m)
    for m in list(bpy.data.images): bpy.data.images.remove(m)
    bpy.ops.import_scene.fbx(filepath=path)
    h = hashlib.sha256(); nv = nf = n = 0
    for o in sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: o.name):
        me = o.data; co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co)
        h.update(o.name.encode()); h.update(np.round(np.array(o.matrix_world), 4).tobytes()); h.update(np.round(co, 4).tobytes())
        h.update(",".join(sl.material.name if sl.material else "-" for sl in o.material_slots).encode())
        nv += len(me.vertices); nf += len(me.polygons); n += 1
    print("FBXHASH", path.split("/")[-2], h.hexdigest(), n, "meshes", nv, "verts", nf, "faces")
