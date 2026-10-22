"""Render source triangles with the exact Unity diagnostic camera/world normal light."""
import bpy,pathlib,sys,json,math
from mathutils import Matrix,Vector
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1];version='V3F' if '--fair' in sys.argv else 'V3E' if '--plump' in sys.argv else 'V3D' if '--envelope' in sys.argv else 'V3C' if '--candidate' in sys.argv else 'V3'
contract=json.loads((R/f'proof/full-visual-overhaul/thumb-rig-probe-12/{sex}_source-camera-contract.json').read_text());flat=contract['sourceToWorld'];M=Matrix([[flat[c*4+r] for c in range(4)] for r in range(4)]);up=M.to_3x3().inverted()@Vector((0,1,0));shade=M.to_3x3().inverted()@Vector((.35,.45,.75)).normalized()
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_FistSurface{version}.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'));weight=next((float(a.split('=')[1]) for a in sys.argv if a.startswith('--weight=')),1.0)
if weight<1:
 for bone in rig.pose.bones:
  if any(bone.name.startswith(side+d) for side in ('Left','Right') for d in ('Thumb','Index','Middle','Ring','Little')):
   bone.rotation_quaternion=bone.rotation_quaternion.slerp(type(bone.rotation_quaternion)((1,0,0,0)),1-weight);bone.location*=weight;bone.scale=Vector((1,1,1)).lerp(bone.scale,weight)
 if body.data.shape_keys:
  for key in body.data.shape_keys.key_blocks:
   if key.name.startswith('Hero_Fist_'):key.value=weight
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();H=rig.data.bones['LeftHand'].matrix_local.inverted()@rig.matrix_world.inverted()@body.matrix_world;region={g.index for g in body.vertex_groups if g.name in ('LeftHand','LeftLowerArm') or any(g.name.startswith('Left'+d) for d in ('Thumb','Index','Middle','Ring','Little'))}
base=[H@v.co for v in body.data.vertices];faces=[tuple(f.vertices) for f in mesh.polygons if all(-.03<base[i].y<.25 and abs(base[i].x)<.14 and abs(base[i].z)<.1 and sum(g.weight for g in body.data.vertices[i].groups if g.group in region)>.2 for i in f.vertices)]
attr=body.data.attributes.get('Hero_Fist_PosedNormal_Left');authoredN=[x.vector.copy() for x in attr.data] if attr else None
geo=bpy.data.meshes.new('Exact source posed triangles');geo.from_pydata([v.co for v in mesh.vertices],[],faces);geo.update();o=bpy.data.objects.new('Exact source hand',geo);bpy.context.collection.objects.link(o)
for old in list(bpy.data.objects):
 if old!=o:bpy.data.objects.remove(old,do_unlink=True)
for f in geo.polygons:f.use_smooth=True
if any(x in sys.argv for x in ('--envelope','--plump','--fair')):
 normals=[(v.normal.lerp(authoredN[i],weight).normalized() if authoredN and authoredN[i].length>.5 else v.normal.copy()) for i,v in enumerate(geo.vertices)];geo.normals_split_custom_set_from_vertices(normals)
mat=bpy.data.materials.new('Unity diagnostic Lambert');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();links=mat.node_tree.links;out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');links.new(em.outputs[0],out.inputs['Surface']);gn=n.new('ShaderNodeNewGeometry');dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=shade;links.new(gn.outputs['Normal'],dot.inputs[0]);clip=n.new('ShaderNodeMath');clip.operation='MAXIMUM';clip.inputs[1].default_value=0;links.new(dot.outputs['Value'],clip.inputs[0]);scale=n.new('ShaderNodeMath');scale.operation='MULTIPLY_ADD';scale.inputs[1].default_value=.65;scale.inputs[2].default_value=.35;links.new(clip.outputs[0],scale.inputs[0]);color=n.new('ShaderNodeMixRGB');color.blend_type='MULTIPLY';color.inputs[0].default_value=1;color.inputs[1].default_value=(.72,.48,.30,1);links.new(scale.outputs[0],color.inputs[2]);links.new(color.outputs[0],em.inputs['Color']);geo.materials.append(mat)
scene=bpy.context.scene;scene.render.film_transparent=False;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=4;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1;scene.world=bpy.data.worlds.new('Unity diagnostic background');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.04,.059,.086,1)
cam=bpy.data.cameras.new('Unity exact source camera');c=bpy.data.objects.new('Unity exact source camera',cam);scene.collection.objects.link(c);scene.camera=c;cam.type='ORTHO';cam.ortho_scale=contract['orthographicHeight'];target=Vector(contract['target']);outdir=R/'proof/full-visual-overhaul/characters/hand-exact-source-camera';outdir.mkdir(exist_ok=True)
for shot in ('front','side'):
 p=Vector(contract[shot+'Position']);forward=(target-p).normalized();right=forward.cross(up).normalized();actualup=right.cross(forward).normalized();c.matrix_world=Matrix(((right.x,actualup.x,-forward.x,p.x),(right.y,actualup.y,-forward.y,p.y),(right.z,actualup.z,-forward.z,p.z),(0,0,0,1)));filename=f'{sex}_{version}_'+('weight_'+str(round(weight*100)).zfill(3)+'_' if '--series' in sys.argv else '')+f'{shot}.png';scene.render.filepath=str(outdir/filename);bpy.ops.render.render(write_still=True)
print('EXACT_SOURCE_HAND_CAMERA',sex,version,'faces',len(faces),flush=True)
