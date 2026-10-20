"""Build an editable, shared opaque botanical kit. Existing terrain files are never loaded or edited."""
import bpy, math, random, json
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
OUT=ROOT/'work/full-visual-overhaul/golf'; PROOF=ROOT/'proof/full-visual-overhaul/golf'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
rng=random.Random(20261007)
def srgb(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def material(name,rgb,rough=.75):
 m=bpy.data.materials.new(name);m.diffuse_color=tuple(srgb(c/255) for c in rgb)+(1,);m.use_nodes=True
 b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=m.diffuse_color;b.inputs['Roughness'].default_value=rough
 return m
mats=[material('RESORT_BARK',(131,94,58)),material('RESORT_LEAF_DARK',(35,99,47)),material('RESORT_LEAF_MID',(72,135,51)),material('RESORT_LEAF_LIGHT',(132,172,63)),material('RESORT_CORAL',(243,119,91)),material('RESORT_GOLD',(248,196,77)),material('RESORT_STONE',(146,145,125))]
verts=[];faces=[];slots=[];weights=[]
def reset():verts.clear();faces.clear();slots.clear();weights.clear()
def vertex(p,weight=0):verts.append(tuple(p));weights.append(weight);return len(verts)-1
def face(ids,slot):faces.append(tuple(ids));slots.append(slot)
def tube(a,b,r1,r2,slot=0,sides=8):
 a=Vector(a);b=Vector(b);d=(b-a).normalized();u=d.cross(Vector((1,0,0)))
 if u.length<.01:u=d.cross(Vector((0,1,0)))
 u.normalize();v=d.cross(u);start=len(verts)
 for c,r in [(a,r1),(b,r2)]:
  for j in range(sides):vertex(c+(u*math.cos(j*math.tau/sides)+v*math.sin(j*math.tau/sides))*r)
 for j in range(sides):face((start+j,start+(j+1)%sides,start+sides+(j+1)%sides,start+sides+j),slot)
 face(tuple(start+j for j in reversed(range(sides))),slot);face(tuple(start+sides+j for j in range(sides)),slot)
def leaf(root,angle,length,width,arch,slot,sections=5,phase=0):
 root=Vector(root);d=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-d.y,d.x,0));start=len(verts)
 for j in range(sections+1):
  t=j/sections;c=root+d*(length*t)+Vector((0,0,arch*math.sin(t*math.pi*.8)-length*.12*t*t));w=width*math.sin(t*math.pi)**.8
  vertex(c-side*w, t*.35);vertex(c+Vector((0,0,w*.20)),t*.35);vertex(c+side*w,t*.35)
 for j in range(sections):
  q=start+j*3;face((q,q+3,q+4,q+1),slot);face((q+1,q+4,q+5,q+2),slot)
def bulb(center,scale,slot,rings=4,sides=7):
 c=Vector(center);start=len(verts)
 for k in range(rings+1):
  phi=k*math.pi/rings
  for j in range(sides):
   a=j*math.tau/sides;vertex(c+Vector((math.sin(phi)*math.cos(a)*scale[0],math.sin(phi)*math.sin(a)*scale[1],math.cos(phi)*scale[2])),.12)
 for k in range(rings):
  for j in range(sides):face((start+k*sides+j,start+k*sides+(j+1)%sides,start+(k+1)*sides+(j+1)%sides,start+(k+1)*sides+j),slot)
def mesh(name):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
 for m in mats:me.materials.append(m)
 for p,slot in zip(me.polygons,slots):p.material_index=slot;p.use_smooth=True
 col=me.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
 for c,w in zip(col.data,weights):c.color=(w,.28,0,1)
 ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);return ob
# Meshes use unit height and near-unit radius. Runtime scales to existing obstacle markers.
reset()
for k in range(14):
 a=k*2.39996;level=.08+(k%3)*.11;leaf((0,0,level),a,.8+(k%4)*.05,.18,.40+(k%3)*.08,1+k%3,6)
for k in range(4):bulb((math.cos(k*1.7)*.23,math.sin(k*1.7)*.23,.66),(.23,.21,.17),2+k%2,3,6)
mesh('BUSH_BROAD')
reset()
for k in range(7):
 a=k*2.4;d=Vector((math.cos(a),math.sin(a),0));
 for j in range(4):
  t=(j+1)/5;root=d*(t*.68)+Vector((0,0,.12+.45*math.sin(t*math.pi*.7)))
  for side in [-1,1]:leaf(root,a+side*.90,.24*(1-t*.6),.055,.08,1+k%3,2)
mesh('FERN')
reset()
for k in range(5):
 a=k*2.4;r=.32;center=(math.cos(a)*r,math.sin(a)*r,.50+(k%2)*.2)
 tube((center[0],center[1],0),center,.02,.008,1,5)
 for j in range(5):leaf(center,j*math.tau/5,.19,.10,.06,4,3)
 bulb(center,(.055,.055,.055),5,3,6)
 leaf((center[0],center[1],.25),a,.30,.08,.14,2,3)
mesh('FLOWER_CORAL')
reset()
last=(0,0,0)
for k in range(12):
 t=(k+1)/12;at=(.16*t*t,.04*math.sin(t*math.pi),t);tube(last,at,.047*(1-.36*k/12),.047*(1-.36*t),0,10);last=at
for k in range(12):
 a=k*math.tau/12+.08*(k%2);leaf(last,a,.88+(k%3)*.04,.11,.19+(k%2)*.09,1+k%3,9)
for k in range(5):bulb((last[0]+.05*math.cos(k),last[1]+.05*math.sin(k),.99),(.026,.027,.03),0,3,6)
mesh('PALM')
reset();tube((0,0,0),(0,0,.93),.05,.012)
for k in range(5):
 z=.20+k*.145;radius=.75-k*.115
 for j in range(9):
  a=j*math.tau/9+k*.25;leaf((0,0,z+.12),a,radius,.11,.06,1+(j+k)%3,3)
mesh('PINE')
reset();tube((0,0,0),(0,0,.64),.08,.028)
for k in range(7):
 a=k*2.4;center=(.42*math.cos(a),.42*math.sin(a),.63+.16*math.sin(k))
 tube((0,0,.45),center,.026,.009);bulb(center,(.43,.43,.30),1+k%3,4,8)
mesh('CANOPY')
reset();tube((0,0,0),(0,0,.93),.15,.14,2,12)
bulb((0,0,.91),(.14,.14,.10),2,3,10)
for sign,z in [(-1,.40),(1,.62)]:
 tube((0,0,z),(sign*.48,0,z+.08),.10,.09,2,8)
 tube((sign*.48,0,z+.08),(sign*.48,0,z+.31),.09,.085,2,8)
 bulb((sign*.48,0,z+.31),(.085,.085,.08),3,3,8)
mesh('CACTUS')
reset();bulb((0,0,.35),(.92,.75,.70),6,3,7);mesh('BOULDER')
# Opaque leaves use two-sided material shading in-game, no alpha silhouettes.
for o in list(bpy.context.scene.objects):o.select_set(o.type=='MESH')
bpy.ops.export_scene.fbx(filepath=str(ROOT/'Unity/Assets/Resources/Course/Resort/BotanicalKit.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,bake_space_transform=False,add_leaf_bones=False,bake_anim=False,path_mode='AUTO')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'BotanicalKit.blend'))
report={}
for o in bpy.context.scene.objects:
 if o.type=='MESH':o.data.calc_loop_triangles();report[o.name]={'triangles':len(o.data.loop_triangles),'vertices':len(o.data.vertices)}
(PROOF/'botanical-kit-manifest.json').write_text(json.dumps(report,indent=2))
# Contact sheet uses the actual authored meshes.
for i,o in enumerate([o for o in bpy.context.scene.objects if o.type=='MESH']):o.location=(i%4*2.6,i//4*2.6,0)
world=bpy.data.worlds.new('Studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.19,.25,.28,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;bpy.context.scene.world=world
for name,energy,loc,size in [('Key',1000,(0,-3,7),7),('Fill',650,(6,6,5),8)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((3,1,0))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('KitCamera');o=bpy.data.objects.new('KitCamera',d);bpy.context.collection.objects.link(o);o.location=(9,-12,11);o.rotation_euler=(Vector((3.9,1.3,.45))-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=12;bpy.context.scene.camera=o
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=1440;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX';sc.render.filepath=str(PROOF/'botanical-kit.png');bpy.ops.render.render(write_still=True)
print('BOTANICAL_KIT_COMPLETE',json.dumps(report))
