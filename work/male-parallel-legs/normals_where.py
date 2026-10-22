import sys, numpy as np, bpy
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-legs')
from leglib import ZONE
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--')+1])
b=bpy.data.objects['Body_M']; me=b.data; n=len(me.vertices)
a=me.attributes['custom_normal']; print('custom_normal attr',a.data_type,a.domain)
cn=np.empty(len(me.corner_normals)*3); me.corner_normals.foreach_get('vector',cn); cn=cn.reshape(-1,3)
cv=np.empty(len(me.loops),np.int32); me.loops.foreach_get('vertex_index',cv)
V=np.empty(n*3); me.vertices.foreach_get('co',V); V=V.reshape(-1,3)
vn=np.zeros((n,3))
for p in me.polygons:
    for v in p.vertices: vn[v]+=np.array(p.normal)*p.area
vn/=np.maximum(np.linalg.norm(vn,axis=1,keepdims=True),1e-12)
ang=np.degrees(np.arccos(np.clip((cn*vn[cv]).sum(1),-1,1)))
zl=ZONE[cv]
big=zl&(ang>2.0)
print('zone loops with >2deg deviation:',big.sum(),'of',zl.sum())
P=V[cv[big]]
print('x range %.3f..%.3f  z range %.3f..%.3f'%(P[:,0].min(),P[:,0].max(),P[:,2].min(),P[:,2].max()))
# histogram by |x| and z
import collections
print('by |x| (cm):',np.histogram(np.abs(P[:,0])*100,bins=[0,5,10,15,20,22,24,27])[0])
print('by z (0.1):',np.histogram(P[:,2],bins=np.arange(0,0.8,0.1))[0])
# attribute raw
raw=np.empty(len(me.loops)*2); a.data.foreach_get('value',raw) if hasattr(a.data[0],'value') else None
print('raw sample',raw[:10] if raw.size else None)
