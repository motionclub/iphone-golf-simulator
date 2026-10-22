import bpy,sys,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
mode=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
if mode=='blend': bpy.ops.wm.open_mainfile(filepath=R+'blender/hole_08.blend')
else: bpy.ops.import_scene.fbx(filepath=R+'Unity/Assets/Resources/Course/hole_08.fbx')
ms=[o for o in bpy.data.objects if o.type=='MESH']
nonp=[o for o in ms if not o.name.startswith(('PLANT_',)) and not o.name.startswith('WATER_') ]
water=[o for o in ms if o.name.startswith('WATER_')]
def bvh(objs):
    V=[];T=[];own=[]
    for o in objs:
        M=o.matrix_world;b=len(V);V+=[M@v.co for v in o.data.vertices];o.data.calc_loop_triangles()
        for t in o.data.loop_triangles: T.append(tuple(b+i for i in t.vertices));own.append(o.name)
    return BVHTree.FromPolygons(V,T),own
tn,on=bvh(nonp); tw,ow=bvh(water)
cnt=0;bad=[]
for o in ms:
    if not o.name.startswith('PLANT_'): continue
    M=o.matrix_world;P=np.array([tuple(M@v.co) for v in o.data.vertices]);zmin=P[:,2].min()
    low=P[P[:,2]<=zmin+0.05];bx,by=low[:,0].mean(),low[:,1].mean()
    vine=o.name.startswith('PLANT_VINE')
    # distance down to nonwater support
    h=tn.ray_cast(Vector((bx,by,zmin+1.0)),Vector((0,0,-1)),60)
    hw=tw.ray_cast(Vector((bx,by,zmin+1.0)),Vector((0,0,-1)),60)
    sup=h[0].z if h[0] else None; wz=hw[0].z if hw[0] else None
    gap=None if sup is None else zmin-sup
    # base sits on water if there is water under it and no solid support within 0.5 m
    if (sup is None or abs(gap)>0.5) and wz is not None and zmin-wz<1.5 and not vine: bad.append((o.name,round(zmin,2),sup,wz))
    # base below water level
    if zmin<-0.05 and not vine: bad.append(('BELOW',o.name,round(zmin,2)))
print(mode,'non-vine plants on/under water:',len(bad),bad[:10])
