import bpy,pathlib,sys,json,collections
from mathutils import Vector
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_FistSurfaceV3B.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'));bpy.context.view_layer.update();obj=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh();report={}
for side in ('Left','Right'):
 H=rig.data.bones[side+'Hand'].matrix_local.inverted()@rig.matrix_world.inverted()@body.matrix_world
 p=[H@v.co for v in body.data.vertices];ids={g.index for g in body.vertex_groups if g.name==side+'Hand' or any(g.name.startswith(side+d) for d in ('Thumb','Index','Middle','Ring','Little'))};verts={i for i,v in enumerate(body.data.vertices) if p[i].y>.035 and sum(g.weight for g in v.groups if g.group in ids)>.2}
 polys=[f for f in mesh.polygons if all(i in verts for i in f.vertices)];edges=collections.Counter(tuple(sorted((a,b))) for f in polys for a,b in zip(f.vertices,list(f.vertices[1:])+[f.vertices[0]]));faces=collections.Counter(tuple(sorted(f.vertices)) for f in polys);coincident=collections.Counter(tuple(sorted(tuple(round(c,5) for c in mesh.vertices[i].co) for i in f.vertices)) for f in polys)
 # Intersection: triangle overlap excluding adjacent vertices. BVH overlap results
 # are filtered with exact segment-triangle penetration to avoid bbox false positives.
 tris=[]
 for f in polys:
  for j in range(1,len(f.vertices)-1):tris.append((f.vertices[0],f.vertices[j],f.vertices[j+1]))
 from mathutils.bvhtree import BVHTree
 bvh=BVHTree.FromPolygons([v.co for v in mesh.vertices],tris,all_triangles=True)
 def hit(a,b,c,p,q):
  d=q-p;e1=b-a;e2=c-a;h=d.cross(e2);det=e1.dot(h)
  if abs(det)<1e-12:return False
  inv=1/det;s=p-a;u=inv*s.dot(h)
  if u<1e-5 or u>1-1e-5:return False
  r=s.cross(e1);v=inv*d.dot(r);t=inv*e2.dot(r)
  return v>1e-5 and u+v<1-1e-5 and 1e-5<t<1-1e-5
 intersections=set()
 for x,y in bvh.overlap(bvh):
  if x>=y or set(tris[x])&set(tris[y]):continue
  a=[mesh.vertices[i].co for i in tris[x]];b=[mesh.vertices[i].co for i in tris[y]]
  if any(hit(*a,b[k],b[(k+1)%3]) or hit(*b,a[k],a[(k+1)%3]) for k in range(3)):intersections.add((x,y))
 classes=collections.Counter();locations=[];gnames={g.index:g.name for g in body.vertex_groups}
 def semantic(t):
  sums={d:sum(g.weight for i in t for g in body.data.vertices[i].groups if gnames[g.group].startswith(side+d)) for d in ('Thumb','Index','Middle','Ring','Little')}
  best=max(sums,key=sums.get);return best if sums[best]>.5 else 'Palm'
 for x,y in intersections:
  classes['-'.join(sorted((semantic(tris[x]),semantic(tris[y]))))]+=1
  locations.extend((sum((p[i] for i in tris[x]),Vector())/3,sum((p[i] for i in tris[y]),Vector())/3))
 report[side]={'intersectionClasses':dict(classes),'intersectionRestYRange':([min(q.y for q in locations),max(q.y for q in locations)] if locations else []),'vertices' :len(verts),'polygons':len(polys),'duplicateFaceIndices':sum(n-1 for n in faces.values() if n>1),'coincidentFacesTo10Micrometres':sum(n-1 for n in coincident.values() if n>1),'nonmanifoldInteriorEdges':sum(n>2 for n in edges.values()),'boundaryEdgesInclCut':sum(n==1 for n in edges.values()),'posedTrianglePenetrationPairs':len(intersections),'penetrationExamples':[[list(tris[x]),list(tris[y])] for x,y in list(intersections)[:20]]}
(R/f'proof/full-visual-overhaul/characters/posed-hand-topology-v3b-{sex}.json').write_text(json.dumps(report,indent=2));print('POSED_HAND_SURFACE_AUDIT',sex,report,flush=True)
