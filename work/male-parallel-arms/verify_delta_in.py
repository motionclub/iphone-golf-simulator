import bpy, sys, numpy as np
a=sys.argv[sys.argv.index('--')+1:]
d=np.load(a[0]); idx=d['indices']; new=d['new'].astype(np.float32); base=d['base'].astype(np.float32)
bpy.ops.wm.open_mainfile(filepath=a[1]); me=bpy.data.objects['Body_M'].data
V=np.zeros(len(me.vertices)*3,dtype=np.float32); me.vertices.foreach_get('co',V); V=V.reshape(-1,3)
print('DELTA_IN_BLEND matches new:',int((V[idx]==new).all(1).sum()),'of',len(idx),' still at base:',int((V[idx]==base).all(1).sum()))
