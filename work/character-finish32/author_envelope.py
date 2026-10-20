import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=r/'work/character-finish32'
data=json.loads((w/'baseline/poses/male_intro.json').read_text());body=data['parts'][0];top=next(p for p in data['parts'] if p['name']=='Kit_Top')
def v3(x):return [Vector(x[i:i+3]) for i in range(0,len(x),3)]
bp=v3(body['vertices']);tris=[body['triangles'][i:i+3] for i in range(0,len(body['triangles']),3)]
bvh=BVHTree.FromPolygons(bp,tris,all_triangles=True)
bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Baseline.blend'));old=bpy.data.objects['Kit_Top'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');baseMatCount=sum(len(p.vertices)-2 for p in old.data.polygons if p.material_index==0);bpy.data.objects.remove(old,do_unlink=True)
m=bpy.data.meshes.new('TailoredPolo32');m.from_pydata(top['vertices'] and v3(top['vertices']),[],[top['triangles'][i:i+3] for i in range(0,len(top['triangles']),3)]);m.update()
o=bpy.data.objects.new('Kit_Top',m);bpy.context.collection.objects.link(o)
mat=bpy.data.materials.get('Kit_Shirt');m.materials.append(mat);m.materials.append(bpy.data.materials.get('Kit_ShirtTrim'))
for f in m.polygons:f.material_index=0 if f.index<baseMatCount else 1
uv=m.uv_layers.new(name='UVMap')
for poly in m.polygons:
 poly.use_smooth=True
 for li in poly.loop_indices:
  vi=m.loops[li].vertex_index;uv.data[li].uv=top['uv'][vi*2:vi*2+2]
for name in body['bones']:o.vertex_groups.new(name=name)
maxdist=0;changed=0
bodyNormals=v3(body['normals']);topNormals=v3(top['normals'])
for v in m.vertices:
 hit,n,fi,dist=bvh.find_nearest(v.co);a,b,c=tris[fi]
 bary=barycentric_transform(hit,bp[a],bp[b],bp[c],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
 # Surface correspondence uses the fixed body; move only the garment shell.
 bn=(bodyNormals[a]*bary.x+bodyNormals[b]*bary.y+bodyNormals[c]*bary.z).normalized()
 signed=(v.co-hit).dot(bn)
 # Preserve the constructed collar and front placket; underarm/chest envelope is structural.
 collar=(v.co.z>1.325 and abs(v.co.x)<.145)
 if not collar:
  lining=topNormals[v.index].dot(bn)<0
  ease=.012 if lining else .016
  if v.co.z<1.13:ease += .007*max(0,1-abs(v.co.z-1.06)/.12)
  v.co=hit+bn*max(ease,signed)
 weights={}
 for vi,alpha in zip((a,b,c),bary):
  for slot in range(4):
   bone=body['indices'][vi*4+slot];weight=body['weights'][vi*4+slot]*max(0,alpha)
   if weight:weights[bone]=weights.get(bone,0)+weight
 weights=sorted(weights.items(),key=lambda x:-x[1])[:4];total=sum(x[1] for x in weights)
 for bone,weight in weights:o.vertex_groups[body['bones'][bone]].add([v.index],weight/total,'REPLACE')
 maxdist=max(maxdist,dist)
# Unity source-local X is reflected relative to Blender FBX space.
for v in m.vertices:v.co.x *= -1
m.flip_normals()
mod=o.modifiers.new('Armature','ARMATURE');mod.object=rig
# Imported split normals retain the original geometric shading as the fixed control.
m.normals_split_custom_set_from_vertices([Vector((-n.x,n.y,n.z)) for n in v3(top['normals'])])
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Polo_Envelope.blend'))
bpy.ops.export_scene.fbx(filepath=str(r/'Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
(w/'envelope-source.json').write_text(json.dumps({'vertices':len(m.vertices),'triangles':len(m.polygons),'maxBodyDistance':maxdist,'method':'Same rest geometry and UV; body-surface barycentric bone binding; legacy runtime sleeve fields bypassed on candidate.'},indent=2))
