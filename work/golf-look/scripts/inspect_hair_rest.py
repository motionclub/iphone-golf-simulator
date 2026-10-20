import bpy,json
from mathutils import Matrix
rig=bpy.data.objects['Rig_Female'];h=bpy.data.objects['Hair_F'];h.hide_viewport=False;h.hide_set(False);rig.animation_data.action=None;rig.data.pose_position='REST';bpy.context.scene.frame_set(-1);bpy.context.view_layer.update()
print('HAIR_REST',list(map(list,h.matrix_world)),flush=True)
print('HEAD_REST',list(map(list,rig.matrix_world@rig.data.bones['Head'].matrix_local)),flush=True)
