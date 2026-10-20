import bpy,sys
from pathlib import Path
w=Path(__file__).resolve().parents[1];sex=sys.argv[-1];path=Path(bpy.data.filepath);rig=bpy.data.objects['Rig_'+sex]
with bpy.data.libraries.load(str(w/'rollback/polo_construction_r29'/path.name),link=False) as (src,dst):dst.objects=['Rig_'+sex]
old=dst.objects[0]
for pb in rig.pose.bones:pb.matrix_basis=old.pose.bones[pb.name].matrix_basis.copy()
bpy.data.objects.remove(old,do_unlink=True)
a=bpy.data.actions['ReadyIdle'];rig.animation_data.action=a
if a.slots:rig.animation_data.action_slot=a.slots[0]
bpy.context.scene.frame_set(-1);bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.save_as_mainfile(filepath=str(w/f'export/Golf_{sex}_SwingProof.blend'))
print('UNKEYED_POSE_RESTORED',sex,flush=True)
