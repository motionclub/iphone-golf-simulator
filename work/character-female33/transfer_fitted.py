import bpy,bmesh,json,numpy as np,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from mathutils.geometry import barycentric_transform
w=Path('work/character-female33');male=Path('work/character-finish32');bpy.ops.wm.open_mainfile(filepath=str(male/'Male_Polo_CuffRebuilt.blend'));o=bpy.data.objects['Kit_Top'];mr=next(x for x in bpy.data.objects if x.type=='ARMATURE');P=np.array([v.co for v in o.data.vertices]);VN=np.array([v.normal for v in o.data.vertices]);F=[list(f.vertices) for f in o.data.polygons];FM=[f.material_index for f in o.data.polygons];UV=[tuple(v.uv) for v in o.data.uv_layers.active.data];roles=[x.name for x in o.data.materials];names=[x.name for x in o.vertex_groups];weights=[[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in o.data.vertices];MB={b.name:np.array(mr.matrix_world@b.matrix_local) for b in mr.data.bones};ML={b.name:(b.tail_local-b.head_local).length for b in mr.data.bones}
# The accepted male garment is the template, including its clean collar/placket/cuffs.
adj=[set() for _ in P]
for face in F:
 for a,b in zip(face,face[1:]+face[:1]):adj[a].add(b);adj[b].add(a)
seen=set();components=[]
for i in range(len(P)):
 if i in seen:continue
 seen.add(i);todo=[i];part=[]
 while todo:
  a=todo.pop();part.append(a)
  for b in adj[a]:
   if b not in seen:seen.add(b);todo.append(b)
 components.append(part)
main=set(max(components,key=len));mainfaces=[f for f in F if all(i in main for i in f)];maleTree=BVHTree.FromPolygons([Vector(p) for p in P],mainfaces,all_triangles=True)
bpy.ops.wm.open_mainfile(filepath=str(w/'Female_Baseline.blend'));rig=next(x for x in bpy.data.objects if x.type=='ARMATURE');FB={b.name:np.array(rig.matrix_world@b.matrix_local) for b in rig.data.bones};FL={b.name:(b.tail_local-b.head_local).length for b in rig.data.bones};transforms={}
for name in names:
 if name not in MB or name not in FB:raise ValueError('Garment bone missing '+name)
 cross=.77 if name in ['Hips','Spine','Chest'] else .84 if name in ['Neck','Head'] else .76 if 'Shoulder' in name else .73 if 'Arm' in name else .80
 along=np.clip(FL[name]/ML[name],.7,1.3);scale=np.diag([cross,along,cross,1.]);transforms[name]=FB[name]@scale@np.linalg.inv(MB[name])
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
Q=P.copy();Q[:,0]*=.78;Q[:,1]=P[:,1]*.86+.025;Q[:,2]-=.020*smooth(1.03,1.40,P[:,2])
for side,sign in [('Left',1),('Right',-1)]:
 name=side+'UpperArm';ma=MB[name][:3,3];fa=FB[name][:3,3];maxis=MB[side+'LowerArm'][:3,3]-ma;faxis=FB[side+'LowerArm'][:3,3]-fa;length=np.linalg.norm(faxis)/np.linalg.norm(maxis);maxis/=np.linalg.norm(maxis);faxis/=np.linalg.norm(faxis);rot=np.array(Vector(maxis).rotation_difference(Vector(faxis)).to_matrix());local=P-ma;axial=(local@maxis)[:,None]*maxis;arm=(local-axial)*.73+axial*length;arm=arm@rot.T+fa;mix=smooth(.14,.28,P[:,0]*sign)*smooth(1.06,1.20,P[:,2]);Q=Q*(1-mix[:,None])+arm*mix[:,None]
Q[:,1]-=.018*smooth(1.23,1.33,P[:,2])*(1-smooth(1.43,1.47,P[:,2]))*(1-smooth(-.09,-.015,P[:,1]))
N=VN.copy()
raw=Q.copy();body=json.loads((w/'baseline/poses/female_intro.json').read_text())['parts'][0];BP=np.array(body['vertices']).reshape(-1,3);BN=np.array(body['normals']).reshape(-1,3);BT=np.array(body['triangles']).reshape(-1,3).tolist();root=np.array(body['rendererToRoot']).reshape(4,4);rootP=BP@root[:3,:3].T+root[:3,3];tree=KDTree(len(BP))
for i,p in enumerate(rootP):tree.insert(Vector(p),i)
tree.balance();coverage=json.loads(Path('Unity/Assets/Resources/Tennis/GarmentCoverage/Tennis_Female.json').read_text());recovered=0
for tri in np.array(coverage['removedTriangleRootPositions']).reshape(-1,3,3):
 hits=[tree.find(Vector(p)) for p in tri]
 if max(hit[2] for hit in hits)>2e-5:raise ValueError('Existing coverage vertex no longer matches body')
 BT.append([h[1] for h in hits]);recovered+=1
BP[:,0]*=-1;BN[:,0]*=-1;BT=[t[::-1] for t in BT];bodyTree=BVHTree.FromPolygons([Vector(p) for p in BP],BT,all_triangles=True)
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
# Keep her existing waist overlap instead of copying the male hem height.
mainIds=np.array(sorted(main));low=Q[mainIds,2].min();Q[mainIds,2]+=(.9752-low)*(1-smooth(low+.02,low+.12,Q[mainIds,2]));corrected=0;largest=0
for i in mainIds:
 q=Vector(Q[i]);hit,_,fi,dist=bodyTree.find_nearest(q)
 if dist>.040:continue
 ids=BT[fi];bc=barycentric_transform(hit,*[Vector(BP[j]) for j in ids],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));n=sum((Vector(BN[j])*a for j,a in zip(ids,bc)),Vector()).normalized();clearance=-100;sd=(q-hit).dot(n)
 if sd<clearance:
  move=min(.018,clearance-sd);Q[i]+=np.array(n)*move;largest=max(largest,move);corrected+=1
# Small construction pieces retain the template's geometry and ride on her fitted shirt.
for group in components:
 if len(group)==len(main):continue
 for i in group:
  hit,normal,fi,dist=maleTree.find_nearest(Vector(P[i]))
  if dist>.055:continue
  ids=mainfaces[fi];bc=barycentric_transform(hit,*[Vector(P[j]) for j in ids],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));Q[i]+=sum((Q[j]-raw[j])*a for j,a in zip(ids,bc))
# Replace only Kit_Top in the female authoring file. The female rig is retained exactly.
old=bpy.data.objects['Kit_Top'];bpy.data.objects.remove(old,do_unlink=True);mesh=bpy.data.meshes.new('FemalePoloTransferred');mesh.from_pydata(Q.tolist(),[],F);mesh.update();top=bpy.data.objects.new('Kit_Top',mesh);bpy.context.collection.objects.link(top)
for role in roles:mesh.materials.append(bpy.data.materials.get(role) or bpy.data.materials.new(role))
for poly,role in zip(mesh.polygons,FM):poly.material_index=role;poly.use_smooth=True
uv=mesh.uv_layers.new(name='UVMap')
if len(uv.data)!=len(UV):raise ValueError('Template UV layout changed')
for loop,value in zip(uv.data,UV):loop.uv=value
for name in names:top.vertex_groups.new(name=name)
for i,row in enumerate(weights):
 for name,value in row:top.vertex_groups[name].add([i],float(value),'REPLACE')
mod=top.modifiers.new('Armature','ARMATURE');mod.object=rig;top.parent=rig
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update();bpy.ops.object.select_all(action='DESELECT');top.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=top
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Female_Polo_Fitted.blend'));bpy.ops.export_scene.fbx(filepath=str(w/'FemalePolo.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
report={'template':'Male_Polo_CuffRebuilt.blend','vertices':len(P),'triangles':len(F),'mainVertices':len(main),'fitAdjustedVertices':corrected,'maxFitDeltaMm':largest*1000,'recoveredExistingBodyTrianglesForOfflineFit':recovered,'bodyChanged':False,'rigChanged':False,'uvTemplateExact':True,'colorsCustomizable':True,'components':len(components)};(w/'transfer-source-report.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
