import bpy
o = bpy.data.objects['Body_F']
bpy.context.view_layer.objects.active = o
for ob in bpy.data.objects: ob.select_set(False)
o.select_set(True)
me = o.data
print('has custom normals before:', me.has_custom_normals)
bpy.ops.mesh.customdata_custom_splitnormals_clear()
for p in me.polygons: p.use_smooth = True
print('has custom normals after:', me.has_custom_normals)
bpy.ops.wm.save_as_mainfile(filepath='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form5/scratch/START_nocustom.blend', copy=True)
print('SAVED')
