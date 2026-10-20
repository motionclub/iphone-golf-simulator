import bpy
from mathutils import Vector
s=bpy.context.scene;r=bpy.data.objects['Rig_Female'];r.data.pose_position='POSE';r.animation_data.action=bpy.data.actions['Drive_Female_RH']
for f in [0,180]:
 s.frame_set(f);bpy.context.view_layer.update()
 print('FRAME',f,'head',list(map(list,r.pose.bones['Head'].matrix)),flush=True)
 for n in ['Hair_F','Face_F']:
  o=bpy.data.objects[n];p=[o.matrix_world@v.co for v in o.data.vertices];print(n,'parentinverse',list(map(list,o.matrix_parent_inverse)),'local',list(map(list,o.matrix_local)),'world',list(map(list,o.matrix_world)),'bounds',[tuple(min(q[i] for q in p) for i in range(3)),tuple(max(q[i] for q in p) for i in range(3))],'constraints',[c.type for c in o.constraints],flush=True)
