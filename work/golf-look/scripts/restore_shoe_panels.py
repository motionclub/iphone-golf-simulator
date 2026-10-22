"""Restore the undegraded saddle overlay from the saved garment backup."""
import bpy,sys,shutil,json
from pathlib import Path
from mathutils import Matrix
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex]
p=Path(bpy.data.filepath);bk=W/'rollback/saddle_restore'/p.name;bk.parent.mkdir(parents=True,exist_ok=True)
if not bk.exists():shutil.copy2(p,bk)
rig.animation_data.action=None;rig.data.pose_position='REST'
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update();rows=[]
for side in ['L','R']:
 name='Golf_SaddlePanel_'+side;bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
 existing=set(bpy.data.objects)
 with bpy.data.libraries.load(str(W/'rollback/lower_lineage'/p.name),link=False) as (src,dst):dst.objects=[name,'Golf_Shoe_'+side]
 panel,source=dst.objects;current=bpy.data.objects['Golf_Shoe_'+side]
 # Match the already repaired last's width, rather than applying repeated scales.
 oldx=[v.co.x for v in source.data.vertices];newx=[v.co.x for v in current.data.vertices]
 ratio=(max(newx)-min(newx))/(max(oldx)-min(oldx));a=(max(oldx)+min(oldx))*.5;b=(max(newx)+min(newx))*.5
 bpy.context.scene.collection.objects.link(panel);panel.name=name;panel.parent=rig
 for mod in panel.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
 for v in panel.data.vertices:v.co.x=b+(v.co.x-a)*ratio
 for obj in list(bpy.data.objects):
  if obj not in existing and obj!=panel:bpy.data.objects.remove(obj,do_unlink=True)
 panel.hide_render=False;panel.hide_viewport=False;panel.data.calc_loop_triangles();rows.append(dict(side=side,tris=len(panel.data.loop_triangles),widthRatio=ratio))
rig.data.pose_position='POSE';rig.animation_data.action=bpy.data.actions['ReadyIdle']
if rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(p))
total=0
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith('Golf_') and not o.hide_render:o.data.calc_loop_triangles();total+=len(o.data.loop_triangles)
(W/f'data/saddle_restore_{sex}.json').write_text(json.dumps(dict(panels=rows,visibleKitTris=total,status='candidate; pose renders and collision checks required'),indent=2)+'\n')
print('RESTORED SADDLES',sex,rows,total,flush=True)
