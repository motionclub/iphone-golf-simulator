import bpy,math,json
from pathlib import Path
from mathutils import Vector
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=R/'work/reference-rebuild/tennis-horizon2'
bpy.ops.wm.open_mainfile(filepath=str(W/'TennisHorizon2.blend'))
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=3;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
sc.world=bpy.data.worlds.new('Coastal daylight source proof');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.24,.46,.74,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.50
bpy.ops.object.light_add(type='SUN',location=(-300,100,500));sun=bpy.context.object;sun.data.energy=2.2;sun.data.color=(1,.95,.82);sun.data.angle=.13;sun.rotation_euler=(Vector((0,600,20))-sun.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.light_add(type='AREA',location=(50,250,130));fill=bpy.context.object;fill.data.energy=100000;fill.data.color=(.68,.83,1);fill.data.size=300;fill.rotation_euler=(Vector((0,600,20))-fill.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.mesh.primitive_plane_add(size=10000,location=(0,600,-4.03));sea=bpy.context.object;sea.name='Source proof sea plane';mat=bpy.data.materials.new('Source proof turquoise sea');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.018,.37,.48,1);bs.inputs['Roughness'].default_value=.36;bs.inputs['Metallic'].default_value=.10;sea.data.materials.append(mat)
bpy.ops.object.camera_add(location=(0,260,86));cam=bpy.context.object;sc.camera=cam;cam.rotation_euler=(Vector((-15,600,20))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=510
sc.render.resolution_x=1400;sc.render.resolution_y=500;sc.render.resolution_percentage=100;sc.render.filepath=str(W/'ridge-panorama-source.png');bpy.ops.render.render(write_still=True)
# Actual reference14 camera geometry, source islands/sea only. Lighting is source
# proof; the dedicated Unity horizon fog still requires the root actual capture.
cam.data.type='PERSP';cam.data.lens_unit='FOV';cam.data.sensor_fit='VERTICAL';cam.data.angle=math.radians(54);cam.location=(2,-15.3,1.8);cam.rotation_euler=(Vector((0,7,1))-cam.location).to_track_quat('-Z','Y').to_euler()
sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.filepath=str(W/'reference14-horizon-source.png');bpy.ops.render.render(write_still=True)
report={'cameraReference14':{'unityPosition':[2,1.8,-15.3],'unityTarget':[0,1,7],'fovVertical':54},'sourceLighting':'Warm sun/cool fill source inspection; not Unity shader/fog acceptance','views':['ridge-panorama-source.png','reference14-horizon-source.png']}
(W/'source-cameras.json').write_text(json.dumps(report,indent=2)+'\n')
