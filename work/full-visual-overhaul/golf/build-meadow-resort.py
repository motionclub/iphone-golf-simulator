"""Editable summer oak kit and country-club landmark; no original courses edited."""
import bpy,math,random,json
from mathutils import Vector
from pathlib import Path
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=root/'work/full-visual-overhaul/golf';proof=root/'proof/full-visual-overhaul/golf'
bpy.ops.wm.open_mainfile(filepath=str(w/'ResortCoastalStone.blend'))
mats=[bpy.data.materials[n] for n in ['RESORT_BARK','RESORT_LEAF_DARK','RESORT_LEAF_MID','RESORT_LEAF_LIGHT']]
verts=[];faces=[];slots=[];winds=[];pivots=[]
def reset():verts.clear();faces.clear();slots.clear();winds.clear();pivots.clear()
def v(point,wind=0,pivot=-1):verts.append(tuple(point));winds.append(wind);pivots.append(pivot);return len(verts)-1
def f(indices,slot):faces.append(tuple(indices));slots.append(slot)
def tube(path,radius,rings,sides,slot):
 start=len(verts)
 for k in range(rings+1):
  t=k/rings;c=path(t);axis=(path(min(1,t+.005))-path(max(0,t-.005))).normalized();side=axis.cross(Vector((1,0,0)))
  if side.length<.01:side=axis.cross(Vector((0,1,0)))
  side.normalize();up=axis.cross(side).normalized()
  for j in range(sides):
   a=j*math.tau/sides;v(c+(side*math.cos(a)+up*math.sin(a))*radius(t))
 for k in range(rings):
  for j in range(sides):f((start+k*sides+j,start+k*sides+(j+1)%sides,start+(k+1)*sides+(j+1)%sides,start+(k+1)*sides+j),slot)
 f(tuple(start+j for j in reversed(range(sides))),slot);f(tuple(start+rings*sides+j for j in range(sides)),slot)
def mass(c,scale,slot,seed,sides,rings):
 start=len(verts)
 for k in range(rings+1):
  phi=math.pi*k/rings
  for j in range(sides):
   a=math.tau*j/sides;r=1+.035*math.sin(a*3.1+phi*4+seed)
   v(c+Vector((math.sin(phi)*math.cos(a)*scale[0]*r,math.sin(phi)*math.sin(a)*scale[1]*r,math.cos(phi)*scale[2]*r)),.07,.72)
 for k in range(rings):
  for j in range(sides):f((start+k*sides+j,start+k*sides+(j+1)%sides,start+(k+1)*sides+(j+1)%sides,start+(k+1)*sides+j),slot)
def leaf(at,angle,length,slot):
 direction=Vector((math.cos(angle),math.sin(angle),.18));side=Vector((-direction.y,direction.x,0));start=len(verts)
 for j in range(4):
  t=j/3;c=at+direction*length*t+Vector((0,0,-.10*t*t));width=.043*math.sin(math.pi*t)
  v(c-side*width,.10,.72);v(c+Vector((0,0,width*.45)),.10,.72);v(c+side*width,.10,.72)
 for j in range(3):
  a=start+j*3;f((a,a+3,a+4,a+1),slot);f((a+1,a+4,a+5,a+2),slot)
def make(name):
 m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update()
 for mat in mats:m.materials.append(mat)
 for face,slot in zip(m.polygons,slots):face.material_index=slot;face.use_smooth=True
 color=m.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
 for data,wind in zip(color.data,winds):data.color=(wind,.28,0,1)
 m.uv_layers.new(name='UVMap');pivot=m.uv_layers.new(name='BotanicalPivot')
 for face in m.polygons:
  for loop in face.loop_indices:pivot.data[loop].uv=(pivots[m.loops[loop].vertex_index],0)
 o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o)
for name,count,sides,rings,sprays in [('OAK',14,12,6,4),('OAK_FAR',9,8,4,1)]:
 reset();rng=random.Random(1116)
 tube(lambda t:Vector((.020*math.sin(t*2),.027*t*t,.72*t)),lambda t:.045*(1-.63*t),9,10 if name=='OAK' else 6,0)
 for j in range(7):
  a=j*math.tau/7;direction=Vector((math.cos(a),math.sin(a),0));base=Vector((.015,0,.39+.05*(j%3)))
  tube(lambda t:base+direction*(.51*t)+Vector((0,0,.34*t-.07*t*t)),lambda t:.019*(1-.87*t),4,5 if name=='OAK' else 3,0)
 for j in range(count):
  a=j*2.39996;r=.25+.46*rng.random();c=Vector((math.cos(a)*r,math.sin(a)*r,.72+.22*math.sin(j*1.9)))
  scale=(.32+.13*rng.random(),.31+.12*rng.random(),.25+.08*rng.random())
  mass(c,scale,1 if j%6==0 else 2 if j%3 else 3,j,sides,rings)
  for k in range(sprays):
   angle=a+k*1.9;leaf(c+Vector((math.cos(angle)*scale[0]*.85,math.sin(angle)*scale[1]*.85,.10)),angle,.15+.07*rng.random(),2 if k%3 else 3)
 make(name)
gold=bpy.data.objects['FLOWER_CORAL'].copy();gold.data=gold.data.copy();gold.name='FLOWER_GOLD';bpy.context.collection.objects.link(gold)
for polygon in gold.data.polygons:
 if polygon.material_index==4:polygon.material_index=5
bpy.ops.wm.save_as_mainfile(filepath=str(w/'ResortSummerOak.blend'))
for o in bpy.data.objects:o.select_set(o.type=='MESH')
bpy.ops.export_scene.fbx(filepath=str(w/'BotanicalKitMeadowCandidate.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_anim=False,use_mesh_modifiers=True,path_mode='STRIP')
report={}
for name in ['OAK','OAK_FAR']:
 m=bpy.data.objects[name].data;m.calc_loop_triangles();report[name]={'triangles':len(m.loop_triangles),'vertices':len(m.vertices)}
(proof/'meadow-oak-source16.json').write_text(json.dumps(report,indent=2)+'\n')

# A separate editable country-club source with authored wall/roof/wood/window roles.
bpy.ops.wm.read_factory_settings(use_empty=True)
materials={}
for name,color in {'MEADOW_WALL':(.73,.71,.60,1),'MEADOW_STONE':(.46,.48,.43,1),'MEADOW_ROOF':(.43,.18,.12,1),'MEADOW_WOOD':(.34,.22,.13,1),'MEADOW_GLASS':(.09,.24,.29,1),'MEADOW_TRIM':(.83,.80,.68,1),'MEADOW_GOLD':(.73,.49,.12,1)}.items():
 m=bpy.data.materials.new(name);m.diffuse_color=color;m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=color;m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.55;materials[name]=m
def cube(name,loc,size,mat,bevel=.06):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(materials[mat])
 if bevel:
  b=o.modifiers.new('Crafted bevel','BEVEL');b.width=bevel;b.segments=2;b=o.modifiers.new('Weighted planes','WEIGHTED_NORMAL');b.keep_sharp=True
 return o
def roof(name,c,width,depth,height):
 x,y,z=c;v=[(x-width/2,y-depth/2,z),(x+width/2,y-depth/2,z),(x+width/2,y+depth/2,z),(x-width/2,y+depth/2,z),(x-width*.28,y,z+height),(x+width*.28,y,z+height)]
 m=bpy.data.meshes.new(name);m.from_pydata(v,[],[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)]);m.materials.append(materials['MEADOW_ROOF']);m.update();o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o)
 b=o.modifiers.new('Roof edge relief','SOLIDIFY');b.thickness=.13;b=o.modifiers.new('Roof bevel','BEVEL');b.width=.06;b.segments=2
cube('CLUB_TERRACE',(0,0,.25),(30,15,.5),'MEADOW_STONE',.15)
cube('CLUB_WALL',(0,1,3.4),(23,10,6.4),'MEADOW_WALL',.12)
cube('CLUB_FOUNDATION',(0,1,.68),(23.3,10.3,.5),'MEADOW_STONE')
cube('CLUB_CORNICE',(0,1,6.3),(23.6,10.6,.30),'MEADOW_TRIM')
roof('CLUB_HIPPED_ROOF',(0,1,6.5),25,12,3.1)
for x in [-8,-4,0,4,8]:
 cube('CLUB_RECESSED_GLAZING',(x,-4.025,3.6),(2.6,.16,3.1),'MEADOW_GLASS',.045)
 for dx in [-1.42,0,1.42]:cube('CLUB_WINDOW_MULLION',(x+dx,-4.17,3.6),(.13,.16,3.4),'MEADOW_TRIM',.025)
 for z in [1.95,3.7,5.3]:cube('CLUB_WINDOW_RAIL',(x,-4.17,z),(2.9,.16,.13),'MEADOW_TRIM',.025)
for x in [-12,-6,0,6,12]:
 cube('CLUB_PORTICO_COLUMN',(x,-6,2.35),(.46,.46,4.4),'MEADOW_TRIM')
 cube('CLUB_COLUMN_BASE',(x,-6,.58),(.85,.85,.55),'MEADOW_STONE')
 cube('CLUB_COLUMN_CAP',(x,-6,4.7),(.78,.78,.3),'MEADOW_TRIM')
cube('CLUB_PORTICO_BEAM',(0,-6,4.8),(25,.60,.45),'MEADOW_TRIM')
for x in range(-12,13,2):cube('CLUB_PERGOLA_RAFTER',(x,-5.1,5.02),(.20,3,.18),'MEADOW_WOOD',.025)
for step in range(4):cube('CLUB_WELCOMING_STAIR',(0,-8.3+step*.5,.07+step*.09),(8,1.0,.14+step*.18),'MEADOW_STONE',.025)
cube('CLUB_CLOCK_TOWER',(7.5,2.5,9.4),(3.5,3.5,6.1),'MEADOW_WALL',.08);cube('CLUB_TOWER_CORNICE',(7.5,2.5,12.35),(4,4,.3),'MEADOW_TRIM')
roof('CLUB_TOWER_ROOF',(7.5,2.5,12.5),4.5,4.5,1.8)
for y in [.71,4.29]:
 cube('CLUB_CLOCK_FACE',(7.5,y,10.7),(1.65,.08,1.65),'MEADOW_TRIM',.2)
 cube('CLUB_CLOCK_HAND',(7.5,y-.06,10.87),(.07,.06,.68),'MEADOW_WOOD',.015)
 cube('CLUB_CLOCK_HAND',(7.71,y-.06,10.69),(.48,.06,.07),'MEADOW_WOOD',.015)
for x in [-13.5,13.5]:
 cube('CLUB_TERRACE_PLANTER',(x,-5.5,.85),(1.4,1.4,1.2),'MEADOW_STONE',.12)
for x in [-10,10]:
 cube('CLUB_TERRACE_BENCH',(x,-7.5,1.08),(3,.8,.18),'MEADOW_WOOD')
 for dx in [-1.1,1.1]:cube('CLUB_BENCH_LEG',(x+dx,-7.5,.72),(.18,.55,.7),'MEADOW_WOOD',.025)
bpy.ops.wm.save_as_mainfile(filepath=str(w/'MeadowCountryClub.blend'))
for o in bpy.data.objects:o.select_set(o.type=='MESH')
bpy.ops.export_scene.fbx(filepath=str(w/'MeadowClubCandidate.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_anim=False,use_mesh_modifiers=True,path_mode='STRIP')
print('MEADOW_SOURCE_COMPLETE',json.dumps(report))
