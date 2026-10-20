import bpy,math,random,json,pathlib
from mathutils import Vector
R=pathlib.Path(__file__).resolve().parents[3];W=R/'work/full-visual-overhaul/golf-art-next'
bpy.ops.wm.open_mainfile(filepath=str(R/'ArtDir/golf/source/BotanicalKit.blend'))
for name in ['BLUFF_0','BLUFF_1','BLUFF_2','SHRUB_0','SHRUB_1']:
 ob=bpy.data.objects.get(name)
 if ob:ob.name='BEFORE_'+name;ob.hide_render=True
mats=[bpy.data.materials[n] for n in ['RESORT_BARK','RESORT_LEAF_DARK','RESORT_LEAF_MID','RESORT_LEAF_LIGHT','RESORT_CORAL','RESORT_GOLD','RESORT_STONE']]
V=[];F=[];M=[];A=[]
def reset():V.clear();F.clear();M.clear();A.clear()
def v(p,a=0):V.append(tuple(p));A.append(a);return len(V)-1
def f(ids,slot):F.append(tuple(ids));M.append(slot)
def mesh(name,smooth=True):
 me=bpy.data.meshes.new(name);me.from_pydata(V,[],F);me.update()
 for m in mats:me.materials.append(m)
 for poly,slot in zip(me.polygons,M):poly.material_index=slot;poly.use_smooth=smooth
 c=me.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
 for data,a in zip(c.data,A):data.color=(a,.28,0,1)
 ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);return ob
# Geological shoulder masses retain broad planar faces. No necked pillows or
# repeating brick modules: irregular vertical joints and shallow raked shelves.
import bmesh
for variant in range(3):
 rng=random.Random(45000+variant)
 parts=[]
 def fracture_chunk(name,center,scale):
  verts=[]
  # A wall slab has four broad faces, fractured corners and a sloping crest.
  # Its ledges interrupt on one side; no complete horizontal ring.
  outline=[(-.62,-.32),(-.46,-.49),(.38,-.48),(.64,-.25),(.57,.36),(.30,.48),(-.44,.44),(-.65,.18)]
  for upper in [False,True]:
   for j,(x,y) in enumerate(outline):
    z=(.85+rng.random()*.15) if upper else 0
    x+=(rng.random()-.5)*.09+(variant-1)*z*.09
    y+=(rng.random()-.5)*.07+z*.06
    verts.append(tuple(Vector(center)+Vector((x*scale[0],y*scale[1],z*scale[2]))))
  # Selective shoulders create large oblique fractures in the outward plane.
  for x,y,z in [(-.38,-.53,.33),(.34,-.51,.57),(-.67,.10,.58),(.63,.20,.37)]:
   verts.append(tuple(Vector(center)+Vector((x*scale[0],y*scale[1],z*scale[2]))))
  me=bpy.data.meshes.new(name);me.from_pydata(verts,[],[]);bm=bmesh.new();bm.from_mesh(me)
  bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False)
  bmesh.ops.dissolve_limit(bm,angle_limit=.12,verts=list(bm.verts),edges=list(bm.edges));bm.to_mesh(me);bm.free();me.update();me.materials.append(mats[6])
  ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
  bevel=ob.modifiers.new('Bounded worn corner bevel','BEVEL');bevel.width=.022;bevel.segments=3;bevel.limit_method='ANGLE';bevel.angle_limit=.24;bevel.harden_normals=True
  normal=ob.modifiers.new('Broad planes with smooth arrises','WEIGHTED_NORMAL');normal.keep_sharp=True;normal.weight=60
  bpy.context.view_layer.objects.active=ob;ob.select_set(True)
  for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
  ob.select_set(False);parts.append(ob)
 fracture_chunk('BLUFF_'+str(variant),(0,0,0),(1,1,1))
 fracture_chunk('Offset lower geological shoulder',(.37,-.08,.015),(.62,.79,.46+rng.random()*.12))
 fracture_chunk('Interrupted upper fracture',(-.38,.06,.44+rng.random()*.11),(.58,.74,.32))
 for ob in bpy.context.selected_objects:ob.select_set(False)
 for ob in parts:ob.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();ob=parts[0];ob.name='BLUFF_'+str(variant)
 # Use the same seven-slot palette contract as the foliage kit.
 ob.data.materials.clear()
 for m in mats:ob.data.materials.append(m)
 for face in ob.data.polygons:face.material_index=6
 col=ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
 for c in col.data:c.color=(0,.28,0,1)
# Overlapping curved broad leaves hide the low dark core; the cushion reads as
# a foliage mass with actual leaf silhouettes at both horizon and aerial views.
def cushion(center,scale,slot):
 start=len(V);sides=9;rings=5
 for k in range(rings+1):
  phi=k*math.pi/rings
  for j in range(sides):
   a=j*math.tau/sides;v(Vector(center)+Vector((math.sin(phi)*math.cos(a)*scale[0],math.sin(phi)*math.sin(a)*scale[1],math.cos(phi)*scale[2])),.02)
 for k in range(rings):
  for j in range(sides):f((start+k*sides+j,start+k*sides+(j+1)%sides,start+(k+1)*sides+(j+1)%sides,start+(k+1)*sides+j),slot)
def leaf(at,angle,length,width,rise,slot):
 d=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-d.y,d.x,0));start=len(V);sections=6
 for k in range(sections+1):
  t=k/sections;point=Vector(at)+d*(length*t)+Vector((0,0,rise*math.sin(t*math.pi)-.12*t*t));wide=width*math.sin(t*math.pi)**.70
  v(point-side*wide,.06+t*.08);v(point+Vector((0,0,wide*.38)),.06+t*.08);v(point+side*wide,.06+t*.08)
 for k in range(sections):
  a=start+k*3;f((a,a+3,a+4,a+1),slot);f((a+1,a+4,a+5,a+2),slot)
for variant in range(2):
 reset();rng=random.Random(61030+variant)
 for j in range(5):
  a=j*2.39996;radius=.23+.08*rng.random();at=Vector((math.cos(a)*radius,math.sin(a)*radius,.27+.08*rng.random()))
  cushion(at,(.29,.29,.20),1)
  for k in range(12):
   angle=k*math.tau/12+j*.53+rng.uniform(-.12,.12);length=.44+.15*rng.random();width=.095+.040*rng.random()
   leaf(at+Vector((0,0,.08+.04*rng.random())),angle,length,width,.11+.11*rng.random(),1 if k%9==0 else 3 if k%7==0 else 2)
 mesh('SHRUB_'+str(variant),True)
# Dedicated candidate export excludes the saved prior meshes.
for ob in bpy.data.objects:ob.select_set(ob.type=='MESH' and not ob.name.startswith('BEFORE_'))
bpy.ops.wm.save_as_mainfile(filepath=str(W/'PrimaryLandscapeForms.blend'))
bpy.ops.export_scene.fbx(filepath=str(W/'BotanicalKitPrimaryFormsCandidate.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=False,bake_anim=False,use_mesh_modifiers=True,path_mode='STRIP')
report={};deps=bpy.context.evaluated_depsgraph_get()
for name in ['BLUFF_0','BLUFF_1','BLUFF_2','SHRUB_0','SHRUB_1']:
 ob=bpy.data.objects[name];ev=ob.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();report[name]={'sourceVertices':len(ob.data.vertices),'exportTriangles':len(me.loop_triangles),'boundsMin':[min(v.co[i] for v in me.vertices) for i in range(3)],'boundsMax':[max(v.co[i] for v in me.vertices) for i in range(3)]};ev.to_mesh_clear()
(W/'primary-forms-manifest.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
