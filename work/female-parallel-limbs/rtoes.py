import bpy, sys
from mathutils import Vector
pre=sys.argv[sys.argv.index('--')+1]
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Body_F': o.hide_render=True
sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='MATERIAL'
sc.render.resolution_x=700; sc.render.resolution_y=420
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=False; w.color=(0.85,0.85,0.86)
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=0.16
for tag,fx in (('R',0.125),('L',-0.125)):
    for nm,d,c in (('front',Vector((0,1,0)),Vector((fx,-3,0.025))),('q',Vector((-0.5*(1 if fx>0 else -1),0.55,-0.45)).normalized(),Vector((fx,-0.14,0.02)))):
        cam.location=c-(d*3 if nm=='q' else Vector((0,0,0))); cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
        if nm=='q': cam.location=Vector((fx,-0.14,0.02))-d*3
        sc.render.filepath=pre+f'_{nm}{tag}.png'; bpy.ops.render.render(write_still=True)
