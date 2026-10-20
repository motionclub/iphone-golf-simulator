"""blender -b export/HeroBase_Female_hands_candidate.blend --python export_fbx_f.py : same exporter settings as work/female-parallel-limbs/export_fbx.py (= Tools/HeroBase/export_male_form.py), written to export/ only."""
import bpy, json, hashlib
from pathlib import Path
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-hands-fingers')
obj = bpy.data.objects['Body_F']; bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
me = obj.data; me.calc_loop_triangles(); tris = len(me.loop_triangles); assert bpy.context.scene.unit_settings.scale_length == 1
dst = W / 'export/HeroBase_Female_Body_hands.fbx'
bpy.ops.export_scene.fbx(filepath=str(dst), use_selection=True, object_types={'MESH'}, global_scale=1, apply_unit_scale=True,
  apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y', use_mesh_modifiers=False, mesh_smooth_type='OFF', add_leaf_bones=False, bake_anim=False)
rep = {'source': 'HeroBase_Female_hands_candidate.blend', 'fbx': str(dst), 'fbx_sha256': hashlib.sha256(dst.read_bytes()).hexdigest(), 'mesh': 'Body_F', 'vertices': len(me.vertices), 'triangles': tris,
       'global_scale': 1, 'forward': '-Z', 'up': 'Y', 'hair': False, 'armature': False, 'note': 'Body only (no hair), same exporter settings as the limbs/male exports; staged in export/ only, NOT installed into ArtDir'}
(W / 'export/export_report.json').write_text(json.dumps(rep, indent=2)); print(json.dumps(rep, indent=2))
