"""Refine the shared kit into organic branch masses and feathered palms; separate candidate source."""
import bpy,math,random,json
from pathlib import Path
from mathutils import Vector
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
bpy.ops.wm.open_mainfile(filepath=str(root/'work/full-visual-overhaul/golf/ResortGeologyKit.blend'))
for name in ['PINE','PALM']:
 o=bpy.data.objects.get(name)
 if o:bpy.data.objects.remove(o,do_unlink=True)
verts=[];faces=[];slots=[];weights=[];pivots=[];CURRENT_PIVOT=-1
def reset():verts.clear();faces.clear();slots.clear();weights.clear();pivots.clear()
def v(p,w=0):verts.append(tuple(p));weights.append(w);pivots.append(CURRENT_PIVOT);return len(verts)-1
def f(ids,slot):faces.append(tuple(ids));slots.append(slot)
def tube(a,b,r1,r2,slot=0,sides=6):
 a=Vector(a);b=Vector(b);d=(b-a).normalized();u=d.cross(Vector((1,0,0)))
 if u.length<.01:u=d.cross(Vector((0,1,0)))
 u.normalize();w=d.cross(u);s=len(verts)
 for c,r in [(a,r1),(b,r2)]:
  for j in range(sides):v(c+(u*math.cos(j*math.tau/sides)+w*math.sin(j*math.tau/sides))*r)
 for j in range(sides):f((s+j,s+(j+1)%sides,s+sides+(j+1)%sides,s+sides+j),slot)
 f(tuple(s+j for j in reversed(range(sides))),slot);f(tuple(s+sides+j for j in range(sides)),slot)
def lobe(c,scale,rot,slot,seed):
 global CURRENT_PIVOT
 previous=CURRENT_PIVOT;CURRENT_PIVOT=c[2]
 rng=random.Random(seed);c=Vector(c);s=len(verts);sides=7;rings=3
 for k in range(rings+1):
  phi=k*math.pi/rings
  for j in range(sides):
   a=j*math.tau/sides+rot;radius=1+(rng.random()-.5)*.30
   p=Vector((math.sin(phi)*math.cos(a)*scale[0]*radius,math.sin(phi)*math.sin(a)*scale[1]*radius,math.cos(phi)*scale[2]*radius))
   # A small skew keeps branch masses from becoming stacked symmetric cones.
   p.x+=p.z*.30;v(c+p,.25)
 for k in range(rings):
  for j in range(sides):f((s+k*sides+j,s+k*sides+(j+1)%sides,s+(k+1)*sides+(j+1)%sides,s+(k+1)*sides+j),slot)
 CURRENT_PIVOT=previous
def make(name):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
 for n in ['RESORT_BARK','RESORT_LEAF_DARK','RESORT_LEAF_MID','RESORT_LEAF_LIGHT']:me.materials.append(bpy.data.materials[n])
 for p,slot in zip(me.polygons,slots):p.material_index=slot;p.use_smooth=True
 col=me.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
 for c,w in zip(col.data,weights):c.color=(w,.28,0,1)
 dummy=me.uv_layers.new(name='UVMap');pivot=me.uv_layers.new(name='BotanicalPivot')
 for poly in me.polygons:
  for loop in poly.loop_indices:pivot.data[loop].uv=(pivots[me.loops[loop].vertex_index],0)
 o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);return o
# A wind-shaped maritime evergreen, with separate asymmetrical branch fans.
reset();tube((0,0,0),(.028,-.015,.98),.042,.009,sides=8)
rng=random.Random(261017)
for k in range(14):
 z=.28+k*.046;a=k*2.39996+.25*math.sin(k);reach=.54*(1-(z-.28)*.75)
 reach*=.82+rng.random()*.34;d=Vector((math.cos(a),math.sin(a),0));c=d*reach+Vector((.02,0,z))
 tube((0,0,z+.065),c,.012,.004,sides=5)
 lobe(c,(.32*(1-z*.40),.23*(1-z*.25),.115+rng.random()*.043),a,1+k%3,610+k)
 # Smaller overlapping needles extend each branch in one direction.
 if k%3==0:lobe(c+d*.19+Vector((0,0,.025)),(.20,.15,.09),a,2,920+k)
for k in range(3):lobe((.02+.03*math.sin(k),0,.84+k*.053),(.18-k*.045,.17-k*.042,.11-k*.018),k,2+k%2,1010+k)
make('PINE')
# Coconut palm crown: curved individual pinnae grow off a narrow rib, with varied droop.
reset();last=Vector((0,0,0))
for k in range(10):
 t=(k+1)/10;at=Vector((.16*t*t,.035*math.sin(t*math.pi),t*.81));tube(last,at,.045*(1-k*.032),.045*(1-(k+1)*.032),0,8);last=at
CURRENT_PIVOT=.81
for k in range(15):
 a=k*math.tau/15+.11*math.sin(k*1.7);d=Vector((math.cos(a),math.sin(a),0));side=Vector((-d.y,d.x,0));length=.82+(k%3)*.065
 def rib(t):return last+d*(length*t)+Vector((0,0,(.16+(k%2)*.035)*math.sin(t*math.pi)-.22*t*t))
 for j in range(6):tube(rib(j/6),rib((j+1)/6),.007*(1-j/7),.005*(1-j/7),1,3)
 # A folded central lamina fills each frond while feathered pinnae articulate its edge.
 for j in range(7):
  t0=j/7;t1=(j+1)/7;c0=rib(t0);c1=rib(t1)
  w0=.10*math.sin(t0*math.pi)**.65;w1=.10*math.sin(t1*math.pi)**.65
  left0=v(c0-side*w0,t0*.28);mid0=v(c0+Vector((0,0,w0*.12)),t0*.28);right0=v(c0+side*w0,t0*.28)
  left1=v(c1-side*w1,t1*.28);mid1=v(c1+Vector((0,0,w1*.12)),t1*.28);right1=v(c1+side*w1,t1*.28)
  f((left0,left1,mid1,mid0),1+k%3);f((mid0,mid1,right1,right0),1+k%3)

 for j in range(1,10):
  t=j/10;c=rib(t);spread=.155*math.sin(t*math.pi)**.7
  for sign in [-1,1]:
   tip=c+side*(sign*spread)+d*.065+Vector((0,0,-.035*(1-t)))
   ids=[v(c-d*.028,t*.32),v(tip-d*.055,t*.32),v(tip,t*.32),v(c+d*.025,t*.32)]
   f(ids,1+(j+k)%3)
for k in range(4):lobe(last+Vector((.05*math.cos(k*1.6),.05*math.sin(k*1.6),-.025)),(.025,.025,.036),k,0,30+k)
make('PALM')
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/full-visual-overhaul/golf/ResortBotanicalProportioned.blend'))
for o in bpy.data.objects:o.select_set(o.type=='MESH')
bpy.ops.export_scene.fbx(filepath=str(root/'Unity/Assets/Resources/Course/Resort/BotanicalKit.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=False,bake_anim=False,use_mesh_modifiers=True,path_mode='STRIP')
report={}
for o in bpy.data.objects:
 if o.type=='MESH':o.data.calc_loop_triangles();report[o.name]={'triangles':len(o.data.loop_triangles),'vertices':len(o.data.vertices)}
(root/'proof/full-visual-overhaul/golf/geology-kit-manifest.json').write_text(json.dumps(report,indent=2))
print('ORGANIC_KIT_COMPLETE',json.dumps(report))
