import bpy, math, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
YD=0.9144
V,F,own,names=[],[],[],[]
for ob in bpy.data.objects:
    if ob.type!='MESH' or "ASSET_LIBRARY" in [c.name for c in ob.users_collection] or ob.name not in bpy.context.scene.objects: continue
    if ob.name.startswith(("DRESS_SMOKE","LAVA_LIGHT","FLAG","HOLE_CUP","BALL_START","MARKER_","TEE_MARKER","PLANT_","WATER_")): continue
    mw=ob.matrix_world; b=len(V); V+=[tuple(mw@v.co) for v in ob.data.vertices]
    for p in ob.data.polygons: F.append(tuple(b+i for i in p.vertices)); own.append(len(names))
    names.append(ob.name)
T=BVHTree.FromPolygons(V,F)
pos=Vector((70*YD,108*YD,14/1.0936)); look=Vector((140*YD,150*YD,1/1.0936))
fwd=(look-pos).normalized(); right=fwd.cross(Vector((0,0,1))).normalized(); up=right.cross(fwd).normalized()
ty=math.tan(math.radians(55)/2); tx=ty*900/1600
pts=[]
for y in range(0,1600,40):
    for x in range(0,900,30):
        u=(x+.5)/900*2-1; v=1-(y+.5)/1600*2
        d=(fwd+right*(u*tx)+up*(v*ty)).normalized()
        h=T.ray_cast(pos,d,3000.0)
        if h[0] is not None and names[own[h[2]]].startswith(("TERRAIN","FAIRWAY","GREEN","TEE_BOX","BUNKER")):
            pts.append((round(h[0].x,1),round(h[0].y,1),round(h[0].z,2),names[own[h[2]]],x,y))
print("HITS",len(pts))
for p in pts[::6]: print("H",p)
