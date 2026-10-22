"""blender -b <src.blend> --python write_blend.py -- <coords.npy> <out.blend>
Sets Body_M vertex coordinates from coords.npy (same vertex order/count), recalculates normals, saves a NEW blend (never overwrites src)."""
import bpy, sys, numpy as np
from pathlib import Path
a=sys.argv[sys.argv.index('--')+1:]; V=np.load(a[0]).astype(np.float32); out=a[1]
b=bpy.data.objects['Body_M']; me=b.data
assert len(me.vertices)==len(V),(len(me.vertices),len(V))
me.vertices.foreach_set('co',V.ravel()); me.update(); me.calc_loop_triangles()
bpy.ops.wm.save_as_mainfile(filepath=out,copy=False)
print('WROTE',out)
