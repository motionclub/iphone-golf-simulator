"""Author a coherent, render-only resort coast on the existing island / headland footprint."""
import bpy, math, random, json, collections
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt
ROOT=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
WORK=ROOT/'work/full-visual-overhaul/tennis'; PROOF=ROOT/'proof/full-visual-overhaul/tennis'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'Unity/Assets/Resources/Tennis/Island/TennisIsland.fbx'))
def bvh(objects):
    vertices=[]; faces=[]
    for ob in objects:
        me=ob.data; me.calc_loop_triangles(); start=len(vertices)
        vertices.extend(ob.matrix_world@v.co for v in me.vertices)
        faces.extend(tuple(start+i for i in t.vertices) for t in me.loop_triangles)
    return BVHTree.FromPolygons(vertices,faces,all_triangles=True)
island=bvh([o for o in bpy.context.scene.objects if o.type=='MESH'])
bpy.ops.import_scene.fbx(filepath=str(ROOT/'Unity/Assets/Resources/Tennis/TropicalV3/TropicalTennisResort.fbx'))
headlands=bvh([o for o in bpy.context.scene.objects if o.type=='MESH' and any(m and m.name.startswith('TropicalV3_021') for m in o.data.materials)])
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)

def material(name,rgb):
    m=bpy.data.materials.new(name);m.diffuse_color=tuple(c for c in rgb)+(1,);m.use_nodes=True
    n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=m.diffuse_color;n.inputs['Roughness'].default_value=.85
    return m
mats=[material('COAST_GRASS',(.12,.29,.09)),material('COAST_SAND',(.78,.72,.58)),
      material('COAST_LIMESTONE',(.72,.73,.64)),material('COAST_SHORE',(.45,.54,.49))]

# Only the footprint is read from the old asset. Old scan foliage heights / textures
# are deliberately not carried into the new terrain or into its manufactured materials.
STEP=2.5; X0=-242.5;Y0=-187.5;NX=192;NY=254
land={};source={}; kind={}
for j in range(NY):
    for i in range(NX):
        x=X0+i*STEP;y=Y0+j*STEP; origin=Vector((x,y,60))
        a=island.ray_cast(origin,Vector((0,0,-1)),90)[0]
        b=headlands.ray_cast(origin,Vector((0,0,-1)),90)[0]
        hit=b if b and (not a or b.z>a.z) else a
        if hit is not None and hit.z>-3.92:
            land[i,j]=True;source[i,j]=hit.z;kind[i,j]=1 if hit is b else 0

distance={}; q=collections.deque()
for i,j in land:
    if any((i+dx,j+dy) not in land for dx,dy in ((-1,0),(1,0),(0,-1),(0,1))):distance[i,j]=0;q.append((i,j))
while q:
    i,j=q.popleft()
    for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
        p=i+dx,j+dy
        if p in land and p not in distance:distance[p]=distance[i,j]+1;q.append(p)


directed={}
for i,j in land:
 q=[(i,j),(i+1,j),(i+1,j+1),(i,j+1)]
 if not all(p in land for p in q):continue
 for a,b in zip(q,q[1:]+q[:1]):
  if (b,a) in directed:del directed[b,a]
  else:directed[a,b]=True
adj=collections.defaultdict(list)
for a,b in directed:adj[a].append(b)
areas=[]
while directed:
 a,b=next(iter(directed));chain=[a];start=a
 while (a,b) in directed:
  del directed[a,b];chain.append(b);a=b
  if a==start:break
  opt=[v for v in adj[a] if (a,v) in directed]
  if not opt:break
  b=opt[0]
 if chain[-1]!=start:continue
 pts=[(X0+i*STEP,Y0+j*STEP) for i,j in chain[:-1]]
 area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pts,pts[1:]+pts[:1]))*.5
 areas.append({'signed_area':area,'points':len(pts)})
print('SHORE_TOPOLOGY',json.dumps(areas))
(PROOF/'shore-topology-audit.json').write_text(json.dumps(areas,indent=2))
