import bpy, numpy as np
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/'
def coords(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    b=bpy.data.objects['Body_M']; n=len(b.data.vertices)
    a=np.zeros(n*3,dtype=np.float64); b.data.vertices.foreach_get('co',a); return a.reshape(-1,3)
A=coords(R+'male-parallel-arms/baseline/HeroBase_Male_Silhouette.blend'); B=coords(R+'male-micro1f/final/HeroBase_Male_Silhouette.blend')
for zlo in (0.0,):
  ma=(A[:,2]<1.40); mb=(B[:,2]<1.40)
  a=A[ma]; b=B[mb]
  print('below z1.40 counts',len(a),len(b))
  if len(a)==len(b):
    ia=np.lexsort((a[:,2],a[:,1],a[:,0])); ib=np.lexsort((b[:,2],b[:,1],b[:,0]))
    d=np.abs(a[ia]-b[ib]).max(1); print('max diff mm',d.max()*1000,'n moved',(d>1e-9).sum())
