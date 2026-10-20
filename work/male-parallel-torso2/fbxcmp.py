"""blender -b --python fbxcmp.py -- a.fbx b.fbx : compare imported Body_M coords by index (and by nearest if order differs)"""
import bpy, sys, numpy as np
from mathutils import kdtree
a, b = sys.argv[sys.argv.index('--') + 1:][:2]
def load(p):
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=p)
    o = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]; M = o.matrix_world
    return np.array([(M @ v.co)[:] for v in o.data.vertices]), len(o.data.polygons)
A, na = load(a); Bv, nb = load(b)
print('verts', len(A), len(Bv), 'polys', na, nb)
if len(A) == len(Bv):
    d = np.linalg.norm(A - Bv, axis=1) * 1000; print('FBXCMP index-wise: max mm', round(float(d.max()), 4), 'moved(>0.001mm)', int((d > 0.001).sum()))
    np.save('r/fbxcmp_d.npy', d); np.save('r/fbxcmp_A.npy', A)
