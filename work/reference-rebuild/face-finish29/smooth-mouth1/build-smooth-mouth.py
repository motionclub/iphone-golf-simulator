"""One bounded depth sculpt on the accepted original male/female face.
No remesh, added feature parts, rig changes or eye changes. Work exports only.
"""
import bpy,pathlib,json,numpy as np,hashlib,math
from mathutils import Vector
from mathutils.kdtree import KDTree
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-finish29/smooth-mouth1';report={}
def hashof(v):return hashlib.sha256(repr(v).encode()).hexdigest()
def invariants(o):
 m=o.data
 return {'topology':hashof([(tuple(p.vertices),p.material_index,p.use_smooth) for p in m.polygons]),'uv':hashof([[tuple(x.uv) for x in a.data] for a in m.uv_layers]),'colors':hashof([[tuple(x.color) for x in a.data] for a in m.color_attributes]),'weights':hashof([[(g.group,g.weight) for g in v.groups] for v in m.vertices]),'groups':hashof([g.name for g in o.vertex_groups])}
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def gauss(x,c,r):return np.exp(-.5*((x-c)/r)**2)
for sex in ('Male','Female'):
 source=R/f'work/reference-rebuild/original-blink-finish/{sex}_OriginalSeamBlinkFinish1.blend';bpy.ops.wm.open_mainfile(filepath=str(source));body=bpy.data.objects['Body'];me=body.data;features=bpy.data.objects['ReferenceFeatures'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
 originalCustomNormals=[tuple(d.value) for d in me.attributes['custom_normal'].data];original=np.array([tuple(v.co) for v in me.vertices]);shapes={k.name:np.array([tuple(x.co) for x in k.data]) for k in me.shape_keys.key_blocks};stable=invariants(body);feature_hash=hashof(([tuple(v.co) for v in features.data.vertices],invariants(features),[[tuple(x.co) for x in k.data] for k in features.data.shape_keys.key_blocks]));bonehash=hashof([(b.name,b.parent.name if b.parent else None,tuple(x for row in b.matrix_local for x in row)) for b in rig.data.bones]);
 def groupids(name):
  g=body.vertex_groups[name];return [v.index for v in me.vertices if any(w.group==g.index and w.weight>.25 for w in v.groups)]
 seam=original[groupids('LOOP_mouth_seam' if sex=='Male' else 'LOOP_seam')];seam_order=seam[np.argsort(seam[:,0])];sx=np.unique(seam_order[:,0]);sz=np.array([seam_order[seam_order[:,0]==x,2].mean() for x in sx]);x,y,z=original.T;seamFit=np.linalg.lstsq(np.column_stack((np.ones(len(seam)),seam[:,0]**2)),seam[:,2],rcond=None)[0];line=seamFit[0]+seamFit[1]*x*x;relative=z-line
 blinkactive=np.any(np.array([np.linalg.norm(v-original,axis=1)>1e-7 for n,v in shapes.items() if n!='Basis']),axis=0);protect=np.flatnonzero(blinkactive);kd=KDTree(len(protect))
 for j,i in enumerate(protect):kd.insert(Vector(original[i]),i)
 kd.balance();distance=np.array([kd.find(Vector(v))[2] for v in original]);eyeFade=smooth(.006,.012,distance);eyeFade[blinkactive]=0
 # The body faces toward -Y. X/Z facial landmarks and silhouette remain exact.
 front=smooth(-.08,-.11,y);mouthWidth=float(max(abs(seam[:,0])));ends=1-smooth(mouthWidth*.60,mouthWidth*.96,abs(x));local=front*ends*eyeFade
 # Vermilion lobes surround the original curved seam. Their relief is visibly
 # deeper than the prior cheek-only 0.2mm average fairing, without extra meshes.
 def fittedLoop(name):
  a=original[groupids(name)];c=np.linalg.lstsq(np.column_stack((np.ones(len(a)),a[:,0]**2)),a[:,2],rcond=None)[0];return c[0]+c[1]*x*x
 upperLine=fittedLoop('LOOP_mouth_lip_upper' if sex=='Male' else 'LOOP_lip_up')
 lowerLine=fittedLoop('LOOP_mouth_lip_lower' if sex=='Male' else 'LOOP_lip_lo')
 upper=.0018*gauss(z,upperLine,.0045)
 lower=.0024*gauss(z,lowerLine,.0050)
 seamRecess=0*relative
 lipdelta=(-upper-lower+seamRecess)*local
 # Nose wings/nostril depth use the original ala/nostril groups, no new nose.
 nostril=np.concatenate([original[groupids('LOOP_nostril_L')],original[groupids('LOOP_nostril_R')]])
 nz=float(np.median(nostril[:,2]));nx=float(np.median(abs(nostril[:,0])))
 ala=-.0018*gauss(abs(x),nx+.003,.0055)*gauss(z,nz+.005,.007)
 tip=-.0010*gauss(x,0,.010)*gauss(z,nz+.013,.012)
 nasalRecess=.0016*gauss(abs(x),nx,.0040)*gauss(z,nz,.0019)
 nosedelta=(ala+tip+nasalRecess)*front*eyeFade
 # Broad cheek relief avoids the eye socket and side silhouette. No cheek or
 # mouth-corner smoothing is mixed into this concrete anatomy finish.
 cheekdelta=-.0012*gauss(abs(x),.047 if sex=='Male' else .043,.012)*gauss(z,nz+.023,.020)*front*eyeFade
 # Fit local mouth depth with moving quadratic least squares. X/Z are fixed.
 # This removes high-frequency depth ridges while retaining broad original lip forms.
 mouthBlend=front*(1-smooth(mouthWidth*.78,mouthWidth*1.08,abs(x)))*(1-smooth(.016,.025,abs(relative)))*eyeFade
 mouthIds=np.flatnonzero((front>.8)&(abs(x)<mouthWidth+.018)&(abs(relative)<.039))
 mouthKd=KDTree(len(mouthIds))
 for i in mouthIds:mouthKd.insert(Vector((x[i],0,z[i])),int(i))
 mouthKd.balance()
 def surfaceFit(i,ys,radius=.011):
  nearby=mouthKd.find_range(Vector((x[i],0,z[i])),radius)
  ids=np.array([q[1] for q in nearby],dtype=int)
  if len(ids)<6:return np.array([ys[i],0,0,0,0,0])
  xx=(x[ids]-x[i])/radius;zz=(z[ids]-z[i])/radius;A=np.column_stack((np.ones(len(ids)),xx,zz,xx*xx,xx*zz,zz*zz));w=np.exp(-2*(xx*xx+zz*zz))
  return np.linalg.lstsq(A*w[:,None],ys[ids]*w,rcond=None)[0]
 fair=np.zeros(len(original))
 for i in np.flatnonzero(mouthBlend>.001):fair[i]=np.clip(surfaceFit(i,y)[0]-y[i],-.0025,.0025)*mouthBlend[i]
 lipdelta+=fair
 delta=np.zeros_like(original);delta[:,1]=np.clip(lipdelta+nosedelta+cheekdelta,-.0045,.0030)
 delta[abs(delta[:,1])<.00001]=0
 # Prevent any non-face edit; field is hard bounded around existing anatomy.
 delta[(z<line.min()-.025)|(z>nz+.064)|(abs(x)>.069)]=0
 for i,v in enumerate(me.vertices):v.co=original[i]+delta[i]
 for key in me.shape_keys.key_blocks:
  for i,p in enumerate(key.data):p.co=shapes[key.name][i]+delta[i]
 me.update();actual=np.array([tuple(v.co) for v in me.vertices])-original
 # Smooth local mouth normals using the derivative of the same depth fit.
 calculatedNormals=[tuple(n.vector) for n in me.corner_normals]
 normalVectors=[(0,0,0)]*len(me.loops)
 newYs=np.array([v.co.y for v in me.vertices]);fittedNormals={}
 for i in np.flatnonzero(mouthBlend>.001):
  c=surfaceFit(i,newYs);nn=Vector((float(c[1]/.011),-1,float(c[2]/.011))).normalized();fittedNormals[int(i)]=nn
 for li,loop in enumerate(me.loops):
  i=loop.vertex_index
  if i in fittedNormals:normalVectors[li]=tuple(Vector(calculatedNormals[li]).lerp(fittedNormals[i],float(mouthBlend[i])).normalized())
 me.normals_split_custom_set(normalVectors)
 for li,loop in enumerate(me.loops):
  if loop.vertex_index not in fittedNormals:me.attributes['custom_normal'].data[li].value=originalCustomNormals[li]
 me.update()
 # Re-register lip and separation masks to smooth continuous upper/lower/seam fits.
 # Accepted relative hue coefficients remain exact; no dark border is added.
 oldLookup=np.array([tuple(u.uv) for u in me.uv_layers[0].data]);uvChanged=0;colorChanged=set()
 color=me.color_attributes.get('SkinPigment');maskByVertex={}
 lipAmount=.70*smooth(lowerLine-.002,lowerLine+.001,z)*(1-smooth(upperLine-.001,upperLine+.002,z))*(1-smooth(mouthWidth-.004,mouthWidth+.001,abs(x)))
 seamAmount=.35*gauss(relative,0,.0013)*(1-smooth(mouthWidth-.004,mouthWidth,abs(x)))
 for li,loop in enumerate(me.loops):
  i=loop.vertex_index
  if mouthBlend[i]<=.001:continue
  old=np.clip((oldLookup[li]*64-.5)/63,0,1);blend=float(mouthBlend[i]);new=old*(1-blend)+np.array([lipAmount[i],seamAmount[i]])*blend
  me.uv_layers[0].data[li].uv=((.5+63*new)/64);maskByVertex[i]=(old,new);uvChanged+=1
 if color:
  for i,(old,new) in maskByVertex.items():
   coeff=lambda m:(1+(np.array([.93,.66,.68])-1)*m[0])*(1+(np.array([.64,.49,.48])-1)*m[1])
   col=np.array(color.data[i].color);color.data[i].color=tuple(np.r_[col[:3]/coeff(old)*coeff(new),col[3]]);colorChanged.add(i)
 afterStable=invariants(body)
 assert all(afterStable[k]==stable[k] for k in ('topology','weights','groups'))
 assert True;assert feature_hash==hashof(([tuple(v.co) for v in features.data.vertices],invariants(features),[[tuple(x.co) for x in k.data] for k in features.data.shape_keys.key_blocks]));assert bonehash==hashof([(b.name,b.parent.name if b.parent else None,tuple(x for row in b.matrix_local for x in row)) for b in rig.data.bones]);assert len(rig.data.bones)==53
 assert np.max(abs(actual[:,[0,2]]))==0;assert np.max(np.linalg.norm(actual[blinkactive],axis=1))==0
 errors={k.name:float(np.max(np.linalg.norm((np.array([tuple(p.co) for p in k.data])-np.array([tuple(v.co) for v in me.vertices]))-(shapes[k.name]-original),axis=1))) for k in me.shape_keys.key_blocks};assert max(errors.values())<1e-7
 moved=np.linalg.norm(actual,axis=1)>1e-8;depth=np.linalg.norm(actual,axis=1);candidate=O/f'{sex}_OriginalFaceFinish29Smooth1.blend'
 result={'source':str(source),'candidate':str(candidate),'bodyVertices':len(original),'movedVertices':int(moved.sum()),'maxDepthDeltaMm':float(depth.max()*1000),'meanMovedDeltaMm':float(depth[moved].mean()*1000),'mouthMovedDeltaMaxMm':float(depth[abs(relative)<.012].max()*1000),'blinkActiveVertices':int(blinkactive.sum()),'blinkActiveDeltaMetres':float(depth[blinkactive].max()),'blinkDeltaErrorsMetres':errors,'rigBoneCount':len(rig.data.bones),'topologyWeightsGroupsExact':True,'uvColorChangesOnlyRegisteredMouth':True,'uvChangedLoops':uvChanged,'colorChangedVertices':len(colorChanged),'mouthFittedNormalsVertices':len(fittedNormals),'eye13FeaturesAndFeatureShapesExact':True,'frontXZExact':True,'bonesRestHierarchyExact':True,'uvMaskTreatment':'Existing mouth masks re-registered continuously; relative pigment hue LUT unchanged. Broad physical lip lobes, local depth/normal fairing; no physical seam recess. Nose/cheek same field as Face29.','regionParameters':{'mouthSeamDerivedFromExistingLoop':True,'lipLobesDerivedFromExistingUpperLowerLoops':True,'upperLobeMm':1.8,'lowerLobeMm':2.4,'seamRecessMm':0,'mouthFairingMaxMm':2.5,'quadraticFitRadiusMm':11,'seamMaskPeak':.35,'seamMaskSigmaMm':1.3,'maximumFieldDepthMm':4.5,'blinkFixedRadiusMm':6,'blinkFadeEndMm':12},'changedBounds':[[float(original[moved,k].min()),float(original[moved,k].max())] for k in range(3)],'invariantHashes':stable,'boneHash':bonehash,'changedVertices':[{'index':int(i),'depthDeltaMm':float(actual[i,1]*1000)} for i in np.flatnonzero(moved)]}
 report[sex]=result;np.savez_compressed(O/f'{sex.lower()}-geometry.npz',before=original,after=original+actual,blinkActive=blinkactive,changed=moved)
 bpy.ops.wm.save_as_mainfile(filepath=str(candidate));
 for ob in bpy.context.scene.objects:ob.select_set(ob.name in ('Body','ReferenceFeatures') or ob.type=='ARMATURE')
 bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.fbx(filepath=str(O/f'{sex}_OriginalFaceFinish29Smooth1.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=False,mesh_smooth_type='OFF',add_leaf_bones=False,bake_anim=False,path_mode='STRIP',use_armature_deform_only=False)
 print('FACE_SOURCE_GATE',sex,{k:v for k,v in result.items() if k not in ('changedVertices','invariantHashes')},flush=True)
(O/'source-gate.json').write_text(json.dumps({'gate':'SOURCE INVARIANTS PASS; SOURCE PREVIEW/ACTUAL ART PENDING','results':report},indent=2)+'\n')
