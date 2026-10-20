import bpy,math,json
from pathlib import Path
from mathutils import Vector
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=R/'work/reference-rebuild/golf-canopy22'
bpy.ops.wm.read_factory_settings(use_empty=True)
objects={};audit=[]
for label,path in [('control',R/'ArtDir/golf/source/BotanicalKit.blend'),('canopy20',R/'work/reference-rebuild/golf-canopy20/GolfTempleCanopy20.blend'),('candidate',W/'GolfTropicalCanopy22.blend')]:
 with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.objects=[n for n in src.objects if n in ['PALM','PALM_FAR']]
 for obj in dst.objects:
  role='far' if obj.name.startswith('PALM_FAR') else 'near';obj.name=label+'_'+role;bpy.context.collection.objects.link(obj);objects[(label,role)]=obj
  uv=obj.data.uv_layers.get('LeafPivot') or obj.data.uv_layers[1];weights={loop.vertex_index:uv.data[i].uv.x for i,loop in enumerate(obj.data.loops)};height=18.3;radius=10.04
  obj.data.calc_loop_triangles();record=dict(label=label,role=role,triangles=len(obj.data.loop_triangles),vertices=len(obj.data.vertices),pivotSchema=sorted(set(round(x,2) for x in weights.values())),roles=[m.name for m in obj.data.materials])
  for v in obj.data.vertices:
   p=weights.get(v.index,-1)
   if p>=0:v.co.z=p+(v.co.z-p)*radius/height
  obj.scale=(radius,radius,height);bpy.context.view_layer.update();obj.hide_render=True
  world=[obj.matrix_world@v.co for v in obj.data.vertices];record['golfBounds']={'min':[min(v[i] for v in world) for i in range(3)],'max':[max(v[i] for v in world) for i in range(3)]};audit.append(record)
palette={'RESORT_BARK':(.28,.24,.20),'RESORT_LEAF_DARK':(.15,.28,.15),'RESORT_LEAF_MID':(.32,.42,.19),'RESORT_LEAF_LIGHT':(.52,.55,.24)}
for mat in bpy.data.materials:
 for k,c in palette.items():
  if mat.name.startswith(k):
   mat.use_nodes=True;mat.diffuse_color=(*c,1);bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Roughness'].default_value=.68
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.resolution_x=640;sc.render.resolution_y=480;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
sc.world=bpy.data.worlds.new('Outdoor fill');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.42,.63,.86,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.45
bpy.ops.object.light_add(type='SUN',location=(-15,-20,25));sun=bpy.context.object;sun.data.energy=2.3;sun.data.angle=.13;sun.data.color=(1,.94,.84);sun.rotation_euler=(Vector((0,0,5))-sun.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(18,-30,24));cam=bpy.context.object;cam.rotation_euler=(Vector((1.46,0,16.5))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=24.6;sc.camera=cam
for (label,role),o in objects.items():
 for p in objects.values():p.hide_render=True
 o.hide_render=False;sc.render.filepath=str(W/f'{label}-{role}-crown.png');bpy.ops.render.render(write_still=True)
(W/'source-audit.json').write_text(json.dumps({'scale':{'height':18.3,'radius':10.04},'representations':audit,'renderPurpose':'Equal camera, golf proportions, hole22 runtime palette; source silhouette proof, not Unity scene acceptance'},indent=2)+'\n')
