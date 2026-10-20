import bpy, sys, math
from mathutils import Vector
argv = sys.argv[sys.argv.index('--')+1:]
out = argv[0]; zc=float(argv[1]); sc=float(argv[2]); az=float(argv[3]) if len(argv)>3 else 0.0
s = bpy.context.scene
s.render.engine='BLENDER_WORKBENCH'
s.render.resolution_x=s.render.resolution_y=1400
sh=s.display.shading; sh.light='STUDIO'; sh.color_type='SINGLE'; sh.single_color=(0.85,0.7,0.6); sh.show_cavity=False
s.display.render_aa='8'
s.view_settings.view_transform='Standard'
s.world = bpy.data.worlds.new('w'); s.world.color=(0.2,0.2,0.22)
for o in bpy.data.objects:
    if o.type in ('EMPTY','LIGHT','CAMERA'): o.hide_render=True
    if o.name=='Hair_F': o.hide_render=True
b=bpy.data.objects['Body_F']
# wireframe overlay: add wireframe modifier-lite using freestyle? use wireframe modifier
md=b.modifiers.new('w','WIREFRAME'); md.thickness=0.00025; md.use_replace=False
cd=bpy.data.cameras.new('c'); cd.type='ORTHO'; cd.clip_start=0.01; cd.clip_end=50; cd.ortho_scale=sc
cam=bpy.data.objects.new('c',cd); s.collection.objects.link(cam); s.camera=cam
a=math.radians(az); t=Vector((0,-0.01,zc))
cam.location=t+Vector((math.sin(a),-math.cos(a),0))*3
cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler()
s.render.filepath=out; bpy.ops.render.render(write_still=True)
