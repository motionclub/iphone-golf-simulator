import bpy,sys,pathlib,math
from mathutils import Matrix,Vector
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1];restMode='--rest' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(R/(f'ArtDir/hero/kit/premium/source/Premium_{sex}_'+('ContinuousHandsV3.blend' if restMode else 'FistSurfaceV3.blend' if '--corrective' in sys.argv else 'ClosedFistV3.blend'))))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'))
if '--dqs' in sys.argv:
 for modifier in body.modifiers:
  if modifier.type=='ARMATURE':modifier.use_deform_preserve_volume=True
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();eval=body.evaluated_get(deps);mesh=eval.to_mesh();hand=rig.data.bones['LeftHand'];toHand=hand.matrix_local.inverted()@rig.matrix_world.inverted()@body.matrix_world
sourceH=[toHand@v.co for v in body.data.vertices];evalH=(rig.data.bones['LeftHand'].matrix_local if restMode else rig.pose.bones['LeftHand'].matrix).inverted()@rig.matrix_world.inverted()@body.matrix_world
originalCoordinates=[v.co.copy() for v in body.data.vertices];verts=[evalH@v.co for v in mesh.vertices];faces=[];groups=[]
ids={g.index:g.name for g in body.vertex_groups};regionGroups={g.index for g in body.vertex_groups if g.name in ('LeftHand','LeftLowerArm') or any(g.name.startswith('Left'+d) for d in ('Thumb','Index','Middle','Ring','Little'))}
for poly in mesh.polygons:
 if not all(-.030<sourceH[v].y<.24 and abs(sourceH[v].x)<.14 and abs(sourceH[v].z)<.1 and sum(g.weight for g in body.data.vertices[v].groups if g.group in regionGroups)>.2 for v in poly.vertices):continue
 faces.append(tuple(poly.vertices));amount=[0]*6
 for v in poly.vertices:
  for g in body.data.vertices[v].groups:
   for k,d in enumerate(('Thumb','Index','Middle','Ring','Little')):
    if ids[g.group].startswith('Left'+d):amount[k+1]+=g.weight
 group=max(range(6),key=lambda k:amount[k]) if max(amount)>.45 else 0;groups.append(group)
geo=bpy.data.meshes.new('Actual evaluated hand');geo.from_pydata(verts,[],faces);geo.update();o=bpy.data.objects.new('Actual evaluated hand',geo);bpy.context.collection.objects.link(o)
for old in list(bpy.data.objects):
 if old!=o:bpy.data.objects.remove(old,do_unlink=True)
mat=bpy.data.materials.new('Skin clay isolated topology');mat.diffuse_color=(.62,.40,.24,1);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.62,.40,.24,1);bs.inputs['Roughness'].default_value=.48;o.data.materials.append(mat)
if '--retained' in sys.argv:
 with bpy.data.libraries.load(str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_Tennis_ThumbRigV2.blend'),link=False) as (src,dst):dst.meshes=[next(n for n in src.meshes if n.startswith('Body'))]
 sourceMesh=dst.meshes[0]
 sourcePositions={tuple(round(c,6) for c in v.co) for v in sourceMesh.vertices}
 originalFlags=[tuple(round(c,6) for c in v) in sourcePositions for v in originalCoordinates]
 debug=bpy.data.materials.new('Retained original purple');debug.diffuse_color=(.7,.05,.7,1);debug.use_nodes=True;debug.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.7,.05,.7,1);o.data.materials.append(debug)
 for p in o.data.polygons:p.material_index=1 if any(originalFlags[v] for v in p.vertices) else 0
for p in o.data.polygons:p.use_smooth=True
scene=bpy.context.scene;scene.world=bpy.data.worlds.new('Hand proof world');scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.world.color=(.09,.12,.16);scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-1.1
for name,point,power,size in [('Key',(-.22,.3,-.28),15,.20),('Fill',(.22,.12,-.15),6,.25),('Rim',(.1,.2,.2),10,.16)]:
 light=bpy.data.lights.new(name,'AREA');light.energy=power;light.shape='DISK';light.size=size;n=bpy.data.objects.new(name,light);scene.collection.objects.link(n);n.location=point;n.rotation_euler=(Vector((0,.07,0))-n.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.cameras.new('Actual Hand Camera');c=bpy.data.objects.new('Actual Hand Camera',cam);scene.collection.objects.link(c);scene.camera=c;cam.type='ORTHO';cam.ortho_scale=.20
out=R/'proof/full-visual-overhaul/characters/hand-v3-source';out.mkdir(exist_ok=True)
for shot,pos in [('palm',(0,.09,-.35)),('side',(-.35,.08,0)),('back',(0,.08,.35)),('threequarter',(-.25,.15,-.25))]:
 c.location=pos;c.rotation_euler=(Vector((0,.07,0))-c.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(f'{sex}_'+('rest_' if restMode else '')+('dqs_' if '--dqs' in sys.argv else '')+('retained_' if '--retained' in sys.argv else '')+('corrective_' if '--corrective' in sys.argv else '')+f'{shot}.png'));bpy.ops.render.render(write_still=True)
print('HAND_V3_ACTUAL_SOURCE_RENDERED',sex,flush=True)
