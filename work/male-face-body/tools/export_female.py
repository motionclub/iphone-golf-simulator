"""Blender -b --factory-startup --python export_female.py -- <blend> <out.fbx>
Same objects/options as work/jaw-sculpt-2026-10-12/export_heads.py (Body + ReferenceFeatures + rig, rest pose, shape keys 0)."""
import bpy, sys, hashlib, json
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE' and o.name.startswith('Rig_'))
rig.data.pose_position = 'REST'; rig.animation_data_clear()
for ob in (body, bpy.data.objects['ReferenceFeatures'], rig):
    ob.hide_set(False); ob.hide_viewport = False; ob.hide_select = False
for ob in bpy.context.scene.objects:
    if ob.name.startswith(('GamePreview', 'NormTest')): ob.hide_set(True)
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.context.scene.objects:
    ob.select_set(ob.name in ('Body', 'ReferenceFeatures') or ob is rig)
    if ob.type == 'MESH' and ob.data.shape_keys:
        for key in ob.data.shape_keys.key_blocks: key.value = 0
bpy.context.view_layer.objects.active = body
assert sorted(o.name for o in bpy.context.selected_objects) == sorted(['Body', 'ReferenceFeatures', rig.name])
bpy.ops.export_scene.fbx(filepath=argv[1], use_selection=True, object_types={'ARMATURE', 'MESH'}, global_scale=1.0, apply_unit_scale=True,
                         apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y', use_mesh_modifiers=False, mesh_smooth_type='OFF',
                         add_leaf_bones=False, bake_anim=False, path_mode='STRIP', use_armature_deform_only=False)
print('EXPORT DONE', argv[1], hashlib.sha256(open(argv[1], 'rb').read()).hexdigest(), len(body.data.vertices))
