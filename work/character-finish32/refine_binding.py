import bpy,bmesh,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=r/'work/character-finish32'
bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Sleeve.blend'));o=bpy.data.objects['Kit_Top'];m=o.data;rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
adj=[set() for _ in m.vertices]
for e in m.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
seen=set();groups=[]
for i in range(len(adj)):
 if i in seen:continue
 q=[i];seen.add(i);ids=[]
 while q:
  j=q.pop();ids.append(j)
  for k in adj[j]:
   if k not in seen:seen.add(k);q.append(k)
 groups.append(ids)
main=set(max(groups,key=len));marker=o.vertex_groups.new(name='_ConstructionMain');marker.add(list(main),1,'REPLACE');mark=marker.index
bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table();layer=bm.verts.layers.deform.active
selected=[]
for e in bm.edges:
 if not all(v[layer].get(mark,0)>.5 for v in e.verts):continue
 p=(e.verts[0].co+e.verts[1].co)*.5
 if .12<abs(p.x)<.35 and 1.12<p.z<1.43 and e.calc_length()>.007:selected.append(e)
bmesh.ops.subdivide_edges(bm,edges=selected,cuts=1,use_grid_fill=True);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free();m.update()
main=[v.index for v in m.vertices if any(g.group==mark and g.weight>.5 for g in v.groups)];o.vertex_groups.remove(marker)
data=json.loads((w/'collision-poses/poses/male_intro.json').read_text());b=data['parts'][0];bp=[Vector((-b['vertices'][i],*b['vertices'][i+1:i+3])) for i in range(0,len(b['vertices']),3)];bt=[b['triangles'][i:i+3][::-1] for i in range(0,len(b['triangles']),3)];tree=BVHTree.FromPolygons(bp,bt,all_triangles=True)
for i in main:
 v=m.vertices[i];hit,n,fi,dist=tree.find_nearest(v.co);ids=bt[fi];bc=barycentric_transform(hit,*[bp[j] for j in ids],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));weights={}
 for j,a in zip(ids,bc):
  for slot in range(4):
   name=b['bones'][b['indices'][j*4+slot]];value=b['weights'][j*4+slot]*max(0,a);weights[name]=weights.get(name,0)+value
 weights=sorted(weights.items(),key=lambda x:-x[1])[:4];total=sum(v for _,v in weights)
 for g in list(v.groups):o.vertex_groups[g.group].remove([i])
 for name,value in weights:o.vertex_groups[name].add([i],value/total,'REPLACE')
if m.has_custom_normals:bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.mesh.customdata_custom_splitnormals_clear()
for f in m.polygons:f.use_smooth=True
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Polo_Refined.blend'))
bpy.ops.export_scene.fbx(filepath=str(r/'Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
(w/'refined-source.json').write_text(json.dumps({'vertices':len(m.vertices),'triangles':len(m.polygons),'refinedEdges':len(selected),'mainRebound':len(main)},indent=2));print('REFINED',len(m.vertices),len(m.polygons),flush=True)
