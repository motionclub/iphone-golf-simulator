"""Work-only physical eyelid closure on the accepted original-seam topology.

One expression, with half/full geometric targets so a spherical lid sweep does
not pass behind the eye at the intermediate pose. No separate closure surface.
"""
import bpy,bmesh,pathlib,json,math,collections,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/original-refinement';REPORT={}
def ss(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
for sex in ('Male','Female'):
 bpy.ops.wm.open_mainfile(filepath=str(O/f'{sex}_OriginalSeamPilot.blend'));sc=bpy.context.scene;body=bpy.data.objects['Body'];feat=bpy.data.objects['ReferenceFeatures'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
 vs=[v.co.copy() for v in body.data.vertices];fvs=[feat.matrix_world@v.co for v in feat.data.vertices]
 eyePolys=[p for p in feat.data.polygons if any(n in feat.data.materials[p.material_index].name for n in ('Sclera','Iris','Pupil','Limbal','Catch'))]
 eyeBVH=BVHTree.FromPolygons(fvs,[p.vertices[:] for p in eyePolys])
 eyeVertices=[fvs[i] for p in eyePolys if 'Sclera' in feat.data.materials[p.material_index].name for i in p.vertices];eyeZ=sum(p.z for p in eyeVertices)/len(eyeVertices)
 bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table();adj=collections.defaultdict(list)
 for e in bm.edges:
  if e.is_boundary and all(v.co.y<-.05 and abs(v.co.z-eyeZ)<.05 for v in e.verts):
   a,b=e.verts;adj[a.index].append(b.index);adj[b.index].append(a.index)
 seen=set();rings=[]
 for a in adj:
  if a in seen:continue
  q=[a];seen.add(a);ids=[]
  while q:
   v=q.pop();ids.append(v)
   for b in adj[v]:
    if b not in seen:seen.add(b);q.append(b)
  if len(ids)>20:rings.append(ids)
 bm.free();assert len(rings)==2,(sex,len(rings))
 eyes=[]
 for ids in rings:
  points=[vs[i] for i in ids];c=sum(points,Vector())/len(points);left=min(points,key=lambda p:p.x);right=max(points,key=lambda p:p.x);half=(max(p.z for p in points)-min(p.z for p in points))*.5
  kd=KDTree(len(points))
  for j,p in enumerate(points):kd.insert(Vector((p.x,0,p.z)),j)
  kd.balance()
  samples=[]
  for j in range(1,20):
   u=j/20;x=left.x+(right.x-left.x)*u
   corner=left.z*(1-u)+right.z*u;centre=c.z-half*.16
   z=corner+4*u*(1-u)*(centre-(left.z+right.z)*.5)
   hit,_,_,_=eyeBVH.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
   if hit is not None:samples.append((u,hit.y-.00065))
  coeff=np.polyfit([v[0] for v in samples],[v[1] for v in samples],2) if len(samples)>=3 else np.array([0,0,c.y-.001])
  eyes.append(dict(ids=ids,c=c,left=left,right=right,half=half,kd=kd,points=points,seamDepth=coeff))
 if body.data.shape_keys:body.shape_key_clear()
 basis=body.shape_key_add(name='Basis');halfKey=body.shape_key_add(name='Hero_Blink_Half');fullKey=body.shape_key_add(name='Hero_Blink')
 stageAudit=[]
 for progress,key in ((.5,halfKey),(1,fullKey)):
  changed=0;maxDelta=0;maxRayAdvance=0
  for i,p in enumerate(vs):
   if p.y>-.050 or abs(p.z-eyeZ)>.045:continue
   candidates=[]
   for e in eyes:
    if p.x<e['left'].x-.017 or p.x>e['right'].x+.017:continue
    _,nearest,dist=e['kd'].find(Vector((p.x,0,p.z)));boundary=e['points'][nearest]
    weight=1-ss(.001,.016,dist)
    if weight<=0:continue
    u=max(0,min(1,(p.x-e['left'].x)/(e['right'].x-e['left'].x)))
    corners=e['left'].z*(1-u)+e['right'].z*u
    centre=e['c'].z-e['half']*.16
    closed=corners+4*u*(1-u)*(centre-(e['left'].z+e['right'].z)*.5)
    overlap=.00006*math.sin(math.pi*u)
    # Upper and lower physical margins overlap by a fraction of a millimetre
    # at full closure, eliminating numerical white slits without an overlay.
    closed+=-overlap if p.z>=closed else overlap
    q=p.copy()
    targetZ=closed
    if progress==1 and sex=='Male':
     side=1 if p.z>=closed else -1
     targetZ+=side*dist*.5
    q.z=p.z+(targetZ-p.z)*weight*progress
    hit,n,_,_=eyeBVH.ray_cast(Vector((q.x,-1,q.z)),Vector((0,1,0)))
    if hit is not None and weight>.08:
     advance=min(.006,max(0,p.y-(hit.y-.00050)));q.y=p.y-advance
     maxRayAdvance=max(maxRayAdvance,advance)
    if progress==1:
     seamWeight=1-ss(.001,.008,dist)
     # The upper/lower boundary must share one depth contour at closure.
     # Original distinct edge depths produced corrugated overlapping highlights.
     depth=float(np.polyval(e['seamDepth'],u))
     q.y=q.y*(1-seamWeight)+depth*seamWeight
    candidates.append((weight,q))
   if candidates:
    weight,q=max(candidates,key=lambda a:a[0]);key.data[i].co=q;delta=(q-p).length
    if delta>1e-8:changed+=1;maxDelta=max(maxDelta,delta)
  stageAudit.append({'progress':progress,'changedVertices':changed,'maxDeltaMetres':maxDelta,'maxEyeFrontAdvanceMetres':maxRayAdvance})
 # The canonical eye sheet includes a few protruding peripheral triangles.
 # Keep the accepted open eye exact. Recess only eye components (not brows)
 # behind the moving skin during closure so those corners cannot ghost through.
 if feat.data.shape_keys:feat.shape_key_clear()
 feat.shape_key_add(name='Basis');eyeHalf=feat.shape_key_add(name='Hero_Blink_Half');eyeFull=feat.shape_key_add(name='Hero_Blink')
 eyeIDs={i for p in eyePolys for i in p.vertices};localBack=feat.matrix_world.to_3x3().inverted()@Vector((0,1,0))
 for key,depth in ((eyeHalf,.0007),(eyeFull,.006)):
  for i in eyeIDs:key.data[i].co=feat.data.vertices[i].co+localBack*depth
 # Show one controlled expression, not an expression catalogue. 50% uses its
 # geometric half target, rather than a straight interpolation through the eye.
 cam=sc.camera;target=Vector((0,0,eyeZ-.018));eyeCentre=sum((e['c'] for e in eyes),Vector())/2;target.y=eyeCentre.y
 sc.cycles.samples=40
 for pct in (0,50,100):
  halfKey.value=1 if pct==50 else 0;fullKey.value=1 if pct==100 else 0;eyeHalf.value=halfKey.value;eyeFull.value=fullKey.value;bpy.context.view_layer.update()
  for angle,offset in (('front',(0,-1.1,.015)),('threequarter',(.42,-1.1,.025))):
   cam.location=eyeCentre+Vector(offset);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'{sex.lower()}_connected_blink_{pct}_{angle}.png');bpy.ops.render.render(write_still=True)
 halfKey.value=0;fullKey.value=0;eyeHalf.value=0;eyeFull.value=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/f'{sex}_OriginalSeamBlink.blend'))
 REPORT[sex]={'baseOriginalSeam':str(O/f'{sex}_OriginalSeamPilot.blend'),'bodyVertices':len(vs),'shapeNames':['Hero_Blink_Half','Hero_Blink'],'parameterWeights':{'0':[0,0],'50':[100,0],'100':[0,100]},'runtimePiecewise':'half=max(0,1-abs(2*blink-1)); full=max(0,2*blink-1)','rings':[{'vertices':len(e['ids']),'centre':list(e['c']),'leftCorner':list(e['left']),'rightCorner':list(e['right'])} for e in eyes],'stages':stageAudit,'openEyeFeatureCoordinatesChanged':0,'eyeRecessionMetres':{'half':.0007,'full':.006},'additionalClosureRenderer':False}
 (O/'connected-blink-manifest.json').write_text(json.dumps(REPORT,indent=2));print('CONNECTED_BLINK',sex,stageAudit)
