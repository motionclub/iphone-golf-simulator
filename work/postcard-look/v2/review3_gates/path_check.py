import bpy,sys,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
src=sys.argv[-1]
if src=='fbx': bpy.ops.import_scene.fbx(filepath=R+'Unity/Assets/Resources/Course/hole_08.fbx')
elif src=='base': bpy.ops.wm.open_mainfile(filepath=R+'work/postcard-look/baseline/blender/hole_08.blend')
else: bpy.ops.wm.open_mainfile(filepath=R+'blender/hole_08.blend')
ms=[o for o in bpy.data.objects if o.type=='MESH']
print(src,'path objs',[o.name for o in ms if 'PATH' in o.name])
def tree(objs):
    V=[];T=[]
    for o in objs:
        me=o.data;M=o.matrix_world;b=len(V);V+=[M@v.co for v in me.vertices];me.calc_loop_triangles()
        for t in me.loop_triangles:
            T.append(tuple(b+i for i in t.vertices))
    return BVHTree.FromPolygons(V,T)
ground=[o for o in ms if o.name.startswith(('TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER'))]
paths=[o for o in ms if 'PATH' in o.name]
G=tree(ground)
up=Vector((0,0,1)); dn=Vector((0,0,-1))
def gz(x,y):
    # topmost ground surface at x,y (ray from high down)
    h=G.ray_cast(Vector((x,y,60)),dn,200)
    return None if h[0] is None else h[0].z
hs=[]
for o in paths:
    M=o.matrix_world; me=o.data
    for v in me.vertices:
        w=M@v.co
        z=gz(w.x,w.y)
        if z is not None: hs.append(w.z-z)
hs=np.array(hs)
print('path verts',len(hs),'height above ground: min %.4f max %.4f p99 %.4f mean %.4f'%(hs.min(),hs.max(),np.percentile(hs,99),hs.mean()))
# dense grid: sample every path triangle at barycentric grid
P=tree(paths)
hh=[]
for o in paths:
    M=o.matrix_world; me=o.data; me.calc_loop_triangles()
    for t in me.loop_triangles:
        a,b,c=[M@me.vertices[i].co for i in t.vertices]
        if (b-a).cross(c-a).z<=0: continue
        for i in range(0,9):
            for j in range(0,9-i):
                p=a+(b-a)*(i/8)+(c-a)*(j/8); z=gz(p.x,p.y)
                if z is not None: hh.append(p.z-z)
hh=np.array(hh); print('dense',len(hh),'min %.4f max %.4f p99.9 %.4f'%(hh.min(),hh.max(),np.percentile(hh,99.9)),'count>0.015',int((hh>0.015).sum()),'count>0.012',int((hh>0.012).sum()),'below ground by >0.5cm',int((hh<-0.005).sum()))
print('hist <-0.14..',[ (lo,int(((hh>=lo)&(hh<hi)).sum())) for lo,hi in [(-1,-0.1),(-0.1,-0.05),(-0.05,-0.02),(-0.02,-0.005),(-0.005,0.005),(0.005,0.0116)]])
# where are very buried samples (< -2cm)? bin by x,y
pts=[]
for o in paths:
    M=o.matrix_world; me=o.data; me.calc_loop_triangles()
    for t in me.loop_triangles:
        a,b,c=[M@me.vertices[i].co for i in t.vertices]
        if (b-a).cross(c-a).z<=0: continue
        p=(a+b+c)/3; z=gz(p.x,p.y)
        if z is not None and p.z-z<-0.02: pts.append((o.name,round(p.x,1),round(p.y,1),round(p.z,3),round(p.z-z,3)))
print('buried tris',len(pts),pts[:12])
for o in paths:
    print(o.name,'tris',len(o.data.polygons),'verts',len(o.data.vertices),'zrange',min((o.matrix_world@v.co).z for v in o.data.vertices),max((o.matrix_world@v.co).z for v in o.data.vertices))
