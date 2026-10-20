"""blender -b blend --python render_plate_frames.py -- out_prefix
front/back at body_bald framing (1280x720, S m/px); left profile at multi-angle sheet framing (S2, anchor X0=791.5, sole row 338.5).
Soft grey clay look, hair hidden."""
import bpy, sys, math
from mathutils import Vector
pre=sys.argv[sys.argv.index('--')+1]
S=0.0025954198473282443; S2=1.7039/288.5; V0=338.5; X0=791.5
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Body_F': o.hide_render=True
    if o.type=='EMPTY': o.hide_render=True
sc.render.engine='BLENDER_WORKBENCH'
sh=sc.display.shading; sh.color_type='SINGLE'; sh.single_color=(0.74,0.74,0.76); sh.show_cavity=False; sh.show_shadows=False
sh.light='MATCAP'; sh.studio_light='clay_studio.exr'
sc.render.resolution_x=1280; sc.render.resolution_y=720; sc.render.resolution_percentage=100
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=False; w.color=(0.85,0.85,0.86)
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'
def shot(name,scale,center,d):
    cam.data.ortho_scale=scale
    d=Vector(d); cam.location=Vector(center)-d*3
    cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f'{pre}_{name}.png'; bpy.ops.render.render(write_still=True)
zc=(679-360)*S
shot('front',1280*S,((640-440)*S,0,zc),(0,1,0))
shot('back',1280*S,((847-640)*S,0,zc),(0,-1,0))
# left profile (camera at +x looking -x): pixel col 640 <-> y=(640-X0)*S2 ; row 360 <-> z=(V0-360)*S2
shot('side',1280*S2,(5.0,(640-X0)*S2,(V0-360)*S2),(-1,0,0))
