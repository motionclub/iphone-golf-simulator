import bpy,json,pathlib
p=pathlib.Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(p/'vendor/polyhaven/fir_tree_01/fir_tree_01_1k.blend'))
for o in bpy.data.objects:
 if o.name in ['fir_tree_01_a_LOD2','fir_tree_01_geometry_nodes']:
  print(o.name)
  if o.type=='MESH':print('ATTRS',[(a.name,a.data_type,a.domain,len(a.data)) for a in o.data.attributes]);print('MATS',[(i,m.name,sum(len(f.vertices)-2 for f in o.data.polygons if f.material_index==i)) for i,m in enumerate(o.data.materials)])
for ng in bpy.data.node_groups:
 if ng.name=='fir_tree_01':
  for n in ng.nodes:
   if n.type in ['COLLECTION_INFO','SWITCH','OBJECT_INFO'] or n.bl_idname.startswith('GeometryNodeCollection'):print(n.name,n.bl_idname,[(s.name,str(s.default_value)) for s in n.inputs if hasattr(s,'default_value')])
for m in bpy.data.materials:
 print('MATERIAL',m.name)
 for n in m.node_tree.nodes if m.node_tree else []:
  if n.type=='TEX_IMAGE':print('IMAGE',n.name,n.image.name if n.image else '',n.image.filepath if n.image else '')
