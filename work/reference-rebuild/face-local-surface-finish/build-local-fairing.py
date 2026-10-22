"""One male-only local surface candidate. Existing topology/identity, no remesh.
Depth-only quadratic fairing leaves frontal X/Z coordinates exact. All face
feature boundaries, blink-active vertices and silhouette side slopes are fixed.
"""
import bpy,pathlib,json,numpy as np,hashlib,math,collections
from mathutils import Vector
from mathutils.kdtree import KDTree
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-local-surface-finish'
SRC=R/'work/reference-rebuild/original-blink-finish/Male_OriginalSeamBlinkFinish1.blend'
bpy.ops.wm.open_mainfile(filepath=str(SRC));body=bpy.data.objects['Body'];me=body.data;feat=bpy.data.objects['ReferenceFeatures'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
def digest(a):return hashlib.sha256(repr(a).encode()).hexdigest()
def stable(o):
 m=o.data
 return {'topology':digest([(tuple(p.vertices),p.material_index,p.use_smooth) for p in m.polygons]),'uv':digest([[tuple(p.uv) for p in l.data] for l in m.uv_layers]),'color':digest([[tuple(p.color) for p in l.data] for l in m.color_attributes]),'weights':digest([[(g.group,g.weight) for g in v.groups] for v in m.vertices]),'groups':digest([g.name for g in o.vertex_groups])}
def ss(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
old=np.array([tuple(v.co) for v in me.vertices]);shapes={k.name:np.array([tuple(p.co) for p in k.data]) for k in me.shape_keys.key_blocks};featureHash=digest(([tuple(v.co) for v in feat.data.vertices],stable(feat),[[tuple(v.co) for v in k.data] for k in feat.data.shape_keys.key_blocks]));before=stable(body);bones=digest([(b.name,b.parent.name if b.parent else None,tuple(x for row in b.matrix_local for x in row)) for b in rig.data.bones]);me.calc_loop_triangles()
# Weld coordinates only in the calculation, never change the source indexing.
keys={};idx=[];unique=[]
for p in old:
 key=tuple(round(float(q),6) for q in p)
 if key not in keys:keys[key]=len(unique);unique.append(p)
 idx.append(keys[key])
idx=np.array(idx);ps=np.array(unique);n=len(ps);area=np.zeros(n);normal=np.zeros((n,3))
for tri in me.loop_triangles:
 a,b,c=tri.vertices;cross=np.cross(old[b]-old[a],old[c]-old[a])
 for i in (a,b,c):area[idx[i]]+=np.linalg.norm(cross)/6;normal[idx[i]]+=cross
normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
changedBlink=np.any(np.array([np.linalg.norm(p-old,axis=1)>1e-7 for name,p in shapes.items() if name!='Basis']),axis=0)
protectIds=set(np.flatnonzero(changedBlink))
for g in body.vertex_groups:
 if any(s in g.name for s in ('mouth','nostril','ala','lid_margin')):
  protectIds.update(v.index for v in me.vertices if any(w.group==g.index and w.weight>.25 for w in v.groups))
kdprotect=KDTree(len(protectIds))
for k,i in enumerate(sorted(protectIds)):kdprotect.insert(Vector(old[i]),i)
kdprotect.balance();dist=np.array([kdprotect.find(Vector(p))[2] for p in ps]);x,y,z=ps.T
# Protect actual contours for 2.5 mm, fade until 7.5 mm; blink-active geometry
# itself is exact. Side slopes and nose anatomy are also outside this field.
mask=ss(1.452,1.470,z)*(1-ss(1.567,1.578,z))*(1-ss(.064,.079,abs(x)))*(1-ss(-.65,-.32,normal[:,1]))*ss(.0025,.0075,dist)
mask*=np.where(z>1.528,ss(.024,.037,abs(x)),1)
mask*=ss(-.07,-.09,y)
mask[np.unique(idx[changedBlink])]=0
radius=.016;kd=KDTree(n)
for i,p in enumerate(ps):kd.insert(Vector((p[0],0,p[2])),i)
kd.balance();hood={}
for i in np.flatnonzero(mask>0):
 js=np.array([j for _,j,d in kd.find_range(Vector((ps[i,0],0,ps[i,2])),radius) if abs(ps[j,1]-ps[i,1])<.024 and normal[j,1]<-.25])
 q=(ps[js][:,[0,2]]-ps[i,[0,2]])/radius;d2=np.sum(q*q,axis=1);w=(1-d2)**3*area[js];A=np.c_[np.ones(len(js)),q[:,0],q[:,1],q[:,0]**2,q[:,0]*q[:,1],q[:,1]**2]
 hood[i]=(js,A,w)
new=ps.copy();residualBefore=[];residualAfter=[]
for passno in range(2):
 target=new[:,1].copy()
 for i,(js,A,w) in hood.items():
  if len(js)<12:continue
  coefficients=np.linalg.lstsq(A*np.sqrt(w)[:,None],new[js,1]*np.sqrt(w),rcond=None)[0]
  correction=(coefficients[0]-new[i,1])*.80*mask[i]
  if passno==0:residualBefore.append(abs(coefficients[0]-new[i,1]))
  target[i]=np.clip(new[i,1]+correction,ps[i,1]-.0018,ps[i,1]+.0018)
 new[:,1]=target
for i,(js,A,w) in hood.items():
 if len(js)<12:continue
 coefficients=np.linalg.lstsq(A*np.sqrt(w)[:,None],new[js,1]*np.sqrt(w),rcond=None)[0];residualAfter.append(abs(coefficients[0]-new[i,1]))
delta=new[idx]-old
for i,v in enumerate(me.vertices):v.co=old[i]+delta[i]
for k in me.shape_keys.key_blocks:
 for i,p in enumerate(k.data):p.co=shapes[k.name][i]+delta[i]
me.update();assert stable(body)==before
assert featureHash==digest(([tuple(v.co) for v in feat.data.vertices],stable(feat),[[tuple(v.co) for v in k.data] for k in feat.data.shape_keys.key_blocks]))
assert bones==digest([(b.name,b.parent.name if b.parent else None,tuple(x for row in b.matrix_local for x in row)) for b in rig.data.bones])
actual=np.array([tuple(v.co) for v in me.vertices])-old
assert np.max(abs(actual[:,[0,2]]))==0;assert np.max(np.linalg.norm(actual[changedBlink],axis=1))==0
assert np.max(np.linalg.norm(actual[list(protectIds)],axis=1))==0
shapeErrors={k.name:float(np.max(np.linalg.norm((np.array([tuple(p.co) for p in k.data])-np.array([tuple(v.co) for v in me.vertices]))-(shapes[k.name]-old),axis=1))) for k in me.shape_keys.key_blocks}
assert max(shapeErrors.values())<1e-7
ds=np.linalg.norm(actual,axis=1);moved=ds>1e-8
def silhouetteProjection(angle):
 a=math.radians(angle);oldU=old[:,0]*math.cos(a)+old[:,1]*math.sin(a);newU=(old+actual)[:,0]*math.cos(a)+(old+actual)[:,1]*math.sin(a);ids=np.flatnonzero((old[:,2]>1.44)&(old[:,2]<1.69));shifts=[]
 for lo in np.linspace(1.44,1.688,250):
  js=ids[(old[ids,2]>=lo)&(old[ids,2]<lo+.002)]
  if len(js):shifts.extend((abs(float(oldU[js].min()-newU[js].min())),abs(float(oldU[js].max()-newU[js].max()))))
 return {'projectionAngleDegrees':angle,'maxOutlineBinShiftMetres':max(shifts),'meanOutlineBinShiftMetres':sum(shifts)/len(shifts),'binWidthMetres':.002}
report={'gate':'SOURCE INVARIANTS PASS; ART/UNITY PENDING','sex':'Male','female':'Unchanged; broad nose/lips do not justify smoothing','source':str(SRC),'candidate':str(O/'Male_OriginalSeamLocalSurfaceFinish1.blend'),'recipe':{'quadraticRadiusMetres':radius,'passes':2,'strength':.8,'maxDepthDeltaMetres':.0018,'frontDepthOnly':True,'protectedRadiusMetres':.0025,'protectedFadeEndMetres':.0075,'field':'Front cheek / outside mouth corners / lower jaw; nose / silhouette sides / eyelid and lip essential boundaries excluded'},'vertices':len(old),'movedVertices':int(moved.sum()),'movedBounds':[[float((old+actual)[moved,k].min()),float((old+actual)[moved,k].max())] for k in range(3)],'displacement':{'maxMetres':float(ds.max()),'meanMovedMetres':float(ds[moved].mean()),'p95MovedMetres':float(np.percentile(ds[moved],95))},'protectedVertexCount':len(protectIds),'protectedVertexMaxDeltaMetres':float(ds[list(protectIds)].max()),'blinkActiveVertexCount':int(changedBlink.sum()),'blinkActiveMaxDeltaMetres':float(ds[changedBlink].max()),'shapeDeltaMaxErrorsMetres':shapeErrors,'boneCount':len(rig.data.bones),'weightsTopologyUvPigmentExact':stable(body)==before,'featuresAllPositionsShapesExact':True,'bonesRestHierarchyExact':True,'frontXZExact':True,'silhouette':[silhouetteProjection(a) for a in (0,20,45,90)],'localQuadraticResidualBeforeMeanMetres':float(np.mean(residualBefore)),'localQuadraticResidualAfterMeanMetres':float(np.mean(residualAfter)),'invariantHashes':before,'changedVertices':[{'index':int(i),'depthDeltaMetres':float(actual[i,1])} for i in np.flatnonzero(moved)]}
(O/'source-gate.json').write_text(json.dumps(report,indent=2)+'\n');np.savez_compressed(O/'source-geometry.npz',before=old,after=old+actual,triangles=np.array([tuple(t.vertices) for t in me.loop_triangles]))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Male_OriginalSeamLocalSurfaceFinish1.blend'))
for ob in bpy.context.scene.objects:ob.select_set(ob.name in ('Body','ReferenceFeatures') or ob.type=='ARMATURE')
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.fbx(filepath=str(O/'Male_OriginalSeamLocalSurfaceFinish1.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=False,mesh_smooth_type='OFF',add_leaf_bones=False,bake_anim=False,path_mode='STRIP',use_armature_deform_only=False)
print(json.dumps({k:v for k,v in report.items() if k not in ('changedVertices','invariantHashes')},indent=2),flush=True)
