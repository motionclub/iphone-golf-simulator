import bpy,math
from pathlib import Path
from mathutils import Vector
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
proof=root/'proof/full-visual-overhaul/golf'
def setup(target,location,scale,path):
 world=bpy.data.worlds.new('Candidate studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.21,.26,1);world.node_tree.nodes['Background'].inputs[1].default_value=.50;bpy.context.scene.world=world
 for name,energy,loc,size in [('CandidateKey',1100,location+Vector((-3,-3,8)),7),('CandidateFill',800,location+Vector((6,6,5)),8)]:
  d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.size=size;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
 d=bpy.data.cameras.new('CandidateCamera');o=bpy.data.objects.new('CandidateCamera',d);bpy.context.collection.objects.link(o);o.location=location;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=scale;bpy.context.scene.camera=o
 sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=1600;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX';sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'work/full-visual-overhaul/golf/ResortBotanicalOrganic.blend'))
keep=['PINE','PALM','BUSH_BROAD','CANOPY']
for o in bpy.data.objects:
 if o.type=='MESH':
  o.hide_render=o.name not in keep
  if o.name in keep:o.location=(keep.index(o.name)*2.4,0,0)
setup(Vector((3.8,0,.55)),Vector((7,-11,6)),10,proof/'organic-botanical-kit.png')
bpy.ops.wm.open_mainfile(filepath=str(root/'work/full-visual-overhaul/golf/TempleArchitecture.blend'))
for o in bpy.data.objects:o.hide_render=not o.name.startswith('TEMPLE')
for m in bpy.data.materials:
 if m.name.startswith('MAT_TEMPLE'):
  rgb=(.57,.48,.34)
  if 'DARK' in m.name:rgb=(.29,.24,.17)
  if 'TRIM' in m.name:rgb=(.79,.68,.49)
  if 'BLOCK_B' in m.name:rgb=(.64,.55,.39)
  if 'RELIEF' in m.name:rgb=(.42,.33,.20)
  if 'RECESS' in m.name:rgb=(.055,.043,.029)
  m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*rgb,1);b.inputs['Roughness'].default_value=.80
setup(Vector((0,236,35.8)),Vector((38,170,61)),49,proof/'temple-architecture-candidate.png')
print('CANDIDATE_RENDERS_COMPLETE')
