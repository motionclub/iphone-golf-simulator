"""blender -b f --python rside.py -- out_prefix : side (+x looking toward -x i.e. camera at +x... ) views of limbs, 3/4 closeups."""
import bpy, sys, math
from mathutils import Vector
pre=sys.argv[sys.argv.index('--')+1]
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Body_F': o.hide_render=True
sc.render.engine='BLENDER_WORKBENCH'
sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='MATERIAL'
sc.render.resolution_x=900; sc.render.resolution_y=900
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=False; w.color=(0.85,0.85,0.86)
sc.render.film_transparent=False
def shot(name,center,d,scale):
    d=Vector(d).normalized(); cam.location=Vector(center)-d*3
    cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler(); cam.data.ortho_scale=scale
    sc.render.filepath=f'{pre}_{name}.png'; bpy.ops.render.render(write_still=True)
# model faces -y (front). Left profile plate: figure faces left of image => camera on -x? camera at +x looking -x sees +y to the left? check by output
shot('full_side',(0,0,0.85),(-1,0,0),1.9)
shot('foot_side',(0.12,0,0.07),(-1,0,0),0.34)
shot('foot_top',(0.12,-0.04,0.05),(0,0,-1),0.34)
shot('foot_q',(0.12,-0.04,0.07),(-0.5,0.6,-0.3),0.34)
shot('hand_side',(0.33,0,0.88),(-1,0,0),0.34)
shot('hand_q',(0.33,0,0.88),(-0.4,-0.8,-0.2),0.34)
