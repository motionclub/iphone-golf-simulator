import bpy,sys,numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import *
from follow_lib import *
sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M'];rig.data.pose_position='REST';bpy.context.view_layer.update();B0=mesh_co(body);BT=mesh_tris(body.data);bt=bvh_from(B0,BT)
def inside(tree,p):
 votes=0
 for d in [(1,.137,.347),(.219,1,.413),(.319,.179,1)]:
  o=Vector(tuple(p));d=Vector(d).normalized();n=0
  for _ in range(64):
   loc,normal,idx,dist=tree.ray_cast(o,d,10)
   if loc is None:break
   n+=1;o=loc+d*.00001
  votes+=n%2
 return votes>=2
for name in ['Golf_Polo']+(['Golf_Trousers'] if sex=='Male' else []):
 o=bpy.data.objects[name];bind=np.array([q.vector[:] for q in o.data.attributes['GolfSourceBind'].data]);ids=np.where(np.linalg.norm(bind,axis=1)>.1)[0];tri=[];bc=[]
 for i in ids:
  loc,n,k,d=bt.find_nearest(tuple(bind[i]));tri.append(BT[k]);bc.append(bary_of(np.array(loc),*B0[BT[k]]))
 tri=np.array(tri);bc=np.array(bc);rig.data.pose_position='POSE';activate_clip(rig,'GolfProof_RH_Top');bpy.context.scene.frame_set(-1);bpy.context.scene.frame_set(0)
 for key in o.data.shape_keys.key_blocks:key.value=float(key.name=='GolfFit_RH_Top')
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();B=evaluated_co(body,dg);N=evaluated_normals(body,dg);Q=evaluated_co(o,dg);tree=bvh_from(B,BT);home=np.einsum('vi,vij->vj',bc,B[tri]);normal=np.einsum('vi,vij->vj',bc,N[tri]);normal/=np.linalg.norm(normal,axis=1)[:,None];cnt=[0,0,0,0];examples=[]
 for k in range(0,len(ids),3):
  plus=inside(tree,home[k]+normal[k]*.0005);minus=inside(tree,home[k]-normal[k]*.0005);cnt[int(plus)+2*int(minus)]+=1
  if plus and not minus and len(examples)<8:examples.append((int(ids[k]),home[k].tolist(),normal[k].tolist(),inside(tree,Q[ids[k]])))
 print(name,'neither/plus/minus/both',cnt,'flipped',examples,flush=True);rig.data.pose_position='REST';bpy.context.view_layer.update()
