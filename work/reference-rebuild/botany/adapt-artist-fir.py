import bpy,bmesh,math,json,pathlib,sys
from mathutils import Vector
P=pathlib.Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(P/'vendor/polyhaven/fir_tree_01/fir_tree_01_1k.blend'))
# Correct relative paths for all artist-authored maps.
for image in bpy.data.images:
 if image.filepath.startswith('//textures/'):
  image.filepath=str(P/'vendor/polyhaven/fir_tree_01/textures'/pathlib.Path(image.filepath).name)
# Copy only author LOD2. Preserve point colors and realized corner UV field.
source={l:bpy.data.objects['fir_tree_01_'+l.lower()+'_LOD2'].copy() for l in 'ABC'}
for l,o in source.items():
 o.data=o.data.copy();bpy.context.collection.objects.link(o)
for o in list(bpy.data.objects):
 if o not in source.values():bpy.data.objects.remove(o,do_unlink=True)
outputs=[];audit=[]
for letter,o in source.items():
 uv=o.data.attributes.get('UVMap')
 if uv and not o.data.uv_layers:
  vals=[tuple(v.vector) for v in uv.data];o.data.attributes.remove(uv)
  layer=o.data.uv_layers.new(name='UVMap')
  for v,u in zip(layer.data,vals):v.uv=u[:2]
 # Split wood from twig cards so the small needles never get solidified.
 o.name='SOURCE_'+letter;o.location=(0,0,0)
 bpy.context.view_layer.objects.active=o;o.select_set(True)
 # Retain material-index grouping during reduction.
 for tier,targets in [('NEAR',{'twig':12500,'trunk':1200,'bark':700,'dead':120})]:
  pieces=[]
  for slot,mat in enumerate(o.data.materials):
   part=o.copy();part.data=o.data.copy();bpy.context.collection.objects.link(part)
   bm=bmesh.new();bm.from_mesh(part.data)
   bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=slot],context='FACES')
   bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
   bm.to_mesh(part.data);bm.free()
   if not part.data.polygons:bpy.data.objects.remove(part,do_unlink=True);continue
   key='twig' if 'twig' in mat.name else 'trunk' if 'trunk' in mat.name else 'dead' if 'dead' in mat.name else 'bark'
   count=sum(len(f.vertices)-2 for f in part.data.polygons)
   bpy.context.view_layer.objects.active=part
   if count>targets[key]:
    d=part.modifiers.new('Bounded author LOD adaptation','DECIMATE');d.ratio=targets[key]/count;d.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=d.name)
   # Decimate has a disconnected-component lower bound. Remove only
   # excess entire low-impact fragments with a stable spatial rank.
   # Native UVs/individual needle scale of retained cards remains exact.
   if sum(len(f.vertices)-2 for f in part.data.polygons)>targets[key]*1.15:
    bm=bmesh.new();bm.from_mesh(part.data);remaining=set(bm.verts);components=[]
    while remaining:
     seed=remaining.pop();stack=[seed];group={seed}
     while stack:
      v=stack.pop()
      for e in v.link_edges:
       w=e.other_vert(v)
       if w in remaining:remaining.remove(w);group.add(w);stack.append(w)
     faces=set(f for v in group for f in v.link_faces)
     if faces:
      center=sum((v.co for v in group),Vector())/len(group)
      area=sum(f.calc_area() for f in faces)
      # Outer silhouette twigs rank ahead of small interior fragments.
      rank=(area**.5)*(1+.09*math.hypot(center.x,center.y))
      components.append((rank,group,faces))
    components.sort(key=lambda x:x[0],reverse=True)
    budget=targets[key];kept=0;discard=[]
    for rank,group,faces in components:
     n=sum(len(f.verts)-2 for f in faces)
     if kept+n<=budget:kept+=n
     else:discard.extend(group)
    bmesh.ops.delete(bm,geom=discard,context='VERTS');bm.to_mesh(part.data);bm.free()
   # Foliage alpha clips the actual small needle texture. No changing needle scale.
   part.name='PART';pieces.append(part)
  bpy.ops.object.select_all(action='DESELECT')
  for part in pieces:part.select_set(True)
  bpy.context.view_layer.objects.active=pieces[0];bpy.ops.object.join()
  tree=pieces[0];tree.name='CONIFER_'+letter+('' if tier=='NEAR' else '_FAR')
  # Stand on the original root and preserve artist shape in metres.
  z=min(v.co.z for v in tree.data.vertices)
  for v in tree.data.vertices:v.co.z-=z
  tree.location=(0,0,0);outputs.append(tree)
  tree.data.calc_loop_triangles()
  audit.append({'name':tree.name,'triangles':len(tree.data.loop_triangles),'bounds':[[float(min(v.co[i] for v in tree.data.vertices)) for i in range(3)],[float(max(v.co[i] for v in tree.data.vertices)) for i in range(3)]],'materials':[m.name for m in tree.data.materials]})
 bpy.data.objects.remove(o,do_unlink=True)
# Retain the two closed source shrub crowns + fern, with bounded reduction.
with bpy.data.libraries.load(str(P/'CoastalBotany.blend'),link=False) as (a,b):b.objects=[n for n in a.objects if n in ['SHRUB_A','SHRUB_B','FERN']]
for o in b.objects:
 bpy.context.collection.objects.link(o)
 for tier,target in [('NEAR',1400 if o.name!='FERN' else 1000),('FAR',300 if o.name!='FERN' else 240)]:
  p=o.copy();p.data=o.data.copy();bpy.context.collection.objects.link(p);p.name=o.name+('' if tier=='NEAR' else '_FAR')+'TEMP'
  bpy.context.view_layer.objects.active=p
  count=sum(len(f.vertices)-2 for f in p.data.polygons)
  d=p.modifiers.new('Closed understory far budget','DECIMATE');d.ratio=min(1,target/count);d.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=d.name)
  p['FINAL_NAME']=o.name+('' if tier=='NEAR' else '_FAR');outputs.append(p)
 bpy.data.objects.remove(o,do_unlink=True)
for p in outputs:
 if 'FINAL_NAME' in p:p.name=p['FINAL_NAME'];del p['FINAL_NAME']
# Replace complex source node blends with the exact native diffuse/normal
# textures used by the lightweight runtime. Retain branch/trunk texture roles.
for mat in bpy.data.materials:
 if not mat.name.startswith('fir_tree_01'):continue
 mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear()
 output=nt.nodes.new('ShaderNodeOutputMaterial');bsdf=nt.nodes.new('ShaderNodeBsdfPrincipled');nt.links.new(bsdf.outputs['BSDF'],output.inputs['Surface'])
 bsdf.inputs['Roughness'].default_value=.84
 role='twig' if 'twig' in mat.name else mat.name.replace('fir_tree_01_','') if 'trunk' in mat.name else 'bark'
 def image(kind,noncolor=False):
  im=bpy.data.images.load(str(P/'vendor/polyhaven/fir_tree_01/textures'/('fir_tree_01_'+role+'_'+kind+'_1k.png')),check_existing=True)
  if noncolor:im.colorspace_settings.name='Non-Color'
  n=nt.nodes.new('ShaderNodeTexImage');n.image=im;return n
 diff=image('diff');nt.links.new(diff.outputs['Color'],bsdf.inputs['Base Color'])
 normal=image('nor_gl',True);n=nt.nodes.new('ShaderNodeNormalMap');n.inputs['Strength'].default_value=.45;nt.links.new(normal.outputs['Color'],n.inputs['Color']);nt.links.new(n.outputs['Normal'],bsdf.inputs['Normal'])
 if role=='twig':alpha=image('alpha',True);nt.links.new(alpha.outputs['Color'],bsdf.inputs['Alpha']);bsdf.inputs['Subsurface Weight'].default_value=.035
# Author materials use artist UV rather than masks referenced by missing attribute.
for mat in bpy.data.materials:
 if not mat.use_nodes:continue
 for node in mat.node_tree.nodes:
  if node.type=='ATTRIBUTE' and node.attribute_name=='UVMap':
   uvnode=mat.node_tree.nodes.new('ShaderNodeTexCoord')
   for link in list(mat.node_tree.links):
    if link.from_node==node:mat.node_tree.links.new(uvnode.outputs['UV'],link.to_socket)
 for node in mat.node_tree.nodes:
  if node.type=='TEX_IMAGE':node.interpolation='Linear'
 mat.surface_render_method='DITHERED' if 'twig' in mat.name else 'DITHERED'
# All models overlap at root in reusable source; proof renderer arranges variants.
for p in outputs:p.hide_render=False;p.hide_set(False)
P2=P/'artist2';P2.mkdir(exist_ok=True)
(P2/'source-manifest.json').write_text(json.dumps({'source':'https://polyhaven.com/a/fir_tree_01','license':'CC0','artists':['Rico Cilliers','Rob Tuytel'],'adaptation':'Artist LOD2 with per-material bounded reduction; original needle UV/scale retained','meshes':audit},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P2/'CoastalBotany.blend'))
bpy.ops.object.select_all(action='DESELECT')
for p in outputs:p.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(P2/'CoastalBotany.fbx'),use_selection=True,apply_unit_scale=True,axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,add_leaf_bones=False,path_mode='STRIP',bake_anim=False)
print(json.dumps(audit,indent=2))
