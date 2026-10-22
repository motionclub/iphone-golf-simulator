import bpy,sys,numpy as np,collections,json,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
mode,n=sys.argv[-2],sys.argv[-1]   # blend|fbx , 08
bpy.ops.wm.read_factory_settings(use_empty=True)
if mode=='blend':
    bpy.ops.wm.open_mainfile(filepath=R+f'blender/hole_{n}.blend')
else:
    bpy.ops.import_scene.fbx(filepath=R+f'Unity/Assets/Resources/Course/hole_{n}.fbx')
dg=bpy.context.evaluated_depsgraph_get()
meshes=[o for o in bpy.data.objects if o.type=='MESH']
def bvh_of(objs):
    verts=[];tris=[];owner=[]
    for o in objs:
        me=o.to_mesh() if False else o.data
        M=o.matrix_world
        base=len(verts)
        verts+= [M@v.co for v in me.vertices]
        me.calc_loop_triangles()
        for t in me.loop_triangles:
            tris.append(tuple(base+i for i in t.vertices)); owner.append(o.name)
    return BVHTree.FromPolygons(verts,tris),owner
nonplant=[o for o in meshes if not o.name.startswith(('PLANT_','BALL','FLAG','HOLE_CUP','TEE_MARKER'))]
tree,owner=bvh_of(nonplant)
print('mode',mode,'hole',n,'meshes',len(meshes),'nonplant',len(nonplant))
# z-up check
allz=np.array([ (o.matrix_world@Vector(o.bound_box[0])).z for o in meshes])
print('zrange',allz.min(),allz.max())
# plants
res=collections.Counter(); onwater=[]; float_=[]; lowest=[]
plants=[o for o in meshes if o.name.startswith('PLANT_')]
for o in plants:
    M=o.matrix_world
    zs=[(M@v.co).z for v in o.data.vertices]
    # base point = lowest vertex xy-centroid of bottom 5% verts
    P=np.array([tuple(M@v.co) for v in o.data.vertices]); zmin=P[:,2].min()
    low=P[P[:,2]<=zmin+0.05]; bx,by=low[:,0].mean(),low[:,1].mean()
    top=P[:,2].max()
    # cast ray down from above highest nonplant thing at xy; use everything
    hits=[]
    org=Vector((bx,by,zmin+1.0))
    # multi-hit down: ray_cast repeatedly
    cur=org; first=None
    h=tree.ray_cast(cur,Vector((0,0,-1)),50.0)
    if h[0] is None: res['nohit']+=1; float_.append((o.name,'nohit')); continue
    nm=owner[h[2]]; gap=zmin-h[0].z
    res[nm.split('_')[0] if not nm.startswith('ROCK') else 'ROCK']+=1
    if nm.startswith('WATER'): onwater.append((o.name,nm,round(zmin,2),round(h[0].z,2)))
    if abs(gap)>1.0 and not o.name.startswith('PLANT_VINE'): float_.append((o.name,nm,round(gap,2)))
print('PLANTS',len(plants),'support',dict(res),'on_water',len(onwater),onwater[:6],'float_(gap>1m non-vine)',len(float_),float_[:6])
# also ground-level plants whose base z <= water level
wz=[]
for o in meshes:
    if o.name.startswith('WATER_OCEAN'):
        wz=[(o.matrix_world@v.co).z for v in o.data.vertices]
print('ocean z',(min(wz),max(wz)) if wz else None)
pz=[]
for o in plants:
    M=o.matrix_world; zmin=min((M@v.co).z for v in o.data.vertices); pz.append(zmin)
if wz: print('plants with base below ocean+0.0:',sum(1 for z in pz if z< max(wz)+0.0), 'min base',min(pz))
# rocks
rocks=[o for o in meshes if o.name.startswith('ROCK_')]
bad=[];wv=[];smallm=[]; ico=[]
seen={}
for o in rocks:
    s=o.matrix_world.to_scale(); sc=np.array(s)
    if sc.max()>2.0+1e-3 or sc.min()<0.5-1e-3 or sc.max()/sc.min()>2.0+1e-3: bad.append((o.name,tuple(np.round(sc,3))))
    me=o.data
    if me.name not in seen:
        b=bmesh.new(); b.from_mesh(me); bmesh.ops.remove_doubles(b,verts=b.verts,dist=1e-4); seen[me.name]=len(b.verts); 
        nf=len(b.faces); 
        # icosahedron: 12 verts, 20 tris
        b.free()
    wv.append((o.name,seen[me.name]))
print('ROCKS',len(rocks),'scale violations(>2 or <0.5 or aniso>2):',len(bad),bad[:8])
print(' welded verts min',min(w for _,w in wv),'count <60:',sum(1 for _,w in wv if w<60),[x for x in wv if x[1]<60][:8],' ==12:',sum(1 for _,w in wv if w==12))
print(' scales range: max comp',max(max(o.matrix_world.to_scale()) for o in rocks) ,'min comp',min(min(o.matrix_world.to_scale()) for o in rocks),'max aniso',max(max(o.matrix_world.to_scale())/min(o.matrix_world.to_scale()) for o in rocks))
# names/materials
mats=sorted({s.material.name for o in meshes for s in o.material_slots if s.material})
print('foam named objs',[o.name for o in meshes if 'FOAM' in o.name.upper()],'foam mats',[m for m in mats if 'FOAM' in m.upper()],'MAT_ legacy',[m for m in mats if m.startswith('MAT_')])
surf=[o for o in meshes if o.name.startswith('WATER_SURF')]
ext=[]
for o in surf:
    P=np.array([tuple(o.matrix_world@v.co) for v in o.data.vertices]); d=P[:,:2].max(0)-P[:,:2].min(0)
    # longest extent via PCA
    c=P[:,:2]-P[:,:2].mean(0); u,s,vt=np.linalg.svd(c,full_matrices=False); pr=c@vt[0]; ext.append((o.name,round(float(pr.max()-pr.min()),1),P[:,:2].mean(0).round(1)))
print('SURF patches',len(surf),'longest m',sorted([e[1] for e in ext])[-5:], 'mats',{s.material.name for o in surf for s in o.material_slots if s.material})
# gaps nearest neighbour centre distance
if len(ext)>1:
    cs=np.array([e[2] for e in ext]); dm=np.linalg.norm(cs[:,None]-cs[None],axis=2)+np.eye(len(cs))*1e9; print(' min centre-to-centre',dm.min().round(1))
