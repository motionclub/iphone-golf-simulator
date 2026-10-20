import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent));from dcommon import *;from follow_lib import *
sex=sys.argv[-1];w=Path(__file__).resolve().parents[1];rig=bpy.data.objects['Rig_'+sex];activate_clip(rig,'ReadyIdle');bpy.context.scene.frame_set(-1);bpy.context.scene.frame_set(0)
objs=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Golf_') and o.name!='Golf_Glove_Right']
for o in objs:
 if o.data.shape_keys:
  for k in o.data.shape_keys.key_blocks:k.value=0
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();V=[];F=[];owner=[]
for o in objs:
 Q=evaluated_co(o,dg);T=mesh_tris(o.data);F.extend((T+len(V)).tolist());V.extend(Q.tolist());owner.extend([o.name]*len(T))
V=np.array(V);F=np.array(F);tree=bvh_from(V,F)
for dist,p,n in json.loads((w/f'data/visible_body_poke_interior_{sex}_r22.json').read_text())['poses'][0]['worst'][:5]:
 p=Vector(p);n=Vector(n);q,nq,k,d=tree.find_nearest(p);print('P',list(p),'N',list(n),'Q',list(q),'Ddot',float((q-p).dot(n)),'piece',owner[k],'face',F[k].tolist(),flush=True)
 for direction in [n,-n,(q-p).normalized()]:print('ray',list(direction),tree.ray_cast(p+direction*.00003,direction,10),flush=True)
