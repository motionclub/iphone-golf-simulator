"""Shaded renders from the locked cameras (plate framing) with Unity-like lighting. blender -b blend --python lockedshade.py -- outdir [cams]"""
import bpy, sys, math
import os; sys_path=__import__('sys').path; sys_path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import applycoords
from pathlib import Path
from mathutils import Vector
argv=sys.argv[sys.argv.index('--')+1:]; out=Path(argv[0]); out.mkdir(parents=True,exist_ok=True)
cams=argv[1].split(',') if len(argv)>1 else ['bald_front','bald_back','sheet_front','sheet_back','left','right']
scale=int(argv[2]) if len(argv)>2 else 1
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
s.render.engine='BLENDER_EEVEE'; s.render.resolution_x=1280*scale; s.render.resolution_y=720*scale; s.render.film_transparent=False
s.render.image_settings.file_format='PNG'; s.render.image_settings.color_mode='RGB'
s.view_settings.view_transform='Standard'; s.view_settings.look='None'
try:
    s.eevee.taa_render_samples=32; s.eevee.use_shadows=True; s.eevee.use_gtao=True; s.eevee.gtao_distance=0.06
except Exception: pass
w=bpy.data.worlds.new('w'); s.world=w; w.use_nodes=True; bg=w.node_tree.nodes['Background']; bg.inputs['Color'].default_value=(lin(.30),lin(.30),lin(.32),1); bg.inputs['Strength'].default_value=0.9
# camera-relative lights as in the plates: soft key upper-left-front, fill right
def sun(nm,rot,energy):
    d=bpy.data.lights.new(nm,'SUN'); d.energy=energy; d.angle=math.radians(25); o=bpy.data.objects.new(nm,d); s.collection.objects.link(o); return o
for n in cams:
    cam=bpy.data.objects['Locked_'+n]; s.camera=cam
    for nm in ('k','f'):
        if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm],do_unlink=True)
    k=sun('k',None,2.6); f=sun('f',None,0.9)
    for o,(pitch,yaw) in ((k,(50,-35)),(f,(20,50))):
        o.parent=cam; o.rotation_mode='XYZ'; o.rotation_euler=(math.radians(pitch),0,math.radians(yaw)); o.location=(0,0,0)
        # light travels along its -Z; camera-local rot: pitch tilts down from above
        o.rotation_euler=(math.radians(-pitch),math.radians(yaw),0)
    s.render.filepath=str(out/f'{n}.png'); bpy.ops.render.render(write_still=True)
print('SHADE_DONE')
