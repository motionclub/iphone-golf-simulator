"""Close-up clay renders. blender -b blend --python closeup.py -- outdir spec...  spec = name:tx,ty,tz:dx,dy,dz:ortho[:lightpitch:lightyaw]
 camera looks from target+d*6 toward target (d = direction from target to camera)."""
import bpy, sys, math
import os; sys_path=__import__('sys').path; sys_path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import applycoords
from pathlib import Path
from mathutils import Vector
argv=sys.argv[sys.argv.index('--')+1:]; out=Path(argv[0]); out.mkdir(parents=True,exist_ok=True); specs=argv[1:]
def lin(c): return ((c+0.055)/1.055)**2.4 if c>0.04045 else c/12.92
applycoords.apply()
s=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Body_M': o.hide_render=True
    if o.type=='EMPTY': o.hide_render=True
body=bpy.data.objects['Body_M']; body.data.materials.clear()
m=bpy.data.materials.new('g'); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value=(lin(.62),lin(.62),lin(.63),1); b.inputs['Roughness'].default_value=0.55
body.data.materials.append(m)
s.render.engine='BLENDER_EEVEE'; s.render.resolution_x=900; s.render.resolution_y=900; s.render.film_transparent=False
s.render.image_settings.file_format='PNG'; s.render.image_settings.color_mode='RGB'
s.view_settings.view_transform='Standard'; s.view_settings.look='None'
try:
    s.eevee.taa_render_samples=24; s.eevee.use_shadows=True; s.eevee.use_gtao=True; s.eevee.gtao_distance=0.04
except Exception: pass
w=bpy.data.worlds.new('w'); s.world=w; w.use_nodes=True; bg=w.node_tree.nodes['Background']; bg.inputs['Color'].default_value=(lin(.26),lin(.26),lin(.28),1); bg.inputs['Strength'].default_value=0.7
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); s.collection.objects.link(cam); s.camera=cam; cam.data.type='ORTHO'; cam.data.clip_end=50; cam.data.clip_start=0.01
import os
CLIP=float(os.environ.get('CLIP','0'))
def sun(nm,energy,ang=8):
    d=bpy.data.lights.new(nm,'SUN'); d.energy=energy; d.angle=math.radians(ang); o=bpy.data.objects.new(nm,d); s.collection.objects.link(o); return o
k=sun('k',3.4); f=sun('f',0.6,25)
if os.environ.get('WIRE'):
    wo=body.copy(); wo.data=body.data.copy(); s.collection.objects.link(wo)
    md=wo.modifiers.new('wf','WIREFRAME'); md.thickness=float(os.environ.get('WIRE_T','0.00022')); md.use_even_offset=True; md.use_replace=True
    wm=bpy.data.materials.new('wm'); wm.use_nodes=True; wb=wm.node_tree.nodes['Principled BSDF']; wb.inputs['Base Color'].default_value=(0.9,0.55,0.1,1); 
    try: wb.inputs['Emission Color'].default_value=(0.9,0.55,0.1,1); wb.inputs['Emission Strength'].default_value=1.0
    except Exception: pass
    wo.data.materials.clear(); wo.data.materials.append(wm)
for sp in specs:
    parts=sp.split(':'); name=parts[0]; t=Vector([float(v) for v in parts[1].split(',')]); d=Vector([float(v) for v in parts[2].split(',')]).normalized(); osc=float(parts[3])
    lp=float(parts[4]) if len(parts)>4 else 55; ly=float(parts[5]) if len(parts)>5 else -40
    cam.location=t+d*6; cam.data.ortho_scale=osc
    if CLIP>0: cam.data.clip_start=6.0-CLIP
    cam.rotation_euler=(-d).to_track_quat('-Z','Y' if os.environ.get('UPY') else 'Z').to_euler()
    for o,(pitch,yaw) in ((k,(lp,ly)),(f,(20,60))):
        o.parent=cam; o.rotation_mode='XYZ'; o.rotation_euler=(math.radians(-pitch),math.radians(yaw),0)
    s.render.filepath=str(out/f'{name}.png'); bpy.ops.render.render(write_still=True)
print('CLOSEUP_DONE')
