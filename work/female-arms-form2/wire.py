import bpy, sys, math
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]; pre=a[0]; zc=float(a[1]); sc_=float(a[2]); xc=float(a[3])
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Body_F': o.hide_render=True
    if o.type=='EMPTY': o.hide_render=True
sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading
sh.type='SOLID'; sh.light='STUDIO'; sh.color_type='SINGLE'; sh.single_color=(0.8,0.8,0.82)
sc.display.render_aa='OFF'
bpy.data.objects['Body_F'].modifiers.clear()
m=bpy.data.objects['Body_F'].modifiers.new('w','WIREFRAME'); m.thickness=0.0006; m.use_replace=False
sc.render.resolution_x=700; sc.render.resolution_y=700
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=False; w.color=(1,1,1)
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=sc_
for name,th in(('front',0),('q3F',-35),('side',-90)):
    t=math.radians(th); pos=Vector((5*math.sin(t)+xc,-5*math.cos(t),zc)); d=(Vector((xc,0,zc))-pos).normalized()
    cam.location=pos; cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f'{pre}_{name}.png'; bpy.ops.render.render(write_still=True)
