import bpy,bmesh,pathlib,json,collections,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/original-blink-finish';out={}
for sex in ('Male','Female'):
 bpy.ops.wm.open_mainfile(filepath=str(O/f'{sex}_OriginalSeamBlinkFinish1.blend'));body=bpy.data.objects['Body'];feat=bpy.data.objects['ReferenceFeatures'];me=body.data;vs=[v.co.copy() for v in me.vertices];closed=[v.co.copy() for v in me.shape_keys.key_blocks['Hero_Blink'].data];fvs=[(feat.matrix_world@v.co)+Vector((0,.012,0)) for v in feat.data.vertices];eyes=[p for p in feat.data.polygons if any(k in feat.data.materials[p.material_index].name for k in ('Sclera','Iris','Pupil','Limbal','Catch'))];eyeids={i for p in eyes for i in p.vertices}
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
 bm.free();snap=json.loads((R/f'proof/reference-rebuild/character-cloth14-control/poses/{sex.lower()}_intro.json').read_text())['parts'][0];names=snap['bones'];weights=[[(names.index(body.vertex_groups[g.group].name),g.weight) for g in v.groups if body.vertex_groups[g.group].name in names] for v in me.vertices];head=names.index('Head');results=[]
 for clip in ('Ready','Serve','Forehand','IntroWave'):
  path=R/f'proof/reference-rebuild/character-motion-matrices17/matrices/{sex.lower()}_{clip}_2.json';record=json.loads(path.read_text());part=record['parts'][0];mats=np.asarray(part['skinMatrices']).reshape(-1,4,4);toRoot=np.asarray(part['rendererToRoot']).reshape(4,4)
  def posed(p,ws):
   v=np.asarray([*p,1]);q=sum((mats[i]@v*w for i,w in ws),np.zeros(4));return Vector((toRoot@q)[:3])
  bs=[posed(p,weights[i]) for i,p in enumerate(closed)];fs=[posed(p,[(head,1)]) for p in fvs];skin=BVHTree.FromPolygons(bs,[p.vertices[:] for p in me.polygons]);eye=BVHTree.FromPolygons(fs,[p.vertices[:] for p in eyes]);regions=[]
  for ids in rings:
   qs=[bs[i] for i in ids];xlo=min(q.x for q in qs);xhi=max(q.x for q in qs);ylo=min(q.y for q in qs)-.001;yhi=max(q.y for q in qs)+.001;leaks=[]
   for j in range(151):
    x=xlo+(xhi-xlo)*(j+.5)/151
    for k in range(121):
     y=ylo+(yhi-ylo)*(k+.5)/121;origin=Vector((x,y,1));eh,en,ei,ed=eye.ray_cast(origin,Vector((0,0,-1)));bh,bn,bi,bd=skin.ray_cast(origin,Vector((0,0,-1)))
     if eh is not None and (bh is None or ed<bd):leaks.append([x,y,eh.z,None if bh is None else bh.z])
   regions.append({'visibleEyeRayCount':len(leaks),'testRays':151*121,'visibleEyeXRange':[min((p[0] for p in leaks),default=0),max((p[0] for p in leaks),default=0)],'visibleEyeYRange':[min((p[1] for p in leaks),default=0),max((p[1] for p in leaks),default=0)],'examples':leaks[:3]})
  results.append({'clip':clip,'time':record['time'],'regions':regions})
 out[sex]=results
(O/'blink-finish1-posed-full-gate.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
