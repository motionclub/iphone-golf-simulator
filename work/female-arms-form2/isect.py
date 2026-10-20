import bpy, bmesh, numpy as np, sys
from mathutils.bvhtree import BVHTree
me=bpy.data.objects['Body_F'].data; bm=bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bvh=BVHTree.FromBMesh(bm); ov=bvh.overlap(bvh)
fv=[set(v.index for v in f.verts) for f in bm.faces]
bad=[(i,j) for i,j in ov if i<j and not (fv[i]&fv[j])]
fs=sorted(set(i for p in bad for i in p)); c=np.array([bm.faces[i].calc_center_median()[:] for i in fs])
print('pairs',len(bad),'faces',len(fs))
import collections
cnt=collections.Counter()
for p in c:
    reg='hand' if p[2]<0.9 and abs(p[0])>0.15 else ('arm' if abs(p[0])>0.12 and 0.9<=p[2]<1.37 else ('head' if p[2]>1.4 else ('torso' if p[2]>0.78 else 'legs')))
    cnt[reg]+=1
print(cnt)
arm=[p for p in c if abs(p[0])>0.12 and 0.9<=p[2]<1.37]; print(np.round(arm[:10],3))
