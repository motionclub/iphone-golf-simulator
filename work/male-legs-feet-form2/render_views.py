"""blender -b --factory-startup --python render_views.py -- <blend> <outdir> [views]
Renders Body_M (face hidden) from the locked plate cameras: shaded clay (eevee, 3 lights) + alpha mask.  Views: bald_front bald_back sheet_front sheet_back left right"""
import sys, math
from pathlib import Path
import numpy as np, bpy
argv=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); out=Path(argv[1]); out.mkdir(parents=True,exist_ok=True)
views=argv[2].split(',') if len(argv)>2 and argv[2] else ['bald_front','bald_back','sheet_front','sheet_back','left','right','q3FL','q3FR','q3BL','q3BR']
import json
Q3=json.load(open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-legs-feet-form2/data/plates/q3cams.json'))
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='EMPTY': o.hide_render=True
face=bpy.data.objects.get('Face_M')
if face: face.hide_render=True
body=bpy.data.objects['Body_M']
def lin(c): return ((c+0.055)/1.055)**2.4 if c>0.04045 else c/12.92
m=bpy.data.materials.new('clay'); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']
g=lin(0.50); b.inputs['Base Color'].default_value=(g,g,g,1); b.inputs['Roughness'].default_value=0.62
try: b.inputs['Specular IOR Level'].default_value=0.25
except Exception: pass
body.data.materials.clear(); body.data.materials.append(m)
sc.render.engine='BLENDER_EEVEE'; sc.render.resolution_x=1280; sc.render.resolution_y=720; sc.render.resolution_percentage=100
sc.render.film_transparent=True; sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGBA'
sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'
try:
    sc.eevee.taa_render_samples=24; sc.eevee.use_shadows=True; sc.eevee.use_gtao=True; sc.eevee.gtao_distance=0.1
except Exception: pass
# world: soft grey ambient
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; bg=w.node_tree.nodes['Background']; bg.inputs[0].default_value=(lin(.55),lin(.55),lin(.57),1); bg.inputs[1].default_value=0.9
for o in [o for o in bpy.data.objects if o.type=='LIGHT']: bpy.data.objects.remove(o)
from mathutils import Vector
def light(name,rot,energy):
    ld=bpy.data.lights.new(name,'SUN'); ld.energy=energy; ld.angle=math.radians(30)
    lo=bpy.data.objects.new(name,ld); sc.collection.objects.link(lo); lo.rotation_euler=rot
light('key',(math.radians(55),0,math.radians(-25)),2.4)
light('fill',(math.radians(70),0,math.radians(65)),0.9)
light('rim',(math.radians(120),0,math.radians(160)),0.8)
W_,H_=1280,720
cd=bpy.data.cameras.new('q3c'); cd.type='ORTHO'; q3o=bpy.data.objects.new('q3c',cd); sc.collection.objects.link(q3o)
def q3_camera(k):
    c=Q3[k]; a=math.radians(c['az']); MPP=c['mpp']; ox=c['ox']; sole=c['sole']
    d=Vector((math.sin(a),-math.cos(a),0.0)); right=Vector((math.cos(a),math.sin(a),0)); up=Vector((0,0,1))
    cr=-(ox-W_/2)*MPP; cu=(sole-H_/2)*MPP; cpt=right*cr+up*cu
    q3o.location=cpt+d*5.0; q3o.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler(); cd.ortho_scale=W_*MPP
    return q3o, a
for v in views:
    if v.startswith('q3'):
        cam,yaw=q3_camera(v); sc.camera=cam
    else:
        cam=bpy.data.objects['Locked_'+v]; sc.camera=cam; yaw=cam.rotation_euler[2]
    for ln,(el,az) in {'key':(55,-25),'fill':(70,65),'rim':(120,160)}.items():
        lo=bpy.data.objects[ln]; lo.rotation_euler=(math.radians(el),0,yaw+math.radians(az))
    sc.render.filepath=str((out/f'{v}.png').resolve()); bpy.ops.render.render(write_still=True)
print('RENDER_DONE')
