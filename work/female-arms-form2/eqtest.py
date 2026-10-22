import bpy, numpy as np, sys
a=sys.argv[sys.argv.index('--')+1:]
def co(p):
    bpy.ops.wm.open_mainfile(filepath=p); me=bpy.data.objects['Body_F'].data; c=np.empty(len(me.vertices)*3,np.float32); me.vertices.foreach_get('co',c); return c.reshape(-1,3)
A=co(a[0]); B=co(a[1]); print('equal',bool((A==B).all()) if A.shape==B.shape else 'shape differs')
