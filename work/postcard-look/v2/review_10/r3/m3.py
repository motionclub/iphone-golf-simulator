import bpy, json, collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree
obs=[o for o in bpy.data.objects if o.type=='MESH' and o.visible_get()]
def bvh_of(L):
    v=[];f=[]
    for o in L:
        off=len(v); mw=o.matrix_world
        v+=[mw@x.co for x in o.data.vertices]; f+=[[off+i for i in p.vertices] for p in o.data.polygons]
    return BVHTree.FromPolygons(v,f)
ground=[o for o in obs if o.name.split('_')[0] in ('TERRAIN','FAIRWAY','GREEN','TEE','BUNKER')]
gb=bvh_of(ground)
pl=[o for o in obs if o.name.startswith('PLANT_')]
bad=[];hz=[]
for o in pl:
    p=o.matrix_world.translation
    h=gb.ray_cast(Vector((p.x,p.y,p.z+3)),Vector((0,0,-1)),10)
    if h[0] is None: bad.append(o.name); continue
    hz.append(abs(h[0].z-p.z))
    # which object
    # find nearest face parent name
print("visible plants",len(pl),"without ground",bad[:5],len(bad),"max height err",max(hz))
# which ground object under each plant
names=collections.Counter()
for o in pl:
    p=o.matrix_world.translation
    best=None
    for g in ground:
        gg=bvh_of([g]) if False else None
    break
# per object bvhs
per={g.name:bvh_of([g]) for g in ground}
for o in pl:
    p=o.matrix_world.translation; bd=None;bn=None
    for n,b in per.items():
        h=b.ray_cast(Vector((p.x,p.y,p.z+3)),Vector((0,0,-1)),10)
        if h[0] is not None and (bd is None or h[0].z>bd): bd=h[0].z;bn=n
    names[bn]+=1
print(names)
# plants within 1.5 m of play surfaces' non-terrain, i.e. on FAIRWAY/GREEN/TEE/BUNKER
# landmark / ball
M=0.9144
for nm,(x,z) in {"tee":(0,0),"approach":(107.1,159.3)}.items():
    p=Vector((x*M,z*M,50))
    res=[(n,b.ray_cast(p,Vector((0,0,-1)),100)[0]) for n,b in per.items()]
    print(nm,[(n,round(h.z,2)) for n,h in res if h is not None])
# landmark cam: Unity (x, y, z)-> blender (x*M, z*M, y/1.0936)
cam=Vector((70*M,108*M,14/1.0936)); look=Vector((140*M,150*M,1/1.0936))
allb=bvh_of([o for o in obs if o.name.split('_')[0] in ('ROCK','TERRAIN','FAIRWAY','GREEN','TEE','BUNKER','PLANT','DRESS')])
d=(look-cam).normalized()
h=allb.ray_cast(cam,d,500)
print("center ray hit dist",(h[1] if h[0] is None else (h[0]-cam).length),"target dist",(look-cam).length, h[0])
near=min(((o.matrix_world.translation-cam).length) for o in obs if o.name.startswith('ROCK_'))
print("nearest rock origin",near)
# fov frame sample ray fractions
import math
from mathutils import Matrix
f=d; up=Vector((0,0,1)); r=f.cross(up).normalized(); u=r.cross(f).normalized()
t=math.tan(math.radians(55/2)); asp=900/1600
hit=collections.Counter()
lava=bvh_of([o for o in obs if o.name.startswith('WATER_LAVA')])
for i in range(-10,11):
  for j in range(-10,11):
    dd=(f+r*(i/10*t*asp)+u*(j/10*t)).normalized()
    hh=allb.ray_cast(cam,dd,600); hl=lava.ray_cast(cam,dd,600)
    if hh[0] is None and hl[0] is None: hit['sky']+=1
    elif hl[0] is not None and (hh[0] is None or hl[3]*0+((hl[0]-cam).length)<(hh[0]-cam).length): hit['lava']+=1
    else: hit['solid:'+hh[3].__class__.__name__ if False else 'solid']+=1
print(hit)
