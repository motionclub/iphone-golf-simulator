import bpy, numpy as np, sys
def coords(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    b=bpy.data.objects['Body_M']; n=len(b.data.vertices)
    a=np.zeros(n*3,dtype=np.float64); b.data.vertices.foreach_get('co',a)
    f=np.array([tuple(p.vertices) for p in b.data.polygons],dtype=object)
    return a.reshape(-1,3), len(b.data.polygons)
A,pa=coords('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-arms/baseline/HeroBase_Male_Silhouette.blend')
np.save('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-arms/data/V_start.npy',A)
B,pb=coords('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1f/final/HeroBase_Male_Silhouette.blend')
print('verts',len(A),len(B),'polys',pa,pb)
if len(A)==len(B):
    d=np.abs(A-B).max(1); mv=d>0
    print('moved verts vs micro1f final:',mv.sum(), 'maxdelta mm', d.max()*1000)
    idx=np.nonzero(mv)[0]
    if len(idx): print('moved z range',A[idx,2].min(),A[idx,2].max(),'x range',A[idx,0].min(),A[idx,0].max())
