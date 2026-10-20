"""One bounded source candidate: accepted Eye13 source + old scoped lid shapes,
with the eye margin's skinning contract corrected to match its Head-only eye.
No base positions/normals/topology/UVs/rig edits. No production Assets writes.
"""
import bpy,bmesh,pathlib,json,math,collections,hashlib
from mathutils import Vector
from mathutils.kdtree import KDTree
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/original-blink-finish';report={}
def ss(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def attr(me):
 return {'positions':hashlib.sha256(str([tuple(v.co) for v in me.vertices]).encode()).hexdigest(),'normals':hashlib.sha256(str([tuple(n.vector) for n in me.corner_normals]).encode()).hexdigest(),'topology':hashlib.sha256(str([(tuple(p.vertices),p.material_index,p.use_smooth) for p in me.polygons]).encode()).hexdigest(),'uv':hashlib.sha256(str([[tuple(u.uv) for u in lay.data] for lay in me.uv_layers]).encode()).hexdigest()}
for sex in ('Male','Female'):
 bpy.ops.wm.open_mainfile(filepath=str(R/f'work/reference-rebuild/original-refinement/{sex}_OriginalSeamBlink.blend'))
 old={name:{'base':[tuple(v.co) for v in bpy.data.objects[name].data.vertices],'shapes':{k.name:[tuple(v.co) for v in k.data] for k in bpy.data.objects[name].data.shape_keys.key_blocks if k.name!='Basis'}} for name in ('Body','ReferenceFeatures')}
 bpy.ops.wm.open_mainfile(filepath=str(R/f'work/reference-rebuild/original-refinement/{sex}_OriginalSeamEyeMaterial.blend'));body=bpy.data.objects['Body'];feat=bpy.data.objects['ReferenceFeatures'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='REST';before={o.name:attr(o.data) for o in (body,feat)};bonesBefore=[(b.name,b.parent.name if b.parent else None,tuple(x for row in b.matrix_local for x in row)) for b in rig.data.bones]
 for ob in (body,feat):
  assert [tuple(v.co) for v in ob.data.vertices]==old[ob.name]['base'],(sex,ob.name,'base differs from old blink source')
  if ob.data.shape_keys:ob.shape_key_clear()
  ob.shape_key_add(name='Basis')
  for name,positions in old[ob.name]['shapes'].items():
   k=ob.shape_key_add(name=name)
   for i,p in enumerate(positions):k.data[i].co=p
   k.value=0
 me=body.data;vs=[v.co.copy() for v in me.vertices];bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();adj=collections.defaultdict(list)
 for e in bm.edges:
  if e.is_boundary and all(v.co.y<-.05 and 1.50<v.co.z<1.64 for v in e.verts):
   a,b=e.verts;adj[a.index].append(b.index);adj[b.index].append(a.index)
 seen=set();rings=[]
 for a in adj:
  if a in seen:continue
  todo=[a];seen.add(a);ids=[]
  while todo:
   i=todo.pop();ids.append(i)
   for j in adj[i]:
    if j not in seen:seen.add(j);todo.append(j)
  if len(ids)>20:rings.append(ids)
 bm.free();assert len(rings)==2,(sex,rings);eyeZ=sum(vs[i].z for ring in rings for i in ring)/sum(len(r) for r in rings);kd=KDTree(sum(len(r) for r in rings))
 for j,i in enumerate(i for ring in rings for i in ring):kd.insert(Vector((vs[i].x,0,vs[i].z)),i)
 kd.balance();oldweights=[{g.group:g.weight for g in v.groups} for v in me.vertices];head=body.vertex_groups['Head'];boneGroups={g.index for g in body.vertex_groups if g.name in rig.data.bones};changed=[];outside=[]
 for i,p in enumerate(vs):
  if p.y>-.05 or abs(p.z-eyeZ)>.045:outside.append(i);continue
  _,nearest,dist=kd.find(Vector((p.x,0,p.z)));amount=1-ss(.004,.016,dist)
  if amount<=0:outside.append(i);continue
  weights={g:w for g,w in oldweights[i].items() if g in boneGroups};h=weights.get(head.index,0);target=h+(1-h)*amount
  if abs(target-h)<1e-8:continue
  scale=(1-target)/max(1e-8,1-h)
  for group,w in weights.items():
   if group!=head.index:
    if w*scale<1e-8:body.vertex_groups[group].remove([i])
    else:body.vertex_groups[group].add([i],w*scale,'REPLACE')
  head.add([i],target,'REPLACE');changed.append({'vertex':i,'distanceMetres':dist,'oldHead':h,'newHead':target})
 bpy.context.view_layer.update();after={o.name:attr(o.data) for o in (body,feat)};assert before==after,(sex,before,after)
 bonesAfter=[(b.name,b.parent.name if b.parent else None,tuple(x for row in b.matrix_local for x in row)) for b in rig.data.bones];assert bonesBefore==bonesAfter
 newweights=[{g.group:g.weight for g in v.groups} for v in me.vertices];assert all(oldweights[i]==newweights[i] for i in outside)
 assert all({g:w for g,w in oldweights[i].items() if g not in boneGroups}=={g:w for g,w in newweights[i].items() if g not in boneGroups} for i in range(len(vs)))
 maximumError=max(abs(sum(w for g,w in weights.items() if g in boneGroups)-1) for weights in newweights);assert maximumError<1e-6,(sex,maximumError)
 assert all(abs(newweights[i].get(head.index,0)-1)<1e-7 for ring in rings for i in ring)
 bpy.ops.wm.save_as_mainfile(filepath=str(O/f'{sex}_OriginalSeamBlinkFinish1.blend'))
 for ob in bpy.context.scene.objects:ob.select_set(ob.name in ('Body','ReferenceFeatures') or ob.type=='ARMATURE')
 bpy.context.view_layer.objects.active=body
 bpy.ops.export_scene.fbx(filepath=str(O/f'{sex}_OriginalSeamBlinkFinish1.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=False,mesh_smooth_type='OFF',add_leaf_bones=False,bake_anim=False,path_mode='STRIP',use_armature_deform_only=False)
 report[sex]={'source':str(R/f'work/reference-rebuild/original-refinement/{sex}_OriginalSeamEyeMaterial.blend'),'candidate':str(O/f'{sex}_OriginalSeamBlinkFinish1.blend'),'reuse':'Prior blink11 half/full positions; corrected local Head skinning contract rather than another closure-shape approximation','sourceBaseAttributesExact':before==after,'attributes':before,'bonesRestHierarchyExact':bonesBefore==bonesAfter,'boneCount':len(bonesBefore),'bodyVertices':len(me.vertices),'featureVertices':len(feat.data.vertices),'affectedWeightVertices':len(changed),'weightFullPinRadiusMetres':.004,'weightTransitionEndMetres':.016,'outsideWeightVerticesExact':len(outside),'maxWeightSumError':maximumError,'boundaryHeadWeights':[1,1],'shapeNames':['Hero_Blink_Half','Hero_Blink'],'runtimeFeatureFullRetreatFactor':2,'changedWeightVertices':changed}
 (O/'blink-finish1-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('BLINK_FINISH1',sex,len(changed),maximumError)
