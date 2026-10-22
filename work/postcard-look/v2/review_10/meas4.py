import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
YD=0.9144
dg=bpy.context.evaluated_depsgraph_get()
sc=bpy.context.scene
def cast(o,d,dist=2000):
    r=sc.ray_cast(dg,o,d,distance=dist); return r
for name,(x,y) in {'tee':(0,0),'approach':(107.1,159.3)}.items():
    p=Vector((x*YD,y*YD,60)); r=cast(p,Vector((0,0,-1)))
    print("LIE",name,r[0],r[4].name if r[4] else None,round(r[1].z,3) if r[0] else None)
# landmark camera
cam=Vector((100*YD,134*YD,8.8/1.0936)); print("cam m",cam)
r=cast(cam+Vector((0,0,60)),Vector((0,0,-1))); print("below cam hit",r[4].name,r[1].z,"cam above ground by",cam.z-r[1].z)
look=Vector((180*YD,160*YD,1.5/1.0936))
d=(look-cam); r=cast(cam,d.normalized(),d.length); print("ray cam->look first hit",r[0],r[4].name if r[4] else None, (r[1]-cam).length if r[0] else None, "of",d.length)
# nearby rocks within 6 m ahead, rays across the frustum
hits=[]
import math
fwd=d.normalized(); up=Vector((0,0,1)); right=fwd.cross(up).normalized(); upv=right.cross(fwd).normalized()
for hx in np.linspace(-0.4,0.4,9):
  for vy in np.linspace(-0.5,0.5,9):
    dirv=(fwd+right*hx*0.9+upv*vy*0.6).normalized()
    r=cast(cam,dirv,60)
    if r[0]: hits.append((round((r[1]-cam).length,1),r[4].name))
print("near hits<15m",sorted(hits)[:8])
