"""blender -b --factory-startup --python fullbody.py -- <blend> <outdir> <mode: plate|turn> [res_scale]
Full-figure clay render of the male HeroBase (grey body, skin head + painted face like the plates).  plate: locked plate cameras + fitted 3/4 cameras ; turn: free turntable angles with a ground plane.  Never saves the blend."""
import sys, math, json
from pathlib import Path
import numpy as np, bpy
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]
blend,out,mode=a[0],Path(a[1]),a[2]; RS=float(a[3]) if len(a)>3 else 1.0
out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-legs/'
def lin(c): return ((c+0.055)/1.055)**2.4 if c>0.04045 else c/12.92
def srgb(c): return tuple(lin(v) for v in c)
body=bpy.data.objects['Body_M']; face=bpy.data.objects.get('Face_M'); me=body.data
for o in bpy.data.objects:
    if o.type in ('EMPTY','CAMERA'): o.hide_render=True
# --- body: grey with skin head via point colour attribute
n=len(me.vertices); V=np.empty(n*3); me.vertices.foreach_get('co',V); V=V.reshape(-1,3)
GREY=(0.50,0.50,0.50); SKIN=(0.74,0.555,0.435)
t=np.clip((V[:,2]-1.405)/(1.435-1.405),0,1); t=t*t*(3-2*t)
col=np.zeros((n,4),np.float32)
for k in range(3): col[:,k]=[lin(GREY[k]*(1-tt)+SKIN[k]*tt) for tt in t]
col[:,3]=1
at=me.color_attributes.new('hc','FLOAT_COLOR','POINT'); at.data.foreach_set('color',col.reshape(-1))
mat=bpy.data.materials.new('body_hc'); mat.use_nodes=True; nt=mat.node_tree; bsdf=nt.nodes['Principled BSDF']
an=nt.nodes.new('ShaderNodeAttribute'); an.attribute_name='hc'; nt.links.new(an.outputs['Color'],bsdf.inputs['Base Color'])
bsdf.inputs['Roughness'].default_value=0.62
try: bsdf.inputs['Specular IOR Level'].default_value=0.25
except Exception: pass
me.materials.clear(); me.materials.append(mat)
# --- face paint slots (same colours as the unity-like previews)
FACE={'Brow':((.17,.14,.115),.34),'Sclera':((.80,.77,.72),.62),'Iris':((.30,.17,.085),.20),'Pupil':((.025,.018,.012),.25),'Limbal':((.09,.045,.025),.22),'Catch':((1,1,1),.9),
      'LidLine':((.115,.07,.05),.40),'Lip':((.76,.52,.43),.42),'LipUp':((.60,.38,.31),.40),'Seam':((.30,.15,.11),.30),'Nostril':((.26,.13,.09),.25),'BrowSoft':((.22,.175,.14),.30),'LidCrease':((.34,.20,.14),.30)}
def mk(name,colv,smooth):
    m=bpy.data.materials.new(name); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=srgb(colv)+(1,); b.inputs['Roughness'].default_value=1.0-smooth
    try: b.inputs['Specular IOR Level'].default_value=0.4
    except Exception: pass
    return m
if face:
    face.hide_render=False
    for i,slot in enumerate(face.material_slots):
        nm=slot.material.name.replace('Face_','') if slot.material else ''
        if nm in FACE: face.material_slots[i].material=mk('f_'+nm,*FACE[nm])
        else: face.material_slots[i].material=mk('f_skin',SKIN,.40)
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE'; sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGBA'
sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'
try:
    sc.eevee.taa_render_samples=48; sc.eevee.use_shadows=True; sc.eevee.use_gtao=True; sc.eevee.gtao_distance=0.12
except Exception: pass
BG=(54/255,54/255,58/255)
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; bg=w.node_tree.nodes['Background']; bg.inputs[0].default_value=srgb(BG)+(1,); bg.inputs[1].default_value=0.0
# ambient fill via a big soft world light would tint the bg; instead use sun rig + one area-like fill sun
for o in [o for o in bpy.data.objects if o.type=='LIGHT']: bpy.data.objects.remove(o)
RIG={'key':(52,-28,2.0),'fill':(68,62,0.8),'rim':(118,158,0.7),'top':(88,0,0.6)}
lights={}
for nm,(el,az,e) in RIG.items():
    ld=bpy.data.lights.new(nm,'SUN'); ld.energy=e; ld.angle=math.radians(28); lo=bpy.data.objects.new(nm,ld); sc.collection.objects.link(lo); lights[nm]=lo
def aim_lights(yaw):
    for nm,(el,az,e) in RIG.items(): lights[nm].rotation_euler=(math.radians(el),0,yaw+math.radians(az))
# world ambient: emissive-free; use a uniform world strength for soft shading but keep film background = BG via compositing trick: render with transparent film, composite onto BG
sc.render.film_transparent=True
w.node_tree.nodes['Background'].inputs[1].default_value=0.0
# ambient: add a weak hemispheric via world colour (white, low strength) -> alpha stays 1 on geometry
bg.inputs[0].default_value=(0.62,0.62,0.66,1); bg.inputs[1].default_value=0.40
cd=bpy.data.cameras.new('c'); cd.type='ORTHO'; co=bpy.data.objects.new('c',cd); sc.collection.objects.link(co)
def render(path,res=(1280,720)):
    sc.render.resolution_x=int(res[0]*RS); sc.render.resolution_y=int(res[1]*RS); sc.render.resolution_percentage=100
    sc.render.filepath=str(path); bpy.ops.render.render(write_still=True)
if mode=='plate':
    Q3=json.load(open(R+'data/q3cams_full.json'))
    for v in ('bald_front','bald_back','sheet_front','sheet_back','left','right'):
        cam=bpy.data.objects['Locked_'+v]; sc.camera=cam; aim_lights(cam.rotation_euler[2]); render(out/f'{v}.png')
    W_,H_=1280,720
    sc.camera=co
    for k,c in Q3.items():
        ang=math.radians(c['az']); MPP=c['mpp']; ox=c['ox']; sole=c['sole']
        d=Vector((math.sin(ang),-math.cos(ang),0.0)); right=Vector((math.cos(ang),math.sin(ang),0)); up=Vector((0,0,1))
        cr=-(ox-W_/2)*MPP; cu=(sole-H_/2)*MPP; cpt=right*cr+up*cu
        co.location=cpt+d*6.0; co.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler(); cd.ortho_scale=W_*MPP
        aim_lights(ang); render(out/f'{k}.png')
else:
    # turntable with a ground plane receiving shadows, camera slightly above, perspective-free (ortho)
    sc.camera=co; cd.ortho_scale=2.15
    for name,az in (('front',0),('q3_front_R',35),('side_R',90),('q3_back_R',145),('back',180),('q3_back_L',215),('side_L',270),('q3_front_L',325)):
        ang=math.radians(az); el=math.radians(7)
        d=Vector((math.sin(ang)*math.cos(el),-math.cos(ang)*math.cos(el),math.sin(el))); tgt=Vector((0,0,0.86))
        co.location=tgt+d*6.0; co.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler(); aim_lights(ang); render(out/f'turn_{name}.png',(800,1000))
print('FULLBODY_DONE',mode)
