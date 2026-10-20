"""Mount the fine pocket opening and fabric lip to the revised trouser surface.
Garment geometry/keys only; all body, weights, rig and actions retained.
"""
import bpy,sys,json,shutil,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));from dcommon import *;from follow_lib import *
w=Path(__file__).resolve().parents[1];path=Path(bpy.data.filepath);bk=w/'rollback/pocket_mount_r24';bk.mkdir(exist_ok=True);shutil.copy2(path,bk/path.name)
rig=bpy.data.objects['Rig_Male'];main=bpy.data.objects['Golf_Trousers'];profile=json.loads(main['GolfCorrectiveProfile']);bones=[b.name for b in rig.data.bones];rest=np.stack([np.array(b.matrix_local.inverted()) for b in rig.data.bones]);rig.data.pose_position='REST';bpy.context.view_layer.update();P=mesh_co(main);T=mesh_tris(main.data);n=len(P)//2;outer=T[~(T>=n).all(1)];tree=bvh_from(P,outer);pockets=[o for o in bpy.data.objects if o.name.startswith(('Golf_PocketLip_','Golf_PocketRecess_'))];inputs={}
def frame(p):
 e=p[1]-p[0];e/=np.linalg.norm(e);normal=np.cross(p[1]-p[0],p[2]-p[0]);normal/=np.linalg.norm(normal);return np.stack([e,np.cross(normal,e),normal],1)
for o in pockets:
 Q=mesh_co(o);assert len(Q)%5==0;homes=[];bc=[];offset=[]
 for start in range(0,len(Q),5):
  center=Q[start:start+5].mean(0);loc,normal,k,d=tree.find_nearest(tuple(center));tri=outer[k];F=frame(P[tri]);b=bary_of(np.array(loc),*P[tri])
  for q in Q[start:start+5]:homes.append(tri);bc.append(b);offset.append(F.T@(q-center))
 inputs[o.name]=(np.array(homes),np.array(bc),np.array(offset),bone_weight_matrix(o,bones),[])
rig.data.pose_position='POSE'
for ai,a in enumerate(profile['anchors']):
 activate_clip(rig,a['action']);bpy.context.scene.frame_set(-1);bpy.context.scene.frame_set(0)
 for k,key in enumerate(profile['anchors'][1:],1):main.data.shape_keys.key_blocks[key['shape']].value=float(ai==k)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();Q=evaluated_co(main,dg);M=np.stack([np.array(rig.matrix_world@rig.pose.bones[b].matrix)@rest[k] for k,b in enumerate(bones)])
 for o in pockets:
  tri,bc,off,weights,targets=inputs[o.name];home=np.einsum('vi,vij->vj',bc,Q[tri]);F=np.stack([frame(q) for q in Q[tri]]);gap=.00035 if 'Lip' in o.name else 0.;target=home+np.einsum('vij,vj->vi',F,off)+F[:,:,2]*gap;S=np.einsum('vb,bij->vij',weights,M);targets.append(np.linalg.solve(S[:,:3,:3],(target-S[:,:3,3])[:,:,None])[:,:,0])
for o in pockets:
 targets=inputs[o.name][-1]
 if o.data.shape_keys:o.shape_key_clear()
 for v,q in zip(o.data.vertices,targets[0]):v.co=q
 o.shape_key_add(name='Basis')
 for k,a in enumerate(profile['anchors'][1:],1):key=o.shape_key_add(name=a['shape']);key.data.foreach_set('co',targets[k].astype(np.float32).ravel())
 o['GolfCorrectiveProfile']=json.dumps(profile)
for key in main.data.shape_keys.key_blocks:key.value=0
activate_clip(rig,'ReadyIdle');bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.save_as_mainfile(filepath=str(w/'export/Golf_Male_Draft.blend'));print('POCKET MOUNT: 4 fine seam components follow the same eight trouser surface anchors; body/rig/weights untouched',flush=True)
