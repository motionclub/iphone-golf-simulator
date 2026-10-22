"""blender -b --factory-startup --python set_positions.py -- <in.blend> <V.npy> <out.blend>   (same topology; positions only)"""
import sys, numpy as np, bpy
src, vp, out = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=src)
me = bpy.data.objects['Body_M'].data
V = np.load(vp); assert len(V) == len(me.vertices)
me.vertices.foreach_set('co', np.asarray(V, np.float64).reshape(-1)); me.update()
bpy.ops.wm.save_as_mainfile(filepath=out); print('SAVED', out)
