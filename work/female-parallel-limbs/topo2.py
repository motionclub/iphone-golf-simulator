import bpy, bmesh, numpy as np
b=bpy.data.objects['Body_F']; me=b.data
v=np.array([tuple(x.co) for x in me.vertices])
# right arm: x>0.2 and z<1.1 and not leg(z<0.78?) arms region
m=(v[:,0]>0.2)&(v[:,2]>0.7)&(v[:,2]<1.15)
idx=np.where(m)[0]
zs=np.round(v[idx,2],3)
import collections
h=collections.Counter(np.round(v[idx,2]/0.01).astype(int))
for k in sorted(h): print('z',k/100,h[k], end=' | ')
print()
# ring structure via edge loops: use bmesh to find vertex valence & rings by z bands
bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
# boundary edges (non-manifold)
nm=[e for e in bm.edges if len(e.link_faces)!=2]
print('non-manifold edges',len(nm))
# feet ring: skin/grey boundary: edges whose two faces differ in material
bd=[e for e in bm.edges if len(e.link_faces)==2 and e.link_faces[0].material_index!=e.link_faces[1].material_index and {e.link_faces[0].material_index,e.link_faces[1].material_index}=={0,1}]
print('grey/skin boundary edges',len(bd))
bz=sorted(set(round(e.verts[0].co.z,3) for e in bd))
print(bz[:10],bz[-10:])
low=[e for e in bd if e.verts[0].co.z<0.3]
print('ankle boundary edges',len(low), 'x>0:',len([e for e in low if e.verts[0].co.x>0]))
for e in low[:6]: print(tuple(e.verts[0].co),tuple(e.verts[1].co))
# hand: verts with x>0.25: print ring z/count
hv=[x for x in bm.verts if x.co.x>0.22 and 0.6<x.co.z<1.0]
print(len(hv))
