"""Shaded ortho renders of Body_M rotated about z by given yaws, plate-like lights. blender -b blend --python q3shade.py -- outdir yaw1,yaw2.. [ortho_scale] [res]"""
import bpy, sys, math
import os; sys_path=__import__('sys').path; sys_path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import applycoords
from pathlib import Path
from mathutils import Vector
argv=sys.argv[sys.argv.index('--')+1:]; out=Path(argv[0]); out.mkdir(parents=True,exist_ok=True)
yaws=[float(v) for v in argv[1].split(',')]
osc=float(argv[2]) if len(argv)>2 else 2.0
res=int(argv[3]) if len(argv)>3 else 900
cz=float(argv[4]) if len(argv)>4 else 0.95
cx=float(argv[5]) if len(argv)>5 else 0.0
def lin(c): return ((c+0.055)/1.055)**2.4 if c>0.04045 else c/12.92
applycoords.apply()
s=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Body_M': o.hide_render=True
    if o.type=='EMPTY': o.hide_render=True
body=bpy.data.objects['Body_M']; body.data.materials.clear()
m=bpy.data.materials.new('g'); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value=(lin(.52),lin(.52),lin(.53),1); b.inputs['Roughness'].default_value=0.62
body.data.materials.append(m)
s.render.engine='BLENDER_EEVEE'; s.render.resolution_x=res; s.render.resolution_y=res; s.render.film_transparent=False
s.render.image_settings.file_format='PNG'; s.render.image_settings.color_mode='RGB'
s.view_settings.view_transform='Standard'; s.view_settings.look='None'
try:
    s.eevee.taa_render_samples=32; s.eevee.use_shadows=True; s.eevee.use_gtao=True; s.eevee.gtao_distance=0.06
except Exception: pass
w=bpy.data.worlds.new('w'); s.world=w; w.use_nodes=True; bg=w.node_tree.nodes['Background']; bg.inputs['Color'].default_value=(lin(.30),lin(.30),lin(.32),1); bg.inputs['Strength'].default_value=0.9
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); s.collection.objects.link(cam); s.camera=cam; cam.data.type='ORTHO'; cam.data.ortho_scale=osc; cam.data.clip_end=50
def sun(nm,energy):
    d=bpy.data.lights.new(nm,'SUN'); d.energy=energy; d.angle=math.radians(25); o=bpy.data.objects.new(nm,d); s.collection.objects.link(o); return o
k=sun('k',2.6); f=sun('f',0.9)
for o,(pitch,yaw) in ((k,(50,-35)),(f,(20,50))):
    o.parent=cam; o.rotation_mode='XYZ'; o.rotation_euler=(math.radians(-pitch),math.radians(yaw),0)
for yaw in yaws:
    # camera on a circle around the figure: yaw 0 = front (camera at -y looking +y); positive yaw moves the camera toward +x
    a=math.radians(yaw); d=Vector((math.sin(a),-math.cos(a),0))
    cam.location=Vector((cx,0,cz))+d*6
    look=(Vector((cx,0,cz))-cam.location).normalized()
    cam.rotation_euler=look.to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(out/f'yaw{int(yaw):+d}.png'); bpy.ops.render.render(write_still=True)
print('Q3_DONE')
