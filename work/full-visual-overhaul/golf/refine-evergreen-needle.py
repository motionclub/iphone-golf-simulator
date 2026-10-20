"""A tapered spruce canopy with sweeping, pointed opaque needle boughs; isolated source."""
import bpy,math,random,json
from pathlib import Path
from mathutils import Vector
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
w=root/'work/full-visual-overhaul/golf'
bpy.ops.wm.open_mainfile(filepath=str(w/'ResortPalmHero.blend'))
for name in ['PINE','PINE_FAR']:
 obj=bpy.data.objects.get(name)
 if obj:bpy.data.objects.remove(obj,do_unlink=True)
mats=[bpy.data.materials[n] for n in ['RESORT_BARK','RESORT_LEAF_DARK','RESORT_LEAF_MID','RESORT_LEAF_LIGHT']]
verts=[];faces=[];slots=[];weights=[];pivots=[]
def reset():verts.clear();faces.clear();slots.clear();weights.clear();pivots.clear()
def v(point,wind=0,pivot=-1):verts.append(tuple(point));weights.append(wind);pivots.append(pivot);return len(verts)-1
def f(ids,slot):faces.append(tuple(ids));slots.append(slot)
def trunk():
 start=len(verts);sides=10;rings=12
 for k in range(rings+1):
  z=k/rings;centre=Vector((.025*z*z,-.009*z,z))
  for j in range(sides):
   angle=j*math.tau/sides;rad=.034*(1-.75*z);v(centre+Vector((rad*math.cos(angle),rad*math.sin(angle),0)))
 for k in range(rings):
  for j in range(sides):f((start+k*sides+j,start+k*sides+(j+1)%sides,start+(k+1)*sides+(j+1)%sides,start+(k+1)*sides+j),0)
 f(tuple(start+j for j in reversed(range(sides))),0);f(tuple(start+rings*sides+j for j in range(sides)),0)
def core(high):
 start=len(verts);sides=18 if high else 10;rings=19 if high else 12
 for k in range(rings+1):
  z=.23+.78*k/rings
  for j in range(sides):
   angle=j*math.tau/sides;rad=(.40*max(0,1-(z-.23)/.78)**.98+.006)*(1+.055*math.sin(j*2.1+k*.8))
   v((.025*z*z+rad*math.cos(angle),rad*math.sin(angle),z+.005*math.sin(j*3.2+k)),.15)
 for k in range(rings):
  for j in range(sides):f((start+k*sides+j,start+k*sides+(j+1)%sides,start+(k+1)*sides+(j+1)%sides,start+(k+1)*sides+j),1 if k%3==0 else 2)
 f(tuple(start+j for j in reversed(range(sides))),1)
def fan(z,angle,reach,width,depth,high,seed):
 rng=random.Random(seed);direction=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-direction.y,direction.x,0));origin=Vector((.025*z*z,0,z))
 def branch(t):return origin+direction*(.022+reach*t)+side*(.018*math.sin(t*math.pi+seed))+Vector((0,0,.025*math.sin(t*math.pi)-.055*t*t))
 # Thin curved bough carries overlapping folded needle sprays, never broad leaves.
 start=len(verts);rings=6 if high else 4;sides=3
 for k in range(rings+1):
  t=k/rings;centre=branch(t);radius=.010*(1-.80*t)
  for j in range(sides):
   a=j*math.tau/sides;v(centre+side*(math.cos(a)*radius)+Vector((0,0,math.sin(a)*radius)),.20,z)
 for k in range(rings):
  for j in range(sides):f((start+k*sides+j,start+k*sides+(j+1)%sides,start+(k+1)*sides+(j+1)%sides,start+(k+1)*sides+j),1)
 pairs=12 if high else 7
 for k in range(pairs):
  t=.04+.94*k/(pairs-1);centre=branch(t);spread=(.10+.12*reach)*math.sin(t*math.pi)**.40
  for sign in [-1,1]:
   # A narrow swept spear overlaps its neighbours and rises a little along the rib.
   at=centre-direction*.030;tip=centre+direction*(.073+.04*reach)+side*(spread*sign)+Vector((0,0,.012+.01*math.sin(k*1.2)))
   midway=(at+tip)*.5;cross=(tip-at).normalized().cross(Vector((0,0,1)));width=.031 if high else .045
   a=v(at,.20,z);b=v(midway+cross*width,.25,z);c=v(tip,.29,z);d=v(midway-cross*width,.25,z);ridge=v(midway+Vector((0,0,.015)),.24,z)
   if high:
    f((a,b,ridge),2);f((b,c,ridge),2);f((c,d,ridge),2);f((d,a,ridge),2)
   else:f((a,b,c,d),2)
 # Three upward terminal spears make a needle-like tapered bough tip.
 for j in [-1,0,1]:
  at=branch(.89);tip=branch(1)+side*(j*.026)+Vector((0,0,.026));cross=side*.021
  f((v(at-cross,.25,z),v(tip,.29,z),v(at+cross,.25,z)),2)
def make(name):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
 for material in mats:mesh.materials.append(material)
 for poly,slot in zip(mesh.polygons,slots):poly.material_index=slot;poly.use_smooth=True
 attr=mesh.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
 for data,wind in zip(attr.data,weights):data.color=(wind,.28,0,1)
 mesh.uv_layers.new(name='UVMap');layer=mesh.uv_layers.new(name='BotanicalPivot')
 for poly in mesh.polygons:
  for loop in poly.loop_indices:layer.data[loop].uv=(pivots[mesh.loops[loop].vertex_index],0)
 obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);return obj
for name,levels,branches in [('PINE',10,6),('PINE_FAR',8,5)]:
 reset();high=name=='PINE';trunk();core(high);rng=random.Random(281007)
 for k in range(levels):
  z=.26+.68*k/(levels-1);t=(z-.23)/.78;reach=.68*(1-t)**.90+.035
  for j in range(branches):
   angle=j*math.tau/branches+k*2.39996+.05*math.sin(k+j);length=reach*(.88+rng.random()*.18)
   fan(z+.006*math.sin(j*1.9),angle,length,length*.23,.038*(1-t)+.010,high,100+k*branches+j)
 make(name)
bpy.ops.wm.save_as_mainfile(filepath=str(w/'ResortEvergreenNeedle.blend'))
for obj in bpy.data.objects:obj.select_set(obj.type=='MESH')
bpy.ops.export_scene.fbx(filepath=str(w/'BotanicalKitNeedleCandidate.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=False,bake_anim=False,use_mesh_modifiers=True,path_mode='STRIP')
report={};deps=bpy.context.evaluated_depsgraph_get()
for name in ['PINE','PINE_FAR']:
 obj=bpy.data.objects[name];ev=obj.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles();report[name]={'triangles':len(mesh.loop_triangles),'vertices':len(mesh.vertices)};ev.to_mesh_clear()
(root/'proof/full-visual-overhaul/golf/evergreen-needle-manifest.json').write_text(json.dumps(report,indent=2));print('NEEDLE_KIT_COMPLETE',json.dumps(report))
