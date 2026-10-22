import bpy,sys,json,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import *
from follow_lib import *
sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M'];rig.data.pose_position='REST';bpy.context.view_layer.update();B0=mesh_co(body);BT=mesh_tris(body.data);tree=bvh_from(B0,BT)
for name in ['Golf_Polo']+(['Golf_Trousers'] if sex=='Male' else []):
 o=bpy.data.objects[name];bind=np.array([q.vector[:] for q in o.data.attributes['GolfSourceBind'].data]);ids=np.where(np.linalg.norm(bind,axis=1)>.1)[0];tri=[];bc=[]
 for i in ids:
  loc,n,k,d=tree.find_nearest(tuple(bind[i]));tri.append(BT[k]);bc.append(bary_of(np.array(loc),*B0[BT[k]]))
 tri=np.array(tri);bc=np.array(bc);rig.data.pose_position='POSE';activate_clip(rig,'ReadyIdle');bpy.context.scene.frame_set(-1);bpy.context.scene.frame_set(0)
 for key in o.data.shape_keys.key_blocks:key.value=0
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();B=evaluated_co(body,dg);N=evaluated_normals(body,dg);Q=evaluated_co(o,dg);home=np.einsum('vi,vij->vj',bc,B[tri]);normal=np.einsum('vi,vij->vj',bc,N[tri]);normal/=np.linalg.norm(normal,axis=1)[:,None];D=Q[ids]-home;dot=(D*normal).sum(1);tan=np.linalg.norm(D-normal*dot[:,None],axis=1)
 print(name,'modifiers',[(m.type,getattr(m,'use_deform_preserve_volume',None)) for m in o.modifiers],'lengths',len(Q),len(o.data.vertices),'gapPercentile',np.percentile(dot*1000,[0,1,50,99,100]),'tanMax',tan.max()*1000,flush=True)
 worst=np.argsort(tan)[-6:];print('worst',[(int(ids[k]),float(dot[k]*1000),float(tan[k]*1000),Q[ids[k]].tolist(),home[k].tolist()) for k in worst],flush=True)
 rig.data.pose_position='REST';bpy.context.view_layer.update()
