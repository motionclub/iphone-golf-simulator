import bpy,bmesh,pathlib,json,collections,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/original-blink-finish';report={}
for sex in ('Male','Female'):
 bpy.ops.wm.open_mainfile(filepath=str(R/f'work/reference-rebuild/original-refinement/{sex}_OriginalSeamBlink.blend'))
 body=bpy.data.objects['Body'];feat=bpy.data.objects['ReferenceFeatures'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
 me=body.data;vs=[v.co.copy() for v in me.vertices];closed=[v.co.copy() for v in me.shape_keys.key_blocks['Hero_Blink'].data]
 bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();adj=collections.defaultdict(list)
 for e in bm.edges:
  if e.is_boundary and all(v.co.y<-.05 and 1.50<v.co.z<1.64 for v in e.verts):
   a,b=e.verts;adj[a.index].append(b.index);adj[b.index].append(a.index)
 seen=set();rings=[]
 for a in adj:
  if a in seen:continue
  todo=[a];seen.add(a);ids=[]
  while todo:
   i=todo.pop();ids.append(i)
   for j in adj[i]:
    if j not in seen:seen.add(j);todo.append(j)
  if len(ids)>20:rings.append(ids)
 bm.free();skin=BVHTree.FromPolygons(closed,[p.vertices[:] for p in me.polygons]);fvs=[(feat.matrix_world@v.co)+Vector((0,.012,0)) for v in feat.data.vertices];eyes=[p for p in feat.data.polygons if any(k in feat.data.materials[p.material_index].name for k in ('Sclera','Iris','Pupil','Limbal','Catch'))];eye=BVHTree.FromPolygons(fvs,[p.vertices[:] for p in eyes]);regions=[]
 for ids in rings:
  points=[vs[i] for i in ids];qs=[closed[i] for i in ids];left=min(points,key=lambda p:p.x);right=max(points,key=lambda p:p.x);cx=(left.x+right.x)/2;zlo=min(q.z for q in qs)-.001;zhi=max(q.z for q in qs)+.001
  leaks=[];bodyNormals=[]
  for j in range(151):
   x=left.x+(right.x-left.x)*(j+.5)/151
   for k in range(121):
    z=zlo+(zhi-zlo)*(k+.5)/121;origin=Vector((x,-1,z));eh,en,ei,ed=eye.ray_cast(origin,Vector((0,1,0)));bh,bn,bi,bd=skin.ray_cast(origin,Vector((0,1,0)))
    if eh is not None and (bh is None or ed<bd):leaks.append({'x':x,'z':z,'eyeDepth':eh.y,'skinDepth':None if bh is None else bh.y})
  weights={};upper=[];lower=[]
  for i in ids:
   groups={body.vertex_groups[g.group].name:g.weight for g in me.vertices[i].groups};weights[i]=groups
   (upper if vs[i].z>=closed[i].z else lower).append(i)
  summary={'boundaryVertices':len(ids),'closureXRange':[left.x,right.x],'closureZRange':[zlo,zhi],'visibleEyeRayCount':len(leaks),'testRays':151*121,'visibleEyeXRange':[min((p['x'] for p in leaks),default=0),max((p['x'] for p in leaks),default=0)],'visibleEyeZRange':[min((p['z'] for p in leaks),default=0),max((p['z'] for p in leaks),default=0)],'leakSamples':leaks[:20],'headWeights':[min(g.get('Head',0) for g in weights.values()),max(g.get('Head',0) for g in weights.values())],'upperVertices':len(upper),'lowerVertices':len(lower)}
  regions.append(summary)
 report[sex]=regions
(O/'blink11-diagnosis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
