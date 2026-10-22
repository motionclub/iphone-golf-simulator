import bpy,numpy as np,collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sc=bpy.context.scene
vis=lambda o: not (o.hide_viewport or o.hide_render)
ground=[o for o in sc.objects if o.type=='MESH' and o.name.startswith(('TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER'))]
bv={}
for o in ground:
    V=[tuple(o.matrix_world@v.co) for v in o.data.vertices]; F=[tuple(p.vertices) for p in o.data.polygons]
    bv[o.name]=BVHTree.FromPolygons(V,F)
plants=[o for o in sc.objects if o.name.startswith('PLANT_') and vis(o)]
print("visible plants",len(plants))
cnt=collections.Counter(); bad=[]
for o in plants:
    p=o.matrix_world.translation
    hits=[]
    for n,b in bv.items():
        h=b.ray_cast(Vector((p.x,p.y,80)),Vector((0,0,-1)),200)
        if h[0] is not None: hits.append((h[0].z,n))
    if not hits: bad.append((o.name,'nohit'));continue
    hits.sort(reverse=True)
    top=hits[0]; cnt[top[1].split('_')[0]]+=1
    if abs(p.z-top[0])>0.05: bad.append((o.name,'z',round(p.z-top[0],3)))
print("plant top surface",dict(cnt),"bad",bad[:5],len(bad))
# the plant surface being FAIRWAY/GREEN/TEE/BUNKER = on play
# distance to shore: lava edge = distance in xy to nearest point where ground ray misses. approximate with sampling ring
objs=bpy.data.objects
for n in ('MARKER_PIN','MARKER_TEE','BALL_START','TEE_MARKER_1','TEE_MARKER_2'):
    if n in objs:
        q=objs[n].matrix_world.translation
        d=min((o.matrix_world.translation.xy-q.xy).length for o in plants)
        print(n,"nearest plant",round(d,2))
# per-plant clearance to edge: cast 16 rays from plant outwards to find nearest nonground
ground_all=BVHTree.FromObject  # unused
allV=[];allF=[]
for o in ground:
    b=len(allV);allV+=[tuple(o.matrix_world@v.co) for v in o.data.vertices];allF+=[tuple(b+p.vertices[i] for i in range(len(p.vertices))) for p in o.data.polygons if len(p.vertices)==3]
    for p in o.data.polygons:
        if len(p.vertices)==4: allF.append(tuple(b+i for i in (p.vertices[0],p.vertices[2],p.vertices[3])))
G=BVHTree.FromPolygons(allV,allF)
mn=9e9;worst=None
ang=np.linspace(0,2*np.pi,48,endpoint=False)
for o in plants:
    p=o.matrix_world.translation
    best=9e9
    for r in np.arange(0.25,3.01,0.25):
        for a in ang:
            x=p.x+r*np.cos(a);y=p.y+r*np.sin(a)
            h=G.ray_cast(Vector((x,y,80)),Vector((0,0,-1)),200)
            if h[0] is None: best=min(best,r);break
        if best<9e8:break
    if best<mn: mn=best;worst=(o.name,tuple(round(c,1) for c in p))
print("min edge clearance (<=3m search)",mn,worst)
