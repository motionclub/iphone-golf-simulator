import bpy,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
dg=bpy.context.evaluated_depsgraph_get()
YD=0.9144;K=1.0936
sc=bpy.context.scene
V=[];F=[];owner=[]
for o in sc.objects:
    if o.type!='MESH' or o.hide_viewport or o.hide_render: continue
    if o.name.startswith(('WATER','LAVA')): continue
    mw=o.matrix_world;b=len(V);V+=[tuple(mw@v.co) for v in o.data.vertices]
    o.data.calc_loop_triangles()
    for t in o.data.loop_triangles: F.append(tuple(b+i for i in t.vertices));owner.append(o.name)
bv=BVHTree.FromPolygons(V,F)
def g(x,y):
    h=bv.ray_cast(Vector((x,y,200)),Vector((0,0,-1)),400); return (h[0].z,owner[h[2]]) if h[0] else None
for nm,(cx,cd) in {'tee':(0,0),'approach':(107.1,159.3)}.items():
    x,y=cx*YD,cd*YD; print(nm,"ball m",round(x,2),round(y,2),"surface",g(x,y))
pin=bpy.data.objects['MARKER_PIN'].matrix_world.translation; print("pin m",tuple(pin),"yd",pin.x/YD,pin.y/YD)
# aim for tee and camera
def cam(ball,aim):
    bx,by=ball[0]*YD,ball[1]*YD; a=Vector((aim[0],aim[1])).normalized()
    z=g(bx,by)[0]
    pos=Vector((bx-a.x*4.5*YD,by-a.y*4.5*YD,z+2.4*YD)); look=Vector((bx+a.x*1.5*YD,by+a.y*1.5*YD,z))
    return pos,look
for nm,ball,aim in (('tee',(0,0),(14.3,66.2)),('approach',(107.1,159.3),(261,164.7))):
    p,l=cam(ball,aim); d=(l-p); h=bv.ray_cast(p,d.normalized(),d.length)
    print(nm,"cam",tuple(round(c,2) for c in p),"ground under cam",g(p.x,p.y),"ray to ball blocked",h[0] is not None)
# lava rim cam
p=Vector((100*YD,134*YD,8.8/K)); l=Vector((180*YD,160*YD,1.5/K)); d=l-p
print("rim cam m",tuple(round(c,2) for c in p),"under",g(p.x,p.y),"to look blocked:",bv.ray_cast(p,d.normalized(),d.length)[0] is not None)
# min distance from lens to any geometry
import mathutils
for nm,pp in (('rimcam',p),):
    loc=bv.find_nearest(pp); print(nm,"nearest geom",round(loc[3],2),owner[loc[2]])
# rays through frustum for rimcam: fraction of rays blocked within 5m
import numpy as np
fw=(l-p).normalized(); up=Vector((0,0,1)); rt=fw.cross(up).normalized(); upv=rt.cross(fw)
bl=0;n=0
for i in range(-8,9):
    for j in range(-12,13):
        ax=math.tan(math.radians(30))*i/8;ay=math.tan(math.radians(30))*(900/1600)*j/12
        # portrait: vertical fov 60 => vertical half tan30; horizontal = tan30*9/16
        dd=(fw+rt*(math.tan(math.radians(30))*(9/16)*i/8)+upv*(math.tan(math.radians(30))*j/12)).normalized()
        h=bv.ray_cast(p,dd,6.0); n+=1; bl+= h[0] is not None
print("rim cam rays blocked within 6 m:",bl,"/",n)
import collections
c=collections.Counter()
for i in range(-8,9):
    for j in range(-12,13):
        dd=(fw+rt*(math.tan(math.radians(30))*(9/16)*i/8)+upv*(math.tan(math.radians(30))*j/12)).normalized()
        h=bv.ray_cast(p,dd,6.0)
        if h[0] is not None: c[owner[h[2]].split('.')[0]]+=1
print("rimcam blockers",dict(c))
p2,l2=cam((107.1,159.3),(261,164.7)); d=l2-p2; h=bv.ray_cast(p2,d.normalized(),d.length+1)
print("approach hit",owner[h[2]] if h[0] else None,h[3] if h[0] else None,"len",d.length)
