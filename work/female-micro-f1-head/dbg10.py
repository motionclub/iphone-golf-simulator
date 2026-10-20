import bpy, sys, math
from mathutils import Vector
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np
which = sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.open_mainfile(filepath='data/b3.blend')
fo = bpy.data.objects['Face_F']; bo = bpy.data.objects['Body_F']
if which == 'face': bo.hide_render = True
if which == 'body': fo.hide_render = True
s = bpy.context.scene
s.render.engine = 'BLENDER_WORKBENCH'; s.render.resolution_x = s.render.resolution_y = 1000
sh = s.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = False
s.world = bpy.data.worlds.new('w'); s.world.color = (0.3, 0.3, 0.32)
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.2
cam = bpy.data.objects.new('c', cd); s.collection.objects.link(cam); s.camera = cam
cam.location = (-0.045, -2.0, 1.553); cam.rotation_euler = (math.pi/2, 0, 0)
for md in (None,): pass
s.render.filepath = f'renders/dbg_{which}.png'; bpy.ops.render.render(write_still=True)
