import bpy, sys, math, json, collections, numpy as np, bmesh
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import hole08_design as D, postcard_check as PC
from mathutils import Vector
from mathutils.bvhtree import BVHTree
H=PC.Hole(D); YD=0.9144
dg=bpy.context.evaluated_depsgraph_get()
def world_verts(o):
    me=o.data; M=np.array(o.matrix_world)
    V=np.array([v.co[:] for v in me.vertices]).reshape(-1,3)
    return (np.c_[V,np.ones(len(V))]@M.T)[:,:3]
def bvh_of(objs):
    vs=[];fs=[];off=0
    for o in objs:
        V=world_verts(o); vs+=V.tolist(); fs+=[[i+off for i in p.vertices] for p in o.data.polygons]; off+=len(V)
    return BVHTree.FromPolygons(vs,fs)
GN=('TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER')
ground=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(GN)]
gb=bvh_of(ground)
res={}
# ---------- rocks
welded_stats=[];scale_stats=[]
rocks=[o for o in bpy.data.objects if o.type=='MESH' and (o.name.startswith('ROCK_') or o.name.startswith('DRESS_BLOCK') or o.name.startswith('DRESS_ARCH'))]
by_mesh=collections.defaultdict(list)
for o in rocks: by_mesh[o.data.name].append(o)
print('ROCK MESHES')
for mn,os_ in sorted(by_mesh.items()):
    me=os_[0].data
    co=np.array([v.co[:] for v in me.vertices]).reshape(-1,3)
    wv=len({tuple(np.round(c,4)) for c in co})
    sc=[]
    for o in os_:
        M=np.array(o.matrix_world)[:3,:3]
        sv=np.linalg.svd(M,compute_uv=False); sc.append((sv.min(),sv.max(),sv.max()/sv.min()))
    sc=np.array(sc)
    print(f"{mn:28s} users {len(os_):3d} verts {len(me.vertices):5d} welded {wv:5d} faces {len(me.polygons):5d} scale min {sc[:,0].min():.3f} max {sc[:,1].max():.3f} ratio max {sc[:,2].max():.3f} objs e.g. {os_[0].name} mats {[m.name for m in me.materials if m]}")
# check names
names=[o.name for o in rocks]
# per-object scale components (local axes lengths)
bad=[]
for o in rocks:
    M=np.array(o.matrix_world)[:3,:3]
    ax=np.linalg.norm(M,axis=0)
    if ax.min()<0.5-1e-3 or ax.max()>2.0+1e-3 or ax.max()/ax.min()>2.0+1e-3: bad.append((o.name,ax.round(3).tolist()))
print('ROCK scale violations (axis norms)',len(bad),bad[:20])
# ---------- plants
pl=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('PLANT_')]
print('plants',len(pl))
cnt=collections.Counter();hitcnt=collections.Counter()
onwater=[];onplay=[];lowz=[]
pin=Vector((H.pin[0]*YD,H.pin[1]*YD,6)); tee=Vector((0,0,6))
allpts=[]
for o in pl:
    V=world_verts(o); base=V[:,2].min(); org=np.array(o.matrix_world.translation)
    x,y=org[0]/YD,org[1]/YD
    lie=H.lie_at((x,y)); cnt[(o.name.rsplit('.',1)[0][:18],lie)]+=1
    vine=o.name.startswith('PLANT_VINE')
    # ray down from above the origin
    hit=gb.ray_cast(Vector((org[0],org[1],50)),Vector((0,0,-1)))
    onp = lie in ('Fairway','Green','Tee','Bunker')
    if not vine:
        if H.in_ellipse(('',) and ('water',)+(0,0,0,0,''), (0,0)) : pass
    if not vine and lie in (PC.WATER,):
        onwater.append((o.name,round(x,1),round(y,1),round(base,2),round(float(org[2]),2)))
    if not vine and base<4.0: lowz.append((o.name,round(base,2),lie))
    if not vine and (lie in (PC.FAIRWAY,PC.GREEN,PC.TEE,PC.BUNKER)):
        onplay.append((o.name,lie,round(x,1),round(y,1)))
print('lie constants',PC.WATER,PC.FAIRWAY,PC.GREEN,PC.TEE,PC.BUNKER,PC.ROUGH)
print('plant lie counts',dict(cnt))
print('non-vine plants on WATER lie',len(onwater),onwater[:15])
print('non-vine plants low base (<4m)',len(lowz),lowz[:10])
print('non-vine plants on play lie',len(onplay),collections.Counter(l for _,l,_,_ in onplay),onplay[:10])
