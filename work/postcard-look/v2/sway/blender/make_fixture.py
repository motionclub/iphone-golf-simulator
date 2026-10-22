"""Writes the plant-sway FBX fixture: a 9-row vertical strip (1 m tall, 0.06 m wide) with the contract colour attribute (R = row / 8, G = 0.37, B = 0, A = 1), exported with the SAME exporter options as
postcard_look_lib.export_look_fbx (colors_type LINEAR, path_mode STRIP, axes -Z / Y, apply_unit_scale, FBX_SCALE_ALL), so Unity's import of it shows what a real PLANT_* mesh from the libs will look like.
usage: Blender -b --factory-startup --python make_fixture.py -- <out.fbx>"""
import sys
import bpy, numpy as np
out = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new("PLANT_TUFT_FIXTURE")
n = 9
verts, faces = [], []
for i in range(n):
    y = i / (n - 1)
    verts += [(-.03, 0, y), (.03, 0, y)]
    if i:
        a = 2 * (i - 1); faces.append((a, a + 1, a + 3, a + 2))
me.from_pydata(verts, [], faces); me.update()
att = me.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
cols = []
for i in range(n):
    cols += [(i / (n - 1), 0.37, 0.0, 1.0)] * 2
att.data.foreach_set("color", np.array(cols, dtype=np.float32).ravel())
me.color_attributes.active_color_name = "Col"; me.color_attributes.render_color_index = 0
ob = bpy.data.objects.new("PLANT_TUFT_FIXTURE", me); bpy.context.scene.collection.objects.link(ob)
mat = bpy.data.materials.new("LK_PLANTS"); ob.data.materials.append(mat)
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.export_scene.fbx(filepath=out, use_selection=True, object_types={'MESH', 'EMPTY'}, axis_forward='-Z', axis_up='Y', apply_unit_scale=True,
                         apply_scale_options='FBX_SCALE_ALL', bake_anim=False, use_mesh_modifiers=True, add_leaf_bones=False, path_mode='STRIP', embed_textures=False, colors_type='LINEAR')
print("fixture written", out)
