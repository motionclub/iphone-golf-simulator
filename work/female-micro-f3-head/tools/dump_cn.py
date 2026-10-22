import sys, bpy, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body_F'].data
nl = len(me.loops); cn = np.empty(nl * 3); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
lv = np.empty(nl, np.int32); me.loops.foreach_get('vertex_index', lv)
np.savez(a[1], cn=cn, lv=lv)
