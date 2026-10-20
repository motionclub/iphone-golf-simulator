import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
w=Path('work/character-finish32');bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Sleeve.blend'));o=bpy.data.objects['Kit_Top'];rig=next(a for a in bpy.data.objects if a.type=='ARMATURE');m=o.data
d=json.loads((w/'baseline/poses/male_intro.json').read_text())['parts'][0];bp=[Vector((-d['vertices'][i],*d['vertices'][i+1:i+3])) for i in range(0,len(d['vertices']),3)];bn=[Vector((-d['normals'][i],*d['normals'][i+1:i+3])) for i in range(0,len(d['normals']),3)];bt=[d['triangles'][i:i+3][::-1] for i in range(0,len(d['triangles']),3)];tree=BVHTree.FromPolygons(bp,bt,all_triangles=True)
bm=bmesh.new();bm.from_mesh(m);components=[];remaining=set(bm.verts)
while remaining:
 todo=[remaining.pop()];component=set(todo)
 while todo:
  v=todo.pop()
  for e in v.link_edges:
   q=e.other_vert(v)
   if q in remaining:remaining.remove(q);component.add(q);todo.append(q)
 components.append(component)
main=max(components,key=len);kill=[]
for f in bm.faces:
 if f.verts[0] not in main:continue
 hit,n,fi,dist=tree.find_nearest(f.calc_center_median());n=sum((bn[i] for i in bt[fi]),Vector()).normalized()
 if f.normal.dot(n)<.25:kill.append(f)
print('REMOVE INNER',len(kill),'COMPONENTS',sorted([len(c) for c in components],reverse=True)[:8],flush=True)
bmesh.ops.delete(bm,geom=kill,context='FACES');bm.to_mesh(m);bm.free();m.update()
bpy.context.view_layer.objects.active=o;o.select_set(True)
if m.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
# Stabilize only garment binding for the corrective probe; no body weights change.
for v in o.data.vertices:
 groups=sorted([(g.group,g.weight) for g in v.groups],key=lambda x:-x[1])
 if not groups or groups[0][1]>=.70:continue
 total=sum(a for _,a in groups[1:]);largest=groups[0][0]
 for index,amount in groups:o.vertex_groups[index].add([v.index],.70 if index==largest else .30*amount/total,'REPLACE')
for f in o.data.polygons:f.use_smooth=True
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Polo_StableShell.blend'))
bpy.ops.export_scene.fbx(filepath=str(w/'review-project/Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
q=json.loads((w/'refined-queue.json').read_text());q[0]['name']='character-finish32-stable-shell';q[0]['env']['VISUAL_CHARACTER_OUT']=str(w.resolve()/'stable-shell');q[0]['env']['VISUAL_CHARACTER_CLOTH_CLIPS']='SliceApproach,IntroWave,EmoteScuba';(w/'stable-shell-queue.json').write_text(json.dumps(q,indent=2))
