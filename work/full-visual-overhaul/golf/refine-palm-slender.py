"""Continuous tapered trunks and curved feathered coconut crowns; independent candidate source."""
import bpy,math,random,json
from pathlib import Path
from mathutils import Vector
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
w=root/'work/full-visual-overhaul/golf'
bpy.ops.wm.open_mainfile(filepath=str(w/'ResortShrubFinish.blend'))
for name in ['PALM','PALM_FAR']:
 o=bpy.data.objects.get(name)
 if o:bpy.data.objects.remove(o,do_unlink=True)
mats=[bpy.data.materials[n] for n in ['RESORT_BARK','RESORT_LEAF_DARK','RESORT_LEAF_MID','RESORT_LEAF_LIGHT']]
verts=[];faces=[];slots=[];weights=[];pivots=[]
def reset():verts.clear();faces.clear();slots.clear();weights.clear();pivots.clear()
def v(point,weight=0,pivot=-1):verts.append(tuple(point));weights.append(weight);pivots.append(pivot);return len(verts)-1
def f(indices,slot):faces.append(tuple(indices));slots.append(slot)
def curved_tube(path,radius,rings,sides,slot,pivot=-1,wind=0):
 start=len(verts)
 for k in range(rings+1):
  t=k/rings;c=path(t);tangent=(path(min(1,t+.002))-path(max(0,t-.002))).normalized()
  side=tangent.cross(Vector((1,0,0)))
  if side.length<.01:side=tangent.cross(Vector((0,1,0)))
  side.normalize();up=tangent.cross(side).normalized()
  for j in range(sides):
   a=j*math.tau/sides;r=radius(t)*(1+.015*math.sin(j*3.1+k*.63))
   v(c+(side*math.cos(a)+up*math.sin(a))*r,wind*t,pivot)
 for k in range(rings):
  for j in range(sides):f((start+k*sides+j,start+k*sides+(j+1)%sides,start+(k+1)*sides+(j+1)%sides,start+(k+1)*sides+j),slot)
 f(tuple(start+j for j in reversed(range(sides))),slot);f(tuple(start+rings*sides+j for j in range(sides)),slot)
def blade(path,width,sections,slot,pivot,wind):
 start=len(verts)
 for k in range(sections+1):
  t=k/sections;point=path(t);tangent=(path(min(1,t+.002))-path(max(0,t-.002))).normalized()
  side=tangent.cross(Vector((0,0,1))).normalized();wide=width*math.sin(math.pi*t)**.60
  # Three curved rows give each leaflet a small folded volume, with no alpha cards.
  v(point-side*wide,wind,pivot);v(point+Vector((0,0,wide*.70)),wind,pivot);v(point+side*wide,wind,pivot)
 for k in range(sections):
  a=start+k*3;f((a,a+3,a+4,a+1),slot);f((a+1,a+4,a+5,a+2),slot)
def fruit(c,scale,slot):
 start=len(verts)
 for k in range(6):
  phi=k*math.pi/5
  for j in range(10):
   a=j*math.tau/10;v(c+Vector((math.sin(phi)*math.cos(a)*scale[0],math.sin(phi)*math.sin(a)*scale[1],math.cos(phi)*scale[2])))
 for k in range(5):
  for j in range(10):f((start+k*10+j,start+k*10+(j+1)%10,start+(k+1)*10+(j+1)%10,start+(k+1)*10+j),slot)
def make(name):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
 for mat in mats:me.materials.append(mat)
 for poly,slot in zip(me.polygons,slots):poly.material_index=slot;poly.use_smooth=True
 col=me.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
 for data,weight in zip(col.data,weights):data.color=(weight,.28,0,1)
 me.uv_layers.new(name='UVMap');layer=me.uv_layers.new(name='BotanicalPivot')
 for poly in me.polygons:
  for loop in poly.loop_indices:layer.data[loop].uv=(pivots[me.loops[loop].vertex_index],0)
 obj=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(obj)
 return obj
for name,fronds,pairs,sections,stem_sides,stem_rings in [('PALM',16,18,4,14,28),('PALM_FAR',12,9,3,8,16)]:
 reset();rng=random.Random(271007)
 def trunk(t):return Vector((.145*t*t,.033*math.sin(t*math.pi),.90*t))
 curved_tube(trunk,lambda t:.033*(1-.37*t)*(1+.025*math.sin(t*47)),stem_rings,stem_sides,0)
 crown=trunk(1)
 for k in range(fronds):
  angle=k*math.tau/fronds+.13*math.sin(k*1.7);direction=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-direction.y,direction.x,0))
  length=.80+.16*math.sin(k*2.3)+rng.random()*.09;arch=.25+.17*(k%4)/3;droop=.42+.29*(k%3)/2
  def rib(t):return crown+direction*(length*t)+side*(.035*math.sin(t*math.pi+k*.3))+Vector((0,0,arch*math.sin(t*math.pi)-droop*t*t-.12*t))
  curved_tube(rib,lambda t:.007*(1-.85*t),12 if name=='PALM' else 8,4 if name=='PALM' else 3,2,.90,.12)
  # Individual curved leaflets grow from the rachis, rather than kite patches.
  for j in range(pairs):
   t=.09+.86*(j+.2*rng.random())/pairs;at=rib(t)
   span=(.215+.025*math.sin(k+j*.9))*math.sin(t*math.pi)**.65
   for sign in [-1,1]:
    sweep=.11+.035*math.sin(j*1.4+k);fall=.045+.04*t
    def leaf(u):return at+side*(sign*span*u)+direction*(sweep*u-.025*u*u)+Vector((0,0,-(fall+.06)*u*u+.018*math.sin(u*math.pi)))
    blade(leaf,(.018 if name=='PALM' else .025)*(.75+.25*math.sin(t*math.pi)),sections,1 if k%6==0 else 2,.90,.10+t*.18)
  # The terminal blade continues the curve and closes the feather fan gracefully.
  tip=rib(.93)
  def end_leaf(u):return tip+direction*(length*.09*u)+Vector((0,0,-.04*u*u))
  blade(end_leaf,.014,sections,2,.90,.28)
 for k in range(5):fruit(crown+Vector((.048*math.cos(k*1.4),.048*math.sin(k*1.4),-.037)),(.027,.027,.037),0)
 make(name)
bpy.ops.wm.save_as_mainfile(filepath=str(w/'ResortPalmSlender.blend'))
for obj in bpy.data.objects:obj.select_set(obj.type=='MESH')
bpy.ops.export_scene.fbx(filepath=str(w/'BotanicalKitPalmSlenderCandidate.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=False,bake_anim=False,use_mesh_modifiers=True,path_mode='STRIP')
report={};deps=bpy.context.evaluated_depsgraph_get()
for name in ['PALM','PALM_FAR']:
 obj=bpy.data.objects[name];ev=obj.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();report[name]={'triangles':len(me.loop_triangles),'vertices':len(me.vertices)};ev.to_mesh_clear()
(root/'proof/full-visual-overhaul/golf/palm-hero-manifest.json').write_text(json.dumps(report,indent=2));print('PALM_HERO_COMPLETE',json.dumps(report))
