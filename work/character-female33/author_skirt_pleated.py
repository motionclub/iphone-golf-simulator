import bpy,bmesh,numpy as np,json,math
from pathlib import Path
from mathutils import Vector
w=Path('work/character-female33');bpy.ops.wm.open_mainfile(filepath=str(w/'Female_KitBaseline.blend'));o=bpy.data.objects['Kit_Bottom'];rig=next(x for x in bpy.data.objects if x.type=='ARMATURE');P=np.array([v.co for v in o.data.vertices]);adj=[set() for _ in P]
for e in o.data.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
seen=set();groups=[]
for i in range(len(P)):
 if i in seen:continue
 todo=[i];seen.add(i);ids=[]
 while todo:
  a=todo.pop();ids.append(a)
  for b in adj[a]:
   if b not in seen:seen.add(b);todo.append(b)
 groups.append(ids)
groups.sort(key=len,reverse=True);under=set(groups[1]);changed=0

def sm(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return float(t*t*(3-2*t))
for v in o.data.vertices:
 if v.index in under:continue
 p=v.co;low=sm(.955,.66,p.z);rad=Vector((p.x,p.y+.006,0));r=rad.length
 if r>0:
  # Shared displacement preserves the skirt's existing turned hem and pleat edges.
  theta=math.atan2(p.x,-p.y-.006)
  folds=[-.60,.60,-1.45,1.45,-2.30,2.30,math.pi]
  crease=0
  for angle in folds:
   d=(theta-angle+math.pi)%(2*math.pi)-math.pi
   # Broad face panels end in a folded return with a small softened edge.
   crease+=.010*math.exp(-((d/.048)**4))-.003*math.exp(-(((d-.070)/.040)**2))
  ease=(.010-crease)*low;p+=rad.normalized()*ease
 changed+=1
for f in o.data.polygons:f.use_smooth=True
bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update();bpy.context.view_layer.objects.active=o
if o.data.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.ops.wm.save_as_mainfile(filepath=str(w/'Female_Skirt_Pleated.blend'))
bpy.ops.export_scene.fbx(filepath=str(w/'FemaleSkirt.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
print(json.dumps({'sourceVertices':len(P),'garmentAdjusted':changed,'undershortsUnchanged':len(under),'rigChanged':False,'bodyChanged':False,'colorsCustomizable':True}))
