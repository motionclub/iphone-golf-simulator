"""Write a staged blend = start blend with Body_M positions replaced by a candidate npy.  blender -b --factory-startup --python make_blend.py -- <start.blend> <V.npy> <out.blend>"""
import sys, numpy as np, bpy
a = sys.argv[sys.argv.index('--') + 1:]; src, npy, out = a
bpy.ops.wm.open_mainfile(filepath=src); me = bpy.data.objects['Body_M'].data
V = np.load(npy); assert len(V) == len(me.vertices) and me.shape_keys is None
co = V.astype(np.float32).astype(np.float64)       # float32 positions as stored in the blend
me.vertices.foreach_set('co', co.ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=out, compress=False); print('MAKE_BLEND_DONE', out)
