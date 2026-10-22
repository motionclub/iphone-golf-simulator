import bpy,sys,numpy as np
from mathutils import Vector
n=sys.argv[-1]
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
bpy.ops.wm.open_mainfile(filepath=R+f'blender/hole_{n}.blend')
pl=[o for o in bpy.data.objects if o.name.startswith('PLANT_')]
sub=[]
for o in pl:
    M=o.matrix_world; zmin=min((M@v.co).z for v in o.data.vertices)
    if zmin<0.0: sub.append((o.name,round(zmin,2),o.hide_viewport,o.hide_render,o.hide_get() if bpy.context.view_layer.objects.get(o.name) else None,[c.name for c in o.users_collection],tuple(np.round(M.translation,1))))
print('SUB',len(sub)); [print(' ',s) for s in sub[:14]]
print('collections',[(c.name,len(c.objects),c.hide_viewport) for c in bpy.data.collections])
