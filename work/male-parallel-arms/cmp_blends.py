import bpy, numpy as np, sys, pickle
a=sys.argv[sys.argv.index('--')+1:]
def load(p):
    bpy.ops.wm.open_mainfile(filepath=p)
    o=bpy.data.objects['Body_M']; me=o.data; n=len(me.vertices)
    V=np.zeros(n*3); me.vertices.foreach_get('co',V); V=V.reshape(-1,3)
    polys=[tuple(p.vertices) for p in me.polygons]
    return V.astype(np.float32),polys,[ob.name for ob in bpy.data.objects]
V0,P0,N0=load(a[0]); V1,P1,N1=load(a[1])
print('verts',len(V0),len(V1),'same polys',P0==P1,'objects',N0==N1,N1)
if len(V0)==len(V1):
    mv=(V0!=V1).any(1); idx=np.nonzero(mv)[0]
    print('moved',mv.sum())
    if mv.sum():
        print('z range of moved',V0[idx,2].min(),V0[idx,2].max(),'x range',V0[idx,0].min(),V0[idx,0].max())
        zone=np.load('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-arms/data/zone.npy')
        print('moved inside my arm zone:',int((mv&zone).sum()),' outside:',int((mv&~zone).sum()))
        d=np.linalg.norm(V1[idx]-V0[idx],axis=1); print('max move mm',1000*d.max())
