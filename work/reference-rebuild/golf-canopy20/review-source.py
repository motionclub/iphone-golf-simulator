import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path.cwd();W=R/'work/reference-rebuild/golf-canopy20'
source=R/'blender/hole_19.blend';bpy.ops.wm.open_mainfile(filepath=str(source))
markers=[]
for o in bpy.data.objects:
 if not o.name.startswith('PLANT_'):continue
 bits=o.name.split('_')
 if len(bits)<5:continue
 try:height=int(bits[3])*.01;radius=int(bits[4])*.01
 except ValueError:continue
 markers.append(dict(name=o.name,kind=bits[2],world=list(o.matrix_world.translation),height=height,radius=radius,worldMatrix=[list(x) for x in o.matrix_world]))
trees=[p for p in markers if p['kind']=='T'];(W/'temple-marker-identity.json').write_text(json.dumps(dict(source=str(source),sourceSHA256=hashlib.sha256(source.read_bytes()).hexdigest(),allMarkers=len(markers),treeCount=len(trees),markers=markers,contract='Candidate prototype only; every PLANT_T name/position/height/radius remains exactly the original. Actual runtime obstacle/collider gate pending root integration.'),indent=2))
print('TREE_MARKERS',len(trees),'ALL_MARKERS',len(markers),'HEIGHTS',[p['height'] for p in trees[:5]],'RADIUS',[p['radius'] for p in trees[:5]],flush=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
objects={}
for label,source in [('before',R/'ArtDir/golf/source/BotanicalKit.blend'),('candidate',W/'GolfTempleCanopy20.blend')]:
 with bpy.data.libraries.load(str(source),link=False) as (src,dst):dst.objects=[n for n in src.objects if n in ['PALM','PALM_FAR']]
 for obj in dst.objects:
  role='far' if obj.name.startswith('PALM_FAR') else 'near';obj.name=label+'_'+role;bpy.context.collection.objects.link(obj);objects[(label,role)]=obj
palette={'RESORT_BARK':(.46,.32,.18),'RESORT_LEAF_DARK':(.17,.36,.21),'RESORT_LEAF_MID':(.26,.46,.23),'RESORT_LEAF_LIGHT':(.34,.54,.28)}
for mat in bpy.data.materials:
 for k,c in palette.items():
  if mat.name.startswith(k):
   mat.use_nodes=True;mat.diffuse_color=(*c,1);bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Roughness'].default_value=.68
height=sorted(p['height'] for p in trees)[len(trees)//2];radius=sorted(p['radius'] for p in trees)[len(trees)//2];height=height or 12.5;radius=radius or 4.65
report=[]
for (label,role),o in objects.items():
 o.data.calc_loop_triangles();piv=o.data.uv_layers[1];weights={loop.vertex_index:piv.data[i].uv.x for i,loop in enumerate(o.data.loops)}
 for v in o.data.vertices:
  centre=weights.get(v.index,-1)
  if centre>=0:v.co.z=centre+(v.co.z-centre)*radius/height
 o.scale=(radius,radius,height);o.hide_render=True
 report.append(dict(label=label,role=role,triangles=len(o.data.loop_triangles),sourceVertices=len(o.data.vertices)))
print('SHAPES',report,'HEIGHT',height,'RADIUS',radius,flush=True)
(W/'budget.json').write_text(json.dumps(dict(treeCount=len(trees),representations=report,medianTrunkScale=height,medianCrownRadiusScale=radius,candidateAllNearTriangles=len(trees)*next(p['triangles'] for p in report if p['label']=='candidate' and p['role']=='near'),candidateAllFarTriangles=len(trees)*next(p['triangles'] for p in report if p['label']=='candidate' and p['role']=='far'),note='Mesh triangles only. Shadows/pass multiplication and selected48yd batching determine actual GPU work; root actual sole-camera capture required.'),indent=2))
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=780;sc.render.resolution_y=880;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
sc.world=bpy.data.worlds.new('Neutral outdoor');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.42,.63,.86,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.45
bpy.ops.mesh.primitive_plane_add(size=100,location=(0,0,-.02));floor=bpy.context.object;mat=bpy.data.materials.new('Neutral ground');mat.diffuse_color=(.4,.46,.3,1);floor.data.materials.append(mat)
bpy.ops.object.light_add(type='SUN',location=(-15,-20,25));sun=bpy.context.object;sun.data.energy=2.3;sun.data.angle=.13;sun.data.color=(1,.94,.84);sun.rotation_euler=(Vector((0,0,5))-sun.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.light_add(type='AREA',location=(10,-14,10));fill=bpy.context.object;fill.data.energy=1500;fill.data.shape='DISK';fill.data.size=12;fill.rotation_euler=(Vector((0,0,5))-fill.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(height*1.15,-height*2.4,height*.86));cam=bpy.context.object;cam.rotation_euler=(Vector((radius*.15,0,height*.51))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=47;sc.camera=cam
for (label,role),o in objects.items():
 for p in objects.values():p.hide_render=True
 o.hide_render=False;sc.render.filepath=str(W/f'{label}-{role}-source.png');bpy.ops.render.render(write_still=True)
