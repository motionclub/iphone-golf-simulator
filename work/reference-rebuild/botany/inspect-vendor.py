import bpy,json,pathlib
p=pathlib.Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(p/'vendor/polyhaven/fir_tree_01/fir_tree_01_1k.blend'))
r=[]
for o in bpy.data.objects:
 x={'name':o.name,'type':o.type,'loc':list(o.location),'scale':list(o.scale),'hide':o.hide_render,'collections':[c.name for c in o.users_collection]}
 if o.type=='MESH': x.update(vertices=len(o.data.vertices),polys=len(o.data.polygons),materials=[m.name if m else None for m in o.data.materials],uv=[u.name for u in o.data.uv_layers])
 x['modifiers']=[]
 for m in o.modifiers:
  d={'name':m.name,'type':m.type}
  if m.type=='NODES':d.update(group=m.node_group.name if m.node_group else None,inputs={s.identifier:str(getattr(m,s.identifier,None)) for s in m.node_group.interface.items_tree if s.item_type=="SOCKET"})
  x['modifiers'].append(d)
 r.append(x)
print(json.dumps(r,indent=2))
(p/'vendor-inspection.json').write_text(json.dumps(r,indent=2))
for n in bpy.data.node_groups:
 if n.type=='GEOMETRY':
  print('NODEGROUP',n.name)
  if hasattr(n,'interface'):print('INTERFACE',[(s.name,s.identifier,getattr(s,'default_value',None)) for s in n.interface.items_tree if s.item_type=='SOCKET'])
