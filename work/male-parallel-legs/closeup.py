"""blender -b --factory-startup --python closeup.py -- <blend> <outdir> <name:az:el:cx:cy:cz:scale[:wire]> ...
Body_M clay close-ups with optional wire overlay. az: 0 = looking +y from -y (front view), 90 = from +x... (camera at azimuth az around the target).  scale = ortho width (m)."""
import sys, math
from pathlib import Path
import numpy as np, bpy
from mathutils import Vector, Matrix
argv=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); out=Path(argv[1]); out.mkdir(parents=True,exist_ok=True)
specs=argv[2:]
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='EMPTY' or o.type=='CAMERA': o.hide_render=True
face=bpy.data.objects.get('Face_M')
if face: face.hide_render=True
body=bpy.data.objects['Body_M']
def lin(c): return ((c+0.055)/1.055)**2.4 if c>0.04045 else c/12.92
def mk(name,rgb,rough):
    m=bpy.data.materials.new(name); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(lin(rgb[0]),lin(rgb[1]),lin(rgb[2]),1); b.inputs['Roughness'].default_value=rough
    try: b.inputs['Specular IOR Level'].default_value=0.2
    except Exception: pass
    return m
body.data.materials.clear(); body.data.materials.append(mk('clay',(.52,.52,.52),.6))
wire=body.copy(); wire.data=body.data; bpy.context.scene.collection.objects.link(wire)
wm=wire.modifiers.new('w','WIREFRAME'); wm.thickness=0.00035; wm.use_replace=False if False else True
wire.data=body.data
wmat=mk('wm',(.05,.05,.07),.9); wire.data.materials.clear() if False else None
sc.render.engine='BLENDER_EEVEE'; sc.render.film_transparent=False
sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGB'
sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'
try:
    sc.eevee.taa_render_samples=16; sc.eevee.use_shadows=True; sc.eevee.use_gtao=True; sc.eevee.gtao_distance=0.05
except Exception: pass
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; bg=w.node_tree.nodes['Background']; bg.inputs[0].default_value=(lin(.22),lin(.22),lin(.24),1); bg.inputs[1].default_value=1.0
for o in [o for o in bpy.data.objects if o.type=='LIGHT']: bpy.data.objects.remove(o)
lights={}
for name,e in (('key',2.6),('fill',0.9),('rim',0.9)):
    ld=bpy.data.lights.new(name,'SUN'); ld.energy=e; ld.angle=math.radians(25); lo=bpy.data.objects.new(name,ld); sc.collection.objects.link(lo); lights[name]=lo
cd=bpy.data.cameras.new('c'); cd.type='ORTHO'; co=bpy.data.objects.new('c',cd); sc.collection.objects.link(co); sc.camera=co
for sp in specs:
    f=sp.split(':'); name=f[0]; az,el,cx,cy,cz,scale=map(float,f[1:7]); wirev='wire' in f[7:]
    clip=[float(x[4:]) for x in f[7:] if x.startswith('clip')]
    # camera at azimuth: az=0 -> camera at -y looking +y ; az=90 -> camera at +x looking -x
    a=math.radians(az); e=math.radians(el)
    d=Vector((math.sin(a)*math.cos(e),-math.cos(a)*math.cos(e),math.sin(e)))
    tgt=Vector((cx,cy,cz)); co.location=tgt+d*4.0
    co.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler()
    cd.ortho_scale=scale
    cd.clip_start=0.01
    if clip:
        # only geometry with (p - tgt).d < clip is visible: camera at 4.0 along d, so clip_start = 4.0 - clip
        cd.clip_start=4.0-clip[0]
    cd.clip_end=20
    sc.render.resolution_x=1000; sc.render.resolution_y=1000
    for k,(el_,az_) in {'key':(50,-30),'fill':(65,60),'rim':(115,160)}.items():
        lights[k].rotation_euler=(math.radians(el_),0,a+math.radians(az_))
    wire.hide_render=not wirev
    sc.render.filepath=str((out/f'{name}.png').resolve()); bpy.ops.render.render(write_still=True)
print('CLOSEUP_DONE')
