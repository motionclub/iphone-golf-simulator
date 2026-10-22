import bpy,sys,numpy as np,collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
bpy.ops.import_scene.fbx(filepath=R+'Unity/Assets/Resources/Course/hole_08.fbx')
meshes=[o for o in bpy.data.objects if o.type=='MESH']
nonplant=[o for o in meshes if not o.name.startswith(('PLANT_','BALL','FLAG','HOLE_CUP','TEE_MARKER','WATER_'))]
verts=[];tris=[];owner=[]
for o in nonplant:
    me=o.data;M=o.matrix_world;b=len(verts);verts+=[M@v.co for v in me.vertices];me.calc_loop_triangles()
    for t in me.loop_triangles: tris.append(tuple(b+i for i in t.vertices));owner.append(o.name)
T=BVHTree.FromPolygons(verts,tris)
d=[];sup=collections.Counter()
for o in meshes:
    if not o.name.startswith('PLANT_VINE'): continue
    M=o.matrix_world;P=np.array([tuple(M@v.co) for v in o.data.vertices]);top=P[P[:,2]>=P[:,2].max()-0.05]
    c=Vector(top.mean(0)); loc,nrm,idx,dist=T.find_nearest(c)
    d.append(dist);sup[owner[idx].split('_')[0]+'_'+owner[idx].split('_')[1][:6]]+=1
d=np.array(d);print('vines',len(d),'root->nearest surface m: max',d.max().round(2),'p95',np.percentile(d,95).round(2),'>0.5:',(d>0.5).sum(),'>1.0:',(d>1.0).sum(),dict(sup))
