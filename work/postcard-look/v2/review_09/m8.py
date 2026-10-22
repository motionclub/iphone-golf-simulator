import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
PFX=('TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER')
vs=[];ps=[];off=0
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith(PFX):
        me=o.data; mw=o.matrix_world
        vs+=[mw@v.co for v in me.vertices]; ps+=[[i+off for i in p.vertices] for p in me.polygons]; off+=len(me.vertices)
g=BVHTree.FromPolygons(vs,ps)
fl=[];bur=[];n=0;water=0
for o in bpy.data.objects:
    if o.type!='MESH' or o.hide_viewport or not o.name.startswith(('ROCK_','DRESS_')) or o.name.startswith('ROCK_SKIN'): continue
    mw=o.matrix_world; Z=np.array([(mw@v.co).z for v in o.data.vertices]); zmin=Z.min(); zmax=Z.max()
    c=mw.translation
    h=g.ray_cast(Vector((c.x,c.y,c.z+50)),Vector((0,0,-1)),120)
    if h[0] is None: water+=1; continue
    n+=1
    gz=h[0].z
    # use bottom center
    if zmin>gz+0.35: fl.append((o.name,round(zmin-gz,2),tuple(round(x,0) for x in c)))
    if zmax<gz+0.1: bur.append((o.name,round(zmax-gz,2)))
print('land props',n,'water/no-ground',water,'floating >0.35',len(fl),fl[:12],'buried',len(bur),bur[:5])
