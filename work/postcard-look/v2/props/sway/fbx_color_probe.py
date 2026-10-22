import bpy, numpy as np, sys, os
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new("PLANT_T")
V = [(0,0,0),(1,0,0),(0,1,0),(0,0,1)]
F = [(0,1,2),(0,1,3),(1,2,3),(0,2,3)]
me.from_pydata(V, [], F)
att = me.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
vals = [(0.0,0.5,0.0,1.0),(0.25,0.1,0.0,1.0),(0.5,0.9,0.0,1.0),(1.0,0.33,0.0,1.0)]
for i,v in enumerate(vals): att.data[i].color = v
ob = bpy.data.objects.new("PLANT_T", me); bpy.context.scene.collection.objects.link(ob)
ob2 = bpy.data.objects.new("PLANT_T.001", me); bpy.context.scene.collection.objects.link(ob2); ob2.location=(3,0,0)
out = sys.argv[sys.argv.index("--")+1]
for ct in ("LINEAR","SRGB"):
    p = os.path.join(out, f"probe_{ct}.fbx")
    for o in bpy.data.objects: o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=p, use_selection=True, object_types={'MESH'}, axis_forward='-Z', axis_up='Y', apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_anim=False, use_mesh_modifiers=True, add_leaf_bones=False, path_mode='STRIP', embed_textures=False, colors_type=ct)
    print("exported", ct, os.path.getsize(p))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=p)
    for o in bpy.data.objects:
        m = o.data
        print(ct, o.name, [(a.name, a.data_type, a.domain) for a in m.color_attributes])
        if len(m.color_attributes):
            a = m.color_attributes[0]
            arr = np.empty(len(a.data)*4); a.data.foreach_get("color", arr); print(np.round(arr.reshape(-1,4),4).tolist()[:12])
    # rebuild for next
    bpy.ops.wm.read_factory_settings(use_empty=True)
    me = bpy.data.meshes.new("PLANT_T"); me.from_pydata(V, [], F)
    att = me.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
    for i,v in enumerate(vals): att.data[i].color = v
    ob = bpy.data.objects.new("PLANT_T", me); bpy.context.scene.collection.objects.link(ob)
    ob2 = bpy.data.objects.new("PLANT_T.001", me); bpy.context.scene.collection.objects.link(ob2); ob2.location=(3,0,0)
