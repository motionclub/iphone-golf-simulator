import bpy, bmesh, math, collections, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
dg=bpy.context.evaluated_depsgraph_get()
obs=[o for o in bpy.data.objects if o.type=='MESH']
print("objects",len(obs))
# tris
tri=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in obs); print("tris",tri)
# prefixes
pre=collections.Counter(o.name.split('_')[0] for o in obs); print(pre)
bad=[o.name for o in obs if o.name.split('_')[0] not in ('TERRAIN','FAIRWAY','GREEN','TEE','BUNKER','ROCK','PLANT','DRESS','WATER','LAVA','MARKER','BALL','HOLE','FLAG','CART')]
print("odd prefixes",bad)
# rocks: welded vertex counts
def weld(o):
    v=np.array([tuple(np.round(x.co,4)) for x in o.data.vertices]); return len(set(map(tuple,v)))
mn=1e9; small=[]
for o in obs:
    if o.name.startswith('ROCK_'):
        w=weld(o); mn=min(mn,w)
        if w<60: small.append((o.name,w))
print("rock min welded",mn,"small",small[:10], len(small))
# scales
mx=0;worst=None;lo=9;hi=0
for o in obs:
    if o.name.split('_')[0] in ('ROCK','PLANT','DRESS'):
        m=o.matrix_world.to_3x3(); u,s,vt=np.linalg.svd(np.array(m))
        r=s.max()/s.min(); 
        if r>mx: mx=r;worst=o.name
        lo=min(lo,s.min()); hi=max(hi,s.max())
print("scale ratio max",mx,worst,"range",lo,hi)
# material names
mats=collections.Counter(s.material.name for o in obs for s in o.material_slots if s.material); print(mats)
print([o.name for o in obs if any(k in o.name.upper() for k in ('FOAM','SURF','SPRAY','SHELF'))])
# plants vs water: raycast down on ground ; water = WATER_LAVA; plants base z
ground=[o for o in obs if o.name.split('_')[0] in ('TERRAIN','FAIRWAY','GREEN','TEE','BUNKER')]
bm=bmesh.new()
for o in ground:
    bm.from_mesh(o.data); 
# build BVH in world per object
verts=[];faces=[]
for o in ground:
    off=len(verts); mw=o.matrix_world
    verts+= [mw@v.co for v in o.data.vertices]
    for p in o.data.polygons: faces.append([off+i for i in p.vertices])
bvh=BVHTree.FromPolygons(verts,faces)
lava=[o for o in obs if o.name.startswith('WATER_LAVA')][0]
lz=max((lava.matrix_world@v.co).z for v in lava.data.vertices); print("lava z",lz)
pl=[o for o in obs if o.name.startswith('PLANT_')]
off=0; miss=[]; low=[]
for o in pl:
    p=o.matrix_world.translation
    h=bvh.ray_cast(Vector((p.x,p.y,p.z+3)),Vector((0,0,-1)),10)
    if h[0] is None: miss.append(o.name)
    elif abs(h[0].z-p.z)>0.1: low.append((o.name,round(h[0].z-p.z,3)))
print("plants",len(pl),"no ground under",len(miss),miss[:5],"off-height",low[:5])
pin=bpy.data.objects['MARKER_PIN'].matrix_world.translation; tee=bpy.data.objects['MARKER_TEE'].matrix_world.translation
print("min plant-pin",min((o.matrix_world.translation-pin).xy.length for o in pl),"tee",min((o.matrix_world.translation-tee).xy.length for o in pl))
