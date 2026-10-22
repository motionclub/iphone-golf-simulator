import bpy, numpy as np, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
YD=0.9144
def bvh(objs):
    vs=[];ps=[];off=0
    for o in objs:
        me=o.data; mw=o.matrix_world
        vs+=[mw@v.co for v in me.vertices]; ps+=[[i+off for i in p.vertices] for p in me.polygons]; off+=len(me.vertices)
    return BVHTree.FromPolygons(vs,ps)
ruin=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('DRESS_RUIN','DRESS_ARCH'))]
other=[o for o in bpy.data.objects if o.type=='MESH' and not o.hide_viewport and not o.name.startswith(('DRESS_RUIN','DRESS_ARCH','WATER')) and o.name not in('BALL_START','HOLE_CUP')]
B=bvh(other)
cam=Vector((-64.06*YD,149.86*YD,26*YD)); look=Vector((-64.06*YD,119.86*YD,10.1*YD))
fwd=(look-cam).normalized(); up=Vector((0,0,1)); right=fwd.cross(up).normalized(); upv=right.cross(fwd).normalized()
fov=math.radians(50); asp=900/1600
pts=[]
for o in ruin:
    for k,v in enumerate(o.data.vertices):
        if k%3==0: pts.append(o.matrix_world@v.co)
vis=0;inf=0;blocked=0;zs=[]
for p in pts:
    d=p-cam; z=d.dot(fwd)
    if z<=0: continue
    ty=d.dot(upv)/z/math.tan(fov/2); tx=d.dot(right)/z/(math.tan(fov/2)*asp)
    if abs(tx)<=1 and abs(ty)<=1:
        inf+=1
        h=B.ray_cast(cam,d.normalized(),d.length-0.05)
        if h[0] is None: vis+=1
        else:
            blocked+=1; zs.append(round(p.z,2))
print('ruin sample pts',len(pts),'in frame',inf,'unblocked',vis,'blocked',blocked)
# camera inside anything? cast up/down
h=B.ray_cast(cam,Vector((0,0,-1)),200); print('ground below cam z',h[0].z if h[0] else None,'cam z',cam.z)
# where in frame is the ruin bbox
allp=np.array([[*(o.matrix_world@v.co)] for o in ruin for v in o.data.vertices])
print('ruin bbox',allp.min(0).round(1),allp.max(0).round(1))

print('blocked z',sorted(zs))
