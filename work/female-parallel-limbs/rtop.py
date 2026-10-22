import bpy, sys
from mathutils import Vector
pre=sys.argv[sys.argv.index('--')+1]
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Body_F': o.hide_render=True
sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='MATERIAL'
sc.render.resolution_x=900; sc.render.resolution_y=600
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=False; w.color=(0.85,0.85,0.86)
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=0.30
# top view of both feet: hide everything above z=0.16 by clipping the camera
cam.data.clip_start=2.84; cam.data.clip_end=3.5     # camera at z=3: sees z<0.16 (distance>2.84)
for tag,fx in (('R',0.115),('L',-0.115)):
    cam.location=Vector((fx,-0.03,3.0)); cam.rotation_euler=Vector((0,0,-1)).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=pre+f'_top{tag}.png'; bpy.ops.render.render(write_still=True)
# toe row from the front, low camera
cam.data.clip_start=0.1; cam.data.clip_end=10; cam.data.ortho_scale=0.30
cam.location=Vector((0,-3,0.02)); cam.rotation_euler=Vector((0,1,0)).to_track_quat('-Z','Y').to_euler()
sc.render.resolution_x=900; sc.render.resolution_y=300
sc.render.filepath=pre+'_toefront.png'; bpy.ops.render.render(write_still=True)
