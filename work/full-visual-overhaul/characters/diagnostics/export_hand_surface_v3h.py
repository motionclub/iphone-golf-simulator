import bpy,pathlib,sys,json
from mathutils import Matrix
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_FistSurfaceV3H.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'));rig.animation_data_clear();rig.data.pose_position='REST'
for key in body.data.shape_keys.key_blocks:key.value=0
with bpy.data.libraries.load(str(R/f'work/match-anim-set/export/HeroBase_{sex}_MatchAnims.blend'),link=False) as (src,dst):dst.armatures=[rig.data.name]
original=dst.armatures[0];old={b.name:b.matrix_local.copy() for b in original.bones}
def export(path):
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='STRIP')
out=R/'work/full-visual-overhaul/characters/exports/HandsV3H';out.mkdir(parents=True,exist_ok=True);export(out/f'{sex}_NewRest.fbx')
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
names=[s+d+j for s in ('Left','Right') for d in ('Thumb','Index','Middle','Ring','Little') for j in ('Proximal','Intermediate','Distal')]
for n in names:rig.data.edit_bones[n].use_connect=False
for n in names:rig.data.edit_bones[n].matrix=old[n];rig.data.edit_bones[n].length=original.bones[n].length
for n in names:rig.data.edit_bones[n].use_connect=original.bones[n].use_connect
bpy.ops.object.mode_set(mode='OBJECT');export(out/f'{sex}.fbx')
print('HAND_V3_SURFACE_FBX_COMPLETE',sex,body.data.shape_keys.key_blocks.keys(),flush=True)
