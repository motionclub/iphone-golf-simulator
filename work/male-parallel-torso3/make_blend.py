"""Write coords of data/V_<tag>.npy into Body_M of a copy of a source blend (positions only).
blender -b --factory-startup --python make_blend.py -- <src.blend> <coords.npy> <out.blend>"""
import sys, numpy as np, bpy
src, npy, out = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=src)
b = bpy.data.objects['Body_M']; me = b.data
V = np.load(npy); assert len(V) == len(me.vertices), (len(V), len(me.vertices))
assert me.shape_keys is None, 'shape keys present'
me.vertices.foreach_set('co', V.astype(np.float64).ravel()); me.update(); me.calc_loop_triangles()
bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
print('MAKE_BLEND_DONE', out)
