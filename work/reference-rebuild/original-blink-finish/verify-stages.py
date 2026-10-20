import bpy,pathlib,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/original-blink-finish';out={};names=json.loads((R/'proof/reference-rebuild/character-cloth14-control/poses/female_intro.json').read_text())['parts'][0]['bones'];head=names.index('Head')
for sex in ('Male','Female'):
 bpy.ops.wm.open_mainfile(filepath=str(R/f'work/reference-rebuild/original-refinement/{sex}_OriginalSeamEyeMaterial.blend'));oldbody=bpy.data.objects['Body'];oldws=[[(names.index(oldbody.vertex_groups[g.group].name),g.weight) for g in v.groups if oldbody.vertex_groups[g.group].name in names] for v in oldbody.data.vertices]
 bpy.ops.wm.open_mainfile(filepath=str(O/f'{sex}_OriginalSeamBlinkFinish1.blend'));body=bpy.data.objects['Body'];feat=bpy.data.objects['ReferenceFeatures'];me=body.data;basis=np.asarray([tuple(v.co) for v in me.vertices]);half=np.asarray([tuple(v.co) for v in me.shape_keys.key_blocks['Hero_Blink_Half'].data])-basis;full=np.asarray([tuple(v.co) for v in me.shape_keys.key_blocks['Hero_Blink'].data])-basis;fbasis=np.asarray([tuple(feat.matrix_world@v.co) for v in feat.data.vertices]);fhalf=np.asarray([tuple(v.co) for v in feat.data.shape_keys.key_blocks['Hero_Blink_Half'].data])-np.asarray([tuple(v.co) for v in feat.data.vertices]);ffull=(np.asarray([tuple(v.co) for v in feat.data.shape_keys.key_blocks['Hero_Blink'].data])-np.asarray([tuple(v.co) for v in feat.data.vertices]))*2;eyes=[p for p in feat.data.polygons if any(k in feat.data.materials[p.material_index].name for k in ('Sclera','Iris','Pupil','Limbal','Catch'))];eyeids={i for p in eyes for i in p.vertices};ws=[[(names.index(body.vertex_groups[g.group].name),g.weight) for g in v.groups if body.vertex_groups[g.group].name in names] for v in me.vertices];results=[]
 for clip in ('Ready','Serve','Forehand','IntroWave'):
  record=json.loads((R/f'proof/reference-rebuild/character-motion-matrices17/matrices/{sex.lower()}_{clip}_2.json').read_text());part=record['parts'][0];mats=np.asarray(part['skinMatrices']).reshape(-1,4,4);toRoot=np.asarray(part['rendererToRoot']).reshape(4,4)
  def poseBody(ps,weights):
   hp=np.c_[ps,np.ones(len(ps))];out=np.zeros((len(ps),4))
   for i,w in enumerate(weights):
    for bone,weight in w:out[i]+=mats[bone]@hp[i]*weight
   return (toRoot@out.T).T[:,:3]
  def poseFeatures(ps):return (toRoot@mats[head]@np.c_[ps,np.ones(len(ps))].T).T[:,:3]
  openbody=poseBody(basis,ws);oldopen=poseBody(basis,oldws);delta=np.linalg.norm(openbody-oldopen,axis=1);openeyes=poseFeatures(fbasis);boxes=[]
  for side in (-1,1):
   ids=[i for i in eyeids if fbasis[i,0]*side>0];ps=openeyes[ids];boxes.append((ps[:,0].min(),ps[:,0].max(),ps[:,1].min(),ps[:,1].max()))
  stages=[]
  for progress in (0,.25,.5,.75,1):
   h=max(0,1-abs(2*progress-1));f=max(0,2*progress-1);bs=poseBody(basis+half*h+full*f,ws);fs=poseFeatures(fbasis+fhalf*h+ffull*f);skin=BVHTree.FromPolygons([Vector(p) for p in bs],[p.vertices[:] for p in me.polygons]);eye=BVHTree.FromPolygons([Vector(p) for p in fs],[p.vertices[:] for p in eyes]);counts=[]
   for xlo,xhi,ylo,yhi in boxes:
    visible=0
    for j in range(121):
     x=xlo+(xhi-xlo)*(j+.5)/121
     for k in range(101):
      y=ylo+(yhi-ylo)*(k+.5)/101;origin=Vector((x,y,1));eh,en,ei,ed=eye.ray_cast(origin,Vector((0,0,-1)));bh,bn,bi,bd=skin.ray_cast(origin,Vector((0,0,-1)))
      visible+=int(eh is not None and (bh is None or ed<bd))
    counts.append(visible)
   stages.append({'blink':progress,'halfWeight':h,'fullWeight':f,'visibleEyeRays':counts,'testRaysPerAperture':121*101})
  assert stages[-1]['visibleEyeRays']==[0,0],(sex,clip,stages)
  results.append({'clip':clip,'time':record['time'],'openPosedMaxWeightCorrectionDeltaMetres':float(delta.max()),'openPosedMeanChangedWeightCorrectionDeltaMetres':float(delta[delta>1e-8].mean()),'stages':stages})
 out[sex]=results
(O/'blink-finish1-stages-gate.json').write_text(json.dumps({'gate':'PASS','rigSource':'Existing Unity recorded matrices17 sample2; canonical renderer/bone mapping from cloth14-control snapshots','fullBlinkVisibleEyeRays':0,'results':out},indent=2)+'\n');print(json.dumps(out,indent=2))
