"""blender -b start.blend --python apply_blend.py -- new_co.npy out.blend : write positions only"""
import bpy, numpy as np, sys
a=sys.argv[sys.argv.index('--')+1:]
new=np.load(a[0]); me=bpy.data.objects['Body_F'].data
assert len(me.vertices)==len(new)
me.vertices.foreach_set('co',new.astype(np.float32).ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=a[1],copy=False)
