import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=r/'work/character-finish32'
bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Envelope.blend'))
o=bpy.data.objects['Kit_Top'];m=o.data;rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
parent=list(range(len(m.vertices)))
def root(a):
 while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
 return a
def join(a,b):parent[root(a)]=root(b)
weld={}
for v in m.vertices:
 k=tuple(round(x,6) for x in v.co)
 if k in weld:join(v.index,weld[k])
 else:weld[k]=v.index
for e in m.edges:join(*e.vertices)
groups={}
for v in m.vertices:groups.setdefault(root(v.index),[]).append(v.index)
groups=sorted(groups.values(),key=len,reverse=True)
rows=[]
for ids in groups:
 lo=[min(m.vertices[i].co[k] for i in ids) for k in range(3)];hi=[max(m.vertices[i].co[k] for i in ids) for k in range(3)]
 rows.append({'count':len(ids),'lo':lo,'hi':hi})
(w/'candidate-components.json').write_text(json.dumps(rows,indent=2))
main=set(groups[0]);collar=next(ids for ids in groups if min(m.vertices[i].co.z for i in ids)>1.30 and max(m.vertices[i].co.z for i in ids)>1.43 and max(m.vertices[i].co.x for i in ids)-min(m.vertices[i].co.x for i in ids)>.15)
faces=[list(f.vertices) for f in m.polygons if all(i in main for i in f.vertices)]
bvh=BVHTree.FromPolygons([v.co for v in m.vertices],faces,all_triangles=True)
changed=0;maxdelta=0
for i in collar:
 v=m.vertices[i];old=v.co.copy();p=v.co.copy()
 hit,n,fi,dist=bvh.find_nearest(p)
 # A visible fold needs clearance above the new torso envelope; preserve neck stand.
 if dist<.042 and (p.z<1.425 or abs(p.x)>.080):
  if n.dot(p-hit)<.006:p=hit+n*.006
 # Front wings fall down and spread gently outward, with a crisp lifted edge.
 front=max(0,min(1,(-p.y-.05)/.09));low=max(0,min(1,(1.42-p.z)/.095))
 p.x*=1+.10*front*low
 p.z-=.008*front*low
 p.y-=.004*front*low
 v.co=p
 if (p-old).length>1e-6:changed+=1;maxdelta=max(maxdelta,(p-old).length)
# Normals must describe the new garment, not the old dented rest shell.
bm=bmesh.new();bm.from_mesh(m);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free();m.update()
if m.has_custom_normals:
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.mesh.customdata_custom_splitnormals_clear()
for p in m.polygons:p.use_smooth=True
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Polo_Collar.blend'))
bpy.ops.export_scene.fbx(filepath=str(r/'Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
(w/'collar-source.json').write_text(json.dumps({'collarVertices':len(collar),'changed':changed,'maxDelta':maxdelta,'vertices':len(m.vertices),'triangles':len(m.polygons)},indent=2))
