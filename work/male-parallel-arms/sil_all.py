"""Render masks from all locked cameras: blender -b file.blend --python sil_all.py -- outdir"""
import bpy, sys
import os; sys_path=__import__('sys').path; sys_path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import applycoords
from pathlib import Path
out=Path(sys.argv[sys.argv.index('--')+1]); out.mkdir(parents=True,exist_ok=True)
applycoords.apply()
s=bpy.context.scene
s.render.film_transparent=True; s.render.image_settings.color_mode='RGBA'; s.render.image_settings.file_format='PNG'
s.render.resolution_x=1280; s.render.resolution_y=720; s.render.resolution_percentage=100
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Body_M': o.hide_render=True
for n in ['bald_front','bald_back','left','right','sheet_front','sheet_back']:
    cam=bpy.data.objects['Locked_'+n]; s.camera=cam; s.render.filepath=str(out/(n+'.png')); bpy.ops.render.render(write_still=True)
    print(n,cam.data.type,tuple(cam.location),tuple(cam.rotation_euler),cam.data.ortho_scale if cam.data.type=='ORTHO' else cam.data.lens, cam.data.shift_x, cam.data.shift_y)
