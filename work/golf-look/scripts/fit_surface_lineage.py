"""Continuous garment fit against corresponding locked-body triangles.
No remeshing, weight, bone, identity or clip changes. Only garment keys.
"""
import bpy,sys,json,shutil,numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import mesh_co,mesh_tris,bone_weight_matrix,evaluated_co,activate_clip
from follow_lib import bvh_from,bary_of,evaluated_normals
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M'];path=Path(bpy.data.filepath);backup=W/'rollback/surface_lineage_r20'/path.name;backup.parent.mkdir(exist_ok=True);shutil.copy2(path,backup)
rig.data.pose_position='REST';bpy.context.view_layer.update();B0=mesh_co(body);BT=mesh_tris(body.data);tree=bvh_from(B0,BT);bones=[b.name for b in rig.data.bones];rest=np.stack([np.array(b.matrix_local.inverted()) for b in rig.data.bones]);profile=json.loads(bpy.data.objects['Golf_Polo']['GolfCorrectiveProfile']);objects=[bpy.data.objects['Golf_Polo']]+([bpy.data.objects['Golf_Trousers']] if sex=='Male' else [])
source={};reports=[]
for o in objects:
 P=mesh_co(o);tris=mesh_tris(o.data);n=len(P);ids=[];home=[];bary=[];ease=[]
 if o.name=='Golf_Polo':
  attr=o.data.attributes['GolfSourceBind'];bind=np.array([q.vector[:] for q in attr.data]);outer=o.data.attributes['GolfOuterFace'];o.data.calc_loop_triangles();outside=set(i for q in o.data.loop_triangles if outer.data[q.polygon_index].value==1 for i in q.vertices)
  selected=np.where(np.linalg.norm(bind,axis=1)>.1)[0]
 else:
  selected=range(n);bind=np.array([q.vector[:] for q in o.data.attributes['GolfSourceBind'].data])
 for i in selected:
  loc,norm,k,d=tree.find_nearest(tuple(bind[i]));t=BT[k];bc=bary_of(np.array(loc),*B0[t]);ids.append(i);home.append(t);bary.append(bc)
  if o.name=='Golf_Polo':gap=.010 if i in outside else .008
  else:
   # Normal shell ease, with a narrow corresponding-body crotch seam.
   gap=.006 if abs(B0[t].mean(0)[0])<.065 and .65<B0[t].mean(0)[2]<.95 else .022
   if i>=n//2:gap-=.0022
  ease.append(gap)
 source[o.name]=(np.array(ids),np.array(home),np.array(bary),np.array(ease),bone_weight_matrix(o,bones),[])
rig.data.pose_position='POSE'
for ai,a in enumerate(profile['anchors']):
 activate_clip(rig,a['action']);bpy.context.scene.frame_set(-1);bpy.context.scene.frame_set(0)
 for o in objects:
  if o.data.shape_keys:
   for k,key in enumerate(profile['anchors'][1:],1):
    if key['shape'] in o.data.shape_keys.key_blocks:o.data.shape_keys.key_blocks[key['shape']].value=float(ai==k)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();B=evaluated_co(body,dg);BN=evaluated_normals(body,dg);M=np.stack([np.array(rig.matrix_world@rig.pose.bones[n].matrix)@rest[k] for k,n in enumerate(bones)])
 for o in objects:
  ids,tri,bc,gap,weights,target=source[o.name];Q=evaluated_co(o,dg);home=np.einsum('vi,vij->vj',bc,B[tri]);N=np.einsum('vi,vij->vj',bc,BN[tri]);N/=np.maximum(np.linalg.norm(N,axis=1)[:,None],1e-10)
  Q[ids]=home+N*gap[:,None];S=np.einsum('vb,bij->vij',weights,M);P=np.linalg.solve(S[:,:3,:3],(Q-S[:,:3,3])[:,:,None])[:,:,0];target.append(P)
  reports.append(dict(action=a['action'],piece=o.name,sourceVertices=len(ids),homeClearanceMm=float(gap.min()*1000)))
for o in objects:
 target=source[o.name][-1];
 if o.data.shape_keys:o.shape_key_clear()
 for v,p in zip(o.data.vertices,target[0]):v.co=p
 o.shape_key_add(name='Basis')
 for k,a in enumerate(profile['anchors'][1:],1):key=o.shape_key_add(name=a['shape']);key.data.foreach_set('co',target[k].astype('float32').ravel());key.value=0
 o['GolfCorrectiveProfile']=json.dumps(profile)
activate_clip(rig,'ReadyIdle');bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.save_as_mainfile(filepath=str(W/f'export/Golf_{sex}_Draft.blend'))
(W/f'data/lineage_fit_{sex}_r19.json').write_text(json.dumps(dict(rows=reports,status='candidate; visual, complete coverage and cross-body collision checks pending'),indent=2))
