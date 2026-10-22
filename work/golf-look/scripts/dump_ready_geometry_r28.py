import bpy,sys,json,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import *
w=Path(__file__).resolve().parents[1];rig=bpy.data.objects['Rig_Male'];body=bpy.data.objects['Body_M'];rig.data.pose_position='REST';bpy.context.view_layer.update();B0=mesh_co(body)
rig.data.pose_position='POSE';activate_clip(rig,'ReadyIdle');bpy.context.scene.frame_set(-1);bpy.context.scene.frame_set(0)
for o in bpy.data.objects:
 if o.name.startswith('Golf_') and o.data.shape_keys:
  for key in o.data.shape_keys.key_blocks:key.value=0
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
np.savez_compressed(w/'data/ready_geometry_source_r28.npz',B0=B0,B=evaluated_co(body,dg),T=mesh_tris(body.data),P=evaluated_co(bpy.data.objects['Golf_Trousers'],dg),PT=mesh_tris(bpy.data.objects['Golf_Trousers'].data))
