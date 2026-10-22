import bpy, sys, math, collections, numpy as np
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import hole08_design as D, postcard_check as PC
from mathutils import Vector
from mathutils.bvhtree import BVHTree
H=PC.Hole(D); YD=0.9144
def wv(o):
    M=np.array(o.matrix_world); V=np.array([v.co[:] for v in o.data.vertices]).reshape(-1,3); return (np.c_[V,np.ones(len(V))]@M.T)[:,:3]
solid=[o for o in bpy.data.objects if o.type=='MESH' and (o.name.startswith(('TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER','ROCK_','DRESS_BLOCK','DRESS_ARCH')))]
vs=[];fs=[];owner=[]
off=0
for o in solid:
    V=wv(o); vs+=V.tolist()
    for p in o.data.polygons:
        fs.append([i+off for i in p.vertices]); owner.append(o.name)
    off+=len(V)
bvh=BVHTree.FromPolygons(vs,fs)
templ=[o for o in bpy.data.objects if o.name in('PLANT_FLOWER_PURPLE','PLANT_TUFT_A')]
for o in templ: print('template',o.name,o.hide_viewport,o.hide_render,o.visible_get(),[c.name for c in o.users_collection],tuple(o.matrix_world.translation), o.parent and o.parent.name)
pl=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('PLANT_')]
tc=collections.Counter(); samples=[]
vine_low=[]; 
for o in pl:
    org=o.matrix_world.translation
    if abs(org.x)<1e-6 and abs(org.y)<1e-6: continue
    V=wv(o)
    vine=o.name.startswith('PLANT_VINE')
    lie=H.lie_at((org.x/YD,org.y/YD))
    # ray down from slightly above origin
    r=bvh.ray_cast(Vector((org.x,org.y,org.z+0.3)),Vector((0,0,-1)),3.0)
    hn=owner[r[2]] if r[0] is not None else None
    key=(('vine' if vine else 'plant'),lie,hn.split('_0')[0] if hn else None)
    tc[key]+=1
    if vine: vine_low.append((V[:,2].min(), o.name))
for k,v in sorted(tc.items(),key=lambda x:str(x)): print(k,v)
vine_low.sort(); print('lowest vine verts',vine_low[:5])
# plant footprint lowest vertex over all plants
allmin=min(wv(o)[:,2].min() for o in pl if abs(o.matrix_world.translation.x)>1e-6)
print('lowest plant vertex overall',allmin)
