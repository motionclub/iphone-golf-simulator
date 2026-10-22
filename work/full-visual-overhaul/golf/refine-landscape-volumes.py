"""Opaque shrub crowns and eroded cliff shoulder volumes, separate candidate source."""
import bpy,math,random,json
from pathlib import Path
from mathutils import Vector
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
bpy.ops.wm.open_mainfile(filepath=str(root/'work/full-visual-overhaul/golf/ResortBotanicalProportioned.blend'))
mats=[bpy.data.materials[n] for n in ['RESORT_BARK','RESORT_LEAF_DARK','RESORT_LEAF_MID','RESORT_LEAF_LIGHT','RESORT_CORAL','RESORT_GOLD','RESORT_STONE']]
verts=[];faces=[];slots=[];weights=[]
def v(p,w=.12):verts.append(tuple(p));weights.append(w);return len(verts)-1
def f(ids,s):faces.append(tuple(ids));slots.append(s)
def lobe(c,scale,slot,seed):
 rng=random.Random(seed);start=len(verts);sides=6;rings=3
 for k in range(rings+1):
  phi=k*math.pi/rings
  for j in range(sides):
   a=j*math.tau/sides+.2*k;r=1+rng.uniform(-.16,.16)
   v(Vector(c)+Vector((math.sin(phi)*math.cos(a)*scale[0]*r,math.sin(phi)*math.sin(a)*scale[1]*r,math.cos(phi)*scale[2]*r)))
 for k in range(rings):
  for j in range(sides):f((start+k*sides+j,start+k*sides+(j+1)%sides,start+(k+1)*sides+(j+1)%sides,start+(k+1)*sides+j),slot)
def leaf(c,angle,length,width,slot):
 d=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-d.y,d.x,0));start=len(verts)
 for k in range(4):
  t=k/3;at=Vector(c)+d*length*t+Vector((0,0,.08*math.sin(t*math.pi)-.10*t*t));w=width*math.sin(t*math.pi)**.8
  v(at-side*w,t*.18);v(at+Vector((0,0,w*.2)),t*.18);v(at+side*w,t*.18)
 for k in range(3):
  a=start+k*3;f((a,a+3,a+4,a+1),slot);f((a+1,a+4,a+5,a+2),slot)
def mesh(name,smooth=True):
 m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update()
 for material in mats:m.materials.append(material)
 for poly,slot in zip(m.polygons,slots):poly.material_index=slot;poly.use_smooth=smooth
 col=m.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
 for c,w in zip(col.data,weights):c.color=(w,.28,0,1)
 o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);return o
for variant in range(2):
 verts.clear();faces.clear();slots.clear();weights.clear();rng=random.Random(620+variant)
 for k in range(9):
  a=k*2.39996;r=.18+.40*rng.random();z=.22+.20*rng.random()
  lobe((math.cos(a)*r,math.sin(a)*r,z),(.32+rng.random()*.12,.30+rng.random()*.12,.24+rng.random()*.08),1+(k+variant)%3,720+variant*30+k)
 for k in range(13):
  a=k*2.39996;r=.36+.20*rng.random();z=.35+rng.random()*.20
  leaf((math.cos(a)*r,math.sin(a)*r,z),a,.31+rng.random()*.13,.08+rng.random()*.04,1+(k+variant)%3)
 mesh('SHRUB_'+str(variant))
for variant in range(3):
 verts.clear();faces.clear();slots.clear();weights.clear();rng=random.Random(2800+variant);sides=11;rings=6
 profile=[.64,.98,.90,.76,.90,.55]
 phases=[rng.uniform(-.05,.05) for _ in range(sides)]
 for k in range(rings):
  t=k/(rings-1);shift=Vector((.09*math.sin(t*5+variant),.08*math.sin(t*4+variant*2),0))
  for j in range(sides):
   a=j*math.tau/sides+.11*math.sin(k+variant);radius=profile[k]*(.83+.30*rng.random())
   z=t+(rng.uniform(-.045,.045) if k>0 else 0);z=min(z,1)
   v(shift+Vector((math.cos(a)*radius*.70,math.sin(a)*radius*.65,z)),0)
 for k in range(rings-1):
  for j in range(sides):f((k*sides+j,k*sides+(j+1)%sides,(k+1)*sides+(j+1)%sides,(k+1)*sides+j),6)
 f(tuple(reversed(range(sides))),6);f(tuple((rings-1)*sides+j for j in range(sides)),6)
 o=mesh('BLUFF_'+str(variant),False)
 bevel=o.modifiers.new('Rounded eroded arrises','BEVEL');bevel.width=.015;bevel.segments=1;bevel.limit_method='ANGLE';bevel.angle_limit=.45
 normal=o.modifiers.new('Weighted geological normals','WEIGHTED_NORMAL');normal.keep_sharp=True
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/full-visual-overhaul/golf/ResortLandscapeKit.blend'))
for o in bpy.data.objects:o.select_set(o.type=='MESH')
bpy.ops.export_scene.fbx(filepath=str(root/'Unity/Assets/Resources/Course/Resort/BotanicalKit.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=False,bake_anim=False,use_mesh_modifiers=True,path_mode='STRIP')
report={};deps=bpy.context.evaluated_depsgraph_get()
for o in bpy.data.objects:
 if o.type!='MESH':continue
 ev=o.evaluated_get(deps);m=ev.to_mesh();m.calc_loop_triangles();report[o.name]={'export_triangles':len(m.loop_triangles),'export_vertices':len(m.vertices),'source_vertices':len(o.data.vertices),'materials':[x.name for x in m.materials if x]};ev.to_mesh_clear()
(root/'proof/full-visual-overhaul/golf/geology-kit-manifest.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
