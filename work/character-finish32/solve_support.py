exec(open('work/character-finish32/solve_clearance.py').read().split('poses=[]')[0])
from mathutils.geometry import barycentric_transform
restTree=BVHTree.FromPolygons([Vector(v) for v in BP],BT.tolist(),all_triangles=True)
samples=np.concatenate([P[ids],P[FT].mean(1)]);supportIds=[];bary=[]
for p in samples:
 hit,n,fi,dist=restTree.find_nearest(Vector(p));tri=BT[fi];bc=barycentric_transform(hit,*[Vector(BP[j]) for j in tri],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));supportIds.append(tri);bary.append(tuple(bc))
supportIds=np.array(supportIds);bary=np.array(bary);poses=[]
for file in sorted((d/'matrices').glob('*.json')):
 report=json.loads(file.read_text());parts={p['name']:p for p in report['parts']};ms=np.array(parts[top['name']]['skinMatrices']).reshape(-1,4,4);bs=np.array(parts[body['name']]['skinMatrices']).reshape(-1,4,4)
 M=np.sum(ms[BI]*BW[:,:,None,None],axis=1);BM=np.sum(bs[BBI]*BBW[:,:,None,None],axis=1);BPos=np.einsum('nij,nj->ni',BM[:,:3,:3],BP)+BM[:,:3,3];BNormal=np.einsum('nij,nj->ni',BM[:,:3,:3],BN);BNormal/=np.maximum(1e-10,np.linalg.norm(BNormal,axis=1))[:,None]
 support=(BPos[supportIds]*bary[:,:,None]).sum(1);norm=(BNormal[supportIds]*bary[:,:,None]).sum(1);norm/=np.maximum(1e-10,np.linalg.norm(norm,axis=1))[:,None]
 poses.append((file.stem,M,support,norm))
print('SUPPORT POSES',len(poses),'SAMPLES',len(samples),flush=True);rows=[]
for iteration in range(14):
 corrections=np.zeros_like(P);score=np.zeros(len(P));worst=0;bad=0
 for label,M,support,norm in poses:
  q=np.einsum('nij,nj->ni',M[:,:3,:3],P)+M[:,:3,3];sample=np.concatenate([q[ids],q[FT].mean(1)]);signed=((sample-support)*norm).sum(1);need=np.maximum(0,.005-signed);bad+=int(np.count_nonzero(signed<0));worst=max(worst,float(-signed.min()))
  accum=np.zeros_like(P);cnt=np.zeros(len(P));g=np.einsum('nji,nj->ni',M[ids,:3,:3],norm[:len(ids)]);dv=g*(need[:len(ids)]/np.maximum(1e-8,(g*g).sum(1)))[:,None];accum[ids]=dv;cnt[ids]=(need[:len(ids)]>0)
  use=np.flatnonzero(need[len(ids):]>0);f=FT[use];nn=norm[len(ids):][use];nf=need[len(ids):][use]
  for j in range(3):
   grad=np.einsum('nji,nj->ni',M[f[:,j],:3,:3],nn);dv=grad*(nf/np.maximum(1e-8,(grad*grad).sum(1)))[:,None];np.add.at(accum,f[:,j],dv);np.add.at(cnt,f[:,j],1)
  delta=accum/np.maximum(1,cnt[:,None]);size=np.linalg.norm(delta,axis=1);win=size>score;corrections[win]=delta[win];score[win]=size[win]
 for _ in range(2):
  acc=np.zeros_like(P);np.add.at(acc,ea,corrections[eb]);corrections=.80*corrections+.20*acc/np.maximum(ec[:,None],1)
 synced=np.zeros((aliasN,3));np.add.at(synced,alias,corrections);corrections=(synced/aliasCount[:,None])[alias];corrections*=active[:,None];length=np.linalg.norm(corrections,axis=1);corrections*=np.minimum(1,.003/np.maximum(length,1e-10))[:,None];P+=corrections
 row={'iteration':iteration,'negativeSupportSamples':bad,'maxSupportDepthMm':worst*1000,'maxSourceChangeMm':float(np.linalg.norm(P-original,axis=1).max()*1000)};rows.append(row);print(json.dumps(row),flush=True)
(w/'support-report.json').write_text(json.dumps(rows,indent=2));np.savez(w/'support-result.npz',original=original,positions=P)
bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Sleeve.blend'));o=bpy.data.objects['Kit_Top'];m=o.data;rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');kd=KDTree(len(original))
for i,p in enumerate(original):kd.insert(Vector((-p[0],p[1],p[2])),i)
kd.balance()
for v in m.vertices:
 _,i,error=kd.find(v.co)
 if error>3e-6:raise RuntimeError('Source correspondence '+str(error))
 delta=P[i]-original[i];v.co+=Vector((-delta[0],delta[1],delta[2]))
m.update()
if m.has_custom_normals:bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.mesh.customdata_custom_splitnormals_clear()
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Polo_Support.blend'))
bpy.ops.export_scene.fbx(filepath=str(r/'Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
