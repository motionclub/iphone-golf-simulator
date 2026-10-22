"""blender -b file --python rclose.py -- out_prefix : closeups of hands/feet (both sides) in 3 views each."""
import bpy, sys
from mathutils import Vector
pre=sys.argv[sys.argv.index('--')+1]
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Body_F': o.hide_render=True
sc.render.engine='BLENDER_WORKBENCH'
sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='MATERIAL'
sc.render.resolution_x=500; sc.render.resolution_y=500
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=False; w.color=(0.85,0.85,0.86)
sc.render.film_transparent=False
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'
def shot(name,center,d,scale):
    d=Vector(d).normalized(); cam.location=Vector(center)-d*3
    cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler(); cam.data.ortho_scale=scale
    sc.render.filepath=f'{pre}_{name}.png'; bpy.ops.render.render(write_still=True)
for side,tag in((1,'R'),(-1,'L')):
    hx=0.235*side; fx=0.1103*side
    shot(f'hand{tag}_front',(hx,0,0.78),(0,1,0),0.32)
    shot(f'hand{tag}_side',(hx,0,0.78),(-side,0,0),0.32)
    shot(f'hand{tag}_q',(hx,0,0.78),(-side*0.6,-0.7,-0.2),0.32)
    shot(f'foot{tag}_front',(fx,0,0.09),(0,1,0),0.30)
    shot(f'foot{tag}_side',(fx,-0.07,0.09),(-side,0,0),0.30)
    shot(f'foot{tag}_q',(fx,-0.07,0.07),(-side*0.6,0.7,-0.35),0.30)
