"""Render actual approved meshes plus production construction maps; no generated imagery."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
R=Path(sys.argv[sys.argv.index('--')+1]);sex=sys.argv[sys.argv.index('--')+2];lod='--lod' in sys.argv
P=R/'proof/full-visual-overhaul/characters';P.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/f'work/match-anim-set/export/HeroBase_{sex}_MatchAnims.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE'); rig.animation_data_clear();rig.data.pose_position='POSE'
# Match the approved relaxed asymmetrical sporty stance while preserving all rest matrices.
for b in rig.pose.bones:b.rotation_mode='QUATERNION';b.rotation_quaternion=(1,0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
# Load corresponding clothing under the identical named rig.
path=R/(f'ArtDir/hero/kit/premium/source/Tennis_{sex}_MatchDistance.blend' if lod else f'work/cloth-overhaul/export/Cloth_{sex}.blend')
with bpy.data.libraries.load(str(path),link=False) as (a,b):b.objects=[n for n in a.objects if n.startswith('Kit_') and not n.endswith('_High')]
for o in b.objects:
 if o is None:continue
 bpy.context.scene.collection.objects.link(o)
 world=o.matrix_world.copy();o.parent=rig;o.matrix_world=world
 for mod in o.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
for o in list(bpy.data.objects):
 if o.type in {'LIGHT','CAMERA'} or 'Collider' in o.name or o.name.startswith('Hair'):bpy.data.objects.remove(o,do_unlink=True)
# Source rig has player bind axes; keep unchanged A pose for repeatable construction proof.
cols={'Kit_Shirt':(.64,.042,.035,1) if sex=='Male' else (.65,.79,.08,1),'Kit_ShirtTrim':(.5,.035,.03,1) if sex=='Male' else (.5,.61,.05,1),'Kit_Shorts':(.055,.12,.43,1) if sex=='Male' else (.9,.9,.86,1),'Kit_ShortsBand':(.045,.09,.30,1) if sex=='Male' else (.78,.78,.75,1),'Kit_Shoe':(.87,.87,.83,1),'Kit_Sole':(.73,.74,.73,1),'Kit_Sock':(.85,.85,.82,1)}
# Real N/M maps on real garment UVs. Neutral data is never painted as garment colour.
for o in bpy.data.objects:
 if o.type!='MESH':continue
 if o.name.startswith('Kit_'):
  tag=o.name[4:].replace('_','');stem=R/f'Unity/Assets/Resources/Tennis/HeroDetail/Kit_{sex}_{tag}'
  mats=[]
  for slot in o.material_slots:
   role=slot.material.name;col=cols.get(role,(.8,.8,.8,1));m=bpy.data.materials.new('PremiumProof_'+sex+'_'+tag+'_'+role);m.use_nodes=True
   nt=m.node_tree;nt.nodes.clear();bs=nt.nodes.new('ShaderNodeBsdfPrincipled');out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
   bs.inputs['Base Color'].default_value=col;bs.inputs['Roughness'].default_value=.76 if role!='Kit_Sole' else .93;bs.inputs['Sheen Weight'].default_value=.22 if role in {'Kit_Shirt','Kit_Shorts','Kit_Sock'} else .04
   maskpath=Path(str(stem)+'_M.png');normpath=Path(str(stem)+'_N.png')
   if maskpath.exists():
    tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(maskpath),check_existing=True);tex.image.colorspace_settings.name='Non-Color'
    sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex.outputs['Color'],sep.inputs['Color'])
    mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[1].default_value=col;mix.inputs[2].default_value=cols.get('Kit_ShirtTrim' if role=='Kit_Shirt' else role,col);nt.links.new(sep.outputs['Blue'],mix.inputs[0])
    cavity=nt.nodes.new('ShaderNodeMath');cavity.operation='MULTIPLY_ADD';cavity.inputs[1].default_value=.25;cavity.inputs[2].default_value=.75;nt.links.new(sep.outputs['Green'],cavity.inputs[0])
    mul=nt.nodes.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;nt.links.new(mix.outputs[0],mul.inputs[1]);nt.links.new(cavity.outputs[0],mul.inputs[2]);nt.links.new(mul.outputs[0],bs.inputs['Base Color'])
   if normpath.exists():
    tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(normpath),check_existing=True);tex.image.colorspace_settings.name='Non-Color'
    normal=nt.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.9;nt.links.new(tex.outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs[0],bs.inputs['Normal'])
   mats.append(m)
  o.data.materials.clear()
  for m in mats:o.data.materials.append(m)
 elif o.name.startswith('Body'):
  for m in o.data.materials:
   m.use_nodes=True;bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
   if bs:
    bs.inputs['Base Color'].default_value=(.64,.40,.24,1) if sex=='Male' else (.73,.48,.31,1)
    bs.inputs['Roughness'].default_value=.65;bs.inputs['Specular IOR Level'].default_value=.28;bs.inputs['Subsurface Weight'].default_value=.025
# Studio floor and flattering real light, not an environment photograph.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.004));floor=bpy.context.object;floor.name='ProofFloor';m=bpy.data.materials.new('WarmPorcelain');m.diffuse_color=(.79,.77,.71,1);floor.data.materials.append(m)
world=bpy.data.worlds.new('PremiumStudio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.79,.84,.92,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4;bpy.context.scene.world=world
for name,pos,energy,size,col in [('Key',(2.7,-4.5,5),600,4,(1,.9,.79)),('Fill',(-3,-2,3.2),350,3.5,(.82,.9,1)),('Edge',(1,2,3.6),480,3,(1,.96,.88))]:
 data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size;data.color=col;o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.render.resolution_x=900;scene.render.resolution_y=1400;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0;scene.view_settings.gamma=1;scene.view_settings.look='AgX - Medium High Contrast';scene.render.film_transparent=False;scene.use_nodes=False;scene.render.image_settings.file_format='PNG'
# Match source faces -Y in Blender; inspect all body vertices to center actual metre-scale source.
body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'))
points=[body.matrix_world@v.co for v in body.data.vertices];zmin=min(v.z for v in points);height=max(v.z for v in points)-zmin;center=Vector((0,0,zmin+height*.51));floor.location.z=zmin-.006
data=bpy.data.cameras.new('CharacterProofCamera');cam=bpy.data.objects.new('CharacterProofCamera',data);bpy.context.collection.objects.link(cam);scene.camera=cam;data.type='ORTHO';data.ortho_scale=height*1.15
poses={'front':Vector((0,-4,height*.52)),'three-quarter':Vector((2,-4,height*.52))}
for label,pos in poses.items():
 cam.location=pos;cam.rotation_euler=(center-pos).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(P/f'{sex.lower()}-studio-{label}{"-lod" if lod else ""}.png');bpy.ops.render.render(write_still=True)
# Facial close-up keeps the exact approved face/paint mesh.
data.ortho_scale=height*.28;center=Vector((0,-.02,zmin+height*.9));cam.location=Vector((.45,-3,height*.9));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.resolution_y=900;scene.render.filepath=str(P/f'{sex.lower()}-studio-face{"-lod" if lod else ""}.png');bpy.ops.render.render(write_still=True)
if not lod:
 bpy.ops.wm.save_as_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_Studio.blend'))
print('STUDIO_RENDER '+sex+' '+str(height)+'m '+('match-distance' if lod else 'full construction'))
