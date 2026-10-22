"""Exports the props library's OWN plant meshes (postcard_props_lib.PLANT_KINDS, as they are on disk right now) as one FBX with the libs' exporter options (colors_type LINEAR, axes -Z / Y, FBX_SCALE_ALL, path STRIP),
so GolfPlantSwayCheck can run PLANT_SWAY_COLORS_UNITY / SWAY_GENTLE on what Unity really imports, before the rebuilt holes are installed. A SNAPSHOT: re-run it when the library changes.
usage: Blender -b --factory-startup --python make_lib_fixture.py"""
import sys, os
import bpy
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../../.."))
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
import postcard_props_lib as PL
out = os.path.join(REPO, "Unity", "Assets", "Editor", "GolfPlantSwayFixture", "plants_lib_fixture.fbx")
x = 0.0
objs = []
for k in PL.PLANT_KINDS:
    lib = PL.library_object(k)
    ob = bpy.data.objects.new(k + ".000", lib.data)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (x, 0, 0); x += 2.5
    objs.append(ob)
bpy.ops.object.select_all(action='DESELECT')
for ob in objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.export_scene.fbx(filepath=out, use_selection=True, object_types={'MESH', 'EMPTY'}, axis_forward='-Z', axis_up='Y', apply_unit_scale=True,
                         apply_scale_options='FBX_SCALE_ALL', bake_anim=False, use_mesh_modifiers=True, add_leaf_bones=False, path_mode='STRIP', embed_textures=False, colors_type='LINEAR')
print("library fixture:", len(objs), "plants ->", out, os.path.getsize(out), "bytes")
