"""Export golf shells and neutral-map inputs; no live assets are installed."""
import bpy,bmesh,sys,json,hashlib,os,numpy as np
from pathlib import Path
from mathutils import Matrix
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];source=Path(bpy.data.filepath);sourceSha=hashlib.sha256(source.read_bytes()).hexdigest()
hair=bpy.data.objects.get('Hair_F') if sex=='Female' else None
if hair:hair.hide_viewport=False;hair.hide_set(False);hair.hide_render=False
rig.animation_data.action=None;rig.data.pose_position='REST'
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
# Remove the hidden tennis kit from this export-only scene. Otherwise Blender
# suffixes the new Kit_Top as .001 and name-based selection exports the old top.
for old in list(bpy.data.objects):
 if old.name.startswith('Kit_'):bpy.data.objects.remove(old,do_unlink=True)
pieces={};rows=[];export=W/'export/kit_v2';export.mkdir(parents=True,exist_ok=True)
def tag(name):
 if name=='Golf_Polo':return 'Top'
 if name.startswith(('Golf_Trousers','Golf_SeatPanel','Golf_PleatedSkort','Golf_InnerShorts','Golf_Belt','Golf_Buckle','Golf_Pocket')):return 'Bottom'
 if name.startswith(('Golf_Cap','Golf_Visor','Golf_CurvedBrim','Golf_BrimStitch')):return 'Head'
 if name=='Golf_Glove_Left':return 'Glove_L'
 if name=='Golf_Glove_Right':return 'Glove_R'
 for s in ['L','R']:
  if name.startswith(('Golf_Shoe_'+s,'Golf_SaddlePanel_'+s,'Golf_Nub_'+s)):return 'Shoe_'+s
 raise RuntimeError('Unmapped golf piece: '+name)
def material(role):
 m=bpy.data.materials.get(role) or bpy.data.materials.new(role);m.use_nodes=True
 rgb=(.12,.12,.13,1) if role=='Kit_Shorts' else (.6,.6,.6,1) if role=='Kit_GolfHardware' else (.93,.93,.93,1)
 m.diffuse_color=rgb;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=rgb;return m
roleNames={'Top':'Kit_Shirt','Bottom':'Kit_Shorts','Head':'Kit_GolfHead','Glove_L':'Kit_GolfGlove','Glove_R':'Kit_GolfGlove','Shoe_L':'Kit_Shoe','Shoe_R':'Kit_Shoe'}
for o in list(bpy.data.objects):
 if o.type!='MESH' or not o.name.startswith('Golf_'):continue
 t=tag(o.name);pieces.setdefault(t,[]).append(o)
 if t=='Head':
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 if o.name=='Golf_Trousers':
  # Solidify emits paired original/inward vertices. Keep the render-facing
  # shell and all turned edges, and omit only its fully hidden inner duplicate.
  # The full construction and lining remain in the draft/proof source.
  n=len(o.data.vertices)//2
  assert len(o.data.vertices)==n*2
  distances=np.array([(o.data.vertices[i].co-o.data.vertices[i+n].co).length for i in range(n)])
  assert np.percentile(distances,99)<.003,'Unexpected trouser solidify ordering'
  bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table()
  remove=[f for f in bm.faces if all(v.index>=n for v in f.verts)]
  print('TROUSER_RENDER_LOD hidden faces',len(remove),'paired displacement mm',float(distances.max()*1000),flush=True)
  bmesh.ops.delete(bm,geom=remove,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(o.data);bm.free()
 # Keep the outer cloth and actual 2 mm turned edge. The hidden, full-area
 # inward duplicate of the polo is a bake source, rather than a render LOD.
 if t=='Top':
  attr=o.data.attributes.get('GolfOuterFace')
  if attr:
   bm=bmesh.new();bm.from_mesh(o.data);layer=bm.faces.layers.int.get('GolfOuterFace');bm.faces.ensure_lookup_table();todo=[f for f in bm.faces if f[layer]==1];main=set(todo)
   while todo:
    f=todo.pop()
    for e in f.edges:
     for g in e.link_faces:
      if g not in main:main.add(g);todo.append(g)
   remove=[f for f in main if f[layer]==0];bmesh.ops.delete(bm,geom=remove,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(o.data);bm.free()
 trim=o.data.attributes.new('GolfTrim','FLOAT','FACE');fabric=o.data.attributes.new('GolfFabric','INT','FACE')
 old=[m.name if m else '' for m in o.data.materials];hardware=o.name.startswith('Golf_Buckle');fid=7 if t=='Top' else 6 if t=='Bottom' else 9 if t=='Head' else 8
 for f in o.data.polygons:
  role=old[min(f.material_index,len(old)-1)] if old else '';tr=1 if 'Trim' in role else 0;id=fid
  if o.name.startswith('Golf_Nub_'):id=3;tr=1
  elif t.startswith('Shoe') and 'Sole' in role:id=4
  trim.data[f.index].value=tr;fabric.data[f.index].value=id
  f.material_index=0
 o.data.materials.clear();o.data.materials.append(material('Kit_GolfHardware' if hardware else roleNames[t]))
for t,objects in pieces.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.hide_set(False);o.hide_viewport=False;o.hide_render=False;o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name='Kit_'+t;o.parent=rig
 # Fresh nonoverlapping low-shell UVs, including all construction components.
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY',ngon_method='BEAUTY');bpy.ops.uv.smart_project(angle_limit=.9,island_margin=.012,area_weight=0);bpy.ops.object.mode_set(mode='OBJECT')
 me=o.data;me.calc_loop_triangles();P=np.array([tuple(v.co) for v in me.vertices]);uv=np.array([tuple(v.uv) for v in me.uv_layers.active.data]);normal=np.array([tuple(n.vector) for n in me.corner_normals]);tri=np.array([tuple(q.vertices) for q in me.loop_triangles]);loops=np.array([tuple(q.loops) for q in me.loop_triangles]);mi=np.array([q.material_index for q in me.loop_triangles]);polys=[q.polygon_index for q in me.loop_triangles]
 prior=export/f'{sex}_Kit_{t}.npz'
 if os.getenv('GOLF_REUSE_UV')=='1' and prior.exists():
  previous=np.load(prior)
  if np.array_equal(previous['tri'],tri) and len(previous['uv'])==len(uv):
   uv=previous['uv'].copy()
   for v,q in zip(me.uv_layers.active.data,uv):v.uv=q
 tr=np.array([me.attributes['GolfTrim'].data[i].value for i in polys]);fid=np.array([me.attributes['GolfFabric'].data[i].value for i in polys]);roles=np.array([m.name for m in me.materials])
 np.savez_compressed(export/f'{sex}_Kit_{t}.npz',P=P,uv=uv,normal=normal,tri=tri,triloops=loops,material=mi,materials=roles,trim=tr,fabric=fid)
 rows.append(dict(tag=t,vertices=len(P),triangles=len(tri),materials=roles.tolist()))
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for t in pieces:bpy.data.objects['Kit_'+t].select_set(True)
hair=bpy.data.objects.get('Hair_F') if sex=='Female' else None
if hair:hair.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(export/f'Golf_{sex}_Kit.fbx'),use_selection=True,global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=False,use_triangles=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='STRIP',object_types={'MESH','ARMATURE'})
bpy.ops.wm.save_as_mainfile(filepath=str(export/f'Golf_{sex}_KitUV.blend'))
report=dict(sex=sex,source=str(source),sourceSha256=sourceSha,parts=rows,totalKitTriangles=sum(x['triangles'] for x in rows),hairIncluded=bool(hair),bones=len(rig.data.bones),status='candidate; UV/maps/import/fit validation pending',poloLOD='primary outer faces and turned edges retained; hidden main inward duplicate removed, collar/placket construction retained')
(W/f'data/export_golf_{sex}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
