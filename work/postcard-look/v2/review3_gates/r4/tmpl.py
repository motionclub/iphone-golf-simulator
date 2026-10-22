import bpy
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
bpy.ops.wm.open_mainfile(filepath=R+'blender/hole_08.blend')
for o in bpy.data.objects:
    if o.name in('PLANT_FLOWER_PURPLE','PLANT_SHRUB_A','PLANT_TUFT_B'):
        print(o.name,tuple(round(x,2) for x in o.location),o.hide_viewport,o.hide_render,[c.name for c in o.users_collection],o.data.users)
for c in bpy.data.collections: print('COL',c.name,len(c.objects),c.hide_viewport,c.hide_render)
