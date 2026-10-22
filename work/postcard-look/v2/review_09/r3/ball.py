import bpy, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
YD=0.9144
dg=bpy.context.evaluated_depsgraph_get()
sc=bpy.context.scene
for name,(x,d) in {'tee':(0,0),'appr':(13.5,269)}.items():
    p=Vector((x*YD,d*YD,60))
    ok,loc,n,idx,ob,mx=sc.ray_cast(dg,p,Vector((0,0,-1)),distance=200)
    print(name,'first hit',ob.name if ob else None,'z',loc.z if ok else None)
    # all hits above ground within 1.5 m radius? props overlapping ball position
    # cast down repeatedly
    q=p.copy(); hits=[]
    for i in range(6):
        ok,loc,n,idx,ob,mx=sc.ray_cast(dg,q,Vector((0,0,-1)),distance=200)
        if not ok: break
        hits.append((ob.name,round(loc.z,3))); q=loc+Vector((0,0,-0.001))
    print(' hit stack',hits)
    # props within 1 m of ball
    for o in bpy.data.objects:
        if o.type=='MESH' and o.name.startswith(('PLANT_','ROCK_','DRESS_')) and not o.name.startswith(('ROCK_SKIN','DRESS_SAND')):
            for v in o.data.vertices:
                w=o.matrix_world@v.co
                if (w.x-p.x)**2+(w.y-p.y)**2<4.0: print('  near prop',o.name); break
# camera for address: 4.5 yd behind ball along aim, 2.4 yd up
