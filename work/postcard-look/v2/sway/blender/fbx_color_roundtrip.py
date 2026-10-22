"""Does a FLOAT_COLOR 'Col' (R weight, G phase, B 0, A 1) survive Blender -> FBX (colors_type LINEAR, the export_look_fbx options) -> Blender import, bit for bit?
usage: Blender -b --factory-startup --python fbx_color_roundtrip.py -- <out.fbx>"""
import sys, os
import bpy, numpy as np
out = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new("PLANT_TUFT_A")
n = 9
verts, faces = [], []
for i in range(n):
    y = i / (n - 1)
    verts += [(-.03, 0, y), (.03, 0, y)]
    if i: a = 2 * (i - 1); faces.append((a, a + 1, a + 3, a + 2))
me.from_pydata(verts, [], faces); me.update()
att = me.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
cols = []
for i in range(n):
    y = i / (n - 1)
    cols += [(y * y * 0 + y, 0.37, 0.0, 1.0)] * 2
att.data.foreach_set("color", np.array(cols, dtype=np.float32).ravel())
me.color_attributes.active_color_name = "Col"; me.color_attributes.render_color_index = 0
ob = bpy.data.objects.new("PLANT_TUFT_A.000", me); bpy.context.scene.collection.objects.link(ob)
mat = bpy.data.materials.new("LK_PLANTS"); ob.data.materials.append(mat)
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.export_scene.fbx(filepath=out, use_selection=True, object_types={'MESH', 'EMPTY'}, axis_forward='-Z', axis_up='Y', apply_unit_scale=True,
                         apply_scale_options='FBX_SCALE_ALL', bake_anim=False, use_mesh_modifiers=True, add_leaf_bones=False, path_mode='STRIP', embed_textures=False, colors_type='LINEAR')
print("exported", out, os.path.getsize(out))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=out)
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    m = o.data
    print("imported", o.name, "attrs", [(a.name, a.data_type, a.domain) for a in m.color_attributes])
    for a in m.color_attributes:
        buf = np.empty(len(a.data) * 4, dtype=np.float32); a.data.foreach_get("color", buf)
        buf = buf.reshape(-1, 4)
        print("  ", a.name, "R range", buf[:, 0].min(), buf[:, 0].max(), "G", np.unique(buf[:, 1].round(4)), "B", np.unique(buf[:, 2].round(4)), "A", np.unique(buf[:, 3].round(4)), "n", len(buf), "verts", len(m.vertices))
