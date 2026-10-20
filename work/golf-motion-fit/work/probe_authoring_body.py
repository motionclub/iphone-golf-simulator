import bpy
from mathutils import Matrix,Vector
r=bpy.data.objects['Rig_Female'];b=bpy.data.objects['Body_F'];print('MODIFIERS',[(m.name,m.type,m.show_viewport,m.show_render,m.object.name if m.type=='ARMATURE' else '') for m in b.modifiers],flush=True);print('WORLD',list(map(list,b.matrix_world)),list(map(list,r.matrix_world)),flush=True)
r.animation_data.action=None;r.data.pose_position='POSE'
for pb in r.pose.bones:pb.matrix_basis=Matrix.Identity(4)
pb=r.pose.bones['LeftUpperArm'];head=pb.bone.head_local;pb.matrix=Matrix.Translation(head)@Matrix.Rotation(-.785398,4,'Y')@Matrix.Translation(-head)@pb.bone.matrix_local;bpy.context.view_layer.update()
e=b.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=e.to_mesh();ids=[v.index for v in b.data.vertices if sum(g.weight for g in v.groups if b.vertex_groups[g.group].name=='LeftUpperArm')>.9];print('POSE_MOTION',max((mesh.vertices[i].co-b.data.vertices[i].co).length for i in ids),flush=True)
