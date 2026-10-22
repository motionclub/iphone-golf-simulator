import bpy,bmesh,math,numpy as np,collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree
objs=bpy.data.objects
def weld(me,tol=1e-4):
    v=np.array([x.co[:] for x in me.vertices]); 
    k=set(map(tuple,np.round(v/tol).astype(np.int64)));return len(k)
rocks=[o for o in objs if o.type=='MESH' and (o.name.startswith('ROCK_') or o.name.startswith('CLIFF_ROCK'))]
meshes={}
for o in rocks: meshes.setdefault(o.data.name,o.data)
w={n:(weld(m),len(m.polygons)) for n,m in meshes.items()}
print("ROCKS",len(rocks),"unique",len(meshes),"minweld",min(v[0] for v in w.values()),"min faces",min(v[1] for v in w.values()))
small=[(n,v) for n,v in w.items() if v[0]<60]; print("small",small[:10])
# skin pieces
sk=[o for o in rocks if o.name.startswith('ROCK_SKIN')]; print("skin",len(sk),"min weld",min(weld(o.data) for o in sk) if sk else None)
# scales
bad=[];mx=0;mn=9;an=0
for o in objs:
    if o.type!='MESH' or not o.name.startswith(('ROCK_','PLANT_','DRESS_')):continue
    s=o.matrix_world.to_3x3().singular_value_decomposition() if False else None
    m=np.array(o.matrix_world.to_3x3()); sv=np.linalg.svd(m,compute_uv=False)
    mx=max(mx,sv.max());mn=min(mn,sv.min());an=max(an,sv.max()/sv.min())
    if o.name.startswith(('ROCK_','PLANT_')) and (sv.max()>2.0001 or sv.min()<0.4999 or sv.max()/sv.min()>2.0001): bad.append((o.name,sv.tolist()))
print("SCALE max",mx,"min",mn,"aniso",an,"bad",bad[:5],len(bad))
# non-uniform scale of rocks via matrix_world including parent
# plants
ground=[o for o in objs if o.type=='MESH' and o.name.startswith(('TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER'))]
V=[];F=[]
for o in ground:
    b=len(V);V+=[tuple(o.matrix_world@v.co) for v in o.data.vertices]
    F+=[tuple(b+i for i in p.vertices) for p in o.data.polygons]
bv=BVHTree.FromPolygons(V,F)
lava=objs['WATER_LAVA']; 
lv=np.array([ (lava.matrix_world@v.co)[:] for v in lava.data.vertices]); print("lava z",lv[:,2].min(),lv[:,2].max(),"bbox",lv.min(0),lv.max(0))
plants=[o for o in objs if o.name.startswith('PLANT_')]
onl=0;off=[];zs=[]
for o in plants:
    p=o.matrix_world.translation
    h=bv.ray_cast(Vector((p.x,p.y,80)),Vector((0,0,-1)),200)
    if h[0] is None: off.append((o.name,tuple(p)));continue
    zs.append(h[0].z)
    d=abs(p.z-h[0].z)
    if d>0.3: off.append((o.name,'float/sink',round(d,3)))
print("PLANTS",len(plants),"nohit_or_off",len(off),off[:5],"min ground z",min(zs))
# nearest plant to pin
pin=objs['MARKER_PIN'].matrix_world.translation
print("plant->pin min",min((o.matrix_world.translation.xy-pin.xy).length for o in plants))
# foam
print("foam-like",[o.name for o in objs if any(k in o.name.upper() for k in ('FOAM','SURF','SPRAY','SHELF'))])
print("mats",sorted({s.material.name for o in objs if o.type=='MESH' for s in o.material_slots if s.material}))
print("tris", sum(len(p.vertices)-2 for o in objs if o.type=='MESH' for p in o.data.polygons))
# prefix list
print(collections.Counter(o.name.split('_')[0] for o in objs))
