import bpy, sys, numpy as np
D=np.load('data/cand_G1.npz'); o=bpy.data.objects['Body_M']; me=o.data
cv=np.zeros(len(me.loops),np.int32); me.loops.foreach_get('vertex_index',cv)
ls=np.zeros(len(me.polygons),np.int32); me.polygons.foreach_get('loop_start',ls)
lt=np.zeros(len(me.polygons),np.int32); me.polygons.foreach_get('loop_total',lt)
polys=[tuple(cv[s:s+t]) for s,t in zip(ls,lt)]
cp=[tuple(D['corner_verts'][s:s+t]) for s,t in zip(D['loop_start'],D['loop_total'])]
def canon(p):
    p=list(p); k=p.index(min(p)); return tuple(p[k:]+p[:k])
print('counts',len(polys),len(cp))
bad=[i for i,(a,b) in enumerate(zip(polys,cp)) if canon(a)!=canon(b)]
print('mismatching polys',len(bad),'first',bad[:5],'last',bad[-3:])
nk=len(cp)-1352
for i in bad[:6]: print(i,polys[i],cp[i], 'reversed-equal' if canon(tuple(reversed(polys[i])))==canon(cp[i]) else '')
# sets equal?
from collections import Counter
sa=Counter(canon(p) for p in polys); sb=Counter(canon(p) for p in cp)
print('same multiset (cyclic):', sa==sb)
sa2=Counter(canon(tuple(sorted(p))) for p in polys); sb2=Counter(canon(tuple(sorted(p))) for p in cp); print('same multiset ignoring order/orientation:', sa2==sb2)
