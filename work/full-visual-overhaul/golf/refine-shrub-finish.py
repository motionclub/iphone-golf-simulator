"""Rounded opaque landscape crown and folded leaf sprays; independent staged source."""
import bpy,math,random,json
from pathlib import Path
from mathutils import Vector
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=root/'work/full-visual-overhaul/golf'
bpy.ops.wm.open_mainfile(filepath=str(w/'ResortPalmDroop.blend'))
for name in ['SHRUB_0','SHRUB_1','BUSH_BROAD']:
 obj=bpy.data.objects.get(name)
 if obj:bpy.data.objects.remove(obj,do_unlink=True)
mats=[bpy.data.materials[n] for n in ['RESORT_BARK','RESORT_LEAF_DARK','RESORT_LEAF_MID','RESORT_LEAF_LIGHT','RESORT_CORAL','RESORT_GOLD','RESORT_STONE']]
verts=[];faces=[];slots=[];winds=[]
def v(p,wind=.10):verts.append(tuple(p));winds.append(wind);return len(verts)-1
def f(ids,slot):faces.append(tuple(ids));slots.append(slot)
def crown(c,scale,slot,seed):
 rng=random.Random(seed);start=len(verts);sides=12;rings=6
 for k in range(rings+1):
  phi=k*math.pi/rings
  for j in range(sides):
   angle=j*math.tau/sides;mod=1+.033*math.sin(j*1.4+k*.7+seed*.1)
   v(Vector(c)+Vector((math.sin(phi)*math.cos(angle)*scale[0]*mod,math.sin(phi)*math.sin(angle)*scale[1]*mod,math.cos(phi)*scale[2]*mod)),.07)
 for k in range(rings):
  for j in range(sides):f((start+k*sides+j,start+k*sides+(j+1)%sides,start+(k+1)*sides+(j+1)%sides,start+(k+1)*sides+j),slot)
def leaf(c,angle,length,width,slot):
 direction=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-direction.y,direction.x,0));start=len(verts);sections=4
 for k in range(sections+1):
  t=k/sections;centre=Vector(c)+direction*length*t+Vector((0,0,.09*math.sin(t*math.pi)-.04*t*t));half=width*math.sin(t*math.pi)**.70
  v(centre-side*half,.15);v(centre+Vector((0,0,half*.28)),.15);v(centre+side*half,.15)
 for k in range(sections):
  a=start+k*3;f((a,a+3,a+4,a+1),slot);f((a+1,a+4,a+5,a+2),slot)
def make(name):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
 for mat in mats:mesh.materials.append(mat)
 for poly,slot in zip(mesh.polygons,slots):poly.material_index=slot;poly.use_smooth=True
 col=mesh.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
 for data,wind in zip(col.data,winds):data.color=(wind,.28,0,1)
 obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);return obj
for name,variant in [('SHRUB_0',0),('SHRUB_1',1),('BUSH_BROAD',2)]:
 verts.clear();faces.clear();slots.clear();winds.clear();rng=random.Random(281130+variant)
 # Interlocking broad rounded masses form a single planted mound, rather than
 # a collection of polyhedron blocks. Thin leaves are secondary articulation.
 crown((0,0,.31),(.43,.41,.31),1,101+variant)
 for k in range(7):
  angle=k*2.39996;reach=.26+.20*rng.random();height=.24+.14*rng.random();centre=(math.cos(angle)*reach,math.sin(angle)*reach,height)
  crown(centre,(.29+.09*rng.random(),.28+.09*rng.random(),.23+.06*rng.random()),1 if k%5==0 else 2,400+variant*30+k)
 for k in range(24):
  angle=k*2.39996;reach=.26+.29*rng.random();height=.33+.19*rng.random()
  leaf((math.cos(angle)*reach,math.sin(angle)*reach,height),angle,.23+.16*rng.random(),.043+.022*rng.random(),2 if k%4 else 3)
 make(name)
bpy.ops.wm.save_as_mainfile(filepath=str(w/'ResortShrubFinish.blend'))
for obj in bpy.data.objects:obj.select_set(obj.type=='MESH')
bpy.ops.export_scene.fbx(filepath=str(w/'BotanicalKitShrubCandidate.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=False,bake_anim=False,use_mesh_modifiers=True,path_mode='STRIP')
report={}
for name in ['SHRUB_0','SHRUB_1','BUSH_BROAD']:
 obj=bpy.data.objects[name];obj.data.calc_loop_triangles();report[name]={'triangles':len(obj.data.loop_triangles),'vertices':len(obj.data.vertices)}
(root/'proof/full-visual-overhaul/golf/shrub-finish-manifest.json').write_text(json.dumps(report,indent=2));print('SHRUB_FINISH_COMPLETE',json.dumps(report))
