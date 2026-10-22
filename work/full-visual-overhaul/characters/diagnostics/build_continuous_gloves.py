"""Continuous fitted golf gloves; inherits original garment UV/material paint.
New hand shell topology and deform weights are reused with a1.3mm material offset.
Source-only staging/export; production install waits actual hand deformation PASS.
"""
import bpy,bmesh,pathlib,sys,json
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_ContinuousHandsV2.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.data.pose_position='REST';body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body_'))
with bpy.data.libraries.load(str(R/f'ArtDir/hero/kit/golf/tailoring/source/Golf_{sex}.blend'),link=False) as(src,dst):dst.objects=[n for n in src.objects if 'Glove' in n]
originals=[o for o in dst.objects if o and o.type=='MESH'];stats=[];gloves=[]
print('GLOVE_ORIGINALS',[(o.name,len(o.data.vertices),[m.name for m in o.data.materials]) for o in originals],flush=True)
for side,letter in [('Left','L'),('Right','R')]:
 original=next(o for o in originals if o.name.endswith('_'+letter) or o.name.endswith(letter) or o.name.endswith(side))
 original.data.calc_loop_triangles();oldVertices=[body.matrix_world.inverted()@original.matrix_world@v.co for v in original.data.vertices];oldTriangles=[list(t.vertices) for t in original.data.loop_triangles];tree=BVHTree.FromPolygons(oldVertices,oldTriangles,all_triangles=True)
 H=rig.data.bones[side+'Hand'].matrix_local.inverted()@rig.matrix_world.inverted()@body.matrix_world
 node=body.copy();node.data=body.data.copy();node.name='Kit_Glove_'+letter;bpy.context.collection.objects.link(node)
 bm=bmesh.new();bm.from_mesh(node.data);layer=bm.verts.layers.deform.active;groups={g.index for g in node.vertex_groups if g.name==side+'Hand' or g.name.startswith(side) and any(d in g.name for d in ('Thumb','Index','Middle','Ring','Little'))}
 def hand(v):
  p=H@v.co;return abs(p.x)<.14 and abs(p.z)<.1 and p.y>-.005 and p.y<.25 and sum(w for g,w in v[layer].items() if g in groups)>.25
 remove=[f for f in bm.faces if not all(hand(v) for v in f.verts)];bmesh.ops.delete(bm,geom=remove,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
 plane=H.inverted()@Vector((0,.008,0));normal=H.to_3x3().transposed()@Vector((0,1,0));bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=plane,plane_no=normal,clear_inner=True,dist=1e-6)
 bm.normal_update()
 for v in bm.verts:v.co+=v.normal*.0013
 bm.to_mesh(node.data);bm.free();node.data.update();node.data.materials.clear()
 for m in original.data.materials:node.data.materials.append(m)
 uv=node.data.uv_layers.active or node.data.uv_layers.new(name='OriginalGloveAtlas')
 oldUV=original.data.uv_layers.active
 def bary(p,a,b,c):
  v0=b-a;v1=c-a;v2=p-a;d00=v0.dot(v0);d01=v0.dot(v1);d11=v1.dot(v1);d20=v2.dot(v0);d21=v2.dot(v1);den=d00*d11-d01*d01
  if abs(den)<1e-12:return (1,0,0)
  y=(d11*d20-d01*d21)/den;z=(d00*d21-d01*d20)/den;return (1-y-z,y,z)
 for poly in node.data.polygons:
  poly.use_smooth=True;closest,n,index,d=tree.find_nearest(poly.center)
  if index is not None:poly.material_index=original.data.loop_triangles[index].material_index
  for loopIndex in poly.loop_indices:
   p=node.data.vertices[node.data.loops[loopIndex].vertex_index].co;closest,n,index,d=tree.find_nearest(p)
   if index is None or not oldUV:continue
   tri=original.data.loop_triangles[index];weights=bary(closest,*[oldVertices[i] for i in tri.vertices]);uv.data[loopIndex].uv=sum((oldUV.data[i].uv*w for i,w in zip(tri.loops,weights)),Vector((0,0)))
 gloves.append(node);stats.append({'part':node.name,'vertices':len(node.data.vertices),'triangles':sum(len(p.vertices)-2 for p in node.data.polygons),'restHandSurfaceOffsetMetres':.0013,'UVContract':'nearest original glove triangle barycentric transfer; original semantic material slots retained','skinWeights':'continuous-hand shell weights copied exactly'})
out=R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_ContinuousGolfGlovesV2.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out))
with bpy.data.libraries.load(str(R/f'work/match-anim-set/export/HeroBase_{sex}_MatchAnims.blend'),link=False) as(src,dst):dst.armatures=[rig.data.name]
originalRig=dst.armatures[0];bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT');thumbs=[s+'Thumb'+j for s in ('Left','Right') for j in ('Proximal','Intermediate','Distal')]
for n in thumbs:rig.data.edit_bones[n].use_connect=False
for n in thumbs:rig.data.edit_bones[n].matrix=originalRig.bones[n].matrix_local;rig.data.edit_bones[n].length=originalRig.bones[n].length
for n in thumbs:rig.data.edit_bones[n].use_connect=originalRig.bones[n].use_connect
bpy.ops.object.mode_set(mode='OBJECT');bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for node in gloves:node.select_set(True)
bpy.context.view_layer.objects.active=rig;export=R/f'work/full-visual-overhaul/characters/exports/Gloves/{sex}.fbx';export.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.fbx(filepath=str(export),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='STRIP')
(R/f'proof/full-visual-overhaul/characters/continuous-gloves-{sex}.json').write_text(json.dumps({'sex':sex,'source':str(out),'runtimeRest':'original53; uniform versioned thumb bridge required','parts':stats,'gate':'SOURCE ONLY, not production; actual both-hand golf-grip visual proof required'},indent=2));print('CONTINUOUS_GLOVES_COMPLETE',stats,flush=True)
