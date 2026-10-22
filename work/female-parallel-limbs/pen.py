"""blender -b file --python pen.py : penetration of hand vertices into the rest of the body (signed distance via BVH)."""
import bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
me=bpy.data.objects['Body_F'].data
bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
mat={m.name:i for i,m in enumerate(me.materials)}
hand_faces=[f for f in bm.faces if f.material_index==mat['Base_Grey_F'] and min(abs(v.co.x) for v in f.verts)>0.195 and all(0.60<v.co.z<0.846 for v in f.verts)]
hf=set(hand_faces)
rest=[f for f in bm.faces if f not in hf]
bmr=bmesh.new()
# build BVH from the rest of the body by copying faces
vm={}
for f in rest:
    for v in f.verts:
        if v not in vm: vm[v]=bmr.verts.new(v.co)
for f in rest:
    try: bmr.faces.new([vm[v] for v in f.verts])
    except ValueError: pass
bmr.normal_update()
bvh=BVHTree.FromBMesh(bmr)
hv=sorted({v for f in hand_faces for v in f.verts},key=lambda v:v.index)
inside=0;rows=[]
for v in hv:
    sd=1 if v.co.x>0 else -1
    d=Vector((sd,0,0))
    loc,nrm,idx,dist=bvh.ray_cast(v.co+d*1e-5,d,0.3)
    if loc is not None and nrm.dot(d)>0:      # first surface met going outward is a back face -> the vertex is inside the body
        inside+=1; rows.append((dist,tuple(np.round(v.co[:],3))))
rows.sort(reverse=True)
print('hand verts',len(hv),'inside rest-of-body',inside,'max depth along x mm',round(rows[0][0]*1000,2) if rows else 0)
print(rows[:5])
