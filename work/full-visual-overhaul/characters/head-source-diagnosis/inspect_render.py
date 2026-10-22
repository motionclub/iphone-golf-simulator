import bpy, pathlib, json, collections
from mathutils import Vector
R=pathlib.Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');O=R/'work/full-visual-overhaul/characters/head-source-diagnosis';report={}
def material(name,c):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.55;return m
for sex in ('Male','Female'):
 path=R/f'work/match-anim-set/export/HeroBase_{sex}_MatchAnims.blend';bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
 body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body_'));face=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Face_'))
 for o in bpy.data.objects:
  o.hide_render=o not in (body,face)
  if o.type=='ARMATURE':
   o.data.pose_position='REST'
 body.hide_render=False;face.hide_render=False;bpy.context.view_layer.update()
 record={'source':str(path),'body':{'name':body.name,'vertices':len(body.data.vertices),'polygons':len(body.data.polygons),'modifiers':[(m.name,m.type) for m in body.modifiers],'shapeKeys':list(body.data.shape_keys.key_blocks.keys()) if body.data.shape_keys else [],'materials':[m.name for m in body.data.materials]},'face':{'name':face.name,'vertices':len(face.data.vertices),'polygons':len(face.data.polygons),'parent':face.parent.name if face.parent else None,'parentType':face.parent_type,'parentBone':face.parent_bone,'modifiers':[(m.name,m.type) for m in face.modifiers],'shapeKeys':list(face.data.shape_keys.key_blocks.keys()) if face.data.shape_keys else []},'faceParts':{}}
 for mi,m in enumerate(face.data.materials):
  polys=[p for p in face.data.polygons if p.material_index==mi];ids={v for p in polys for v in p.vertices};ps=[face.data.vertices[v].co for v in ids]
  record['faceParts'][m.name]={'polygons':len(polys),'vertices':len(ids),'localBounds':[[min(p[k] for p in ps),max(p[k] for p in ps)] for k in range(3)] if ps else []}
 # Boundary graph in posed/rest world space. Component centers identify true eye apertures.
 edgeCounts=collections.Counter(tuple(sorted((p.vertices[i],p.vertices[(i+1)%len(p.vertices)]))) for p in body.data.polygons for i in range(len(p.vertices)))
 adj=collections.defaultdict(set)
 for (a,b),count in edgeCounts.items():
  if count==1:adj[a].add(b);adj[b].add(a)
 seen=set();components=[]
 for start in adj:
  if start in seen:continue
  q=[start];seen.add(start);ids=[]
  while q:
   a=q.pop();ids.append(a)
   for b in adj[a]:
    if b not in seen:seen.add(b);q.append(b)
  ps=[body.matrix_world@body.data.vertices[v].co for v in ids];components.append({'count':len(ids),'worldCentre':list(sum(ps,Vector())/len(ps)),'worldBounds':[[min(p[k] for p in ps),max(p[k] for p in ps)] for k in range(3)]})
 record['bodyBoundaryComponents']=components;report[sex]=record
 eyeids={v for p in face.data.polygons if face.data.materials[p.material_index].name=='Face_Sclera' for v in p.vertices};eyes=[face.matrix_world@face.data.vertices[i].co for i in eyeids];eye=sum(eyes,Vector())/len(eyes)
 # Original sources have world +Z up, -Y forward. Camera is a neutral 3/4 source inspection.
 target=eye+Vector((0,0,.003));camData=bpy.data.cameras.new('DiagnosisCamera');cam=bpy.data.objects.new('DiagnosisCamera',camData);sc.collection.objects.link(cam);cam.location=target+Vector((.33,-.9,.04));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camData.type='ORTHO';camData.ortho_scale=.43;sc.camera=cam
 skin=material('DiagnosisSkin',(.68,.43,.29));body.data.materials.clear();body.data.materials.append(skin)
 for p in body.data.polygons:p.material_index=0
 for i,m in enumerate(list(face.data.materials)):
  n=m.name;c=(.68,.43,.29)
  if 'Sclera' in n:c=(.88,.89,.85)
  elif 'Pupil' in n or 'Limbal' in n or 'Brow' in n or 'Nostril' in n or 'Lid' in n or 'Seam' in n:c=(.06,.032,.018)
  elif 'Iris' in n:c=(.19,.085,.025)
  elif 'Catch' in n:c=(1,1,1)
  elif 'Lip' in n:c=(.53,.22,.16)
  face.data.materials[i]=material('Diagnosis_'+n,c)
 for name,loc,energy,size in [('Key',target+Vector((-1,-1.2,1.2)),35,1.5),('Fill',target+Vector((1,-.8,.5)),18,1.4)]:
  d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
 sc.world=bpy.data.worlds.new('DiagnosisWorld');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.26,.29,.32,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.25
 sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=480;sc.render.resolution_y=540;sc.render.resolution_percentage=100;sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.use_nodes=False;sc.render.film_transparent=False;sc.view_settings.exposure=-1.5;sc.view_settings.gamma=1
 for label,visible in [('skin_only',False),('original_face',True)]:
  face.hide_render=not visible;sc.render.filepath=str(O/f'{sex}_{label}.png');bpy.ops.render.render(write_still=True)
 (O/'source-topology.json').write_text(json.dumps(report,indent=2));print('SOURCE_DIAGNOSIS',sex,body.name,face.name,len(body.data.vertices),len(face.data.vertices),eye[:])
