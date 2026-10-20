"""Authored closed lid patches from the approved body's two real aperture loops.
No body/face positions or skeleton are modified. A regular quad patch fills each hole,
overlaps 2mm into skin, retains the actual curved rim depth, and has smooth normals.
"""
import bpy, bmesh, json, math, pathlib, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=pathlib.Path(__file__).resolve().parents[3];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'work/match-anim-set/export/HeroBase_{sex}_MatchAnims.blend'))
body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body_'))
face=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Face_'))
bpy.context.view_layer.update()
evaluated=body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
if len(evaluated.vertices)!=len(body.data.vertices):raise RuntimeError('Body modifier changed aperture vertex topology')
bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table()
boundary={e for e in bm.edges if e.is_boundary};loops=[]
while boundary:
 start=next(iter(boundary));todo=list(start.verts);visited=set();edges=set()
 while todo:
  v=todo.pop()
  if v in visited:continue
  visited.add(v)
  for e in v.link_edges:
   if e.is_boundary:edges.add(e);todo.extend(e.verts)
 boundary-=edges
 loops.append([body.matrix_world@evaluated.vertices[v.index].co for v in visited])
if len(loops)!=2 or not all(len(p)>20 for p in loops):raise RuntimeError('Expected two exact body aperture boundaries')
worldVerts=[body.matrix_world@v.co for v in evaluated.vertices]
tree=BVHTree.FromPolygons(worldVerts,[list(p.vertices) for p in body.data.polygons],all_triangles=False)
worldToFace=face.matrix_world.inverted();rot=worldToFace.to_3x3()
positions=[];normals=[];indices=[];stats=[]
for loop in sorted(loops,key=lambda p:sum(v.x for v in p)/len(p)):
 cx=sum(p.x for p in loop)/len(loop);cz=sum(p.z for p in loop)/len(loop)
 # Sample vertical intersections with the ordered hole polygon. Angle sorting orders
 # an eye aperture without replacing its convex outline or its curved depth profile.
 loop.sort(key=lambda p:math.atan2(p.z-cz,p.x-cx))
 xmin=min(p.x for p in loop);xmax=max(p.x for p in loop)
 def contour(x):
  cuts=[]
  x=min(xmax-1e-7,max(xmin+1e-7,x))
  for a,b in zip(loop,loop[1:]+loop[:1]):
   if (a.x<=x<b.x) or (b.x<=x<a.x):
    t=(x-a.x)/(b.x-a.x);cuts.append(a.lerp(b,t))
  if len(cuts)<2:raise RuntimeError('Open aperture contour')
  return min(cuts,key=lambda p:p.z),max(cuts,key=lambda p:p.z)
 N=64;M=20;base=len(positions)//3;world=[]
 for i in range(N+1):
  x=xmin-.002+(xmax-xmin+.004)*i/N;lo,hi=contour(x)
  for j in range(M+1):
   t=j/M
   z=(lo.z-.002)*(1-t)+(hi.z+.002)*t
   rimY=lo.y*(1-t)+hi.y*t
   # Overlap vertices sit on the nearest real surrounding skin; interior preserves
   # the actual aperture rim depth and bulges out gently as a closed eyelid.
   outside=x<xmin or x>xmax or z<lo.z or z>hi.z
   if outside:
    closest,n,_,_=tree.find_nearest(Vector((x,rimY,z)))
    y=closest.y-.00012
   else:
    w=max(0,1-((x-cx)/((xmax-xmin)*.5))**2)
    v=max(0,1-((z-(lo.z+hi.z)*.5)/max(.00001,(hi.z-lo.z)*.5))**2)
    y=rimY-.0014*w*v-.00012
   world.append(Vector((x,y,z)))
 for i in range(N):
  for j in range(M):
   a=base+i*(M+1)+j;b=a+M+1;c=b+1;d=a+1
   # X cross Z points toward camera (-Y), the source's face direction.
   indices.extend([a,b,c,a,c,d])
 accum=[Vector() for _ in world]
 for k in range(0,len(indices),3):
  ia,ib,ic=indices[k:k+3]
  if ia<base:continue
  a,b,c=[world[q-base] for q in (ia,ib,ic)];n=(b-a).cross(c-a)
  for q in (ia,ib,ic):accum[q-base]+=n
 for p,n in zip(world,accum):
  positions.extend(worldToFace@p);normals.extend((rot@n.normalized()).normalized())
 stats.append(dict(boundaryVertices=len(loop),xRange=[xmin,xmax],vertices=len(world),triangles=N*M*2))
mesh=bpy.data.meshes.new('Fitted_ClosedLids_'+sex)
mesh.from_pydata([tuple(positions[i:i+3]) for i in range(0,len(positions),3)],[],[indices[i:i+3] for i in range(0,len(indices),3)])
mesh.update();mesh.normals_split_custom_set_from_vertices([tuple(normals[i:i+3]) for i in range(0,len(normals),3)])
ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.collection.objects.link(ob);ob.matrix_world=face.matrix_world.copy()
for p in mesh.polygons:p.use_smooth=True
out=ROOT/'Unity/Assets/Resources/Tennis/HeroDetail';out.mkdir(parents=True,exist_ok=True)
eyeMaterial=next(i for i,m in enumerate(face.data.materials) if m.name=='Face_Sclera')
eyeIndices=set(i for p in face.data.polygons if p.material_index==eyeMaterial for i in p.vertices)
eyePositions=[face.data.vertices[i].co for i in eyeIndices]
eyeNormals=[face.data.vertices[i].normal for i in eyeIndices]
payload=dict(sourceEyeMin=[min(v[d] for v in eyePositions) for d in range(3)],sourceEyeMax=[max(v[d] for v in eyePositions) for d in range(3)],sourceEyeNormal=list(sum(eyeNormals,Vector()).normalized()),version=1,sex=sex,coordinateSpace='approved Face mesh local',sourceBoundsMin=[min(v.co[d] for v in face.data.vertices) for d in range(3)],sourceBoundsMax=[max(v.co[d] for v in face.data.vertices) for d in range(3)],positions=list(positions),normals=list(normals),triangles=indices,apertures=stats)
(out/f'FaceLids_{sex}.json').write_text(json.dumps(payload,separators=(',',':')))
source=ROOT/'ArtDir/hero/kit/premium/source';source.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(source/f'Premium_{sex}_FittedLids.blend'))
(ROOT/f'proof/full-visual-overhaul/characters/lid-aperture-{sex}.json').write_text(json.dumps(dict(gate='SOURCE ONLY: exact two original hole loops retained; visual 0/50/100 pending',apertures=stats),indent=2))
print('FITTED_LID_APERTURES',sex,json.dumps(stats))
