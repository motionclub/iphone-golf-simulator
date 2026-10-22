"""Labeled source-geometry photographs, using recorded Unity Ready bone matrices.
These are Blender previews, not actual Unity/player acceptance.
"""
import bpy,pathlib,json,numpy as np
from mathutils import Vector
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/original-blink-finish';names=json.loads((R/'proof/reference-rebuild/character-cloth14-control/poses/female_intro.json').read_text())['parts'][0]['bones'];head=names.index('Head');D=np.array([[1,0,0],[0,0,-1],[0,1,0]])
for sex in ('Male','Female'):
 bpy.ops.wm.open_mainfile(filepath=str(O/f'{sex}_OriginalSeamBlinkFinish1.blend'));sc=bpy.context.scene;body=bpy.data.objects['Body'];feat=bpy.data.objects['ReferenceFeatures'];me=body.data;fm=feat.data;basis=np.asarray([tuple(v.co) for v in me.vertices]);half=np.asarray([tuple(v.co) for v in me.shape_keys.key_blocks['Hero_Blink_Half'].data])-basis;full=np.asarray([tuple(v.co) for v in me.shape_keys.key_blocks['Hero_Blink'].data])-basis;fbasis=np.asarray([tuple(feat.matrix_world@v.co) for v in fm.vertices]);fhalf=np.asarray([tuple(v.co) for v in fm.shape_keys.key_blocks['Hero_Blink_Half'].data])-np.asarray([tuple(v.co) for v in fm.vertices]);ffull=(np.asarray([tuple(v.co) for v in fm.shape_keys.key_blocks['Hero_Blink'].data])-np.asarray([tuple(v.co) for v in fm.vertices]))*2;ws=[[(names.index(body.vertex_groups[g.group].name),g.weight) for g in v.groups if body.vertex_groups[g.group].name in names] for v in me.vertices];record=json.loads((R/f'proof/reference-rebuild/character-motion-matrices17/matrices/{sex.lower()}_Ready_2.json').read_text());part=record['parts'][0];mats=np.asarray(part['skinMatrices']).reshape(-1,4,4);toRoot=np.asarray(part['rendererToRoot']).reshape(4,4)
 def poseBody(ps):
  hp=np.c_[ps,np.ones(len(ps))];out=np.zeros((len(ps),4))
  for i,w in enumerate(ws):
   for bone,weight in w:out[i]+=mats[bone]@hp[i]*weight
  return (D@(toRoot@out.T)[:3]).T
 def poseFeatures(ps):return (D@(toRoot@mats[head]@np.c_[ps,np.ones(len(ps))].T)[:3]).T
 def cloneSurface(source,name):
  mesh=bpy.data.meshes.new(name);mesh.from_pydata([tuple(v.co) for v in source.vertices],[],[p.vertices[:] for p in source.polygons]);mesh.update()
  for m in source.materials:mesh.materials.append(m)
  for p,old in zip(mesh.polygons,source.polygons):p.material_index=old.material_index;p.use_smooth=old.use_smooth
  for lay in source.uv_layers:
   uv=mesh.uv_layers.new(name=lay.name)
   for i,u in enumerate(lay.data):uv.data[i].uv=u.uv
  for attribute in source.color_attributes:
   dest=mesh.color_attributes.new(name=attribute.name,type=attribute.data_type,domain=attribute.domain)
   for i,color in enumerate(attribute.data):dest.data[i].color=color.color
  ob=bpy.data.objects.new(name,mesh);sc.collection.objects.link(ob);return ob
 tempBody=cloneSurface(me,'SourceProofBody');tempFeat=cloneSurface(fm,'SourceProofFeatures')
 for ob in sc.objects:
  if ob.type=='MESH':ob.hide_render=ob not in (tempBody,tempFeat)
 eyeIds={i for p in fm.polygons if 'Sclera' in fm.materials[p.material_index].name for i in p.vertices};posed=poseFeatures(fbasis);eyeCentre=Vector(posed[list(eyeIds)].mean(axis=0));target=eyeCentre+Vector((0,0,-.018));sc.cycles.samples=16;sc.render.resolution_x=480;sc.render.resolution_y=560;sc.render.threads=2;sc.camera.data.ortho_scale=.39
 for pct in (0,25,50,75,100):
  b=pct/100;h=max(0,1-abs(2*b-1));f=max(0,2*b-1);bs=poseBody(basis+half*h+full*f);fs=poseFeatures(fbasis+fhalf*h+ffull*f)
  for ob,ps in ((tempBody,bs),(tempFeat,fs)):
   for v,p in zip(ob.data.vertices,ps):v.co=p
   ob.data.update()
  for angle,delta in [('front',(0,-1.1,.015))]+([('threequarter',(.42,-1.1,.025))] if pct==100 else []):
   sc.camera.location=eyeCentre+Vector(delta);sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'{sex.lower()}_source_ready_blink_{pct}_{angle}.png');bpy.ops.render.render(write_still=True);print('SOURCE_BLINK_PROOF',sex,pct,angle,flush=True)
