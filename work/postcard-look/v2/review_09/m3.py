import bpy, numpy as np, math, collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree
dg=bpy.context.evaluated_depsgraph_get()
PFX=('TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER')
def bvh(objs):
    vs=[];ps=[];off=0
    for o in objs:
        me=o.data; mw=o.matrix_world
        vs+= [mw@v.co for v in me.vertices]
        for p in me.polygons: ps.append([i+off for i in p.vertices])
        off+=len(me.vertices)
    return BVHTree.FromPolygons(vs,ps)
ground=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(PFX)]
gb=bvh(ground)
props=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('ROCK_','DRESS_','PLANT_')) and not o.name.startswith('ROCK_SKIN')]
skin=bvh([o for o in bpy.data.objects if o.name.startswith('ROCK_SKIN')])
# play tops z
pl=[o for o in bpy.data.objects if o.name.startswith(PFX[1:])]
pb=bvh(pl)
res=collections.Counter(); worst=0; offg=[]; onplay=[]; edge=[]
plants=[o for o in props if o.name.startswith('PLANT_')]
for o in plants:
    p=o.matrix_world.translation
    h=gb.ray_cast(Vector((p.x,p.y,p.z+30)),Vector((0,0,-1)),80)
    if h[0] is None: offg.append((o.name,tuple(p))); continue
    dz=abs(h[0].z-p.z); worst=max(worst,dz)
    if h[0].z<5.0: res['ground_z<5']+=1
    if dz>0.2: res['dz>0.2']+=1
    # play surface under? 
    hp=pb.ray_cast(Vector((p.x,p.y,p.z+30)),Vector((0,0,-1)),80)
    if hp[0] is not None: onplay.append((o.name,tuple(round(c,1) for c in p)))
    # edge sampling: 4 neighbours at 0.6m
    miss=0
    for dx,dy in((0.6,0),(-0.6,0),(0,0.6),(0,-0.6)):
        q=gb.ray_cast(Vector((p.x+dx,p.y+dy,p.z+30)),Vector((0,0,-1)),80)
        if q[0] is None or q[0].z<p.z-0.8: miss+=1
    if miss: edge.append((o.name,miss,tuple(round(c,1) for c in p)))
print('plants',len(plants),'no ground',len(offg),offg[:3],'worst dz',worst,dict(res))
print('on play surfaces (not terrain)',len(onplay),onplay[:6])
print('plants with a neighbour at 0.6 m off ground/drop>0.8:',len(edge),edge[:10])
# plant verts min z
zmin=min(min((o.matrix_world@v.co).z for v in o.data.vertices[:3]) for o in plants); print('min z',zmin)
# water level
for o in bpy.data.objects:
    if o.name.startswith(('WATER_OCEAN','WATER_SHELF')):
        zs=[(o.matrix_world@v.co).z for v in o.data.vertices]; print(o.name,min(zs),max(zs))
# all props: any above play surface?
inter=0; near_tee=0
for o in props:
    zs=[o.matrix_world@v.co for v in o.data.vertices]
# playsurface z top vs ground: props that overlap play surfaces in xy: any vertex with a play surface hit under and vertex z<hit+... 
