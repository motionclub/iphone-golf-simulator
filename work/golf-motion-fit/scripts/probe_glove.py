import bpy,sys,numpy as np
s=sys.argv[-1];r=bpy.data.objects['Rig_'+s];r.animation_data.action=bpy.data.actions['AddressPutt_'+s+'_LH'];bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith('Golf_Glove'):
  co=np.array([tuple(v.co) for v in o.data.vertices]);m=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh();posed=np.array([tuple(v.co) for v in m.vertices]);print('GLOVE_PROBE',o.name,'rest',co.min(0),co.max(0),'pose',posed.min(0),posed.max(0),'materials',set(p.material_index for p in o.data.polygons),'keys',[(k.name,k.value) for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else None,'groups',[(g.name,len([v for v in o.data.vertices if any(x.group==g.index and x.weight>.5 for x in v.groups)])) for g in o.vertex_groups if 'Arm' in g.name or 'Hand' in g.name])
