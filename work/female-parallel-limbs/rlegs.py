import bpy, sys
from mathutils import Vector
pre=sys.argv[sys.argv.index('--')+1]
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Body_F': o.hide_render=True
sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='MATERIAL'
sc.render.resolution_x=600; sc.render.resolution_y=900
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=False; w.color=(0.85,0.85,0.86)
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=1.0
for name,d in (('q1',(-0.55,-0.75,-0.05)),('q2',(0.6,0.7,-0.05)),('side',(-1,0,0))):
    dv=Vector(d).normalized(); cam.location=Vector((0.0,0.0,0.34))-dv*3; cam.rotation_euler=dv.to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f'{pre}_{name}.png'; bpy.ops.render.render(write_still=True)
