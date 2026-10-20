"""Rebuild just four equipment meshes against the installed golf FBX's exact rig.
No clip/body/rest edit. Meshes generated in original Club-local metres then transformed
by the imported Club rest matrix, preserving the current game's lie preparation.
"""
import bpy,sys,pathlib,json
from mathutils import Matrix
ROOT=pathlib.Path(__file__).resolve().parents[3];sex=sys.argv[-1];tag='f' if sex=='Female' else 'm'
sys.path.insert(0,str(ROOT/'blender/scripts'));import golf_clubs,golf_swing
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(ROOT/f'Unity/Assets/Resources/Hero/golfer_{tag}.fbx'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.data.pose_position='REST'
for o in list(bpy.data.objects):
 if o!=rig:bpy.data.objects.remove(o,do_unlink=True)
objects=[rig]
clubRest=rig.data.bones['Club'].matrix_local.copy()
for c in golf_clubs.CLUBS:
 ob=golf_clubs.build(c);bpy.context.collection.objects.link(ob)
 golf_swing.prepare_club_mesh(ob,golf_swing.LIE[c])
 # Original generator's Club rest is identity; FBX's imported rest conversion carries
 # this same original root into the live bind frame.
 ob.data.transform(clubRest);ob.parent=rig;ob.matrix_parent_inverse=Matrix.Identity(4)
 ob.vertex_groups.new(name='Club').add(list(range(len(ob.data.vertices))),1,'REPLACE')
 ob.modifiers.new('Club bind','ARMATURE').object=rig;objects.append(ob)
out=ROOT/f'Unity/Assets/Resources/Golf/Equipment/{sex}.fbx'
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(out),use_selection=True,object_types={'ARMATURE','MESH'},
 apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',
 use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,armature_nodetype='NULL',
 bake_anim=False,path_mode='AUTO')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/f'ArtDir/hero/kit/premium/source/Premium_{sex}_GolfEquipment.blend'))
print('GOLF_EQUIPMENT_RIG',sex,len(rig.data.bones),out)
