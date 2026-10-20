import bpy,sys
p='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form2/tools/soft_plate_matcap.png'
sl=bpy.context.preferences.studio_lights.load(p,'MATCAP')
print('LOADED',sl.name if sl else None)
print([s.name for s in bpy.context.preferences.studio_lights if 'soft' in s.name])
