import bpy,sys,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import mesh_co,evaluated_co,bone_weight_matrix,activate_clip
s=sys.argv[-1];r=bpy.data.objects['Rig_'+s];names=[b.name for b in r.data.bones]
activate_clip(r,'ReadyIdle');bpy.context.scene.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
M=np.stack([np.array(r.matrix_world@r.pose.bones[n].matrix)@np.array(r.data.bones[n].matrix_local.inverted()) for n in names])
for n in ['Body_F' if s=='Female' else 'Body_M','Golf_Polo','Golf_Shoe_L']:
 o=bpy.data.objects[n];w=bone_weight_matrix(o,names);m=np.einsum('vb,bij->vij',w,M);co=mesh_co(o);p=np.einsum('vij,vj->vi',m[:,:3,:3],co)+m[:,:3,3];act=evaluated_co(o,dg)
 print(n,'matrix',np.array(o.matrix_world),'parentInverse',np.array(o.matrix_parent_inverse),'weights',w.sum(1).min(),w.sum(1).max(),'LBS ERROR mm',np.linalg.norm(p-act,axis=1).max()*1000,flush=True)
