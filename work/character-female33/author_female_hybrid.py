import bpy,bmesh,numpy as np,json
from pathlib import Path
w=Path('work/character-female33')
def components(o):
 adj=[set() for _ in o.data.vertices]
 for e in o.data.edges:
  a,b=e.vertices;adj[a].add(b);adj[b].add(a)
 groups=[];seen=set()
 for i in range(len(adj)):
  if i in seen:continue
  todo=[i];seen.add(i);ids=[]
  while todo:
   a=todo.pop();ids.append(a)
   for b in adj[a]:
    if b not in seen:seen.add(b);todo.append(b)
  groups.append(ids)
 return sorted(groups,key=len,reverse=True)
def collect(o,keep):
 ids=sorted(keep);idx={old:new for new,old in enumerate(ids)};verts=[list(o.data.vertices[i].co) for i in ids];weights=[[(o.vertex_groups[g.group].name,g.weight) for g in o.data.vertices[i].groups] for i in ids];faces=[];uv=[];roles=[]
 for f in o.data.polygons:
  if all(i in keep for i in f.vertices):
   faces.append([idx[i] for i in f.vertices]);roles.append(o.data.materials[f.material_index].name);uv.extend([list(o.data.uv_layers.active.data[i].uv) for i in f.loop_indices])
 return verts,weights,faces,uv,roles
bpy.ops.wm.open_mainfile(filepath=str(w/'Female_Polo_CuffFit.blend'));o=bpy.data.objects['Kit_Top'];g=components(o);trim=collect(o,set(i for a in g[1:] for i in a))
bpy.ops.wm.open_mainfile(filepath=str(w/'Female_Baseline.blend'));o=bpy.data.objects['Kit_Top'];g=components(o);keep=set(i for a in g if len(a)==7322 or len(a) in [235,230,213,141,138] for i in a);base=collect(o,keep);rig=next(x for x in bpy.data.objects if x.type=='ARMATURE');bpy.data.objects.remove(o,do_unlink=True)
P,W,F,UV,R=base;p,wgt,f,uv,r=trim;offset=len(P);P+=p;W+=wgt;F += [[i+offset for i in a] for a in f];UV+=uv;R+=r
m=bpy.data.meshes.new('FemalePoloFittedConstruction');m.from_pydata(P,[],F);m.update();o=bpy.data.objects.new('Kit_Top',m);bpy.context.collection.objects.link(o);roles=list(dict.fromkeys(R))
for name in roles:m.materials.append(bpy.data.materials.get(name) or bpy.data.materials.new(name))
for f,name in zip(m.polygons,R):f.material_index=roles.index(name);f.use_smooth=True
uv=m.uv_layers.new(name='UVMap')
for a,b in zip(uv.data,UV):a.uv=b
for name in dict.fromkeys(n for row in W for n,v in row):o.vertex_groups.new(name=name)
for i,row in enumerate(W):
 for name,value in row:o.vertex_groups[name].add([i],value,'REPLACE')
mod=o.modifiers.new('Armature','ARMATURE');mod.object=rig;o.parent=rig;bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free();m.update();bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Female_Polo_FittedConstruction.blend'));bpy.ops.export_scene.fbx(filepath=str(w/'FemalePoloFittedConstruction.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False);print('DONE',len(P),len(F))
